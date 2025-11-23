"""风险管理模块"""
from typing import Dict, Optional, Tuple
from src.utils.logger import setup_logger
from src.utils.helpers import safe_divide

logger = setup_logger(__name__)


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Dict):
        """
        初始化风险管理器
        
        Args:
            config: 风险配置字典
        """
        self.max_position_size = config.get('max_position', 0.2)  # 最大仓位比例
        self.position_size = config.get('position_size', 0.1)  # 默认仓位大小
        self.stop_loss_z = config.get('stop_loss_z', 3.0)  # 止损Z-score阈值
        self.max_correlation_deviation = config.get('max_correlation_deviation', 0.2)  # 最大相关性偏差
        logger.info("风险管理器初始化完成")
    
    def calculate_position_size(self, account_balance: float, 
                               base_position_size: Optional[float] = None) -> float:
        """
        计算仓位大小
        
        Args:
            account_balance: 账户余额
            base_position_size: 基础仓位大小（可选）
        
        Returns:
            仓位大小（金额）
        """
        size = base_position_size if base_position_size is not None else self.position_size
        position_amount = account_balance * size
        
        # 确保不超过最大仓位限制
        max_amount = account_balance * self.max_position_size
        return min(position_amount, max_amount)
    
    def check_stop_loss(self, current_zscore: float, entry_zscore: float) -> bool:
        """
        检查是否触发止损
        
        Args:
            current_zscore: 当前Z-score
            entry_zscore: 入场Z-score
        
        Returns:
            是否触发止损
        """
        # 如果价差进一步扩大（与入场方向相反），触发止损
        if entry_zscore > 0:  # 做空价差入场
            if current_zscore > self.stop_loss_z:
                logger.warning(f"触发止损: 当前Z-score {current_zscore:.2f} > 止损阈值 {self.stop_loss_z}")
                return True
        elif entry_zscore < 0:  # 做多价差入场
            if current_zscore < -self.stop_loss_z:
                logger.warning(f"触发止损: 当前Z-score {current_zscore:.2f} < 止损阈值 {-self.stop_loss_z}")
                return True
        
        return False
    
    def validate_correlation(self, current_correlation: float, 
                            base_correlation: float) -> bool:
        """
        验证相关性是否在可接受范围内
        
        Args:
            current_correlation: 当前相关性
            base_correlation: 基准相关性
        
        Returns:
            相关性是否有效
        """
        deviation = abs(current_correlation - base_correlation)
        
        if deviation > self.max_correlation_deviation:
            logger.warning(
                f"相关性偏差过大: 当前={current_correlation:.3f}, "
                f"基准={base_correlation:.3f}, 偏差={deviation:.3f}"
            )
            return False
        
        return True
    
    def check_max_drawdown(self, current_equity: float, peak_equity: float) -> Tuple[bool, float]:
        """
        检查最大回撤
        
        Args:
            current_equity: 当前权益
            peak_equity: 峰值权益
        
        Returns:
            (是否超过限制, 回撤比例)
        """
        if peak_equity == 0:
            return False, 0.0
        
        drawdown = safe_divide(peak_equity - current_equity, peak_equity)
        max_drawdown_limit = 0.3  # 30%最大回撤限制
        
        if drawdown > max_drawdown_limit:
            logger.warning(f"回撤超过限制: {drawdown*100:.2f}% > {max_drawdown_limit*100}%")
            return True, drawdown
        
        return False, drawdown
    
    def calculate_risk_metrics(self, trades: list) -> Dict:
        """
        计算风险指标
        
        Args:
            trades: 交易记录列表
        
        Returns:
            风险指标字典
        """
        if not trades:
            return {}
        
        # 计算胜率
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        # 计算平均盈亏
        pnls = [t.get('pnl', 0) for t in trades]
        avg_profit = sum([p for p in pnls if p > 0]) / len([p for p in pnls if p > 0]) if any(p > 0 for p in pnls) else 0
        avg_loss = sum([p for p in pnls if p < 0]) / len([p for p in pnls if p < 0]) if any(p < 0 for p in pnls) else 0
        
        # 计算盈亏比
        profit_loss_ratio = abs(safe_divide(avg_profit, avg_loss)) if avg_loss != 0 else 0
        
        return {
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'total_trades': len(trades)
        }

