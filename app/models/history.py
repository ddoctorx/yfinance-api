"""
历史数据模型
定义K线数据、技术指标等结构
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class HistoryRecord(BaseModel):
    """单条历史记录"""

    date: datetime = Field(..., description="日期")
    open: Optional[float] = Field(default=None, description="开盘价")
    high: Optional[float] = Field(default=None, description="最高价")
    low: Optional[float] = Field(default=None, description="最低价")
    close: Optional[float] = Field(default=None, description="收盘价")
    volume: Optional[int] = Field(default=None, description="成交量")
    dividends: Optional[float] = Field(default=None, description="股息")
    stock_splits: Optional[float] = Field(default=None, description="拆股")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "date": "2024-01-02T00:00:00",
                "open": 184.01,
                "high": 186.77,
                "low": 183.93,
                "close": 186.15,
                "volume": 68987200,
                "dividends": 0.0,
                "stock_splits": 0.0
            }
        }


class HistoryData(BaseModel):
    """历史数据响应"""

    data: List[HistoryRecord] = Field(..., description="历史记录列表")
    period: str = Field(..., description="数据周期")
    interval: str = Field(..., description="数据间隔")
    total_records: int = Field(..., description="总记录数")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "date": "2024-01-02T00:00:00",
                        "open": 184.01,
                        "high": 186.77,
                        "low": 183.93,
                        "close": 186.15,
                        "volume": 68987200
                    }
                ],
                "period": "1y",
                "interval": "1d",
                "total_records": 252
            }
        }


class HistoryParams(BaseModel):
    """历史数据查询参数"""

    period: Optional[str] = Field(
        default="1y",
        description="数据周期",
        pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"
    )
    interval: Optional[str] = Field(
        default="1d",
        description="数据间隔",
        pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$"
    )
    start: Optional[str] = Field(
        default=None,
        description="开始日期 (YYYY-MM-DD)",
        pattern="^\\d{4}-\\d{2}-\\d{2}$"
    )
    end: Optional[str] = Field(
        default=None,
        description="结束日期 (YYYY-MM-DD)",
        pattern="^\\d{4}-\\d{2}-\\d{2}$"
    )
    auto_adjust: bool = Field(
        default=True,
        description="是否自动调整价格(除权除息)"
    )
    prepost: bool = Field(
        default=False,
        description="是否包含盘前盘后数据"
    )
    actions: bool = Field(
        default=True,
        description="是否包含分红和拆股信息"
    )

    @validator('start', 'end')
    def validate_date_format(cls, v):
        """验证日期格式"""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('日期格式必须是 YYYY-MM-DD')
        return v

    @validator('end')
    def validate_end_after_start(cls, v, values):
        """验证结束日期在开始日期之后"""
        start = values.get('start')
        if start and v:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(v, '%Y-%m-%d')
            if end_date <= start_date:
                raise ValueError('结束日期必须晚于开始日期')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "period": "1y",
                "interval": "1d",
                "start": "2024-01-01",
                "end": "2024-12-31",
                "auto_adjust": True,
                "prepost": False,
                "actions": True
            }
        }


class DividendRecord(BaseModel):
    """股息记录"""

    date: datetime = Field(..., description="除权日期")
    dividend: float = Field(..., description="股息金额")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SplitRecord(BaseModel):
    """拆股记录"""

    date: datetime = Field(..., description="拆股日期")
    stock_split: float = Field(..., description="拆股比例")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ActionsData(BaseModel):
    """股息和拆股数据"""

    dividends: List[DividendRecord] = Field(
        default_factory=list, description="股息记录")
    splits: List[SplitRecord] = Field(default_factory=list, description="拆股记录")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "dividends": [
                    {
                        "date": "2024-02-09T00:00:00",
                        "dividend": 0.24
                    }
                ],
                "splits": [
                    {
                        "date": "2020-08-31T00:00:00",
                        "stock_split": 4.0
                    }
                ]
            }
        }
