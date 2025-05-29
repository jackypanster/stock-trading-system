"""
数据获取和管理模块

提供股票数据获取、缓存管理、调度等功能。
"""

from .fetcher import (
    StockDataFetcher,
    MockDataFetcher,
    FailingDataFetcher,
    DataFetchError
)
from .scheduler import (
    DataScheduler,
    MarketTimeChecker
)

# 为了向后兼容，提供DataManager别名
DataManager = StockDataFetcher

__all__ = [
    'StockDataFetcher',
    'MockDataFetcher', 
    'FailingDataFetcher',
    'DataFetchError',
    'DataScheduler',
    'MarketTimeChecker',
    'DataManager'  # 向后兼容别名
]
