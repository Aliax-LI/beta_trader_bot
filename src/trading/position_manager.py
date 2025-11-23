"""仓位管理模块"""
from typing import Dict, Optional, List
from src.utils.logger import setup_logger
from src.utils.time_utils import get_current_timestamp

logger = setup_logger(__name__)


class Position:
    """仓位类"""
    
    def __init__(self, pair_name: str, asset1: str, asset2: str,
                 quantity1: float, quantity2: float, entry_zscore: float,
                 entry_price1: float, entry_price2: float):
        """
        初始化仓位
        
        Args:
            pair_name: 配对名称
            asset1: 第一个资产符号
            asset2: 第二个资产符号
            quantity1: 第一个资产的数量（正数表示多头，负数表示空头）
            quantity2: 第二个资产的数量
            entry_zscore: 入场Z-score
            entry_price1: 第一个资产的入场价格
            entry_price2: 第二个资产的入场价格
        """
        self.pair_name = pair_name
        self.asset1 = asset1
        self.asset2 = asset2
        self.quantity1 = quantity1
        self.quantity2 = quantity2
        self.entry_zscore = entry_zscore
        self.entry_price1 = entry_price1
        self.entry_price2 = entry_price2
        self.entry_timestamp = get_current_timestamp()
        self.exit_timestamp = None
        self.exit_price1 = None
        self.exit_price2 = None
        self.pnl = 0.0
        self.is_closed = False
    
    def close(self, exit_price1: float, exit_price2: float):
        """
        平仓
        
        Args:
            exit_price1: 第一个资产的出场价格
            exit_price2: 第二个资产的出场价格
        """
        self.exit_price1 = exit_price1
        self.exit_price2 = exit_price2
        self.exit_timestamp = get_current_timestamp()
        
        # 计算盈亏
        pnl1 = (exit_price1 - self.entry_price1) * self.quantity1
        pnl2 = (exit_price2 - self.entry_price2) * self.quantity2
        self.pnl = pnl1 + pnl2
        
        self.is_closed = True
        logger.info(f"仓位已平仓: {self.pair_name}, PnL={self.pnl:.2f}")
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'pair_name': self.pair_name,
            'asset1': self.asset1,
            'asset2': self.asset2,
            'quantity1': self.quantity1,
            'quantity2': self.quantity2,
            'entry_zscore': self.entry_zscore,
            'entry_price1': self.entry_price1,
            'entry_price2': self.entry_price2,
            'entry_timestamp': self.entry_timestamp,
            'exit_timestamp': self.exit_timestamp,
            'exit_price1': self.exit_price1,
            'exit_price2': self.exit_price2,
            'pnl': self.pnl,
            'is_closed': self.is_closed
        }


class PositionManager:
    """仓位管理器"""
    
    def __init__(self):
        """初始化仓位管理器"""
        self.positions: Dict[str, Position] = {}  # {pair_name: Position}
        logger.info("仓位管理器初始化完成")
    
    def open_position(self, pair_name: str, asset1: str, asset2: str,
                     quantity1: float, quantity2: float, entry_zscore: float,
                     entry_price1: float, entry_price2: float) -> Position:
        """
        开仓
        
        Args:
            pair_name: 配对名称
            asset1: 第一个资产符号
            asset2: 第二个资产符号
            quantity1: 第一个资产的数量
            quantity2: 第二个资产的数量
            entry_zscore: 入场Z-score
            entry_price1: 第一个资产的入场价格
            entry_price2: 第二个资产的入场价格
        
        Returns:
            仓位对象
        """
        if pair_name in self.positions and not self.positions[pair_name].is_closed:
            logger.warning(f"{pair_name} 已有未平仓位，无法开新仓")
            return self.positions[pair_name]
        
        position = Position(
            pair_name, asset1, asset2,
            quantity1, quantity2, entry_zscore,
            entry_price1, entry_price2
        )
        
        self.positions[pair_name] = position
        logger.info(f"开仓: {pair_name}, q1={quantity1:.4f}, q2={quantity2:.4f}")
        return position
    
    def close_position(self, pair_name: str, exit_price1: float, 
                      exit_price2: float) -> Optional[Position]:
        """
        平仓
        
        Args:
            pair_name: 配对名称
            exit_price1: 第一个资产的出场价格
            exit_price2: 第二个资产的出场价格
        
        Returns:
            仓位对象（如果存在）
        """
        if pair_name not in self.positions:
            logger.warning(f"{pair_name} 没有持仓")
            return None
        
        position = self.positions[pair_name]
        
        if position.is_closed:
            logger.warning(f"{pair_name} 仓位已关闭")
            return position
        
        position.close(exit_price1, exit_price2)
        return position
    
    def get_position(self, pair_name: str) -> Optional[Position]:
        """
        获取仓位
        
        Args:
            pair_name: 配对名称
        
        Returns:
            仓位对象（如果存在）
        """
        return self.positions.get(pair_name)
    
    def get_all_positions(self, include_closed: bool = False) -> List[Position]:
        """
        获取所有仓位
        
        Args:
            include_closed: 是否包含已平仓的仓位
        
        Returns:
            仓位列表
        """
        if include_closed:
            return list(self.positions.values())
        else:
            return [p for p in self.positions.values() if not p.is_closed]
    
    def has_position(self, pair_name: str) -> bool:
        """
        检查是否有持仓
        
        Args:
            pair_name: 配对名称
        
        Returns:
            是否有持仓
        """
        position = self.positions.get(pair_name)
        return position is not None and not position.is_closed
    
    def get_total_pnl(self) -> float:
        """
        获取总盈亏（仅已平仓的仓位）
        
        Returns:
            总盈亏
        """
        closed_positions = [p for p in self.positions.values() if p.is_closed]
        return sum(p.pnl for p in closed_positions)

