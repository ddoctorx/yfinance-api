"""
SEC财报数据模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal


class SecFilingInfo(BaseModel):
    """SEC文件基本信息"""
    accession_number: str = Field(description="文件接收号")
    filing_type: str = Field(description="文件类型 (10-K, 10-Q等)")
    filing_date: datetime = Field(description="文件日期")
    period_of_report: datetime = Field(description="报告期")
    company_name: str = Field(description="公司名称")
    cik: str = Field(description="CIK编号")
    ticker: Optional[str] = Field(None, description="股票代码")


class FinancialStatement(BaseModel):
    """财务报表基本模型"""
    concept: str = Field(description="财务概念名称")
    label: str = Field(description="显示标签")
    value: Optional[Decimal] = Field(None, description="数值")
    unit: Optional[str] = Field(None, description="单位")
    period: str = Field(description="报告期")
    form: str = Field(description="表单类型")


class IncomeStatementData(BaseModel):
    """损益表数据"""
    revenue: Optional[Decimal] = Field(None, description="营业收入")
    cost_of_revenue: Optional[Decimal] = Field(None, description="营业成本")
    gross_profit: Optional[Decimal] = Field(None, description="毛利润")
    operating_income: Optional[Decimal] = Field(None, description="营业利润")
    net_income: Optional[Decimal] = Field(None, description="净利润")
    earnings_per_share: Optional[Decimal] = Field(None, description="每股收益")
    period: str = Field(description="报告期")
    form_type: str = Field(description="表单类型")


class BalanceSheetData(BaseModel):
    """资产负债表数据"""
    total_assets: Optional[Decimal] = Field(None, description="总资产")
    total_liabilities: Optional[Decimal] = Field(None, description="总负债")
    stockholders_equity: Optional[Decimal] = Field(None, description="股东权益")
    cash_and_equivalents: Optional[Decimal] = Field(None, description="现金及等价物")
    period: str = Field(description="报告期")
    form_type: str = Field(description="表单类型")


class CashFlowData(BaseModel):
    """现金流量表数据"""
    operating_cash_flow: Optional[Decimal] = Field(None, description="经营现金流")
    investing_cash_flow: Optional[Decimal] = Field(None, description="投资现金流")
    financing_cash_flow: Optional[Decimal] = Field(None, description="筹资现金流")
    free_cash_flow: Optional[Decimal] = Field(None, description="自由现金流")
    period: str = Field(description="报告期")
    form_type: str = Field(description="表单类型")


class QuarterlyFinancials(BaseModel):
    """季度财务数据"""
    quarter: str = Field(description="季度 (如 Q1 2024)")
    filing_date: datetime = Field(description="文件日期")
    period_end_date: datetime = Field(description="期末日期")
    income_statement: Optional[IncomeStatementData] = Field(
        None, description="损益表")
    balance_sheet: Optional[BalanceSheetData] = Field(
        None, description="资产负债表")
    cash_flow: Optional[CashFlowData] = Field(None, description="现金流量表")


class AnnualFinancials(BaseModel):
    """年度财务数据"""
    year: int = Field(description="年份")
    filing_date: datetime = Field(description="文件日期")
    period_end_date: datetime = Field(description="期末日期")
    income_statement: Optional[IncomeStatementData] = Field(
        None, description="损益表")
    balance_sheet: Optional[BalanceSheetData] = Field(
        None, description="资产负债表")
    cash_flow: Optional[CashFlowData] = Field(None, description="现金流量表")


class CompanyFinancialsResponse(BaseModel):
    """公司财务数据响应"""
    ticker: str = Field(description="股票代码")
    company_name: str = Field(description="公司名称")
    cik: str = Field(description="CIK编号")
    last_updated: datetime = Field(description="最后更新时间")
    annual_reports: List[AnnualFinancials] = Field(description="年度报告")
    quarterly_reports: List[QuarterlyFinancials] = Field(description="季度报告")


class SecNewsItem(BaseModel):
    """SEC新闻条目"""
    title: str = Field(description="新闻标题")
    summary: Optional[str] = Field(None, description="新闻摘要")
    link: str = Field(description="新闻链接")
    publication_date: datetime = Field(description="发布日期")
    form_type: Optional[str] = Field(None, description="文件类型")


class SecNewsResponse(BaseModel):
    """SEC新闻响应"""
    ticker: str = Field(description="股票代码")
    company_name: str = Field(description="公司名称")
    news_items: List[SecNewsItem] = Field(description="新闻列表")
    total_count: int = Field(description="新闻总数")
    last_updated: datetime = Field(description="最后更新时间")


class FinancialRatios(BaseModel):
    """财务比率"""
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    debt_to_equity: Optional[float] = Field(None, description="负债权益比")
    current_ratio: Optional[float] = Field(None, description="流动比率")
    roa: Optional[float] = Field(None, description="资产回报率")
    roe: Optional[float] = Field(None, description="净资产收益率")
    period: str = Field(description="计算期间")


class SecErrorResponse(BaseModel):
    """SEC API错误响应"""
    error: str = Field(description="错误信息")
    error_code: str = Field(description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
