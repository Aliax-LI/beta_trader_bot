"""监控面板模块"""
from typing import Dict, Optional
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Dashboard:
    """监控面板"""
    
    def __init__(self):
        """初始化监控面板"""
        logger.info("监控面板初始化完成")
    
    def get_status_summary(self, account_info: Dict, positions: list, 
                          alerts: list) -> Dict:
        """
        获取状态摘要
        
        Args:
            account_info: 账户信息
            positions: 持仓列表
            alerts: 警报列表
        
        Returns:
            状态摘要字典
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'account': {
                'balance': account_info.get('balance', {}),
                'total_pnl': account_info.get('total_pnl', 0),
                'open_positions': account_info.get('open_positions', 0)
            },
            'positions': [p.to_dict() if hasattr(p, 'to_dict') else p for p in positions],
            'recent_alerts': [a.to_dict() if hasattr(a, 'to_dict') else a for a in alerts[-10:]]
        }
    
    def format_status_report(self, status: Dict) -> str:
        """
        格式化状态报告
        
        Args:
            status: 状态字典
        
        Returns:
            格式化的报告字符串
        """
        report = f"""
========== 系统状态报告 ==========
时间: {status.get('timestamp', 'N/A')}

账户信息:
  总盈亏: {status.get('account', {}).get('total_pnl', 0):.2f}
  持仓数量: {status.get('account', {}).get('open_positions', 0)}

持仓详情:
"""
        for pos in status.get('positions', []):
            if isinstance(pos, dict):
                report += f"  - {pos.get('pair_name', 'N/A')}: "
                report += f"PnL={pos.get('pnl', 0):.2f}, "
                report += f"状态={'已平仓' if pos.get('is_closed') else '持仓中'}\n"
        
        report += "\n最近警报:\n"
        for alert in status.get('recent_alerts', []):
            if isinstance(alert, dict):
                report += f"  [{alert.get('level', 'N/A')}] {alert.get('message', 'N/A')}\n"
        
        report += "============================\n"
        return report

