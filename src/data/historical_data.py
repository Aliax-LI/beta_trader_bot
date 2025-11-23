"""历史数据管理模块"""
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from src.data.data_fetcher import DataFetcher
from src.data.database import Database
from src.utils.logger import setup_logger
from src.utils.time_utils import datetime_to_timestamp, parse_date

logger = setup_logger(__name__)


class HistoricalDataManager:
    """历史数据管理器"""
    
    def __init__(self, exchange_name: str, sandbox: bool = True, 
                 db_path: str = "data/trading.db"):
        """
        初始化历史数据管理器
        
        Args:
            exchange_name: 交易所名称
            sandbox: 是否使用测试环境
            db_path: 数据库路径
        """
        self.data_fetcher = DataFetcher(exchange_name, sandbox)
        self.database = Database(db_path)
        logger.info("历史数据管理器初始化完成")
    
    def download_and_save(self, symbols: List[str], timeframe: str = '1h',
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None,
                         limit: int = 1000):
        """
        下载并保存历史数据
        
        Args:
            symbols: 交易对符号列表
            timeframe: 时间周期
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
            limit: 每次请求的数据条数
        """
        since = None
        if start_date:
            since = datetime_to_timestamp(parse_date(start_date))
        
        for symbol in symbols:
            try:
                logger.info(f"开始下载 {symbol} 的历史数据...")
                df = self.data_fetcher.fetch_ohlcv(symbol, timeframe, since, limit)
                
                if not df.empty:
                    self.database.save_prices(symbol, df)
                    logger.info(f"{symbol} 数据下载完成，共 {len(df)} 条")
                else:
                    logger.warning(f"{symbol} 数据为空")
                    
            except Exception as e:
                logger.error(f"下载 {symbol} 数据失败: {str(e)}")
    
    def get_historical_data(self, symbol: str, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取历史数据（优先从数据库，如果不存在则从交易所获取）
        
        Args:
            symbol: 交易对符号
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            历史数据DataFrame
        """
        start_time = None
        end_time = None
        
        if start_date:
            start_time = datetime_to_timestamp(parse_date(start_date))
        if end_date:
            end_time = datetime_to_timestamp(parse_date(end_date))
        
        # 先从数据库获取
        df = self.database.get_prices(symbol, start_time, end_time)
        
        # 如果数据库中没有数据，从交易所获取
        if df.empty:
            logger.info(f"数据库中没有 {symbol} 的数据，从交易所获取...")
            df = self.data_fetcher.fetch_ohlcv(symbol, '1h', start_time, 1000)
            if not df.empty:
                self.database.save_prices(symbol, df)
        
        return df
    
    def update_latest_data(self, symbols: List[str], timeframe: str = '1h'):
        """
        更新最新数据
        
        Args:
            symbols: 交易对符号列表
            timeframe: 时间周期
        """
        for symbol in symbols:
            try:
                # 获取数据库中最新的时间戳
                latest_df = self.database.get_prices(symbol)
                since = None
                
                if not latest_df.empty:
                    latest_timestamp = latest_df['timestamp'].max()
                    since = int(latest_timestamp) + 1  # 从下一条开始
                
                # 获取新数据
                df = self.data_fetcher.fetch_ohlcv(symbol, timeframe, since, 500)
                
                if not df.empty:
                    self.database.save_prices(symbol, df)
                    logger.info(f"{symbol} 数据更新完成，新增 {len(df)} 条")
                    
            except Exception as e:
                logger.error(f"更新 {symbol} 数据失败: {str(e)}")

