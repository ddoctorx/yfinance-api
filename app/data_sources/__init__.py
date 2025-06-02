"""
数据源模块
提供多数据源抽象层和降级机制
"""

from .base import DataSourceInterface, BaseDataSource, DataSourceError
from .yfinance_source import YFinanceDataSource
from .polygon_source import PolygonDataSource
from .fallback_manager import FallbackManager
from .sec_source import SecDataSource

__all__ = [
    "DataSourceInterface",
    "BaseDataSource",
    "DataSourceError",
    "YFinanceDataSource",
    "PolygonDataSource",
    "FallbackManager",
    "SecDataSource"
]
