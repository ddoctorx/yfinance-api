"""
数据适配器基类
定义数据格式转换的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo


class DataAdapterInterface(ABC):
    """数据适配器接口"""

    @abstractmethod
    def adapt_fast_quote(self, raw_data: Dict[str, Any]) -> FastQuoteData:
        """转换快速报价数据"""
        pass

    @abstractmethod
    def adapt_detailed_quote(self, raw_data: Dict[str, Any]) -> QuoteData:
        """转换详细报价数据"""
        pass

    @abstractmethod
    def adapt_company_info(self, raw_data: Dict[str, Any]) -> CompanyInfo:
        """转换公司信息数据"""
        pass

    @abstractmethod
    def adapt_history_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """转换历史数据"""
        pass


class BaseDataAdapter(DataAdapterInterface):
    """数据适配器基类"""

    def safe_get_float(self, data: Dict[str, Any], key: str, default: float = None) -> Optional[float]:
        """安全获取浮点数值"""
        value = data.get(key, default)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def safe_get_int(self, data: Dict[str, Any], key: str, default: int = None) -> Optional[int]:
        """安全获取整数值"""
        value = data.get(key, default)
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def safe_get_str(self, data: Dict[str, Any], key: str, default: str = None) -> Optional[str]:
        """安全获取字符串值"""
        value = data.get(key, default)
        if value is None:
            return None
        return str(value).strip() if value else default

    def safe_float_from_attr(self, obj, attr_name: str, default: float = None) -> Optional[float]:
        """从对象属性安全获取浮点数值"""
        if not obj or not hasattr(obj, attr_name):
            return default
        value = getattr(obj, attr_name, default)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def safe_int_from_attr(self, obj, attr_name: str, default: int = None) -> Optional[int]:
        """从对象属性安全获取整数值"""
        if not obj or not hasattr(obj, attr_name):
            return default
        value = getattr(obj, attr_name, default)
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def safe_str_from_attr(self, obj, attr_name: str, default: str = None) -> Optional[str]:
        """从对象属性安全获取字符串值"""
        if not obj or not hasattr(obj, attr_name):
            return default
        value = getattr(obj, attr_name, default)
        if value is None:
            return None
        return str(value).strip() if value else default

    def calculate_change_metrics(self, current_price: float, previous_close: float) -> tuple:
        """计算价格变化指标"""
        if not current_price or not previous_close or previous_close == 0:
            return None, None

        change = current_price - previous_close
        change_percent = (change / previous_close) * 100
        return change, change_percent
