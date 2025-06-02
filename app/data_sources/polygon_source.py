"""
Polygon.io 数据源实现
提供对 Polygon.io API 的封装和调用
使用官方的 polygon-api-client 库
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date
import concurrent.futures

from polygon import RESTClient
from polygon.rest.models import (
    TickerSnapshot,
    TickerDetails,
    Agg,
)

from .base import BaseDataSource, DataSourceType
from app.adapters.polygon_adapter import PolygonDataAdapter
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.models.history import HistoryData
from app.core.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import TickerNotFoundError, YahooAPIError

logger = get_logger(__name__)


class PolygonDataSource(BaseDataSource):
    """Polygon.io 数据源 - 使用官方客户端"""

    def __init__(self):
        super().__init__(DataSourceType.POLYGON, "Polygon.io")
        self.client = None
        self.adapter = PolygonDataAdapter()

        # 速率限制配置
        self.rate_limit_delay = 1.0  # 请求间隔（秒）
        self.last_request_time = 0

        logger.info("Polygon.io数据源初始化完成", use_official_client=True)

    def _ensure_client(self):
        """确保客户端已初始化"""
        if self.client is None:
            api_key = settings.polygon_api_key
            if not api_key:
                raise ValueError("POLYGON_API_KEY未配置")

            self.client = RESTClient(api_key=api_key)
            logger.debug("Polygon.io客户端初始化完成")

    async def _make_sync_call(self, func, *args, **kwargs):
        """将同步调用转换为异步调用"""
        loop = asyncio.get_event_loop()

        # 使用线程池执行同步操作
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, func, *args, **kwargs)

        return result

    async def _rate_limit(self):
        """实施速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug("速率限制等待", sleep_time=sleep_time)
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    async def get_fast_quote(self, symbol: str) -> FastQuoteData:
        """获取快速报价数据"""
        try:
            logger.debug("获取Polygon快速报价", symbol=symbol)
            self._ensure_client()

            # 使用正确的最新交易和报价API调用方式
            def get_last_quote():
                return self.client.get_last_quote(ticker=symbol)

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                quote = await loop.run_in_executor(executor, get_last_quote)

            # 使用适配器转换数据
            quote_data = self.adapter.adapt_fast_quote_from_quote(quote)

            logger.debug("Polygon快速报价获取成功",
                         symbol=symbol,
                         price=quote_data.last_price)

            return quote_data

        except Exception as e:
            logger.error("Polygon快速报价获取失败",
                         symbol=symbol,
                         error=str(e))
            raise TickerNotFoundError(f"无法获取 {symbol} 的Polygon快速报价: {str(e)}")

    async def get_detailed_quote(self, symbol: str) -> QuoteData:
        """获取详细报价数据"""
        try:
            logger.debug("获取Polygon详细报价", symbol=symbol)
            self._ensure_client()

            # 获取最新报价和ticker详情
            def get_quote_and_details():
                quote = self.client.get_last_quote(ticker=symbol)
                details = self.client.get_ticker_details(symbol)
                return quote, details

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                quote, details = await loop.run_in_executor(executor, get_quote_and_details)

            # 使用适配器转换数据
            quote_data = self.adapter.adapt_detailed_quote_from_quote_and_details(
                quote, details)

            logger.debug("Polygon详细报价获取成功",
                         symbol=symbol,
                         price=quote_data.last_price)

            return quote_data

        except Exception as e:
            logger.error("Polygon详细报价获取失败",
                         symbol=symbol,
                         error=str(e))
            raise TickerNotFoundError(f"无法获取 {symbol} 的Polygon详细报价: {str(e)}")

    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """获取公司信息"""
        try:
            logger.debug("获取Polygon公司信息", symbol=symbol)
            self._ensure_client()

            # 使用ticker详情API
            def get_ticker_details():
                return self.client.get_ticker_details(symbol)

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                details = await loop.run_in_executor(executor, get_ticker_details)

            # 使用适配器转换数据
            company_info = self.adapter.adapt_company_info_from_details(
                details)

            logger.debug("Polygon公司信息获取成功",
                         symbol=symbol,
                         name=company_info.name)

            return company_info

        except Exception as e:
            logger.error("Polygon公司信息获取失败",
                         symbol=symbol,
                         error=str(e))
            raise TickerNotFoundError(f"无法获取 {symbol} 的Polygon公司信息: {str(e)}")

    async def get_history_data(self,
                               symbol: str,
                               period: str = "1mo",
                               interval: str = "1d") -> HistoryData:
        """获取历史数据"""
        try:
            logger.debug("获取Polygon历史数据",
                         symbol=symbol,
                         period=period,
                         interval=interval)
            self._ensure_client()

            # 计算日期范围
            to_date = datetime.now().date()

            # 根据period计算from_date
            if period == "1mo":
                from_date = to_date - timedelta(days=30)
            elif period == "3mo":
                from_date = to_date - timedelta(days=90)
            elif period == "6mo":
                from_date = to_date - timedelta(days=180)
            elif period == "1y":
                from_date = to_date - timedelta(days=365)
            else:
                from_date = to_date - timedelta(days=30)  # 默认1个月

            # 使用聚合数据API
            def get_aggregate_bars():
                return list(self.client.list_aggs(
                    ticker=symbol,
                    multiplier=1,
                    timespan="day",
                    from_=from_date.strftime("%Y-%m-%d"),
                    to=to_date.strftime("%Y-%m-%d"),
                    limit=50000
                ))

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                aggs = await loop.run_in_executor(executor, get_aggregate_bars)

            # 使用适配器转换数据
            history_data = self.adapter.adapt_history_data_from_aggs(aggs)

            logger.debug("Polygon历史数据获取成功",
                         symbol=symbol,
                         count=len(history_data.prices) if hasattr(history_data, 'prices') else 0)

            return history_data

        except Exception as e:
            logger.error("Polygon历史数据获取失败",
                         symbol=symbol,
                         error=str(e))
            raise TickerNotFoundError(f"无法获取 {symbol} 的Polygon历史数据: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            logger.debug("开始Polygon健康检查")
            self._ensure_client()

            # 使用市场状态API进行健康检查
            def get_market_status():
                return self.client.get_market_status()

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                status = await loop.run_in_executor(executor, get_market_status)

            logger.debug("Polygon健康检查成功", status=status)

            return {
                "status": "healthy",
                "message": "Polygon.io API 连接正常",
                "market_status": status
            }

        except Exception as e:
            logger.error("Polygon健康检查失败", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"Polygon.io API 连接失败: {str(e)}"
            }

    # 调试方法
    async def get_raw_quote(self, symbol: str):
        """获取原始报价数据用于调试"""
        try:
            self._ensure_client()

            def get_last_quote():
                return self.client.get_last_quote(ticker=symbol)

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                quote = await loop.run_in_executor(executor, get_last_quote)

            return quote
        except Exception as e:
            logger.error("获取原始报价失败", symbol=symbol, error=str(e))
            raise

    async def get_raw_ticker_details(self, symbol: str):
        """获取原始ticker详情用于调试"""
        try:
            self._ensure_client()

            def get_ticker_details():
                return self.client.get_ticker_details(symbol)

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                details = await loop.run_in_executor(executor, get_ticker_details)

            return details
        except Exception as e:
            logger.error("获取原始ticker详情失败", symbol=symbol, error=str(e))
            raise

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, FastQuoteData]:
        """批量获取报价数据"""
        try:
            logger.debug("批量获取Polygon报价", symbols=symbols, count=len(symbols))

            results = {}

            # 使用并发获取提高性能
            tasks = []
            for symbol in symbols:
                task = self.get_fast_quote(symbol)
                tasks.append((symbol, task))

            # 并发执行所有请求
            for symbol, task in tasks:
                try:
                    quote_data = await task
                    results[symbol] = quote_data
                except Exception as e:
                    logger.warning("批量获取中单个股票失败",
                                   symbol=symbol,
                                   error=str(e))
                    # 继续处理其他股票，不中断整个批量操作

            logger.debug("Polygon批量报价获取完成",
                         successful=len(results),
                         total=len(symbols))

            return results

        except Exception as e:
            logger.error("Polygon批量报价获取失败", symbols=symbols, error=str(e))
            raise YahooAPIError(f"批量获取报价失败: {str(e)}")

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
        """获取历史数据（兼容yfinance接口）"""
        try:
            logger.debug("获取Polygon历史数据（兼容接口）",
                         symbol=symbol,
                         period=period)

            # 调用内部的历史数据方法
            history_data = await self.get_history_data(symbol, period)

            # 添加兼容性字段
            history_data.update({
                "interval": interval,
                "period": period,
                "auto_adjust": auto_adjust,
                "prepost": prepost,
                "actions": actions
            })

            logger.debug("Polygon历史数据获取成功（兼容接口）",
                         symbol=symbol,
                         records_count=len(history_data.get('timestamps', [])))

            return history_data

        except Exception as e:
            logger.error("Polygon历史数据获取失败（兼容接口）",
                         symbol=symbol,
                         error=str(e))
            raise YahooAPIError(f"获取历史数据失败: {str(e)}")

    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, 'client') and self.client:
            try:
                # 注意：官方客户端没有明确的close方法，但我们可以清理引用
                self.client = None
            except Exception:
                pass
