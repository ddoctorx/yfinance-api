"""
数据适配器模块
提供不同数据源的数据格式转换和标准化
"""

from .base import DataAdapterInterface, BaseDataAdapter
from .polygon_adapter import PolygonDataAdapter
from .data_normalizer import DataNormalizer

__all__ = [
    "DataAdapterInterface",
    "BaseDataAdapter",
    "PolygonDataAdapter",
    "DataNormalizer"
]
