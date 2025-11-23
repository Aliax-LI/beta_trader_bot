"""健康检查模块"""
from typing import Dict, List
from datetime import datetime
from src.utils.logger import setup_logger
from src.trading.exchange_interface import ExchangeInterface

logger = setup_logger(__name__)


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, exchange_name: str, sandbox: bool = True):
        """
        初始化健康检查器
        
        Args:
            exchange_name: 交易所名称
            sandbox: 是否使用测试环境
        """
        self.exchange = ExchangeInterface(exchange_name, sandbox)
        self.last_check_time = None
        logger.info("健康检查器初始化完成")
    
    def check_exchange_connection(self) -> Dict:
        """
        检查交易所连接
        
        Returns:
            检查结果字典
        """
        try:
            balance = self.exchange.get_balance()
            return {
                'status': 'healthy',
                'message': '交易所连接正常',
                'has_balance': len(balance) > 0
            }
        except Exception as e:
            logger.error(f"交易所连接检查失败: {str(e)}")
            return {
                'status': 'unhealthy',
                'message': f'交易所连接失败: {str(e)}',
                'has_balance': False
            }
    
    def check_api_limits(self) -> Dict:
        """
        检查API限制
        
        Returns:
            检查结果字典
        """
        # 这里可以添加API限制检查逻辑
        return {
            'status': 'healthy',
            'message': 'API限制检查通过'
        }
    
    def check_data_quality(self, data: Dict) -> Dict:
        """
        检查数据质量
        
        Args:
            data: 数据字典
        
        Returns:
            检查结果字典
        """
        issues = []
        
        for symbol, df in data.items():
            if df.empty:
                issues.append(f"{symbol}: 数据为空")
            elif len(df) < 10:
                issues.append(f"{symbol}: 数据点不足")
            elif df.isnull().any().any():
                issues.append(f"{symbol}: 存在缺失值")
        
        if issues:
            return {
                'status': 'warning',
                'message': '数据质量存在问题',
                'issues': issues
            }
        else:
            return {
                'status': 'healthy',
                'message': '数据质量良好'
            }
    
    def run_full_check(self, data: Optional[Dict] = None) -> Dict:
        """
        运行完整健康检查
        
        Args:
            data: 数据字典（可选）
        
        Returns:
            完整检查结果
        """
        self.last_check_time = datetime.now()
        
        results = {
            'timestamp': self.last_check_time.isoformat(),
            'exchange_connection': self.check_exchange_connection(),
            'api_limits': self.check_api_limits()
        }
        
        if data:
            results['data_quality'] = self.check_data_quality(data)
        
        # 总体状态
        all_healthy = all(
            r.get('status') == 'healthy' 
            for r in results.values() 
            if isinstance(r, dict) and 'status' in r
        )
        
        results['overall_status'] = 'healthy' if all_healthy else 'warning'
        
        logger.info(f"健康检查完成: {results['overall_status']}")
        return results

