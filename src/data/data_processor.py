"""数据处理和特征工程模块"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict
from src.utils.math_utils import (
    calculate_correlation, 
    calculate_hedge_ratio, 
    calculate_zscore,
    calculate_spread,
    test_cointegration
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DataProcessor:
    """数据处理器，用于特征工程和统计分析"""
    
    def __init__(self, lookback_period: int = 60):
        """
        初始化数据处理器
        
        Args:
            lookback_period: 回看期（数据点数）
        """
        self.lookback_period = lookback_period
    
    def prepare_pair_data(self, price1: pd.Series, price2: pd.Series) -> pd.DataFrame:
        """
        准备配对数据
        
        Args:
            price1: 第一个资产的价格序列
            price2: 第二个资产的价格序列
        
        Returns:
            包含处理后的数据的DataFrame
        """
        # 对齐数据
        aligned_data = pd.DataFrame({
            'price1': price1,
            'price2': price2
        }).dropna()
        
        if len(aligned_data) < self.lookback_period:
            logger.warning(f"数据点不足，需要至少 {self.lookback_period} 个数据点")
            return pd.DataFrame()
        
        return aligned_data
    
    def calculate_pair_statistics(self, price1: np.ndarray, price2: np.ndarray) -> Dict:
        """
        计算配对统计指标
        
        Args:
            price1: 第一个资产的价格序列
            price2: 第二个资产的价格序列
        
        Returns:
            统计指标字典
        """
        if len(price1) != len(price2) or len(price1) < self.lookback_period:
            return {}
        
        # 计算相关性
        correlation = calculate_correlation(price1, price2)
        
        # 计算对冲比率
        hedge_ratio = calculate_hedge_ratio(price1, price2)
        
        # 计算价差
        spread = calculate_spread(price1, price2, hedge_ratio)
        
        # 计算价差的统计量
        spread_mean = np.mean(spread)
        spread_std = np.std(spread)
        
        # 协整检验
        is_cointegrated, pvalue = test_cointegration(price1, price2)
        
        # 计算当前Z-score
        current_zscore = (spread[-1] - spread_mean) / spread_std if spread_std > 0 else 0
        
        return {
            'correlation': correlation,
            'hedge_ratio': hedge_ratio,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'current_spread': spread[-1],
            'current_zscore': current_zscore,
            'is_cointegrated': is_cointegrated,
            'cointegration_pvalue': pvalue
        }
    
    def calculate_rolling_zscore(self, spread: np.ndarray, window: Optional[int] = None) -> np.ndarray:
        """
        计算滚动Z-score
        
        Args:
            spread: 价差序列
            window: 滚动窗口大小
        
        Returns:
            Z-score数组
        """
        if window is None:
            window = self.lookback_period
        
        return calculate_zscore(spread, window)
    
    def normalize_prices(self, prices: pd.Series) -> pd.Series:
        """
        价格归一化（相对于第一个价格）
        
        Args:
            prices: 价格序列
        
        Returns:
            归一化后的价格序列
        """
        if len(prices) == 0 or prices.iloc[0] == 0:
            return prices
        
        return prices / prices.iloc[0]
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """
        计算收益率
        
        Args:
            prices: 价格序列
        
        Returns:
            收益率序列
        """
        return prices.pct_change().dropna()
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加技术指标
        
        Args:
            df: 包含价格数据的DataFrame
        
        Returns:
            添加了技术指标的DataFrame
        """
        result_df = df.copy()
        
        if 'close' in result_df.columns:
            # 移动平均线
            result_df['sma_20'] = result_df['close'].rolling(window=20).mean()
            result_df['sma_50'] = result_df['close'].rolling(window=50).mean()
            
            # RSI
            result_df['rsi'] = self._calculate_rsi(result_df['close'], period=14)
            
            # MACD
            macd, signal = self._calculate_macd(result_df['close'])
            result_df['macd'] = macd
            result_df['macd_signal'] = signal
        
        return result_df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, 
                        fast: int = 12, slow: int = 26, 
                        signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """计算MACD指标"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        return macd, macd_signal

