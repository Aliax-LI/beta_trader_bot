"""主程序入口"""
import argparse
import time
import asyncio
from typing import Dict
from src.utils.logger import setup_logger
from src.utils.helpers import load_config, load_env_file
from src.data.historical_data import HistoricalDataManager
from src.data.data_processor import DataProcessor
from src.strategies.pairs_trading import PairsTradingStrategy
from src.trading.execution_engine import ExecutionEngine
from src.monitoring.health_check import HealthChecker
from src.monitoring.alerts import AlertManager
from src.monitoring.dashboard import Dashboard

logger = setup_logger(__name__)


class PairsTradingBot:
    """配对交易机器人主类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化交易机器人
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        load_env_file()
        self.config = load_config(config_path)
        
        # 初始化组件
        app_config = self.config.get('app', {})
        trading_config = self.config.get('trading', {})
        strategy_config = self.config.get('strategy', {})
        
        # 交易所配置
        exchanges_config = load_config("config/exchanges.yaml")
        exchange_name = list(exchanges_config.get('exchanges', {}).keys())[0]
        sandbox = trading_config.get('sandbox', True)
        
        # 初始化各个模块
        self.data_manager = HistoricalDataManager(exchange_name, sandbox)
        self.data_processor = DataProcessor()
        self.strategy = PairsTradingStrategy(strategy_config)
        self.execution_engine = ExecutionEngine(
            exchange_name, 
            sandbox, 
            strategy_config.get('pairs_trading', {})
        )
        self.health_checker = HealthChecker(exchange_name, sandbox)
        self.alert_manager = AlertManager()
        self.dashboard = Dashboard()
        
        # 运行配置
        self.update_interval = trading_config.get('update_interval', 300)
        self.enabled = trading_config.get('enabled', False)
        
        logger.info(f"配对交易机器人初始化完成: 环境={app_config.get('environment')}, "
                   f"实盘交易={'启用' if self.enabled else '禁用'}")
    
    def run(self):
        """运行交易机器人"""
        if not self.enabled:
            logger.warning("实盘交易未启用，请在配置文件中设置 trading.enabled=true")
            return
        
        logger.info("开始运行交易机器人...")
        
        # 加载配对配置
        pairs_config = load_config("config/pairs_config.yaml")
        pairs = pairs_config.get('pairs', [])
        
        try:
            while True:
                # 健康检查
                health_status = self.health_checker.run_full_check()
                if health_status.get('overall_status') != 'healthy':
                    self.alert_manager.alert_system_error(
                        "系统健康检查失败",
                        health_status
                    )
                
                # 处理每个配对
                for pair_config in pairs:
                    if not pair_config.get('enabled', True):
                        continue
                    
                    try:
                        self._process_pair(pair_config)
                    except Exception as e:
                        logger.error(f"处理配对失败: {pair_config.get('name')}, 错误: {str(e)}")
                        self.alert_manager.alert_system_error(
                            f"处理配对失败: {str(e)}",
                            {'pair': pair_config.get('name')}
                        )
                
                # 显示状态
                account_info = self.execution_engine.get_account_info()
                status = self.dashboard.get_status_summary(
                    account_info,
                    self.execution_engine.position_manager.get_all_positions(),
                    self.alert_manager.get_recent_alerts(10)
                )
                logger.info(self.dashboard.format_status_report(status))
                
                # 等待下次更新
                logger.info(f"等待 {self.update_interval} 秒后进行下次更新...")
                time.sleep(self.update_interval)
        
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭...")
        except Exception as e:
            logger.error(f"运行异常: {str(e)}")
            self.alert_manager.alert_system_error(f"运行异常: {str(e)}")
    
    def _process_pair(self, pair_config: Dict):
        """
        处理单个配对
        
        Args:
            pair_config: 配对配置字典
        """
        pair_name = pair_config.get('name')
        asset1 = pair_config.get('asset1')
        asset2 = pair_config.get('asset2')
        
        logger.debug(f"处理配对: {pair_name}")
        
        # 获取最新数据
        data1 = self.data_manager.get_historical_data(asset1)
        data2 = self.data_manager.get_historical_data(asset2)
        
        if data1.empty or data2.empty:
            logger.warning(f"{pair_name}: 数据不足")
            return
        
        # 准备数据
        data = {
            asset1: data1,
            asset2: data2
        }
        
        # 计算交易信号
        signal = self.strategy.calculate_signals(
            data,
            pair_name=pair_name,
            asset1_symbol=asset1,
            asset2_symbol=asset2
        )
        
        # 执行信号
        if signal.get('signal') != 'hold':
            account_info = self.execution_engine.get_account_info()
            balance = sum(account_info.get('balance', {}).values())
            
            result = self.execution_engine.execute_signal(
                signal,
                pair_name,
                balance
            )
            
            if result:
                self.alert_manager.alert_trade_execution(
                    pair_name,
                    result.get('success', False),
                    result
                )
                
                # 更新策略持仓状态
                if result.get('success'):
                    self.strategy.update_position(
                        pair_name,
                        signal.get('signal'),
                        signal.get('quantity1', 0),
                        signal.get('quantity2', 0),
                        signal.get('zscore', 0)
                    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='配对交易机器人')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='配置文件路径')
    parser.add_argument('--sandbox', action='store_true',
                       help='使用测试环境')
    parser.add_argument('--live', action='store_true',
                       help='启用实盘交易')
    
    args = parser.parse_args()
    
    # 创建机器人实例
    bot = PairsTradingBot(args.config)
    
    # 如果指定了--live，启用实盘交易
    if args.live:
        bot.enabled = True
        logger.warning("实盘交易模式已启用！")
    
    # 运行机器人
    bot.run()


if __name__ == "__main__":
    main()

