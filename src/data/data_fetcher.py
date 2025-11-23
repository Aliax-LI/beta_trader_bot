"""数据获取模块（CCXT集成）"""
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
from src.utils.logger import setup_logger
from src.utils.helpers import get_env_var

logger = setup_logger(__name__)


class DataFetcher:
    """数据获取器，使用CCXT库从交易所获取数据"""
    
    def __init__(self, exchange_name: str, sandbox: bool = True):
        """
        初始化数据获取器
        
        Args:
            exchange_name: 交易所名称（如 'binance', 'okx'）
            sandbox: 是否使用测试环境
        """
        self.exchange_name = exchange_name
        self.sandbox = sandbox
        self.exchange = self._create_exchange()
        logger.info(f"初始化数据获取器: {exchange_name}, 沙盒模式: {sandbox}")
    
    def _create_exchange(self) -> ccxt.Exchange:
        """创建交易所实例"""
        exchange_class = getattr(ccxt, self.exchange_name)
        
        config = {
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        }
        
        # 如果是沙盒模式
        if self.sandbox:
            config['sandbox'] = True
        
        # 加载API密钥
        api_key = get_env_var(f"{self.exchange_name.upper()}_API_KEY")
        secret = get_env_var(f"{self.exchange_name.upper()}_SECRET_KEY")
        
        if api_key and secret:
            config['apiKey'] = api_key
            config['secret'] = secret
        
        # OKX需要passphrase
        if self.exchange_name.lower() == 'okx':
            passphrase = get_env_var("OKX_PASSPHRASE")
            if passphrase:
                config['password'] = passphrase
        
        return exchange_class(config)
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', 
                    since: Optional[int] = None, limit: int = 500) -> pd.DataFrame:
        """
        获取OHLCV数据
        
        Args:
            symbol: 交易对符号（如 'BTC/USDT'）
            timeframe: 时间周期（如 '1h', '1d'）
            since: 起始时间戳（毫秒）
            limit: 返回数据条数
        
        Returns:
            DataFrame，包含 open, high, low, close, volume 列
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            df.drop('timestamp', axis=1, inplace=True)
            
            logger.debug(f"获取 {symbol} 数据成功，共 {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取 {symbol} 数据失败: {str(e)}")
            return pd.DataFrame()
    
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """
        获取当前价格信息
        
        Args:
            symbol: 交易对符号
        
        Returns:
            价格信息字典
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"获取 {symbol} 价格失败: {str(e)}")
            return None
    
    def fetch_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """
        获取订单簿
        
        Args:
            symbol: 交易对符号
            limit: 订单簿深度
        
        Returns:
            订单簿字典
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            logger.error(f"获取 {symbol} 订单簿失败: {str(e)}")
            return None
    
    async def fetch_multiple_ohlcv(self, symbols: List[str], 
                                   timeframe: str = '1h', 
                                   limit: int = 500) -> Dict[str, pd.DataFrame]:
        """
        异步获取多个交易对的OHLCV数据
        
        Args:
            symbols: 交易对符号列表
            timeframe: 时间周期
            limit: 返回数据条数
        
        Returns:
            交易对到DataFrame的字典
        """
        async def fetch_one(symbol):
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                self.fetch_ohlcv, 
                symbol, 
                timeframe, 
                None, 
                limit
            )
            return symbol, df
        
        tasks = [fetch_one(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        return {symbol: df for symbol, df in results}
    
    def get_supported_timeframes(self) -> List[str]:
        """
        获取支持的时间周期列表
        
        Returns:
            时间周期列表
        """
        return list(self.exchange.timeframes.keys()) if hasattr(self.exchange, 'timeframes') else []

