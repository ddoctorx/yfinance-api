"""
报价数据模型
定义实时行情和快照数据的结构
"""

from typing import Optional
from pydantic import BaseModel, Field


class QuoteData(BaseModel):
    """实时报价数据"""

    # 基本价格信息
    last_price: Optional[float] = Field(default=None, description="最新价格")
    previous_close: Optional[float] = Field(default=None, description="前收盘价")
    open_price: Optional[float] = Field(default=None, description="开盘价")
    day_high: Optional[float] = Field(default=None, description="日最高价")
    day_low: Optional[float] = Field(default=None, description="日最低价")

    # 价格变化
    change: Optional[float] = Field(default=None, description="价格变化")
    change_percent: Optional[float] = Field(
        default=None, description="价格变化百分比")

    # 交易量
    volume: Optional[int] = Field(default=None, description="成交量")
    average_volume: Optional[int] = Field(default=None, description="平均成交量")

    # 市场数据
    market_cap: Optional[int] = Field(default=None, description="市值")
    shares_outstanding: Optional[int] = Field(default=None, description="流通股数")

    # 52周数据
    fifty_two_week_high: Optional[float] = Field(
        default=None, description="52周最高价")
    fifty_two_week_low: Optional[float] = Field(
        default=None, description="52周最低价")

    # 估值指标
    pe_ratio: Optional[float] = Field(default=None, description="市盈率")
    forward_pe: Optional[float] = Field(default=None, description="前瞻市盈率")
    price_to_book: Optional[float] = Field(default=None, description="市净率")

    # 股息信息
    dividend_rate: Optional[float] = Field(default=None, description="股息率")
    dividend_yield: Optional[float] = Field(default=None, description="股息收益率")

    # 财务指标
    eps: Optional[float] = Field(default=None, description="每股收益")
    beta: Optional[float] = Field(default=None, description="贝塔系数")

    # 元信息
    currency: Optional[str] = Field(default=None, description="货币")
    exchange: Optional[str] = Field(default=None, description="交易所")
    sector: Optional[str] = Field(default=None, description="行业板块")
    industry: Optional[str] = Field(default=None, description="细分行业")

    class Config:
        json_schema_extra = {
            "example": {
                "last_price": 175.43,
                "previous_close": 174.21,
                "open_price": 175.00,
                "day_high": 176.80,
                "day_low": 173.50,
                "change": 1.22,
                "change_percent": 0.70,
                "volume": 52847300,
                "market_cap": 2745234567890,
                "pe_ratio": 28.45,
                "dividend_yield": 0.44,
                "currency": "USD",
                "exchange": "NASDAQ",
                "sector": "Technology"
            }
        }


class FastQuoteData(BaseModel):
    """快速报价数据(来自fast_info)"""

    last_price: Optional[float] = Field(default=None, description="最新价格")
    previous_close: Optional[float] = Field(default=None, description="前收盘价")
    open_price: Optional[float] = Field(default=None, description="开盘价")
    day_high: Optional[float] = Field(default=None, description="日最高价")
    day_low: Optional[float] = Field(default=None, description="日最低价")
    volume: Optional[int] = Field(default=None, description="成交量")
    market_cap: Optional[int] = Field(default=None, description="市值")
    shares: Optional[int] = Field(default=None, description="股数")
    currency: Optional[str] = Field(default=None, description="货币")

    # 计算字段
    @property
    def change(self) -> Optional[float]:
        """计算价格变化"""
        if self.last_price is not None and self.previous_close is not None:
            return self.last_price - self.previous_close
        return None

    @property
    def change_percent(self) -> Optional[float]:
        """计算价格变化百分比"""
        if self.last_price is not None and self.previous_close is not None and self.previous_close != 0:
            return ((self.last_price - self.previous_close) / self.previous_close) * 100
        return None


class CompanyInfo(BaseModel):
    """公司基本信息"""

    name: Optional[str] = Field(default=None, description="公司名称")
    sector: Optional[str] = Field(default=None, description="行业板块")
    industry: Optional[str] = Field(default=None, description="细分行业")
    country: Optional[str] = Field(default=None, description="国家")
    website: Optional[str] = Field(default=None, description="官网")
    business_summary: Optional[str] = Field(default=None, description="业务概述")
    employees: Optional[int] = Field(default=None, description="员工数量")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "country": "United States",
                "website": "https://www.apple.com",
                "business_summary": "Apple Inc. designs, manufactures, and markets smartphones...",
                "employees": 164000
            }
        }
