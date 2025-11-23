"""数学工具测试"""
import numpy as np
import pytest
from src.utils.math_utils import (
    calculate_correlation,
    calculate_hedge_ratio,
    calculate_zscore
)


def test_calculate_correlation():
    """测试相关性计算"""
    series1 = np.array([1, 2, 3, 4, 5])
    series2 = np.array([2, 4, 6, 8, 10])
    
    correlation = calculate_correlation(series1, series2)
    assert correlation == pytest.approx(1.0, abs=0.01)


def test_calculate_hedge_ratio():
    """测试对冲比率计算"""
    price1 = np.array([1, 2, 3, 4, 5])
    price2 = np.array([2, 4, 6, 8, 10])
    
    hedge_ratio = calculate_hedge_ratio(price1, price2)
    assert hedge_ratio == pytest.approx(2.0, abs=0.1)


def test_calculate_zscore():
    """测试Z-score计算"""
    series = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    zscores = calculate_zscore(series)
    
    assert len(zscores) == len(series)
    assert np.mean(zscores) == pytest.approx(0.0, abs=0.1)

