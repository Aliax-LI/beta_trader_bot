"""可视化模块"""
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class Visualizer:
    """可视化工具类"""
    
    def __init__(self):
        """初始化可视化工具"""
        logger.info("可视化工具初始化完成")
    
    def plot_equity_curve(self, equity_curve: pd.Series, save_path: Optional[str] = None):
        """
        绘制权益曲线
        
        Args:
            equity_curve: 权益曲线
            save_path: 保存路径（可选）
        """
        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve.index, equity_curve.values, linewidth=2)
        plt.title('权益曲线', fontsize=14, fontweight='bold')
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('权益', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"权益曲线已保存: {save_path}")
        
        plt.close()
    
    def plot_drawdown(self, equity_curve: pd.Series, save_path: Optional[str] = None):
        """
        绘制回撤曲线
        
        Args:
            equity_curve: 权益曲线
            save_path: 保存路径（可选）
        """
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak * 100
        
        plt.figure(figsize=(12, 6))
        plt.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        plt.plot(drawdown.index, drawdown.values, linewidth=2, color='red')
        plt.title('回撤曲线', fontsize=14, fontweight='bold')
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('回撤 (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"回撤曲线已保存: {save_path}")
        
        plt.close()
    
    def plot_pair_prices(self, price1: pd.Series, price2: pd.Series, 
                        save_path: Optional[str] = None):
        """
        绘制配对价格图
        
        Args:
            price1: 第一个资产的价格序列
            price2: 第二个资产的价格序列
            save_path: 保存路径（可选）
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # 价格图
        ax1.plot(price1.index, price1.values, label='Asset 1', linewidth=2)
        ax1.plot(price2.index, price2.values, label='Asset 2', linewidth=2)
        ax1.set_title('配对价格', fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 价差图
        spread = price2 - price1
        ax2.plot(spread.index, spread.values, label='价差', linewidth=2, color='green')
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('价差', fontsize=14, fontweight='bold')
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('价差', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"配对价格图已保存: {save_path}")
        
        plt.close()
    
    def plot_zscore(self, zscores: pd.Series, entry_threshold: float, 
                   exit_threshold: float, save_path: Optional[str] = None):
        """
        绘制Z-score图
        
        Args:
            zscores: Z-score序列
            entry_threshold: 入场阈值
            exit_threshold: 出场阈值
            save_path: 保存路径（可选）
        """
        plt.figure(figsize=(12, 6))
        plt.plot(zscores.index, zscores.values, linewidth=2, label='Z-score')
        plt.axhline(y=entry_threshold, color='red', linestyle='--', label=f'入场阈值 ({entry_threshold})')
        plt.axhline(y=-entry_threshold, color='red', linestyle='--')
        plt.axhline(y=exit_threshold, color='green', linestyle='--', label=f'出场阈值 ({exit_threshold})')
        plt.axhline(y=-exit_threshold, color='green', linestyle='--')
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.title('Z-score 时间序列', fontsize=14, fontweight='bold')
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('Z-score', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Z-score图已保存: {save_path}")
        
        plt.close()
    
    def plot_performance_summary(self, metrics: Dict, save_path: Optional[str] = None):
        """
        绘制绩效摘要图
        
        Args:
            metrics: 绩效指标字典
            save_path: 保存路径（可选）
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 收益率指标
        ax1 = axes[0, 0]
        returns_data = {
            '总收益率': metrics.get('total_return', 0) * 100,
            '年化收益率': metrics.get('annual_return', 0) * 100
        }
        ax1.bar(returns_data.keys(), returns_data.values(), color=['blue', 'green'])
        ax1.set_title('收益率指标', fontsize=12, fontweight='bold')
        ax1.set_ylabel('收益率 (%)', fontsize=10)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 风险指标
        ax2 = axes[0, 1]
        risk_data = {
            '最大回撤': abs(metrics.get('max_drawdown', 0)) * 100,
            '年化波动率': metrics.get('annual_volatility', 0) * 100
        }
        ax2.bar(risk_data.keys(), risk_data.values(), color=['red', 'orange'])
        ax2.set_title('风险指标', fontsize=12, fontweight='bold')
        ax2.set_ylabel('百分比 (%)', fontsize=10)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 比率指标
        ax3 = axes[1, 0]
        ratio_data = {
            '夏普比率': metrics.get('sharpe_ratio', 0),
            'Calmar比率': metrics.get('calmar_ratio', 0)
        }
        ax3.bar(ratio_data.keys(), ratio_data.values(), color=['purple', 'brown'])
        ax3.set_title('比率指标', fontsize=12, fontweight='bold')
        ax3.set_ylabel('比率', fontsize=10)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 交易统计
        ax4 = axes[1, 1]
        trade_data = {
            '总交易次数': metrics.get('total_trades', 0),
            '胜率': metrics.get('win_rate', 0) * 100
        }
        ax4.bar(trade_data.keys(), trade_data.values(), color=['cyan', 'magenta'])
        ax4.set_title('交易统计', fontsize=12, fontweight='bold')
        ax4.set_ylabel('数值', fontsize=10)
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"绩效摘要图已保存: {save_path}")
        
        plt.close()

