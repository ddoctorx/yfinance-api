"""
yfinance 服务层
封装对 yfinance 库的所有调用，提供统一的业务接口
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger, log_yfinance_call
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.utils.exceptions import TickerNotFoundError, YahooAPIError
from app.utils.cache import quote_cache, history_cache, financial_cache, news_cache

logger = get_logger(__name__)

# 线程池执行器，用于异步执行同步的yfinance调用
executor = ThreadPoolExecutor(max_workers=10)


class YFinanceService:
    """yfinance 服务类"""

    def __init__(self):
        self.session_timeout = settings.yf_session_timeout
        self.max_retries = settings.yf_max_retries

    async def _run_in_executor(self, func, *args, **kwargs) -> Any:
        """在线程池中执行同步函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, func, *args, **kwargs)

    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """获取yfinance Ticker对象"""
        try:
            return yf.Ticker(symbol)
        except Exception as e:
            logger.error(f"创建Ticker对象失败", symbol=symbol, error=str(e))
            raise YahooAPIError(f"无法创建Ticker对象: {str(e)}")

    def _safe_get_float(self, data: dict, key: str) -> Optional[float]:
        """安全获取浮点数值"""
        value = data.get(key)
        if value is None or pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_get_int(self, data: dict, key: str) -> Optional[int]:
        """安全获取整数值"""
        value = data.get(key)
        if value is None or pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @quote_cache
    async def get_fast_quote(self, symbol: str) -> FastQuoteData:
        """获取快速报价数据"""
        start_time = time.time()

        try:
            ticker = await self._run_in_executor(self._get_ticker, symbol)
            fast_info = await self._run_in_executor(lambda: ticker.fast_info)

            if not fast_info:
                raise TickerNotFoundError(symbol)

            # 构建快速报价数据
            quote_data = FastQuoteData(
                last_price=self._safe_get_float(fast_info, 'lastPrice'),
                previous_close=self._safe_get_float(
                    fast_info, 'previousClose'),
                open_price=self._safe_get_float(fast_info, 'open'),
                day_high=self._safe_get_float(fast_info, 'dayHigh'),
                day_low=self._safe_get_float(fast_info, 'dayLow'),
                volume=self._safe_get_int(fast_info, 'lastVolume'),
                market_cap=self._safe_get_int(fast_info, 'marketCap'),
                shares=self._safe_get_int(fast_info, 'shares'),
                currency=fast_info.get('currency'),
            )

            response_time = time.time() - start_time
            log_yfinance_call(symbol, "fast_quote", True, response_time)

            return quote_data

        except TickerNotFoundError:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "fast_quote", False,
                              response_time, f"股票代码未找到: {symbol}")
            raise
        except Exception as e:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "fast_quote", False,
                              response_time, str(e))
            raise YahooAPIError(f"获取快速报价失败: {str(e)}")

    @quote_cache
    async def get_detailed_quote(self, symbol: str) -> QuoteData:
        """获取详细报价数据"""
        start_time = time.time()

        try:
            ticker = await self._run_in_executor(self._get_ticker, symbol)
            info = await self._run_in_executor(lambda: ticker.info)
            fast_info = await self._run_in_executor(lambda: ticker.fast_info)

            if not info and not fast_info:
                raise TickerNotFoundError(symbol)

            # 合并info和fast_info数据
            combined_data = {**info, **fast_info} if info else fast_info

            # 构建详细报价数据
            quote_data = QuoteData(
                last_price=self._safe_get_float(combined_data, 'currentPrice') or
                self._safe_get_float(combined_data, 'lastPrice'),
                previous_close=self._safe_get_float(
                    combined_data, 'previousClose'),
                open_price=self._safe_get_float(combined_data, 'open'),
                day_high=self._safe_get_float(combined_data, 'dayHigh'),
                day_low=self._safe_get_float(combined_data, 'dayLow'),
                volume=self._safe_get_int(combined_data, 'volume') or
                self._safe_get_int(combined_data, 'lastVolume'),
                average_volume=self._safe_get_int(
                    combined_data, 'averageVolume'),
                market_cap=self._safe_get_int(combined_data, 'marketCap'),
                shares_outstanding=self._safe_get_int(
                    combined_data, 'sharesOutstanding'),
                fifty_two_week_high=self._safe_get_float(
                    combined_data, 'fiftyTwoWeekHigh'),
                fifty_two_week_low=self._safe_get_float(
                    combined_data, 'fiftyTwoWeekLow'),
                pe_ratio=self._safe_get_float(combined_data, 'trailingPE'),
                forward_pe=self._safe_get_float(combined_data, 'forwardPE'),
                price_to_book=self._safe_get_float(
                    combined_data, 'priceToBook'),
                dividend_rate=self._safe_get_float(
                    combined_data, 'dividendRate'),
                dividend_yield=self._safe_get_float(
                    combined_data, 'dividendYield'),
                eps=self._safe_get_float(combined_data, 'trailingEps'),
                beta=self._safe_get_float(combined_data, 'beta'),
                currency=combined_data.get('currency'),
                exchange=combined_data.get('exchange'),
                sector=combined_data.get('sector'),
                industry=combined_data.get('industry'),
            )

            # 计算变化值和百分比
            if quote_data.last_price and quote_data.previous_close:
                quote_data.change = quote_data.last_price - quote_data.previous_close
                if quote_data.previous_close != 0:
                    quote_data.change_percent = (
                        quote_data.change / quote_data.previous_close) * 100

            response_time = time.time() - start_time
            log_yfinance_call(symbol, "detailed_quote", True, response_time)

            return quote_data

        except TickerNotFoundError:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "detailed_quote", False,
                              response_time, f"股票代码未找到: {symbol}")
            raise
        except Exception as e:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "detailed_quote",
                              False, response_time, str(e))
            raise YahooAPIError(f"获取详细报价失败: {str(e)}")

    @quote_cache
    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """获取公司基本信息"""
        start_time = time.time()

        try:
            ticker = await self._run_in_executor(self._get_ticker, symbol)
            info = await self._run_in_executor(lambda: ticker.info)

            if not info:
                raise TickerNotFoundError(symbol)

            company_info = CompanyInfo(
                name=info.get('longName') or info.get('shortName'),
                sector=info.get('sector'),
                industry=info.get('industry'),
                country=info.get('country'),
                website=info.get('website'),
                business_summary=info.get('longBusinessSummary'),
                employees=self._safe_get_int(info, 'fullTimeEmployees'),
            )

            response_time = time.time() - start_time
            log_yfinance_call(symbol, "company_info", True, response_time)

            return company_info

        except TickerNotFoundError:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "company_info", False,
                              response_time, f"股票代码未找到: {symbol}")
            raise
        except Exception as e:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "company_info",
                              False, response_time, str(e))
            raise YahooAPIError(f"获取公司信息失败: {str(e)}")

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, FastQuoteData]:
        """批量获取报价数据"""
        logger.info(f"批量获取报价", symbols=symbols, count=len(symbols))

        # 使用asyncio.gather并发获取
        tasks = [self.get_fast_quote(symbol) for symbol in symbols]
        results = {}

        try:
            quotes = await asyncio.gather(*tasks, return_exceptions=True)

            for symbol, quote in zip(symbols, quotes):
                if isinstance(quote, Exception):
                    logger.warning(f"获取{symbol}报价失败", error=str(quote))
                    continue
                results[symbol] = quote

            logger.info(f"批量获取报价完成", successful=len(
                results), total=len(symbols))
            return results

        except Exception as e:
            logger.error(f"批量获取报价失败", error=str(e))
            raise YahooAPIError(f"批量获取报价失败: {str(e)}")

    @history_cache
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
        start_time = time.time()

        try:
            ticker = await self._run_in_executor(self._get_ticker, symbol)

            # 构建参数
            kwargs = {
                "period": period,
                "interval": interval,
                "auto_adjust": auto_adjust,
                "prepost": prepost,
                "actions": actions,
            }

            if start:
                kwargs["start"] = start
            if end:
                kwargs["end"] = end

            # 获取历史数据
            history = await self._run_in_executor(lambda: ticker.history(**kwargs))

            if history.empty:
                raise TickerNotFoundError(symbol, {"reason": "无历史数据"})

            # 转换为字典格式
            result = {
                "data": history.reset_index().to_dict("records"),
                "period": period,
                "interval": interval,
                "total_records": len(history),
            }

            response_time = time.time() - start_time
            log_yfinance_call(symbol, "history", True, response_time,
                              records=len(history), period=period, interval=interval)

            return result

        except TickerNotFoundError:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "history", False,
                              response_time, f"股票代码未找到: {symbol}")
            raise
        except Exception as e:
            response_time = time.time() - start_time
            log_yfinance_call(symbol, "history", False, response_time, str(e))
            raise YahooAPIError(f"获取历史数据失败: {str(e)}")


# 创建全局服务实例
yfinance_service = YFinanceService()
