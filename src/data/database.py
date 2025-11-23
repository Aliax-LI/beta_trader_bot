"""数据库操作模块"""
import sqlite3
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
from src.utils.logger import setup_logger
from src.utils.helpers import ensure_dir

logger = setup_logger(__name__)


class Database:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/trading.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        ensure_dir(str(Path(db_path).parent))
        self.db_path = db_path
        self._init_database()
        logger.info(f"数据库初始化完成: {db_path}")
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair_name TEXT NOT NULL,
                asset1 TEXT NOT NULL,
                asset2 TEXT NOT NULL,
                action TEXT NOT NULL,
                price1 REAL,
                price2 REAL,
                quantity1 REAL,
                quantity2 REAL,
                zscore REAL,
                timestamp INTEGER NOT NULL,
                exchange TEXT,
                order_id TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # 创建价格数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                UNIQUE(symbol, timestamp)
            )
        ''')
        
        # 创建配对统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pair_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pair_name TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                correlation REAL,
                hedge_ratio REAL,
                spread_mean REAL,
                spread_std REAL,
                current_zscore REAL,
                is_cointegrated INTEGER,
                UNIQUE(pair_name, timestamp)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_trade(self, trade_data: Dict) -> Optional[int]:
        """
        保存交易记录
        
        Args:
            trade_data: 交易数据字典
        
        Returns:
            插入的记录ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO trades (
                    pair_name, asset1, asset2, action, price1, price2,
                    quantity1, quantity2, zscore, timestamp, exchange, order_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('pair_name'),
                trade_data.get('asset1'),
                trade_data.get('asset2'),
                trade_data.get('action'),
                trade_data.get('price1'),
                trade_data.get('price2'),
                trade_data.get('quantity1'),
                trade_data.get('quantity2'),
                trade_data.get('zscore'),
                trade_data.get('timestamp', int(datetime.now().timestamp() * 1000)),
                trade_data.get('exchange'),
                trade_data.get('order_id'),
                trade_data.get('status', 'pending')
            ))
            
            trade_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"交易记录已保存: ID={trade_id}")
            return trade_id
            
        except Exception as e:
            logger.error(f"保存交易记录失败: {str(e)}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def save_prices(self, symbol: str, df: pd.DataFrame):
        """
        保存价格数据
        
        Args:
            symbol: 交易对符号
            df: 包含OHLCV数据的DataFrame
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            df['symbol'] = symbol
            df['timestamp'] = df.index.astype('int64') // 10**6  # 转换为毫秒时间戳
            
            df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']].to_sql(
                'prices',
                conn,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            logger.debug(f"价格数据已保存: {symbol}, {len(df)} 条")
            
        except Exception as e:
            logger.error(f"保存价格数据失败: {str(e)}")
        finally:
            conn.close()
    
    def get_trades(self, pair_name: Optional[str] = None, 
                   start_time: Optional[int] = None,
                   end_time: Optional[int] = None) -> pd.DataFrame:
        """
        获取交易记录
        
        Args:
            pair_name: 配对名称（可选）
            start_time: 起始时间戳（可选）
            end_time: 结束时间戳（可选）
        
        Returns:
            交易记录DataFrame
        """
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if pair_name:
            query += " AND pair_name = ?"
            params.append(pair_name)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC"
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e:
            logger.error(f"获取交易记录失败: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_prices(self, symbol: str, start_time: Optional[int] = None,
                   end_time: Optional[int] = None) -> pd.DataFrame:
        """
        获取价格数据
        
        Args:
            symbol: 交易对符号
            start_time: 起始时间戳（可选）
            end_time: 结束时间戳（可选）
        
        Returns:
            价格数据DataFrame
        """
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM prices WHERE symbol = ?"
        params = [symbol]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp ASC"
        
        try:
            df = pd.read_sql_query(query, conn, params=params)
            if not df.empty:
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('datetime', inplace=True)
            return df
        except Exception as e:
            logger.error(f"获取价格数据失败: {str(e)}")
            return pd.DataFrame()
        finally:
            conn.close()

