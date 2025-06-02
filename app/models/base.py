"""
基础数据模型
定义通用的响应格式和基础模型
"""

from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

# 用于泛型响应的类型变量
T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """通用API响应格式"""

    symbol: str = Field(..., description="股票代码")
    data: T = Field(..., description="响应数据")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="响应时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ErrorResponse(BaseModel):
    """错误响应格式"""

    detail: str = Field(..., description="错误详情")
    code: str = Field(..., description="错误代码")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="额外错误信息")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(default="healthy", description="服务状态")
    version: str = Field(..., description="API版本")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="检查时间")
    dependencies: Dict[str, str] = Field(
        default_factory=dict, description="依赖服务状态")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")

    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class DateRange(BaseModel):
    """日期范围"""

    start: Optional[datetime] = Field(default=None, description="开始日期")
    end: Optional[datetime] = Field(default=None, description="结束日期")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class CacheInfo(BaseModel):
    """缓存信息"""

    backend: str = Field(..., description="缓存后端类型")
    ttl_seconds: int = Field(..., description="缓存过期时间(秒)")
    redis_url: Optional[str] = Field(default=None, description="Redis连接URL")


class BatchRequest(BaseModel):
    """批量请求"""

    symbols: list[str] = Field(..., min_items=1,
                               max_items=10, description="股票代码列表")

    class Config:
        json_schema_extra = {
            "example": {
                "symbols": ["AAPL", "MSFT", "GOOGL"]
            }
        }


class BatchResponse(BaseModel, Generic[T]):
    """批量响应格式"""

    data: Dict[str, T] = Field(..., description="按symbol分组的响应数据")
    errors: Dict[str, str] = Field(
        default_factory=dict, description="按symbol分组的错误信息")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="响应时间戳")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
