"""回测引擎模块（基于Backtrader）"""
import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from src.strategies.pairs_trading import PairsTradingStrategy
from src.data.data_processor import DataProcessor
from src.utils.logger import setup_logger
from src.utils.time_utils import parse_date

logger = setup_logger(__name__)


class PairsTradingStrategyBT(bt.Strategy):
    """Backtrader版本的配对交易策略"""
    
    params = (
        ('lookback_period', 60),
        ('z_entry_threshold', 2.0),
        ('z_exit_threshold', 0.5),
        ('correlation_threshold', 0.8),
        ('position_size', 0.1),
    )
    
    def __init__(self):
        """初始化策略"""
        self.data1 = self.datas[0]
        self.data2 = self.datas[1]
        self.order1 = None
        self.order2 = None
        self.position = None
        self.entry_zscore = None
        
        # 数据处理器
        self.data_processor = DataProcessor(self.params.lookback_period)
        
        # 存储历史数据
        self.price1_history = []
        self.price2_history = []
    
    def next(self):
        """每个bar执行一次"""
        # 收集价格数据
        self.price1_history.append(self.data1.close[0])
        self.price2_history.append(self.data2.close[0])
        
        # 确保有足够的数据
        if len(self.price1_history) < self.params.lookback_period:
            return
        
        # 转换为numpy数组
        price1_array = np.array(self.price1_history[-self.params.lookback_period:])
        price2_array = np.array(self.price2_history[-self.params.lookback_period:])
        
        # 计算统计指标
        stats = self.data_processor.calculate_pair_statistics(price1_array, price2_array)
        
        correlation = stats.get('correlation', 0)
        current_zscore = stats.get('current_zscore', 0)
        
        # 检查相关性
        if correlation < self.params.correlation_threshold:
            return
        
        # 生成交易信号
        if self.position is None:
            # 无持仓，检查入场
            if current_zscore > self.params.z_entry_threshold:
                # 做空价差：卖出asset2，买入asset1
                size = self.broker.getcash() * self.params.position_size / self.data1.close[0]
                self.order1 = self.buy(data=self.data1, size=size)
                size2 = size * stats.get('hedge_ratio', 1.0)
                self.order2 = self.sell(data=self.data2, size=size2)
                self.position = 'short_spread'
                self.entry_zscore = current_zscore
                logger.debug(f"做空价差: Z-score={current_zscore:.2f}")
            
            elif current_zscore < -self.params.z_entry_threshold:
                # 做多价差：买入asset2，卖出asset1
                size = self.broker.getcash() * self.params.position_size / self.data2.close[0]
                self.order1 = self.sell(data=self.data1, size=size)
                size2 = size * stats.get('hedge_ratio', 1.0)
                self.order2 = self.buy(data=self.data2, size=size2)
                self.position = 'long_spread'
                self.entry_zscore = current_zscore
                logger.debug(f"做多价差: Z-score={current_zscore:.2f}")
        
        else:
            # 有持仓，检查出场
            if abs(current_zscore) < self.params.z_exit_threshold:
                # 平仓
                if self.position == 'short_spread':
                    self.order1 = self.sell(data=self.data1)
                    self.order2 = self.buy(data=self.data2)
                elif self.position == 'long_spread':
                    self.order1 = self.buy(data=self.data1)
                    self.order2 = self.sell(data=self.data2)
                
                self.position = None
                self.entry_zscore = None
                logger.debug(f"平仓: Z-score={current_zscore:.2f}")


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_cash: float = 100000, commission: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金
            commission: 手续费率
        """
        self.initial_cash = initial_cash
        self.commission = commission
        logger.info(f"回测引擎初始化: 初始资金={initial_cash}, 手续费={commission}")
    
    def run_backtest(self, data1: pd.DataFrame, data2: pd.DataFrame,
                    strategy_params: Dict, start_date: str, end_date: str) -> Dict:
        """
        运行回测
        
        Args:
            data1: 第一个资产的价格数据
            data2: 第二个资产的价格数据
            strategy_params: 策略参数
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            回测结果字典
        """
        try:
            # 创建Cerebro引擎
            cerebro = bt.Cerebro()
            
            # 设置初始资金
            cerebro.broker.setcash(self.initial_cash)
            
            # 设置手续费
            cerebro.broker.setcommission(commission=self.commission)
            
            # 添加数据
            data1_bt = bt.feeds.PandasData(dataname=data1)
            data2_bt = bt.feeds.PandasData(dataname=data2)
            cerebro.adddata(data1_bt)
            cerebro.adddata(data2_bt)
            
            # 添加策略
            cerebro.addstrategy(
                PairsTradingStrategyBT,
                lookback_period=strategy_params.get('lookback_period', 60),
                z_entry_threshold=strategy_params.get('z_entry_threshold', 2.0),
                z_exit_threshold=strategy_params.get('z_exit_threshold', 0.5),
                correlation_threshold=strategy_params.get('correlation_threshold', 0.8),
                position_size=strategy_params.get('position_size', 0.1)
            )
            
            # 添加分析器
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            
            # 运行回测
            logger.info("开始运行回测...")
            results = cerebro.run()
            
            # 获取最终价值
            final_value = cerebro.broker.getvalue()
            
            # 获取分析结果
            strat = results[0]
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            returns = strat.analyzers.returns.get_analysis()
            trades = strat.analyzers.trades.get_analysis()
            
            # 计算绩效指标
            total_return = (final_value - self.initial_cash) / self.initial_cash
            
            result = {
                'initial_cash': self.initial_cash,
                'final_value': final_value,
                'total_return': total_return,
                'sharpe_ratio': sharpe.get('sharperatio', 0),
                'max_drawdown': drawdown.get('max', {}).get('drawdown', 0),
                'total_trades': trades.get('total', {}).get('total', 0),
                'win_rate': self._calculate_win_rate(trades),
                'returns': returns
            }
            
            logger.info(f"回测完成: 总收益率={total_return*100:.2f}%")
            return result
        
        except Exception as e:
            logger.error(f"回测失败: {str(e)}")
            return {}
    
    def _calculate_win_rate(self, trades_analysis: Dict) -> float:
        """计算胜率"""
        total = trades_analysis.get('total', {}).get('total', 0)
        won = trades_analysis.get('won', {}).get('total', 0)
        
        if total == 0:
            return 0.0
        
        return won / total

