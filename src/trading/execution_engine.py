"""执行引擎模块"""
from typing import Dict, Optional
from src.trading.exchange_interface import ExchangeInterface
from src.trading.order_manager import OrderManager, OrderStatus
from src.trading.position_manager import PositionManager
from src.strategies.risk_management import RiskManager
from src.utils.logger import setup_logger
from src.utils.helpers import safe_divide

logger = setup_logger(__name__)


class ExecutionEngine:
    """交易执行引擎"""
    
    def __init__(self, exchange_name: str, sandbox: bool = True, 
                 risk_config: Optional[Dict] = None):
        """
        初始化执行引擎
        
        Args:
            exchange_name: 交易所名称
            sandbox: 是否使用测试环境
            risk_config: 风险配置字典
        """
        self.exchange = ExchangeInterface(exchange_name, sandbox)
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager(risk_config or {})
        logger.info("执行引擎初始化完成")
    
    def execute_signal(self, signal: Dict, pair_name: str, 
                      account_balance: float) -> Optional[Dict]:
        """
        执行交易信号
        
        Args:
            signal: 信号字典
            pair_name: 配对名称
            account_balance: 账户余额
        
        Returns:
            执行结果字典
        """
        signal_type = signal.get('signal')
        
        if signal_type == 'hold':
            return None
        
        # 获取资产符号
        asset1 = signal.get('metadata', {}).get('asset1', 'asset1')
        asset2 = signal.get('metadata', {}).get('asset2', 'asset2')
        
        quantity1 = signal.get('quantity1', 0)
        quantity2 = signal.get('quantity2', 0)
        zscore = signal.get('zscore', 0)
        
        # 获取当前价格
        ticker1 = self.exchange.get_ticker(asset1)
        ticker2 = self.exchange.get_ticker(asset2)
        
        if not ticker1 or not ticker2:
            logger.error("无法获取价格信息")
            return None
        
        price1 = ticker1['last']
        price2 = ticker2['last']
        
        # 计算实际交易数量（考虑仓位大小限制）
        if signal_type in ['buy_spread', 'sell_spread']:
            # 计算需要的资金
            cost1 = abs(quantity1) * price1
            cost2 = abs(quantity2) * price2
            total_cost = cost1 + cost2
            
            # 根据账户余额调整仓位大小
            position_size = self.risk_manager.calculate_position_size(account_balance)
            
            if total_cost > position_size:
                # 按比例缩小
                scale = safe_divide(position_size, total_cost)
                quantity1 *= scale
                quantity2 *= scale
                logger.info(f"调整仓位大小: scale={scale:.3f}")
        
        # 确定交易方向
        side1 = 'buy' if quantity1 > 0 else 'sell'
        side2 = 'buy' if quantity2 > 0 else 'sell'
        
        # 创建订单
        order = self.order_manager.create_order(
            pair_name, asset1, asset2,
            side1, side2, abs(quantity1), abs(quantity2),
            order_type='market'
        )
        
        # 执行订单
        try:
            # 执行第一个资产的订单
            order1_result = self.exchange.place_market_order(
                asset1, side1, abs(quantity1)
            )
            
            if order1_result:
                order.exchange_order_id1 = order1_result.get('id')
                order.filled_quantity1 = order1_result.get('filled', abs(quantity1))
                order.filled_price1 = order1_result.get('price', price1)
            
            # 执行第二个资产的订单
            order2_result = self.exchange.place_market_order(
                asset2, side2, abs(quantity2)
            )
            
            if order2_result:
                order.exchange_order_id2 = order2_result.get('id')
                order.filled_quantity2 = order2_result.get('filled', abs(quantity2))
                order.filled_price2 = order2_result.get('price', price2)
            
            # 更新订单状态
            if order1_result and order2_result:
                order.update_status(OrderStatus.FILLED)
                
                # 更新仓位
                if signal_type in ['buy_spread', 'sell_spread']:
                    # 开仓
                    self.position_manager.open_position(
                        pair_name, asset1, asset2,
                        quantity1, quantity2, zscore,
                        order.filled_price1, order.filled_price2
                    )
                elif signal_type == 'close':
                    # 平仓
                    self.position_manager.close_position(
                        pair_name,
                        order.filled_price1, order.filled_price2
                    )
                
                logger.info(f"订单执行成功: {order.order_id}")
                return {
                    'success': True,
                    'order_id': order.order_id,
                    'filled_quantity1': order.filled_quantity1,
                    'filled_quantity2': order.filled_quantity2,
                    'filled_price1': order.filled_price1,
                    'filled_price2': order.filled_price2
                }
            else:
                order.update_status(OrderStatus.REJECTED)
                logger.error(f"订单执行失败: {order.order_id}")
                return {
                    'success': False,
                    'order_id': order.order_id,
                    'error': '订单执行失败'
                }
        
        except Exception as e:
            order.update_status(OrderStatus.REJECTED)
            logger.error(f"执行订单异常: {str(e)}")
            return {
                'success': False,
                'order_id': order.order_id,
                'error': str(e)
            }
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            账户信息字典
        """
        balance = self.exchange.get_balance()
        positions = self.position_manager.get_all_positions()
        total_pnl = self.position_manager.get_total_pnl()
        
        return {
            'balance': balance,
            'open_positions': len(positions),
            'total_pnl': total_pnl,
            'positions': [p.to_dict() for p in positions]
        }

