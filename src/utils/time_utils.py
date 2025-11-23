"""时间工具模块"""
from datetime import datetime, timedelta
from typing import Optional
import pytz


def get_current_timestamp() -> int:
    """
    获取当前时间戳（毫秒）
    
    Returns:
        当前时间戳
    """
    return int(datetime.now().timestamp() * 1000)


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    将时间戳转换为datetime对象
    
    Args:
        timestamp: 时间戳（毫秒）
    
    Returns:
        datetime对象
    """
    return datetime.fromtimestamp(timestamp / 1000)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    将datetime对象转换为时间戳（毫秒）
    
    Args:
        dt: datetime对象
    
    Returns:
        时间戳
    """
    return int(dt.timestamp() * 1000)


def parse_date(date_str: str) -> datetime:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串（格式：YYYY-MM-DD）
    
    Returns:
        datetime对象
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化datetime对象
    
    Args:
        dt: datetime对象
        fmt: 格式字符串
    
    Returns:
        格式化后的字符串
    """
    return dt.strftime(fmt)


def get_utc_now() -> datetime:
    """
    获取当前UTC时间
    
    Returns:
        UTC datetime对象
    """
    return datetime.now(pytz.UTC)


def add_seconds(dt: datetime, seconds: int) -> datetime:
    """
    给datetime对象添加秒数
    
    Args:
        dt: datetime对象
        seconds: 要添加的秒数
    
    Returns:
        新的datetime对象
    """
    return dt + timedelta(seconds=seconds)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """
    给datetime对象添加分钟数
    
    Args:
        dt: datetime对象
        minutes: 要添加的分钟数
    
    Returns:
        新的datetime对象
    """
    return dt + timedelta(minutes=minutes)


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    给datetime对象添加小时数
    
    Args:
        dt: datetime对象
        hours: 要添加的小时数
    
    Returns:
        新的datetime对象
    """
    return dt + timedelta(hours=hours)

