"""
数据标准化器
确保不同数据源的数据格式一致性
"""

from typing import Dict, Any, Optional
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataNormalizer:
    """数据标准化器"""

    @staticmethod
    def normalize_fast_quote(quote: FastQuoteData, source: str) -> FastQuoteData:
        """标准化快速报价数据"""
        try:
            # 基本数据验证和清理
            normalized = FastQuoteData(
                last_price=DataNormalizer._safe_round(quote.last_price, 4),
                previous_close=DataNormalizer._safe_round(
                    quote.previous_close, 4),
                open_price=DataNormalizer._safe_round(quote.open_price, 4),
                day_high=DataNormalizer._safe_round(quote.day_high, 4),
                day_low=DataNormalizer._safe_round(quote.day_low, 4),
                volume=quote.volume,
                market_cap=quote.market_cap,
                shares=quote.shares,
                currency=quote.currency or "USD"
            )

            # 数据一致性检查
            DataNormalizer._validate_price_consistency(normalized, source)

            return normalized

        except Exception as e:
            logger.warning(f"快速报价数据标准化失败", source=source, error=str(e))
            return quote

    @staticmethod
    def normalize_detailed_quote(quote: QuoteData, source: str) -> QuoteData:
        """标准化详细报价数据"""
        try:
            # 基础价格数据标准化
            normalized = QuoteData(
                last_price=DataNormalizer._safe_round(quote.last_price, 4),
                previous_close=DataNormalizer._safe_round(
                    quote.previous_close, 4),
                open_price=DataNormalizer._safe_round(quote.open_price, 4),
                day_high=DataNormalizer._safe_round(quote.day_high, 4),
                day_low=DataNormalizer._safe_round(quote.day_low, 4),
                volume=quote.volume,
                average_volume=quote.average_volume,

                # 市值和股数
                market_cap=quote.market_cap,
                shares_outstanding=quote.shares_outstanding,

                # 52周数据
                fifty_two_week_high=DataNormalizer._safe_round(
                    quote.fifty_two_week_high, 4),
                fifty_two_week_low=DataNormalizer._safe_round(
                    quote.fifty_two_week_low, 4),

                # 财务比率
                pe_ratio=DataNormalizer._safe_round(quote.pe_ratio, 2),
                forward_pe=DataNormalizer._safe_round(quote.forward_pe, 2),
                price_to_book=DataNormalizer._safe_round(
                    quote.price_to_book, 2),

                # 股息信息
                dividend_rate=DataNormalizer._safe_round(
                    quote.dividend_rate, 4),
                dividend_yield=DataNormalizer._safe_round(
                    quote.dividend_yield, 4),

                # 其他财务数据
                eps=DataNormalizer._safe_round(quote.eps, 4),
                beta=DataNormalizer._safe_round(quote.beta, 4),

                # 变化数据
                change=DataNormalizer._safe_round(quote.change, 4),
                change_percent=DataNormalizer._safe_round(
                    quote.change_percent, 2),

                # 元数据
                currency=quote.currency or "USD",
                exchange=quote.exchange,
                sector=quote.sector,
                industry=quote.industry
            )

            # 重新计算变化数据以确保一致性
            if normalized.last_price and normalized.previous_close and normalized.previous_close != 0:
                calculated_change = normalized.last_price - normalized.previous_close
                calculated_change_percent = (
                    calculated_change / normalized.previous_close) * 100

                normalized.change = DataNormalizer._safe_round(
                    calculated_change, 4)
                normalized.change_percent = DataNormalizer._safe_round(
                    calculated_change_percent, 2)

            # 数据一致性检查
            DataNormalizer._validate_detailed_quote_consistency(
                normalized, source)

            return normalized

        except Exception as e:
            logger.warning(f"详细报价数据标准化失败", source=source, error=str(e))
            return quote

    @staticmethod
    def normalize_company_info(info: CompanyInfo, source: str) -> CompanyInfo:
        """标准化公司信息"""
        try:
            normalized = CompanyInfo(
                name=DataNormalizer._clean_string(info.name),
                sector=DataNormalizer._normalize_sector(info.sector),
                industry=DataNormalizer._clean_string(info.industry),
                description=DataNormalizer._clean_string(info.description),
                website=DataNormalizer._normalize_website(info.website),
                employees=info.employees,
                country=DataNormalizer._normalize_country(info.country),
                market_cap=info.market_cap,
                currency=info.currency or "USD"
            )

            return normalized

        except Exception as e:
            logger.warning(f"公司信息标准化失败", source=source, error=str(e))
            return info

    @staticmethod
    def _safe_round(value: Optional[float], digits: int) -> Optional[float]:
        """安全的浮点数四舍五入"""
        if value is None:
            return None
        try:
            return round(float(value), digits)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clean_string(value: Optional[str]) -> Optional[str]:
        """清理字符串数据"""
        if not value:
            return None

        cleaned = str(value).strip()

        # 移除多余的空格
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")

        return cleaned if cleaned else None

    @staticmethod
    def _normalize_sector(sector: Optional[str]) -> Optional[str]:
        """标准化行业分类"""
        if not sector:
            return None

        sector_mapping = {
            "tech": "Technology",
            "technology": "Technology",
            "healthcare": "Healthcare",
            "health care": "Healthcare",
            "financial": "Financial Services",
            "finance": "Financial Services",
            "energy": "Energy",
            "consumer": "Consumer Cyclical",
            "utilities": "Utilities",
            "real estate": "Real Estate",
            "industrials": "Industrials",
            "materials": "Basic Materials",
            "communication": "Communication Services"
        }

        sector_lower = sector.lower().strip()
        for key, standard_name in sector_mapping.items():
            if key in sector_lower:
                return standard_name

        return DataNormalizer._clean_string(sector)

    @staticmethod
    def _normalize_website(website: Optional[str]) -> Optional[str]:
        """标准化网站URL"""
        if not website:
            return None

        website = website.strip().lower()

        # 确保有协议前缀
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"

        return website

    @staticmethod
    def _normalize_country(country: Optional[str]) -> Optional[str]:
        """标准化国家名称"""
        if not country:
            return None

        country_mapping = {
            "us": "United States",
            "usa": "United States",
            "united states": "United States",
            "cn": "China",
            "china": "China",
            "jp": "Japan",
            "japan": "Japan",
            "uk": "United Kingdom",
            "gb": "United Kingdom",
            "united kingdom": "United Kingdom"
        }

        country_lower = country.lower().strip()
        return country_mapping.get(country_lower, DataNormalizer._clean_string(country))

    @staticmethod
    def _validate_price_consistency(quote: FastQuoteData, source: str):
        """验证价格数据一致性"""
        issues = []

        # 检查价格是否为负数
        if quote.last_price and quote.last_price < 0:
            issues.append("负数的当前价格")

        if quote.previous_close and quote.previous_close < 0:
            issues.append("负数的前收盘价")

        # 检查当日高低价是否合理
        if quote.day_high and quote.day_low and quote.day_high < quote.day_low:
            issues.append("当日最高价低于最低价")

        # 检查当前价格是否在合理范围内
        if (quote.last_price and quote.day_high and quote.day_low and
                not (quote.day_low <= quote.last_price <= quote.day_high)):
            issues.append("当前价格超出当日高低价范围")

        if issues:
            logger.warning(f"价格数据一致性问题", source=source, issues=issues)

    @staticmethod
    def _validate_detailed_quote_consistency(quote: QuoteData, source: str):
        """验证详细报价数据一致性"""
        issues = []

        # 基础价格验证
        DataNormalizer._validate_price_consistency(quote, source)

        # 检查财务比率合理性
        if quote.pe_ratio and (quote.pe_ratio < 0 or quote.pe_ratio > 1000):
            issues.append(f"异常的PE比率: {quote.pe_ratio}")

        if quote.dividend_yield and (quote.dividend_yield < 0 or quote.dividend_yield > 50):
            issues.append(f"异常的股息收益率: {quote.dividend_yield}")

        # 检查变化数据一致性
        if (quote.last_price and quote.previous_close and quote.change and
                abs((quote.last_price - quote.previous_close) - quote.change) > 0.01):
            issues.append("价格变化计算不一致")

        if issues:
            logger.warning(f"详细报价数据一致性问题", source=source, issues=issues)

    @staticmethod
    def compare_sources(data1: Any, data2: Any, source1: str, source2: str) -> Dict[str, Any]:
        """比较不同数据源的数据差异"""
        differences = {}

        if isinstance(data1, FastQuoteData) and isinstance(data2, FastQuoteData):
            differences = DataNormalizer._compare_fast_quotes(data1, data2)
        elif isinstance(data1, QuoteData) and isinstance(data2, QuoteData):
            differences = DataNormalizer._compare_detailed_quotes(data1, data2)
        elif isinstance(data1, CompanyInfo) and isinstance(data2, CompanyInfo):
            differences = DataNormalizer._compare_company_info(data1, data2)

        if differences:
            logger.info(
                "数据源差异分析",
                source1=source1,
                source2=source2,
                differences=differences
            )

        return differences

    @staticmethod
    def _compare_fast_quotes(quote1: FastQuoteData, quote2: FastQuoteData) -> Dict[str, Any]:
        """比较快速报价数据"""
        differences = {}

        fields = ["last_price", "previous_close",
                  "open_price", "day_high", "day_low", "volume"]

        for field in fields:
            val1 = getattr(quote1, field)
            val2 = getattr(quote2, field)

            if val1 != val2:
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    diff_percent = abs(val1 - val2) / max(val1,
                                                          val2) * 100 if max(val1, val2) > 0 else 0
                    differences[field] = {
                        "source1": val1,
                        "source2": val2,
                        "diff_percent": round(diff_percent, 2)
                    }
                else:
                    differences[field] = {"source1": val1, "source2": val2}

        return differences

    @staticmethod
    def _compare_detailed_quotes(quote1: QuoteData, quote2: QuoteData) -> Dict[str, Any]:
        """比较详细报价数据"""
        # 继承快速报价的比较逻辑
        differences = DataNormalizer._compare_fast_quotes(quote1, quote2)

        # 添加详细数据字段比较
        additional_fields = [
            "market_cap", "pe_ratio", "dividend_rate", "dividend_yield",
            "eps", "beta", "change", "change_percent"
        ]

        for field in additional_fields:
            val1 = getattr(quote1, field)
            val2 = getattr(quote2, field)

            if val1 != val2 and field not in differences:
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    diff_percent = abs(val1 - val2) / max(val1,
                                                          val2) * 100 if max(val1, val2) > 0 else 0
                    differences[field] = {
                        "source1": val1,
                        "source2": val2,
                        "diff_percent": round(diff_percent, 2)
                    }
                else:
                    differences[field] = {"source1": val1, "source2": val2}

        return differences

    @staticmethod
    def _compare_company_info(info1: CompanyInfo, info2: CompanyInfo) -> Dict[str, Any]:
        """比较公司信息数据"""
        differences = {}

        fields = ["name", "sector", "industry", "employees", "country"]

        for field in fields:
            val1 = getattr(info1, field)
            val2 = getattr(info2, field)

            if val1 != val2:
                differences[field] = {"source1": val1, "source2": val2}

        return differences
