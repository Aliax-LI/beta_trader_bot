"""回测入口"""
import argparse
import pandas as pd
from src.utils.logger import setup_logger
from src.utils.helpers import load_config
from src.data.historical_data import HistoricalDataManager
from src.backtest.backtest_engine import BacktestEngine
from src.backtest.performance import PerformanceAnalyzer
from src.backtest.visualization import Visualizer

logger = setup_logger(__name__)


def run_backtest(pair_config: dict, backtest_config: dict, strategy_config: dict):
    """
    运行回测
    
    Args:
        pair_config: 配对配置
        backtest_config: 回测配置
        strategy_config: 策略配置
    """
    logger.info(f"开始回测: {pair_config.get('name')}")
    
    # 初始化数据管理器
    exchange_name = pair_config.get('exchange', 'binance')
    data_manager = HistoricalDataManager(exchange_name, sandbox=True)
    
    # 获取历史数据
    asset1 = pair_config.get('asset1')
    asset2 = pair_config.get('asset2')
    start_date = backtest_config.get('start_date')
    end_date = backtest_config.get('end_date')
    
    logger.info(f"获取历史数据: {asset1}, {asset2}")
    data1 = data_manager.get_historical_data(asset1, start_date, end_date)
    data2 = data_manager.get_historical_data(asset2, start_date, end_date)
    
    if data1.empty or data2.empty:
        logger.error("数据不足，无法进行回测")
        return
    
    # 对齐数据
    aligned_data = pd.merge(
        data1[['close']], 
        data2[['close']], 
        left_index=True, 
        right_index=True, 
        suffixes=('_1', '_2')
    )
    
    data1_aligned = pd.DataFrame({'close': aligned_data['close_1']})
    data2_aligned = pd.DataFrame({'close': aligned_data['close_2']})
    
    # 创建回测引擎
    initial_cash = backtest_config.get('initial_cash', 100000)
    commission = backtest_config.get('commission', 0.001)
    engine = BacktestEngine(initial_cash, commission)
    
    # 运行回测
    result = engine.run_backtest(
        data1_aligned,
        data2_aligned,
        strategy_config.get('pairs_trading', {}),
        start_date,
        end_date
    )
    
    if not result:
        logger.error("回测失败")
        return
    
    # 绩效分析
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(result)
    print(report)
    
    # 可视化（可选）
    try:
        visualizer = Visualizer()
        # 这里可以添加可视化代码
        logger.info("回测完成")
    except Exception as e:
        logger.warning(f"可视化失败: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='配对交易回测')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='配置文件路径')
    parser.add_argument('--pair-config', type=str, default='config/pairs_config.yaml',
                       help='配对配置文件路径')
    parser.add_argument('--optimize', action='store_true',
                       help='运行参数优化')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    pairs_config = load_config(args.pair_config)
    
    # 获取第一个启用的配对
    pairs = pairs_config.get('pairs', [])
    enabled_pairs = [p for p in pairs if p.get('enabled', True)]
    
    if not enabled_pairs:
        logger.error("没有启用的配对")
        return
    
    # 运行回测
    for pair_config in enabled_pairs:
        run_backtest(
            pair_config,
            config.get('backtest', {}),
            config.get('strategy', {})
        )


if __name__ == "__main__":
    main()

