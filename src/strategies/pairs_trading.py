"""配对交易策略（核心）"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from src.strategies.base_strategy import BaseStrategy
from src.data.data_processor import DataProcessor
from src.strategies.risk_management import RiskManager
from src.utils.math_utils import (
    calculate_correlation,
    calculate_hedge_ratio,
    calculate_zscore,
    calculate_spread
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PairsTradingStrategy(BaseStrategy):
    """配对交易策略"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化配对交易策略
        
        Args:
            config: 策略配置字典
        """
        super().__init__(config)
        
        strategy_config = config.get('pairs_trading', {})
        self.lookback_period = strategy_config.get('lookback_period', 60)
        self.z_entry_threshold = strategy_config.get('z_entry_threshold', 2.0)
        self.z_exit_threshold = strategy_config.get('z_exit_threshold', 0.5)
        self.correlation_threshold = strategy_config.get('correlation_threshold', 0.8)
        
        self.data_processor = DataProcessor(self.lookback_period)
        self.risk_manager = RiskManager(strategy_config)
        
        # 存储配对状态
        self.pair_states = {}  # {pair_name: {hedge_ratio, spread_mean, spread_std, position}}
        
        logger.info(f"配对交易策略初始化完成: lookback={self.lookback_period}, "
                   f"entry_z={self.z_entry_threshold}, exit_z={self.z_exit_threshold}")
    
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """
        验证数据有效性
        
        Args:
            data: 包含价格数据的字典
        
        Returns:
            数据是否有效
        """
        if len(data) < 2:
            logger.warning("数据不足：需要至少两个资产的价格数据")
            return False
        
        # 检查数据长度
        min_length = min(len(df) for df in data.values() if isinstance(df, pd.DataFrame))
        if min_length < self.lookback_period:
            logger.warning(f"数据长度不足：需要至少 {self.lookback_period} 个数据点")
            return False
        
        return True
    
    def _update_pair_state(self, pair_name: str, price1: np.ndarray, price2: np.ndarray):
        """
        更新配对状态
        
        Args:
            pair_name: 配对名称
            price1: 第一个资产的价格序列
            price2: 第二个资产的价格序列
        """
        # 计算统计指标
        stats = self.data_processor.calculate_pair_statistics(price1, price2)
        
        if pair_name not in self.pair_states:
            self.pair_states[pair_name] = {'position': None}
        
        self.pair_states[pair_name].update({
            'hedge_ratio': stats.get('hedge_ratio', 1.0),
            'spread_mean': stats.get('spread_mean', 0.0),
            'spread_std': stats.get('spread_std', 1.0),
            'correlation': stats.get('correlation', 0.0),
            'is_cointegrated': stats.get('is_cointegrated', False),
            'current_zscore': stats.get('current_zscore', 0.0)
        })
    
    def calculate_signals(self, data: Dict[str, pd.DataFrame], 
                          pair_name: str = "default",
                          asset1_symbol: str = "asset1",
                          asset2_symbol: str = "asset2") -> Dict[str, Any]:
        """
        计算交易信号
        
        Args:
            data: 包含价格数据的字典
            pair_name: 配对名称
            asset1_symbol: 第一个资产的符号
            asset2_symbol: 第二个资产的符号
        
        Returns:
            信号字典
        """
        # 验证数据
        if not self.validate_data(data):
            return {
                'signal': 'hold',
                'quantity1': 0,
                'quantity2': 0,
                'zscore': 0,
                'metadata': {'error': '数据无效'}
            }
        
        # 获取价格数据
        df1 = data.get(asset1_symbol)
        df2 = data.get(asset2_symbol)
        
        if df1 is None or df2 is None:
            logger.error(f"缺少价格数据: {asset1_symbol} 或 {asset2_symbol}")
            return {
                'signal': 'hold',
                'quantity1': 0,
                'quantity2': 0,
                'zscore': 0,
                'metadata': {'error': '缺少价格数据'}
            }
        
        # 对齐数据
        aligned_data = self.data_processor.prepare_pair_data(
            df1['close'] if 'close' in df1.columns else df1.iloc[:, 0],
            df2['close'] if 'close' in df2.columns else df2.iloc[:, 0]
        )
        
        if aligned_data.empty:
            return {
                'signal': 'hold',
                'quantity1': 0,
                'quantity2': 0,
                'zscore': 0,
                'metadata': {'error': '数据对齐失败'}
            }
        
        # 获取最近的数据
        recent_data = aligned_data.tail(self.lookback_period)
        price1 = recent_data['price1'].values
        price2 = recent_data['price2'].values
        
        # 更新配对状态
        self._update_pair_state(pair_name, price1, price2)
        
        state = self.pair_states[pair_name]
        current_zscore = state['current_zscore']
        correlation = state['correlation']
        is_cointegrated = state['is_cointegrated']
        
        # 检查相关性
        if correlation < self.correlation_threshold:
            logger.debug(f"相关性不足: {correlation:.3f} < {self.correlation_threshold}")
            return {
                'signal': 'hold',
                'quantity1': 0,
                'quantity2': 0,
                'zscore': current_zscore,
                'metadata': {
                    'correlation': correlation,
                    'reason': '相关性不足'
                }
            }
        
        # 检查协整关系（可选，但建议检查）
        if not is_cointegrated:
            logger.debug("未通过协整检验")
            # 可以选择继续交易或暂停
        
        # 获取当前持仓
        current_position = state.get('position')
        
        # 生成交易信号
        signal = 'hold'
        quantity1 = 0
        quantity2 = 0
        
        if current_position is None:
            # 无持仓，检查入场信号
            if current_zscore > self.z_entry_threshold:
                # 做空价差：卖出asset2，买入asset1
                signal = 'sell_spread'
                quantity1 = 1  # 买入asset1
                quantity2 = -state['hedge_ratio']  # 卖出asset2（按对冲比率）
                logger.info(f"生成做空价差信号: Z-score={current_zscore:.2f}")
                
            elif current_zscore < -self.z_entry_threshold:
                # 做多价差：买入asset2，卖出asset1
                signal = 'buy_spread'
                quantity1 = -1  # 卖出asset1
                quantity2 = state['hedge_ratio']  # 买入asset2（按对冲比率）
                logger.info(f"生成做多价差信号: Z-score={current_zscore:.2f}")
        
        else:
            # 有持仓，检查出场信号
            entry_zscore = current_position.get('entry_zscore', 0)
            
            # 检查止损
            if self.risk_manager.check_stop_loss(current_zscore, entry_zscore):
                signal = 'close'
                quantity1 = -current_position.get('quantity1', 0)
                quantity2 = -current_position.get('quantity2', 0)
                logger.info(f"触发止损平仓: Z-score={current_zscore:.2f}")
            
            # 检查止盈（Z-score回归到阈值内）
            elif abs(current_zscore) < self.z_exit_threshold:
                signal = 'close'
                quantity1 = -current_position.get('quantity1', 0)
                quantity2 = -current_position.get('quantity2', 0)
                logger.info(f"价差回归，平仓: Z-score={current_zscore:.2f}")
        
        return {
            'signal': signal,
            'quantity1': quantity1,
            'quantity2': quantity2,
            'zscore': current_zscore,
            'metadata': {
                'correlation': correlation,
                'hedge_ratio': state['hedge_ratio'],
                'is_cointegrated': is_cointegrated,
                'spread_mean': state['spread_mean'],
                'spread_std': state['spread_std']
            }
        }
    
    def update_position(self, pair_name: str, signal: str, 
                       quantity1: float, quantity2: float, zscore: float):
        """
        更新持仓状态
        
        Args:
            pair_name: 配对名称
            signal: 交易信号
            quantity1: 第一个资产的数量
            quantity2: 第二个资产的数量
            zscore: 当前Z-score
        """
        if pair_name not in self.pair_states:
            self.pair_states[pair_name] = {}
        
        if signal in ['buy_spread', 'sell_spread']:
            # 开仓
            self.pair_states[pair_name]['position'] = {
                'quantity1': quantity1,
                'quantity2': quantity2,
                'entry_zscore': zscore
            }
            logger.info(f"{pair_name} 开仓: q1={quantity1:.4f}, q2={quantity2:.4f}")
        
        elif signal == 'close':
            # 平仓
            self.pair_states[pair_name]['position'] = None
            logger.info(f"{pair_name} 平仓")

