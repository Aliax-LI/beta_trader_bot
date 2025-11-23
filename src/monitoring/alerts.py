"""警报系统模块"""
from typing import Dict, List, Optional
from enum import Enum
from src.utils.logger import setup_logger
from src.utils.time_utils import get_current_timestamp

logger = setup_logger(__name__)


class AlertLevel(Enum):
    """警报级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert:
    """警报类"""
    
    def __init__(self, level: AlertLevel, message: str, 
                 pair_name: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        初始化警报
        
        Args:
            level: 警报级别
            message: 警报消息
            pair_name: 配对名称（可选）
            metadata: 元数据（可选）
        """
        self.level = level
        self.message = message
        self.pair_name = pair_name
        self.metadata = metadata or {}
        self.timestamp = get_current_timestamp()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'level': self.level.value,
            'message': self.message,
            'pair_name': self.pair_name,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class AlertManager:
    """警报管理器"""
    
    def __init__(self):
        """初始化警报管理器"""
        self.alerts: List[Alert] = []
        self.max_alerts = 1000  # 最大保存警报数量
        logger.info("警报管理器初始化完成")
    
    def add_alert(self, level: AlertLevel, message: str,
                  pair_name: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        添加警报
        
        Args:
            level: 警报级别
            message: 警报消息
            pair_name: 配对名称
            metadata: 元数据
        """
        alert = Alert(level, message, pair_name, metadata)
        self.alerts.append(alert)
        
        # 限制警报数量
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 记录日志
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.info)
        
        log_msg = f"[{pair_name}] {message}" if pair_name else message
        log_method(log_msg)
    
    def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """
        获取最近的警报
        
        Args:
            limit: 返回数量限制
        
        Returns:
            警报列表
        """
        return self.alerts[-limit:]
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """
        按级别获取警报
        
        Args:
            level: 警报级别
        
        Returns:
            警报列表
        """
        return [alert for alert in self.alerts if alert.level == level]
    
    def clear_alerts(self):
        """清空警报"""
        self.alerts.clear()
        logger.info("警报已清空")
    
    def alert_high_zscore(self, pair_name: str, zscore: float, threshold: float):
        """Z-score过高警报"""
        self.add_alert(
            AlertLevel.WARNING,
            f"Z-score过高: {zscore:.2f} > {threshold}",
            pair_name,
            {'zscore': zscore, 'threshold': threshold}
        )
    
    def alert_low_correlation(self, pair_name: str, correlation: float, threshold: float):
        """相关性过低警报"""
        self.add_alert(
            AlertLevel.WARNING,
            f"相关性过低: {correlation:.3f} < {threshold}",
            pair_name,
            {'correlation': correlation, 'threshold': threshold}
        )
    
    def alert_trade_execution(self, pair_name: str, success: bool, details: Dict):
        """交易执行警报"""
        level = AlertLevel.INFO if success else AlertLevel.ERROR
        message = f"交易执行{'成功' if success else '失败'}: {details.get('order_id', 'N/A')}"
        self.add_alert(level, message, pair_name, details)
    
    def alert_system_error(self, error_message: str, metadata: Optional[Dict] = None):
        """系统错误警报"""
        self.add_alert(
            AlertLevel.CRITICAL,
            f"系统错误: {error_message}",
            metadata=metadata
        )

