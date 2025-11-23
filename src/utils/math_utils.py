"""数学工具模块"""
import numpy as np
from typing import Tuple, Optional
from scipy import stats
from statsmodels.tsa.stattools import coint


def calculate_correlation(series1: np.ndarray, series2: np.ndarray) -> float:
    """
    计算两个时间序列的相关性
    
    Args:
        series1: 第一个时间序列
        series2: 第二个时间序列
    
    Returns:
        相关系数
    """
    if len(series1) != len(series2) or len(series1) < 2:
        return 0.0
    
    correlation = np.corrcoef(series1, series2)[0, 1]
    return float(correlation) if not np.isnan(correlation) else 0.0


def calculate_hedge_ratio(price1: np.ndarray, price2: np.ndarray) -> float:
    """
    使用OLS回归计算对冲比率
    
    Args:
        price1: 第一个资产的价格序列
        price2: 第二个资产的价格序列
    
    Returns:
        对冲比率
    """
    if len(price1) != len(price2) or len(price1) < 2:
        return 1.0
    
    # 使用最小二乘法计算对冲比率
    slope, intercept, r_value, p_value, std_err = stats.linregress(price1, price2)
    return float(slope) if not np.isnan(slope) else 1.0


def calculate_zscore(series: np.ndarray, window: Optional[int] = None) -> np.ndarray:
    """
    计算Z-score
    
    Args:
        series: 时间序列
        window: 滚动窗口大小，如果为None则使用全部数据
    
    Returns:
        Z-score数组
    """
    if len(series) == 0:
        return np.array([])
    
    if window is None or window >= len(series):
        mean = np.mean(series)
        std = np.std(series)
        if std == 0:
            return np.zeros_like(series)
        return (series - mean) / std
    
    # 滚动窗口计算
    zscores = np.zeros_like(series)
    for i in range(window, len(series)):
        window_data = series[i-window:i]
        mean = np.mean(window_data)
        std = np.std(window_data)
        if std == 0:
            zscores[i] = 0
        else:
            zscores[i] = (series[i] - mean) / std
    
    return zscores


def calculate_spread(price1: np.ndarray, price2: np.ndarray, 
                     hedge_ratio: float) -> np.ndarray:
    """
    计算价差
    
    Args:
        price1: 第一个资产的价格序列
        price2: 第二个资产的价格序列
        hedge_ratio: 对冲比率
    
    Returns:
        价差序列
    """
    return price2 - hedge_ratio * price1


def test_cointegration(series1: np.ndarray, series2: np.ndarray, 
                      significance_level: float = 0.05) -> Tuple[bool, float]:
    """
    协整检验
    
    Args:
        series1: 第一个时间序列
        series2: 第二个时间序列
        significance_level: 显著性水平
    
    Returns:
        (是否协整, p值)
    """
    if len(series1) != len(series2) or len(series1) < 10:
        return False, 1.0
    
    try:
        score, pvalue, _ = coint(series1, series2)
        is_cointegrated = pvalue < significance_level
        return is_cointegrated, float(pvalue)
    except Exception:
        return False, 1.0


def calculate_returns(prices: np.ndarray) -> np.ndarray:
    """
    计算收益率
    
    Args:
        prices: 价格序列
    
    Returns:
        收益率序列
    """
    if len(prices) < 2:
        return np.array([])
    
    returns = np.diff(prices) / prices[:-1]
    return returns

