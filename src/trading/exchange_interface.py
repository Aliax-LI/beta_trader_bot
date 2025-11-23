"""交易所接口模块（CCXT）"""
import ccxt
from typing import Dict, Optional, List
from src.utils.logger import setup_logger
from src.utils.helpers import get_env_var

logger = setup_logger(__name__)


class ExchangeInterface:
    """交易所接口封装类"""
    
    def __init__(self, exchange_name: str, sandbox: bool = True):
        """
        初始化交易所接口
        
        Args:
            exchange_name: 交易所名称
            sandbox: 是否使用测试环境
        """
        self.exchange_name = exchange_name
        self.sandbox = sandbox
        self.exchange = self._create_exchange()
        logger.info(f"交易所接口初始化: {exchange_name}, 沙盒模式: {sandbox}")
    
    def _create_exchange(self) -> ccxt.Exchange:
        """创建交易所实例"""
        exchange_class = getattr(ccxt, self.exchange_name)
        
        config = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        }
        
        if self.sandbox:
            config['sandbox'] = True
        
        # 加载API密钥
        api_key = get_env_var(f"{self.exchange_name.upper()}_API_KEY")
        secret = get_env_var(f"{self.exchange_name.upper()}_SECRET_KEY")
        
        if api_key and secret:
            config['apiKey'] = api_key
            config['secret'] = secret
        
        if self.exchange_name.lower() == 'okx':
            passphrase = get_env_var("OKX_PASSPHRASE")
            if passphrase:
                config['password'] = passphrase
        
        return exchange_class(config)
    
    def get_balance(self) -> Dict[str, float]:
        """
        获取账户余额
        
        Returns:
            余额字典 {symbol: balance}
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance.get('total', {})
        except Exception as e:
            logger.error(f"获取余额失败: {str(e)}")
            return {}
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        获取当前价格
        
        Args:
            symbol: 交易对符号
        
        Returns:
            价格信息字典
        """
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"获取 {symbol} 价格失败: {str(e)}")
            return None
    
    def place_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """
        下市价单
        
        Args:
            symbol: 交易对符号
            side: 方向 ('buy' 或 'sell')
            amount: 数量
        
        Returns:
            订单信息字典
        """
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            logger.info(f"市价单已提交: {symbol} {side} {amount}")
            return order
        except Exception as e:
            logger.error(f"下单失败: {symbol} {side} {amount}, 错误: {str(e)}")
            return None
    
    def place_limit_order(self, symbol: str, side: str, amount: float, 
                         price: float) -> Optional[Dict]:
        """
        下限价单
        
        Args:
            symbol: 交易对符号
            side: 方向 ('buy' 或 'sell')
            amount: 数量
            price: 价格
        
        Returns:
            订单信息字典
        """
        try:
            order = self.exchange.create_limit_order(symbol, side, amount, price)
            logger.info(f"限价单已提交: {symbol} {side} {amount} @ {price}")
            return order
        except Exception as e:
            logger.error(f"下单失败: {symbol} {side} {amount} @ {price}, 错误: {str(e)}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            symbol: 交易对符号
        
        Returns:
            是否成功
        """
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"订单已取消: {order_id}")
            return True
        except Exception as e:
            logger.error(f"取消订单失败: {order_id}, 错误: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            symbol: 交易对符号
        
        Returns:
            订单信息字典
        """
        try:
            return self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            logger.error(f"查询订单失败: {order_id}, 错误: {str(e)}")
            return None
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取未完成订单列表
        
        Args:
            symbol: 交易对符号（可选）
        
        Returns:
            订单列表
        """
        try:
            if symbol:
                return self.exchange.fetch_open_orders(symbol)
            else:
                return self.exchange.fetch_open_orders()
        except Exception as e:
            logger.error(f"获取未完成订单失败: {str(e)}")
            return []

