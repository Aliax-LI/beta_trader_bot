"""辅助函数模块"""
import os
from typing import Any, Dict, Optional
from pathlib import Path
import yaml
from dotenv import load_dotenv


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_env_file(env_path: str = ".env") -> None:
    """
    加载环境变量文件
    
    Args:
        env_path: .env文件路径
    """
    if os.path.exists(env_path):
        load_dotenv(env_path)


def ensure_dir(directory: str) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    获取环境变量
    
    Args:
        key: 环境变量键
        default: 默认值
    
    Returns:
        环境变量值
    """
    return os.getenv(key, default)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法，避免除零错误
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 默认值（当分母为0时返回）
    
    Returns:
        除法结果
    """
    if denominator == 0:
        return default
    return numerator / denominator

