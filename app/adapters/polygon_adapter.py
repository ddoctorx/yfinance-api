"""
Polygon.io 数据适配器
将 Polygon.io API 响应转换为内部数据格式
支持官方 polygon-api-client 库的对象格式
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from .base import BaseDataAdapter
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.models.history import HistoryData
from app.core.logging import get_logger

logger = get_logger(__name__)


class PolygonDataAdapter(BaseDataAdapter):
    """Polygon.io 数据适配器"""

    def adapt_fast_quote_from_snapshot(self, snapshot) -> FastQuoteData:
        """
        从官方客户端的TickerSnapshot对象转换为快速报价数据
        """
        try:
            # 获取各种价格信息
            last_price = None
            previous_close = None
            open_price = None
            day_high = None
            day_low = None
            volume = None

            # 从快照对象中提取数据
            if hasattr(snapshot, 'value') and snapshot.value:
                last_price = self.safe_float_from_attr(snapshot, 'value')

            # 获取session数据（当日交易数据）
            if hasattr(snapshot, 'session') and snapshot.session:
                session = snapshot.session
                open_price = self.safe_float_from_attr(session, 'open')
                day_high = self.safe_float_from_attr(session, 'high')
                day_low = self.safe_float_from_attr(session, 'low')
                volume = self.safe_int_from_attr(session, 'volume')

                # 如果value不可用，尝试使用close价格
                if last_price is None:
                    last_price = self.safe_float_from_attr(session, 'close')

            # 获取前一日收盘价
            if hasattr(snapshot, 'prevDay') and snapshot.prevDay:
                prev_day = snapshot.prevDay
                previous_close = self.safe_float_from_attr(prev_day, 'c')

            # 构建快速报价数据
            quote_data = FastQuoteData(
                last_price=last_price,
                previous_close=previous_close,
                open_price=open_price,
                day_high=day_high,
                day_low=day_low,
                volume=volume,
                change=None,         # 后续计算
                change_percent=None,  # 后续计算
                shares=None,      # 需要从ticker details获取
                currency="USD"    # Polygon主要是美股，默认USD
            )

            # 计算变化值和百分比
            if quote_data.last_price and quote_data.previous_close:
                quote_data.change, quote_data.change_percent = self.calculate_change_metrics(
                    quote_data.last_price, quote_data.previous_close
                )

            logger.debug("Polygon快速报价数据转换成功",
                         last_price=last_price,
                         previous_close=previous_close)

            return quote_data

        except Exception as e:
            logger.error("Polygon快速报价数据转换失败", error=str(e))
            raise ValueError(
                f"Failed to adapt Polygon snapshot data: {str(e)}")

    def adapt_detailed_quote_from_objects(self, snapshot, details=None) -> QuoteData:
        """
        从官方客户端的对象转换为详细报价数据
        """
        try:
            # 首先获取基础快速报价数据
            fast_quote = self.adapt_fast_quote_from_snapshot(snapshot)

            # 构建详细报价数据
            quote_data = QuoteData(
                last_price=fast_quote.last_price,
                previous_close=fast_quote.previous_close,
                open_price=fast_quote.open_price,
                day_high=fast_quote.day_high,
                day_low=fast_quote.day_low,
                volume=fast_quote.volume,
                average_volume=None,  # Polygon不直接提供
                market_cap=None,
                shares_outstanding=None,
                fifty_two_week_high=None,  # Polygon不直接提供
                fifty_two_week_low=None,   # Polygon不直接提供
                pe_ratio=None,        # Polygon不提供
                forward_pe=None,      # Polygon不提供
                price_to_book=None,   # Polygon不提供
                dividend_rate=None,   # 需要从dividends API获取
                dividend_yield=None,  # 需要计算
                eps=None,            # Polygon不提供
                beta=None,           # Polygon不提供
                currency=fast_quote.currency,
                exchange=None,
                sector=None,
                industry=None
            )

            # 如果有详情数据，添加额外信息
            if details:
                quote_data.market_cap = self.safe_int_from_attr(
                    details, 'market_cap')
                quote_data.shares_outstanding = self.safe_int_from_attr(
                    details, 'share_class_shares_outstanding')
                quote_data.exchange = self.safe_str_from_attr(
                    details, 'primary_exchange')
                quote_data.sector = self._map_sic_to_sector(
                    self.safe_str_from_attr(details, 'sic_description')
                )
                quote_data.industry = self.safe_str_from_attr(
                    details, 'sic_description')

            # 复制计算得出的变化值
            quote_data.change = fast_quote.change
            quote_data.change_percent = fast_quote.change_percent

            logger.debug("Polygon详细报价数据转换成功",
                         last_price=quote_data.last_price)

            return quote_data

        except Exception as e:
            logger.error("Polygon详细报价数据转换失败", error=str(e))
            raise ValueError(
                f"Failed to adapt Polygon detailed quote data: {str(e)}")

    def adapt_company_info_from_details(self, ticker_details) -> CompanyInfo:
        """
        从官方客户端的TickerDetails对象转换为公司信息
        """
        try:
            # 安全获取公司信息
            symbol = self.safe_str_from_attr(ticker_details, 'ticker', '')
            name = self.safe_str_from_attr(ticker_details, 'name', symbol)

            # 尝试获取description，如果不存在则构造默认描述
            description = self.safe_str_from_attr(
                ticker_details, 'description')
            if not description:
                # 如果没有description，使用可用信息构造一个
                market = self.safe_str_from_attr(ticker_details, 'market', '')
                ticker_type = self.safe_str_from_attr(
                    ticker_details, 'type', '')
                if market and ticker_type:
                    description = f"{name} 是一家在{market}市场交易的{ticker_type}公司。"
                else:
                    description = f"{name} 公司信息。"

            sector = self.safe_str_from_attr(
                ticker_details, 'sic_description', '')
            industry = self.safe_str_from_attr(
                ticker_details, 'sic_description', '')
            website = self.safe_str_from_attr(
                ticker_details, 'homepage_url', '')
            employees = self.safe_int_from_attr(
                ticker_details, 'total_employees')
            market_cap = self.safe_float_from_attr(
                ticker_details, 'market_cap')

            # 获取地址信息
            address_parts = []
            if hasattr(ticker_details, 'address') and ticker_details.address:
                address = ticker_details.address
                if hasattr(address, 'address1') and address.address1:
                    address_parts.append(address.address1)
                if hasattr(address, 'city') and address.city:
                    address_parts.append(address.city)
                if hasattr(address, 'state') and address.state:
                    address_parts.append(address.state)
                if hasattr(address, 'postal_code') and address.postal_code:
                    address_parts.append(address.postal_code)

            headquarters = ', '.join(address_parts) if address_parts else ''

            return CompanyInfo(
                symbol=symbol,
                name=name,
                description=description,
                sector=sector,
                industry=industry,
                website=website,
                employees=employees,
                market_cap=market_cap,
                headquarters=headquarters
            )

        except Exception as e:
            logger.warning("转换公司信息时出错", error=str(e))
            # 返回最小可用信息
            symbol = getattr(ticker_details, 'ticker', 'UNKNOWN')
            name = getattr(ticker_details, 'name', symbol)
            return CompanyInfo(
                symbol=symbol,
                name=name,
                description=f"{name} 公司信息。",
                sector='',
                industry='',
                website='',
                employees=None,
                market_cap=None,
                headquarters=''
            )

    def adapt_history_data_from_aggs(self, aggs) -> Dict[str, Any]:
        """
        从官方客户端的Agg响应对象转换为历史数据（新格式）
        """
        try:
            # 处理不同的响应格式
            if hasattr(aggs, 'results') and aggs.results:
                aggs_list = list(aggs.results)
            elif isinstance(aggs, (list, tuple)):
                aggs_list = list(aggs)
            else:
                logger.warning("无效的Aggs响应格式", aggs_type=type(aggs))
                return {"prices": [], "volumes": [], "timestamps": []}

            if not aggs_list:
                return {"prices": [], "volumes": [], "timestamps": []}

            # 构建历史数据列表
            history_list = []

            for agg in aggs_list:
                try:
                    # 从Agg对象中提取数据
                    timestamp = self.safe_int_from_attr(agg, 't')
                    if not timestamp:
                        continue

                    # Polygon返回的时间戳是毫秒，需要转换为秒
                    date = datetime.fromtimestamp(timestamp / 1000).date()

                    open_price = self.safe_float_from_attr(agg, 'o')
                    high_price = self.safe_float_from_attr(agg, 'h')
                    low_price = self.safe_float_from_attr(agg, 'l')
                    close_price = self.safe_float_from_attr(agg, 'c')
                    volume = self.safe_int_from_attr(agg, 'v')

                    history_data = HistoryData(
                        date=date,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume
                    )

                    history_list.append(history_data)

                except Exception as agg_error:
                    logger.warning("跳过无效的Agg数据", error=str(agg_error))
                    continue

            logger.debug("Polygon历史数据转换成功", bars_count=len(history_list))
            return history_list

        except Exception as e:
            logger.error("Polygon历史数据转换失败", error=str(e))
            raise ValueError(f"Failed to adapt Polygon aggs data: {str(e)}")

    # 保留原有的方法以兼容旧格式
    def adapt_fast_quote(self, raw_data: Dict[str, Any]) -> FastQuoteData:
        """
        转换 Polygon Snapshot API 响应为快速报价数据（原有JSON格式）
        """
        try:
            if "results" not in raw_data:
                raise ValueError("Invalid Polygon snapshot response format")

            results = raw_data["results"]

            # 获取最新价格信息
            last = results.get("last", {})
            prev_day = results.get("prevDay", {})

            # 当前价格
            last_price = self.safe_get_float(last, "price")

            # 前收盘价
            previous_close = self.safe_get_float(prev_day, "c")

            # 当天OHLC数据 - 如果没有当天数据，使用前一天数据
            min_data = results.get("min", {})
            open_price = self.safe_get_float(
                min_data, "o") or self.safe_get_float(prev_day, "o")
            day_high = self.safe_get_float(
                min_data, "h") or self.safe_get_float(prev_day, "h")
            day_low = self.safe_get_float(
                min_data, "l") or self.safe_get_float(prev_day, "l")
            volume = self.safe_get_int(
                min_data, "v") or self.safe_get_int(prev_day, "v")

            quote_data = FastQuoteData(
                last_price=last_price,
                previous_close=previous_close,
                open_price=open_price,
                day_high=day_high,
                day_low=day_low,
                volume=volume,
                market_cap=None,  # 需要从ticker details获取
                shares=None,      # 需要从ticker details获取
                currency="USD"    # Polygon主要是美股，默认USD
            )

            logger.debug("Polygon快速报价数据转换成功",
                         last_price=last_price,
                         previous_close=previous_close)

            return quote_data

        except Exception as e:
            logger.error("Polygon快速报价数据转换失败", error=str(e), raw_data=raw_data)
            raise ValueError(
                f"Failed to adapt Polygon snapshot data: {str(e)}")

    def adapt_detailed_quote(self, raw_data: Dict[str, Any]) -> QuoteData:
        """
        转换详细报价数据 (Snapshot + Ticker Details)

        需要合并两个API的响应：
        1. Snapshot API - 价格数据
        2. Ticker Details API - 公司财务数据
        """
        try:
            # 首先获取基础快速报价数据
            fast_quote = self.adapt_fast_quote(raw_data)

            # 获取额外的ticker details数据
            ticker_details = raw_data.get("ticker_details", {})

            # 构建详细报价数据
            quote_data = QuoteData(
                last_price=fast_quote.last_price,
                previous_close=fast_quote.previous_close,
                open_price=fast_quote.open_price,
                day_high=fast_quote.day_high,
                day_low=fast_quote.day_low,
                volume=fast_quote.volume,
                average_volume=None,  # Polygon不直接提供
                market_cap=self.safe_get_int(ticker_details, "market_cap"),
                shares_outstanding=self.safe_get_int(
                    ticker_details, "share_class_shares_outstanding"),
                fifty_two_week_high=None,  # Polygon不直接提供
                fifty_two_week_low=None,   # Polygon不直接提供
                pe_ratio=None,        # Polygon不提供
                forward_pe=None,      # Polygon不提供
                price_to_book=None,   # Polygon不提供
                dividend_rate=None,   # 需要从dividends API获取
                dividend_yield=None,  # 需要计算
                eps=None,            # Polygon不提供
                beta=None,           # Polygon不提供
                currency=fast_quote.currency,
                exchange=self.safe_get_str(ticker_details, "primary_exchange"),
                sector=self._map_sic_to_sector(
                    ticker_details.get("sic_description")),
                industry=self.safe_get_str(ticker_details, "sic_description")
            )

            # 计算变化值和百分比
            if quote_data.last_price and quote_data.previous_close:
                quote_data.change, quote_data.change_percent = self.calculate_change_metrics(
                    quote_data.last_price, quote_data.previous_close
                )

            logger.debug("Polygon详细报价数据转换成功",
                         last_price=quote_data.last_price)

            return quote_data

        except Exception as e:
            logger.error("Polygon详细报价数据转换失败", error=str(e))
            raise ValueError(
                f"Failed to adapt Polygon detailed quote data: {str(e)}")

    def adapt_company_info(self, raw_data: Dict[str, Any]) -> CompanyInfo:
        """
        转换 Polygon Ticker Details API 响应为公司信息

        Polygon Ticker Details API 响应格式:
        {
            "results": {
                "name": "Apple Inc.",
                "description": "...",
                "homepage_url": "https://www.apple.com",
                "total_employees": 147000,
                "address": {"city": "Cupertino", "state": "CA"},
                "sic_description": "Electronic Computers",
                "market_cap": 2500000000000,
                ...
            }
        }
        """
        try:
            if "results" not in raw_data:
                raise ValueError(
                    "Invalid Polygon ticker details response format")

            results = raw_data["results"]
            address = results.get("address", {})

            company_info = CompanyInfo(
                name=self.safe_get_str(results, "name"),
                sector=self._map_sic_to_sector(results.get("sic_description")),
                industry=self.safe_get_str(results, "sic_description"),
                description=self.safe_get_str(results, "description"),
                website=self.safe_get_str(results, "homepage_url"),
                employees=self.safe_get_int(results, "total_employees"),
                country=self._get_country_from_address(address),
                market_cap=self.safe_get_int(results, "market_cap"),
                currency="USD"  # Polygon主要是美股
            )

            logger.debug("Polygon公司信息转换成功", name=company_info.name)

            return company_info

        except Exception as e:
            logger.error("Polygon公司信息转换失败", error=str(e))
            raise ValueError(f"Failed to adapt Polygon company info: {str(e)}")

    def adapt_history_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换 Polygon Aggregates API 响应为历史数据

        Polygon Aggregates API 响应格式:
        {
            "results": [
                {
                    "t": 1577836800000,  # timestamp in milliseconds
                    "o": 74.06,          # open
                    "h": 75.15,          # high  
                    "l": 73.80,          # low
                    "c": 75.09,          # close
                    "v": 135480400       # volume
                }, ...
            ]
        }
        """
        try:
            if "results" not in raw_data:
                raise ValueError("Invalid Polygon aggregates response format")

            results = raw_data["results"]

            if not results:
                return {"prices": [], "volumes": [], "timestamps": []}

            # 构建数据列表
            timestamps = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []

            for bar in results:
                # Polygon返回的时间戳是毫秒，需要转换为秒
                timestamp = bar.get("t", 0) / 1000
                timestamps.append(datetime.fromtimestamp(timestamp))

                opens.append(self.safe_get_float(bar, "o"))
                highs.append(self.safe_get_float(bar, "h"))
                lows.append(self.safe_get_float(bar, "l"))
                closes.append(self.safe_get_float(bar, "c"))
                volumes.append(self.safe_get_int(bar, "v"))

            # 构建与yfinance格式兼容的数据结构
            history_data = {
                "prices": {
                    "Open": opens,
                    "High": highs,
                    "Low": lows,
                    "Close": closes
                },
                "volumes": volumes,
                "timestamps": timestamps,
                "data_source": "polygon"
            }

            logger.debug("Polygon历史数据转换成功", bars_count=len(results))

            return history_data

        except Exception as e:
            logger.error("Polygon历史数据转换失败", error=str(e))
            raise ValueError(f"Failed to adapt Polygon history data: {str(e)}")

    def _map_sic_to_sector(self, sic_description: Optional[str]) -> Optional[str]:
        """
        将SIC描述映射到标准行业分类
        这是一个简化的映射，实际应用中可能需要更复杂的映射逻辑
        """
        if not sic_description:
            return None

        sic_lower = sic_description.lower()

        # 简单的关键词映射
        if any(keyword in sic_lower for keyword in ["technology", "software", "computer", "electronic"]):
            return "Technology"
        elif any(keyword in sic_lower for keyword in ["financial", "bank", "insurance"]):
            return "Financial Services"
        elif any(keyword in sic_lower for keyword in ["healthcare", "pharmaceutical", "medical"]):
            return "Healthcare"
        elif any(keyword in sic_lower for keyword in ["energy", "oil", "gas"]):
            return "Energy"
        elif any(keyword in sic_lower for keyword in ["retail", "consumer"]):
            return "Consumer Cyclical"
        elif any(keyword in sic_lower for keyword in ["utilities", "electric", "water"]):
            return "Utilities"
        elif any(keyword in sic_lower for keyword in ["real estate", "property"]):
            return "Real Estate"
        elif any(keyword in sic_lower for keyword in ["industrial", "manufacturing"]):
            return "Industrials"
        elif any(keyword in sic_lower for keyword in ["material", "chemical", "metal"]):
            return "Basic Materials"
        elif any(keyword in sic_lower for keyword in ["communication", "media", "telecom"]):
            return "Communication Services"
        else:
            return "Other"

    def _get_country_from_address(self, address: Dict[str, Any]) -> str:
        """
        从地址字典中推断国家代码
        """
        if not address:
            return "US"  # 默认美国

        # 根据州代码判断是否为美国
        state = address.get("state", "").upper()
        if state and len(state) == 2:
            # 美国州代码通常是2位字母
            return "US"

        # 根据国家字段
        country = address.get("country", "").upper()
        if country:
            return country

        return "US"  # 默认美国

    def _get_country_from_address_obj(self, address_obj) -> str:
        """
        从官方客户端的地址对象中推断国家代码
        """
        if not address_obj:
            return "US"  # 默认美国

        # 根据州代码判断是否为美国
        state = self.safe_str_from_attr(address_obj, 'state', "").upper()
        if state and len(state) == 2:
            # 美国州代码通常是2位字母
            return "US"

        # 根据国家字段
        country = self.safe_str_from_attr(address_obj, 'country', "").upper()
        if country:
            return country

        return "US"  # 默认美国

    def adapt_detailed_quote_from_snapshot_and_details(self, snapshot, ticker_details) -> QuoteData:
        """
        从官方客户端的TickerSnapshot和TickerDetails对象转换为详细报价数据
        """
        try:
            # 先获取快速报价的基础数据
            fast_quote = self.adapt_fast_quote_from_snapshot(snapshot)

            # 从ticker详情中获取额外信息
            company_name = self.safe_str_from_attr(
                ticker_details, 'name', fast_quote.symbol)
            market_cap = self.safe_float_from_attr(
                ticker_details, 'market_cap')
            pe_ratio = None  # Polygon.io基础数据中通常不包含PE比率

            # 计算涨跌额和涨跌幅
            change = None
            change_percent = None
            if fast_quote.last_price and fast_quote.previous_close:
                change = fast_quote.last_price - fast_quote.previous_close
                change_percent = (change / fast_quote.previous_close) * 100

            # 市场状态
            market_status = self.safe_str_from_attr(
                snapshot, 'market_status', 'unknown')

            return QuoteData(
                symbol=fast_quote.symbol,
                last_price=fast_quote.last_price,
                bid_price=fast_quote.bid_price,
                bid_size=fast_quote.bid_size,
                ask_price=fast_quote.ask_price,
                ask_size=fast_quote.ask_size,
                open_price=fast_quote.open_price,
                day_high=fast_quote.day_high,
                day_low=fast_quote.day_low,
                previous_close=fast_quote.previous_close,
                volume=fast_quote.volume,
                avg_volume=None,  # 基础API中不包含
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                change=change,
                change_percent=change_percent,
                company_name=company_name,
                exchange="NASDAQ",  # 大多数股票的默认值
                currency="USD",
                timezone="America/New_York",
                is_market_open=market_status.lower() in [
                    'open', 'extended-hours'],
                last_updated=fast_quote.last_updated,
                fifty_two_week_high=None,  # 基础API中不包含
                fifty_two_week_low=None,   # 基础API中不包含
                dividend_yield=None,       # 基础API中不包含
                earnings_per_share=None    # 基础API中不包含
            )

        except Exception as e:
            logger.error("Polygon详细报价转换失败", error=str(e))
            raise ValueError(f"数据转换失败: {str(e)}")

    def adapt_fast_quote_from_quote(self, quote) -> FastQuoteData:
        """
        从官方客户端的Quote对象转换为快速报价数据
        """
        try:
            # 从Quote对象中提取数据
            symbol = self.safe_str_from_attr(quote, 'ticker', '')
            last_price = self.safe_float_from_attr(quote, 'last_quote_price')
            if not last_price:
                # 尝试其他可能的价格字段
                last_price = self.safe_float_from_attr(quote, 'bid') or \
                    self.safe_float_from_attr(quote, 'ask')

            volume = self.safe_int_from_attr(quote, 'last_quote_size')

            # 创建快速报价数据
            quote_data = FastQuoteData(
                symbol=symbol,
                last_price=last_price,
                volume=volume,
                bid=self.safe_float_from_attr(quote, 'bid'),
                ask=self.safe_float_from_attr(quote, 'ask'),
                bid_size=self.safe_int_from_attr(quote, 'bid_size'),
                ask_size=self.safe_int_from_attr(quote, 'ask_size'),
                timestamp=self.safe_int_from_attr(
                    quote, 'last_quote_timestamp'),
                previous_close=None,  # Quote数据中通常不包含前收盘价
                change=None,
                change_percent=None
            )

            logger.debug("Quote对象转换为快速报价成功",
                         symbol=symbol,
                         price=last_price)

            return quote_data

        except Exception as e:
            logger.error("Quote对象转换失败", error=str(e))
            # 返回默认数据
            return FastQuoteData(
                symbol="UNKNOWN",
                last_price=0.0,
                volume=0,
                timestamp=int(datetime.now().timestamp() * 1000)
            )

    def adapt_detailed_quote_from_quote_and_details(self, quote, details) -> QuoteData:
        """
        从官方客户端的Quote和TickerDetails对象转换为详细报价数据
        """
        try:
            # 先获取快速报价的基础数据
            fast_quote = self.adapt_fast_quote_from_quote(quote)

            # 从details中获取额外信息
            company_name = self.safe_str_from_attr(
                details, 'name', fast_quote.symbol)
            market_cap = self.safe_float_from_attr(details, 'market_cap')
            pe_ratio = None  # Polygon.io基础数据中通常不包含PE比率

            # 创建详细报价数据
            quote_data = QuoteData(
                symbol=fast_quote.symbol,
                last_price=fast_quote.last_price,
                volume=fast_quote.volume,
                bid=fast_quote.bid,
                ask=fast_quote.ask,
                bid_size=fast_quote.bid_size,
                ask_size=fast_quote.ask_size,
                timestamp=fast_quote.timestamp,
                previous_close=fast_quote.previous_close,
                change=fast_quote.change,
                change_percent=fast_quote.change_percent,
                company_name=company_name,
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                day_high=None,  # Quote数据中通常不包含当日最高价
                day_low=None,   # Quote数据中通常不包含当日最低价
                year_high=None,
                year_low=None
            )

            logger.debug("Quote和Details对象转换为详细报价成功",
                         symbol=fast_quote.symbol,
                         price=fast_quote.last_price)

            return quote_data

        except Exception as e:
            logger.error("Quote和Details对象转换失败", error=str(e))
            # 返回默认数据
            return QuoteData(
                symbol="UNKNOWN",
                last_price=0.0,
                volume=0,
                timestamp=int(datetime.now().timestamp() * 1000),
                company_name="Unknown Company"
            )
