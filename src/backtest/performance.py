"""绩效分析模块"""
import pandas as pd
import numpy as np
from typing import Dict, List
from src.utils.logger import setup_logger
from src.utils.helpers import safe_divide

logger = setup_logger(__name__)


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self):
        """初始化绩效分析器"""
        logger.info("绩效分析器初始化完成")
    
    def calculate_metrics(self, equity_curve: pd.Series, trades: List[Dict]) -> Dict:
        """
        计算绩效指标
        
        Args:
            equity_curve: 权益曲线
            trades: 交易记录列表
        
        Returns:
            绩效指标字典
        """
        if len(equity_curve) == 0:
            return {}
        
        # 计算收益率序列
        returns = equity_curve.pct_change().dropna()
        
        # 总收益率
        total_return = (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]
        
        # 年化收益率
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        years = days / 365.0
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0
        
        # 夏普比率（假设无风险利率为0）
        sharpe_ratio = safe_divide(annual_return, annual_volatility)
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # Calmar比率
        calmar_ratio = safe_divide(annual_return, abs(max_drawdown)) if max_drawdown != 0 else 0
        
        # 交易统计
        trade_stats = self._analyze_trades(trades)
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'total_trades': trade_stats.get('total_trades', 0),
            'win_rate': trade_stats.get('win_rate', 0),
            'avg_profit': trade_stats.get('avg_profit', 0),
            'avg_loss': trade_stats.get('avg_loss', 0),
            'profit_factor': trade_stats.get('profit_factor', 0)
        }
    
    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        计算最大回撤
        
        Args:
            equity_curve: 权益曲线
        
        Returns:
            最大回撤（负数）
        """
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min()
    
    def _analyze_trades(self, trades: List[Dict]) -> Dict:
        """
        分析交易记录
        
        Args:
            trades: 交易记录列表
        
        Returns:
            交易统计字典
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        # 提取盈亏
        pnls = [t.get('pnl', 0) for t in trades if t.get('is_closed', False)]
        
        if not pnls:
            return {
                'total_trades': len(trades),
                'win_rate': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        
        win_rate = len(winning_trades) / len(pnls) if pnls else 0
        avg_profit = np.mean(winning_trades) if winning_trades else 0
        avg_loss = abs(np.mean(losing_trades)) if losing_trades else 0
        
        total_profit = sum(winning_trades) if winning_trades else 0
        total_loss = abs(sum(losing_trades)) if losing_trades else 0
        profit_factor = safe_divide(total_profit, total_loss)
        
        return {
            'total_trades': len(pnls),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
    
    def generate_report(self, metrics: Dict) -> str:
        """
        生成绩效报告
        
        Args:
            metrics: 绩效指标字典
        
        Returns:
            报告字符串
        """
        report = f"""
========== 绩效报告 ==========

收益率指标:
  总收益率: {metrics.get('total_return', 0)*100:.2f}%
  年化收益率: {metrics.get('annual_return', 0)*100:.2f}%
  年化波动率: {metrics.get('annual_volatility', 0)*100:.2f}%

风险指标:
  最大回撤: {metrics.get('max_drawdown', 0)*100:.2f}%
  夏普比率: {metrics.get('sharpe_ratio', 0):.3f}
  Calmar比率: {metrics.get('calmar_ratio', 0):.3f}

交易统计:
  总交易次数: {metrics.get('total_trades', 0)}
  胜率: {metrics.get('win_rate', 0)*100:.2f}%
  平均盈利: {metrics.get('avg_profit', 0):.2f}
  平均亏损: {metrics.get('avg_loss', 0):.2f}
  盈亏比: {metrics.get('profit_factor', 0):.3f}

============================
"""
        return report

