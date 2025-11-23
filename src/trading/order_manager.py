"""订单管理模块"""
from typing import Dict, Optional, List
from enum import Enum
from src.utils.logger import setup_logger
from src.utils.time_utils import get_current_timestamp

logger = setup_logger(__name__)


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """订单类"""
    
    def __init__(self, order_id: str, pair_name: str, asset1: str, asset2: str,
                 side1: str, side2: str, quantity1: float, quantity2: float,
                 price1: Optional[float] = None, price2: Optional[float] = None,
                 order_type: str = "market"):
        """
        初始化订单
        
        Args:
            order_id: 订单ID
            pair_name: 配对名称
            asset1: 第一个资产符号
            asset2: 第二个资产符号
            side1: 第一个资产的交易方向 ('buy' 或 'sell')
            side2: 第二个资产的交易方向
            quantity1: 第一个资产的数量
            quantity2: 第二个资产的数量
            price1: 第一个资产的价格（限价单）
            price2: 第二个资产的价格（限价单）
            order_type: 订单类型 ('market' 或 'limit')
        """
        self.order_id = order_id
        self.pair_name = pair_name
        self.asset1 = asset1
        self.asset2 = asset2
        self.side1 = side1
        self.side2 = side2
        self.quantity1 = quantity1
        self.quantity2 = quantity2
        self.price1 = price1
        self.price2 = price2
        self.order_type = order_type
        self.status = OrderStatus.PENDING
        self.timestamp = get_current_timestamp()
        self.exchange_order_id1 = None
        self.exchange_order_id2 = None
        self.filled_quantity1 = 0.0
        self.filled_quantity2 = 0.0
        self.filled_price1 = 0.0
        self.filled_price2 = 0.0
    
    def update_status(self, status: OrderStatus):
        """
        更新订单状态
        
        Args:
            status: 新状态
        """
        self.status = status
        logger.debug(f"订单 {self.order_id} 状态更新为: {status.value}")
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'pair_name': self.pair_name,
            'asset1': self.asset1,
            'asset2': self.asset2,
            'side1': self.side1,
            'side2': self.side2,
            'quantity1': self.quantity1,
            'quantity2': self.quantity2,
            'price1': self.price1,
            'price2': self.price2,
            'order_type': self.order_type,
            'status': self.status.value,
            'timestamp': self.timestamp,
            'exchange_order_id1': self.exchange_order_id1,
            'exchange_order_id2': self.exchange_order_id2,
            'filled_quantity1': self.filled_quantity1,
            'filled_quantity2': self.filled_quantity2,
            'filled_price1': self.filled_price1,
            'filled_price2': self.filled_price2
        }


class OrderManager:
    """订单管理器"""
    
    def __init__(self):
        """初始化订单管理器"""
        self.orders: Dict[str, Order] = {}  # {order_id: Order}
        self._order_counter = 0
        logger.info("订单管理器初始化完成")
    
    def create_order(self, pair_name: str, asset1: str, asset2: str,
                    side1: str, side2: str, quantity1: float, quantity2: float,
                    price1: Optional[float] = None, price2: Optional[float] = None,
                    order_type: str = "market") -> Order:
        """
        创建订单
        
        Args:
            pair_name: 配对名称
            asset1: 第一个资产符号
            asset2: 第二个资产符号
            side1: 第一个资产的交易方向
            side2: 第二个资产的交易方向
            quantity1: 第一个资产的数量
            quantity2: 第二个资产的数量
            price1: 第一个资产的价格（限价单）
            price2: 第二个资产的价格（限价单）
            order_type: 订单类型
        
        Returns:
            订单对象
        """
        self._order_counter += 1
        order_id = f"order_{self._order_counter}_{get_current_timestamp()}"
        
        order = Order(
            order_id, pair_name, asset1, asset2,
            side1, side2, quantity1, quantity2,
            price1, price2, order_type
        )
        
        self.orders[order_id] = order
        logger.info(f"创建订单: {order_id}, {pair_name}, {side1} {asset1}, {side2} {asset2}")
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单
        
        Args:
            order_id: 订单ID
        
        Returns:
            订单对象（如果存在）
        """
        return self.orders.get(order_id)
    
    def get_orders_by_pair(self, pair_name: str) -> List[Order]:
        """
        获取指定配对的所有订单
        
        Args:
            pair_name: 配对名称
        
        Returns:
            订单列表
        """
        return [order for order in self.orders.values() if order.pair_name == pair_name]
    
    def get_pending_orders(self) -> List[Order]:
        """
        获取所有待处理订单
        
        Returns:
            订单列表
        """
        return [order for order in self.orders.values() 
                if order.status == OrderStatus.PENDING]
    
    def update_order(self, order_id: str, **kwargs):
        """
        更新订单信息
        
        Args:
            order_id: 订单ID
            **kwargs: 要更新的字段
        """
        order = self.orders.get(order_id)
        if order:
            for key, value in kwargs.items():
                if hasattr(order, key):
                    setattr(order, key, value)
            logger.debug(f"订单 {order_id} 已更新")

