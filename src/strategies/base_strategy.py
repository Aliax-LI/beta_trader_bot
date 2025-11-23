"""策略基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseStrategy(ABC):
    """策略基类，所有策略都应继承此类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化策略
        
        Args:
            config: 策略配置字典
        """
        self.config = config
        self.name = config.get('name', self.__class__.__name__)
        logger.info(f"初始化策略: {self.name}")
    
    @abstractmethod
    def calculate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        计算交易信号（子类必须实现）
        
        Args:
            data: 包含价格数据的字典
        
        Returns:
            信号字典，包含：
            - signal: 信号类型 ('buy', 'sell', 'close', 'hold')
            - quantity1: 第一个资产的交易数量
            - quantity2: 第二个资产的交易数量
            - zscore: 当前Z-score
            - metadata: 其他元数据
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """
        验证数据有效性（子类必须实现）
        
        Args:
            data: 包含价格数据的字典
        
        Returns:
            数据是否有效
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取策略配置
        
        Returns:
            配置字典
        """
        return self.config
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新策略配置
        
        Args:
            new_config: 新的配置字典
        """
        self.config.update(new_config)
        logger.info(f"策略 {self.name} 配置已更新")

