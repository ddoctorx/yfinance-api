"""
yfinance 数据源包装器
将现有的 yfinance_service 包装为标准数据源接口
"""

from typing import Dict, List, Optional, Any

from .base import BaseDataSource, DataSourceType
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.services.yfinance_service import yfinance_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class YFinanceDataSource(BaseDataSource):
    """yfinance 数据源包装器"""

    def __init__(self):
        super().__init__(DataSourceType.YFINANCE, "Yahoo Finance")
        self.service = yfinance_service

    async def get_fast_quote(self, symbol: str) -> FastQuoteData:
        """获取快速报价数据"""
        async def _fetch():
            return await self.service.get_fast_quote(symbol)

        return await self.execute_with_metrics("get_fast_quote", _fetch)

    async def get_detailed_quote(self, symbol: str) -> QuoteData:
        """获取详细报价数据"""
        async def _fetch():
            return await self.service.get_detailed_quote(symbol)

        return await self.execute_with_metrics("get_detailed_quote", _fetch)

    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """获取公司信息"""
        async def _fetch():
            return await self.service.get_company_info(symbol)

        return await self.execute_with_metrics("get_company_info", _fetch)

    async def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        auto_adjust: bool = True,
        prepost: bool = True,
        actions: bool = True
    ) -> Dict[str, Any]:
        """获取历史数据"""
        async def _fetch():
            return await self.service.get_history(
                symbol=symbol,
                period=period,
                interval=interval,
                start=start,
                end=end,
                auto_adjust=auto_adjust,
                prepost=prepost,
                actions=actions
            )

        return await self.execute_with_metrics("get_history", _fetch)

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, FastQuoteData]:
        """批量获取报价数据"""
        async def _fetch():
            return await self.service.get_batch_quotes(symbols)

        return await self.execute_with_metrics("get_batch_quotes", _fetch)
