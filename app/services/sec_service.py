"""
SEC数据服务
处理SEC财报数据的业务逻辑和缓存
包括基础财务数据和高级功能（XBRL转换、全文搜索、内幕交易等）
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from urllib.parse import quote

from app.data_sources.sec_source import SecDataSource
from app.data_sources.sec_advanced_source import SecAdvancedDataSource
from app.models.sec import (
    CompanyFinancialsResponse,
    SecNewsResponse,
    FinancialRatios,
    SecErrorResponse
)
from app.utils.cache import get_cache_value, set_cache_value
from app.core.logging import get_logger
from app.utils.exceptions import FinanceAPIException
from app.core.config import settings

logger = get_logger(__name__)


class SecService:
    """SEC数据服务 - 包含基础财务数据和高级功能"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化SEC服务

        Args:
            api_key: SEC API密钥（必需）

        Raises:
            FinanceAPIException: 当SEC API不可用时抛出
        """
        # 初始化基础数据源
        try:
            self.data_source = SecDataSource(api_key=api_key)
        except Exception as e:
            logger.error(f"SEC基础数据源初始化失败: {e}")
            raise FinanceAPIException(
                message=f"SEC基础服务不可用: {str(e)}",
                code="SEC_SERVICE_UNAVAILABLE"
            )

        # 初始化高级数据源
        try:
            self.advanced_data_source = SecAdvancedDataSource(api_key=api_key)
            self.advanced_available = True
            logger.info("SEC高级功能已启用")
        except Exception as e:
            logger.warning(f"SEC高级数据源初始化失败: {e}, 将仅提供基础功能")
            self.advanced_data_source = None
            self.advanced_available = False

        # 缓存配置
        self.cache_config = {
            # 基础功能缓存
            'financials': {'ttl': 3600},    # 财务数据缓存1小时
            'news': {'ttl': 1800},          # 新闻缓存30分钟
            'ratios': {'ttl': 3600},        # 财务比率缓存1小时

            # 高级功能缓存
            'xbrl': {'ttl': 7200},          # XBRL数据缓存2小时
            'search': {'ttl': 1800},        # 搜索结果缓存30分钟
            'insider': {'ttl': 3600},       # 内幕交易缓存1小时
            'holdings': {'ttl': 21600},     # 机构持股缓存6小时
            'ipo': {'ttl': 3600},           # IPO数据缓存1小时
            'compensation': {'ttl': 86400},  # 薪酬数据缓存24小时
            'governance': {'ttl': 86400},   # 治理数据缓存24小时
            'enforcement': {'ttl': 7200},   # 执法数据缓存2小时
            'mapping': {'ttl': 86400},      # 映射数据缓存24小时
        }

    async def get_company_financials(
        self,
        ticker: str,
        years: int = 5,
        include_quarterly: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司财务数据

        Args:
            ticker: 股票代码
            years: 获取年数 (1-10)
            include_quarterly: 是否包含季度数据
            use_cache: 是否使用缓存

        Returns:
            公司财务数据字典

        Raises:
            FinanceAPIException: 获取数据失败时抛出
        """
        # 参数验证
        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        if not (1 <= years <= 10):
            raise FinanceAPIException(
                message="年数必须在1-10之间",
                code="INVALID_YEARS"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:financials:{ticker}:{years}:{include_quarterly}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取财务数据: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取财务数据: {ticker}")
            result = await self.data_source.get_company_financials(
                ticker=ticker,
                years=years,
                include_quarterly=include_quarterly
            )

            if not result:
                raise FinanceAPIException(
                    message=f"未找到股票代码 {ticker} 的财务数据",
                    code="DATA_NOT_FOUND"
                )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['financials']['ttl']
                    )
                    logger.debug(f"财务数据已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取财务数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取财务数据失败: {str(e)}",
                code="FINANCIALS_ERROR"
            )

    async def get_quarterly_revenue(
        self,
        ticker: str,
        quarters: int = 8,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取季度收入情况

        Args:
            ticker: 股票代码
            quarters: 获取季度数 (1-20)
            use_cache: 是否使用缓存

        Returns:
            季度收入数据字典
        """
        if not (1 <= quarters <= 20):
            raise FinanceAPIException(
                message="季度数必须在1-20之间",
                code="INVALID_QUARTERS"
            )

        # 获取财务数据
        financials = await self.get_company_financials(
            ticker=ticker,
            years=max(1, quarters // 4 + 1),
            include_quarterly=True,
            use_cache=use_cache
        )

        # 提取季度收入数据
        quarterly_revenues = []
        quarterly_data = financials.get('quarterly_financials', [])

        for i, quarter_info in enumerate(quarterly_data[:quarters]):
            revenue = quarter_info.get('revenue', 0)
            if revenue:
                quarterly_revenues.append({
                    'quarter': quarter_info.get('quarter', f'Q{i+1}'),
                    'revenue': float(revenue),
                    'filing_date': quarter_info.get('filing_date', ''),
                    'fiscal_year': quarter_info.get('fiscal_year', 2023),
                    'currency': 'USD'
                })

        # 计算同比增长率
        for i, current in enumerate(quarterly_revenues):
            # 寻找同期季度 (一年前)
            current_year = current['fiscal_year']
            current_quarter_num = current['quarter']

            for prev in quarterly_revenues[i+1:]:
                if (prev['fiscal_year'] == current_year - 1 and
                        prev['quarter'].split()[0] == current_quarter_num.split()[0]):
                    if prev['revenue'] > 0:
                        growth_rate = (
                            (current['revenue'] - prev['revenue']) /
                            prev['revenue']
                        ) * 100
                        current['yoy_growth_rate'] = round(growth_rate, 2)
                    break

        return {
            'ticker': ticker,
            'company_name': financials.get('company_name', f'{ticker} Corporation'),
            'quarterly_data': quarterly_revenues,
            'total_quarters': len(quarterly_revenues),
            'last_updated': datetime.now().isoformat()
        }

    async def get_company_news(
        self,
        ticker: str,
        limit: int = 20,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司SEC新闻

        Args:
            ticker: 股票代码
            limit: 新闻数量限制 (1-100)
            use_cache: 是否使用缓存

        Returns:
            SEC新闻数据字典
        """
        if not (1 <= limit <= 100):
            raise FinanceAPIException(
                message="新闻数量限制必须在1-100之间",
                code="INVALID_LIMIT"
            )

        ticker = ticker.upper().strip()
        cache_key = f"sec:news:{ticker}:{limit}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取SEC新闻: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取新闻缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取新闻: {ticker}")
            news_items = await self.data_source.get_company_news(
                ticker=ticker,
                limit=limit
            )

            result = {
                'ticker': ticker,
                'company_name': f'{ticker} Corporation',
                'news_items': news_items,
                'total_count': len(news_items),
                'last_updated': datetime.now().isoformat()
            }

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['news']['ttl']
                    )
                    logger.debug(f"SEC新闻已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"新闻缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取SEC新闻失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取SEC新闻失败: {str(e)}",
                code="NEWS_ERROR"
            )

    async def get_financial_ratios(
        self,
        ticker: str,
        period: str = "annual",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        计算财务比率

        Args:
            ticker: 股票代码
            period: 期间类型 ("annual" 或 "quarterly")
            use_cache: 是否使用缓存

        Returns:
            财务比率数据字典
        """
        if period not in ["annual", "quarterly"]:
            raise FinanceAPIException(
                message="期间类型必须是 'annual' 或 'quarterly'",
                code="INVALID_PERIOD"
            )

        ticker = ticker.upper().strip()
        cache_key = f"sec:ratios:{ticker}:{period}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取财务比率: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取比率缓存失败: {e}")

        try:
            # 获取财务数据
            financials = await self.get_company_financials(
                ticker=ticker,
                years=2,
                include_quarterly=(period == "quarterly"),
                use_cache=use_cache
            )

            # 获取最新的财务数据
            if period == "annual" and financials.get('annual_financials'):
                latest = financials['annual_financials'][0]
            elif period == "quarterly" and financials.get('quarterly_financials'):
                latest = financials['quarterly_financials'][0]
            else:
                raise FinanceAPIException(
                    message=f"未找到 {period} 财务数据",
                    code="DATA_NOT_FOUND"
                )

            # 计算比率
            ratios = {}
            period_info = f"{period}_{latest.get('fiscal_year', 2023)}"

            if latest.get('total_assets') and latest.get('total_debt'):
                # 计算负债权益比
                if latest.get('total_assets') > 0:
                    ratios['debt_to_equity'] = round(
                        float(latest.get('total_debt', 0) /
                              latest.get('total_assets')), 4
                    )

                # 计算ROA (需要净利润和总资产)
                if latest.get('net_income') and latest.get('total_assets') > 0:
                    ratios['roa'] = round(
                        float(latest.get('net_income') /
                              latest.get('total_assets')) * 100, 2
                    )

                # 计算ROE (使用总资产作为近似)
                if latest.get('net_income') and latest.get('total_assets') > 0:
                    ratios['roe'] = round(
                        float(latest.get('net_income') /
                              latest.get('total_assets')) * 100, 2
                    )

            result = {
                'ticker': ticker,
                'period': period_info,
                'ratios': ratios,
                'calculation_date': datetime.now().isoformat(),
                'data_source': 'SEC EDGAR'
            }

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['ratios']['ttl']
                    )
                    logger.debug(f"财务比率已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"比率缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"计算财务比率失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"计算财务比率失败: {str(e)}",
                code="RATIOS_ERROR"
            )

    async def get_annual_comparison(
        self,
        ticker: str,
        years: int = 5,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取年度财务对比数据

        Args:
            ticker: 股票代码
            years: 对比年数 (2-10)
            use_cache: 是否使用缓存

        Returns:
            年度对比数据字典
        """
        if not (2 <= years <= 10):
            raise FinanceAPIException(
                message="对比年数必须在2-10之间",
                code="INVALID_YEARS"
            )

        # 获取财务数据
        financials = await self.get_company_financials(
            ticker=ticker,
            years=years,
            include_quarterly=False,
            use_cache=use_cache
        )

        annual_data = financials.get('annual_financials', [])
        if len(annual_data) < 2:
            raise FinanceAPIException(
                message=f"需要至少2年的数据进行对比，当前只有{len(annual_data)}年",
                code="INSUFFICIENT_DATA"
            )

        # 构建对比数据
        comparison_data = []
        for i, year_data in enumerate(annual_data):
            item = {
                'fiscal_year': year_data.get('fiscal_year'),
                'revenue': year_data.get('revenue', 0),
                'net_income': year_data.get('net_income', 0),
                'total_assets': year_data.get('total_assets', 0),
                'total_debt': year_data.get('total_debt', 0),
                'filing_date': year_data.get('filing_date', ''),
            }

            # 计算同比增长率
            if i < len(annual_data) - 1:
                prev_year = annual_data[i + 1]

                # 收入增长率
                if prev_year.get('revenue', 0) > 0:
                    revenue_growth = (
                        (item['revenue'] - prev_year.get('revenue', 0)) /
                        prev_year.get('revenue', 0)
                    ) * 100
                    item['revenue_growth_rate'] = round(revenue_growth, 2)

                # 净利润增长率
                if prev_year.get('net_income', 0) > 0:
                    income_growth = (
                        (item['net_income'] - prev_year.get('net_income', 0)) /
                        prev_year.get('net_income', 0)
                    ) * 100
                    item['net_income_growth_rate'] = round(income_growth, 2)

            comparison_data.append(item)

        return {
            'ticker': ticker,
            'company_name': financials.get('company_name', f'{ticker} Corporation'),
            'comparison_years': years,
            'annual_comparison': comparison_data,
            'summary': {
                'total_years': len(comparison_data),
                'latest_year': comparison_data[0]['fiscal_year'] if comparison_data else None,
                'earliest_year': comparison_data[-1]['fiscal_year'] if comparison_data else None
            },
            'last_updated': datetime.now().isoformat()
        }

    # ===== 高级功能：XBRL转换 =====

    async def convert_xbrl_to_json(
        self,
        filing_url: str,
        include_dimensions: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        将XBRL文件转换为JSON格式

        Args:
            filing_url: SEC XBRL文件URL
            include_dimensions: 是否包含维度信息
            use_cache: 是否使用缓存

        Returns:
            转换后的JSON数据

        Raises:
            FinanceAPIException: 转换失败时抛出
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not filing_url or not filing_url.strip():
            raise FinanceAPIException(
                message="XBRL文件URL不能为空",
                code="INVALID_FILING_URL"
            )

        # 构建缓存键
        cache_key = f"sec:xbrl:convert:{quote(filing_url)}:{include_dimensions}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取XBRL转换数据: {filing_url}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取转换数据
            logger.info(f"从SEC数据源转换XBRL: {filing_url}")
            result = await self.advanced_data_source.convert_xbrl_to_json(
                filing_url=filing_url,
                include_dimensions=include_dimensions
            )

            if not result:
                raise FinanceAPIException(
                    message=f"XBRL文件转换失败: {filing_url}",
                    code="XBRL_CONVERSION_FAILED"
                )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['xbrl']['ttl']
                    )
                    logger.debug(f"XBRL转换数据已缓存: {filing_url}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"XBRL转换失败: {filing_url}, 错误: {e}")
            raise FinanceAPIException(
                message=f"XBRL转换失败: {str(e)}",
                code="XBRL_CONVERSION_ERROR"
            )

    async def get_company_xbrl_data(
        self,
        ticker: str,
        form_type: str = "10-K",
        fiscal_year: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司XBRL数据

        Args:
            ticker: 股票代码
            form_type: 报表类型
            fiscal_year: 财政年度
            use_cache: 是否使用缓存

        Returns:
            公司XBRL数据
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        # 参数验证
        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:xbrl:company:{ticker}:{form_type}:{fiscal_year}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取公司XBRL数据: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取公司XBRL数据: {ticker}")
            result = await self.advanced_data_source.get_company_xbrl_data(
                ticker=ticker,
                form_type=form_type,
                fiscal_year=fiscal_year
            )

            if not result:
                raise FinanceAPIException(
                    message=f"未找到股票代码 {ticker} 的XBRL数据",
                    code="XBRL_DATA_NOT_FOUND"
                )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['xbrl']['ttl']
                    )
                    logger.debug(f"公司XBRL数据已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取公司XBRL数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取公司XBRL数据失败: {str(e)}",
                code="XBRL_DATA_ERROR"
            )

    # ===== 高级功能：全文搜索 =====

    async def full_text_search(
        self,
        query: str,
        form_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        SEC文件全文搜索

        Args:
            query: 搜索查询语句
            form_types: 文件类型列表
            date_from: 开始日期
            date_to: 结束日期
            limit: 结果数量限制
            use_cache: 是否使用缓存

        Returns:
            搜索结果
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not query or not query.strip():
            raise FinanceAPIException(
                message="搜索查询不能为空",
                code="INVALID_SEARCH_QUERY"
            )

        # 构建缓存键
        cache_key = f"sec:search:fulltext:{quote(query)}:{'-'.join(form_types or [])}:{date_from}:{date_to}:{limit}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取全文搜索结果: {query}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源搜索
            logger.info(f"执行SEC全文搜索: {query}")
            result = await self.advanced_data_source.full_text_search(
                query=query,
                form_types=form_types,
                date_from=date_from,
                date_to=date_to,
                limit=limit
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['search']['ttl']
                    )
                    logger.debug(f"全文搜索结果已缓存: {query}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"全文搜索失败: {query}, 错误: {e}")
            raise FinanceAPIException(
                message=f"全文搜索失败: {str(e)}",
                code="FULLTEXT_SEARCH_ERROR"
            )

    async def search_company_filings(
        self,
        ticker: str,
        query: str,
        form_types: Optional[List[str]] = None,
        years: int = 3,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        在公司文件中搜索

        Args:
            ticker: 股票代码
            query: 搜索查询
            form_types: 文件类型列表
            years: 搜索年数
            use_cache: 是否使用缓存

        Returns:
            搜索结果
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        if not query or not query.strip():
            raise FinanceAPIException(
                message="搜索查询不能为空",
                code="INVALID_SEARCH_QUERY"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:search:company:{ticker}:{quote(query)}:{'-'.join(form_types or [])}:{years}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取公司文件搜索结果: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源搜索
            logger.info(f"在公司文件中搜索: {ticker}, 查询: {query}")
            result = await self.advanced_data_source.search_company_filings(
                ticker=ticker,
                query=query,
                form_types=form_types,
                years=years
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['search']['ttl']
                    )
                    logger.debug(f"公司文件搜索结果已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"公司文件搜索失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"公司文件搜索失败: {str(e)}",
                code="COMPANY_SEARCH_ERROR"
            )

    # ===== 高级功能：内幕交易数据 =====

    async def get_insider_trading(
        self,
        ticker: str,
        days_back: int = 90,
        include_derivatives: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取内幕交易数据

        Args:
            ticker: 股票代码
            days_back: 查询天数
            include_derivatives: 是否包含衍生品交易
            use_cache: 是否使用缓存

        Returns:
            内幕交易数据
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        if not (1 <= days_back <= 365):
            raise FinanceAPIException(
                message="查询天数必须在1-365之间",
                code="INVALID_DAYS_BACK"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:insider:{ticker}:{days_back}:{include_derivatives}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取内幕交易数据: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取内幕交易数据: {ticker}")
            result = await self.advanced_data_source.get_insider_trading(
                ticker=ticker,
                days_back=days_back,
                include_derivatives=include_derivatives
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['insider']['ttl']
                    )
                    logger.debug(f"内幕交易数据已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取内幕交易数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取内幕交易数据失败: {str(e)}",
                code="INSIDER_TRADING_ERROR"
            )

    # ===== 高级功能：机构持股数据 =====

    async def get_institutional_holdings(
        self,
        ticker: str,
        quarters: int = 4,
        min_value: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取机构持股数据

        Args:
            ticker: 股票代码
            quarters: 查询季度数
            min_value: 最小持股价值
            use_cache: 是否使用缓存

        Returns:
            机构持股数据
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        if not (1 <= quarters <= 8):
            raise FinanceAPIException(
                message="查询季度数必须在1-8之间",
                code="INVALID_QUARTERS"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:holdings:{ticker}:{quarters}:{min_value}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取机构持股数据: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取机构持股数据: {ticker}")
            result = await self.advanced_data_source.get_institutional_holdings(
                ticker=ticker,
                quarters=quarters,
                min_value=min_value
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['holdings']['ttl']
                    )
                    logger.debug(f"机构持股数据已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取机构持股数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取机构持股数据失败: {str(e)}",
                code="INSTITUTIONAL_HOLDINGS_ERROR"
            )

    # ===== 高级功能：IPO数据 =====

    async def get_recent_ipos(
        self,
        days_back: int = 30,
        min_offering_amount: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取最近IPO数据

        Args:
            days_back: 查询天数
            min_offering_amount: 最小募资金额
            use_cache: 是否使用缓存

        Returns:
            IPO数据
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not (1 <= days_back <= 365):
            raise FinanceAPIException(
                message="查询天数必须在1-365之间",
                code="INVALID_DAYS_BACK"
            )

        # 构建缓存键
        cache_key = f"sec:ipo:recent:{days_back}:{min_offering_amount}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取最近IPO数据")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取最近IPO数据")
            result = await self.advanced_data_source.get_recent_ipos(
                days_back=days_back,
                min_offering_amount=min_offering_amount
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['ipo']['ttl']
                    )
                    logger.debug(f"最近IPO数据已缓存")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取最近IPO数据失败, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取最近IPO数据失败: {str(e)}",
                code="IPO_DATA_ERROR"
            )

    async def get_company_ipo_details(
        self,
        ticker: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司IPO详情

        Args:
            ticker: 股票代码
            use_cache: 是否使用缓存

        Returns:
            公司IPO详情
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:ipo:company:{ticker}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取公司IPO详情: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取公司IPO详情: {ticker}")
            result = await self.advanced_data_source.get_company_ipo_details(ticker=ticker)

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['ipo']['ttl']
                    )
                    logger.debug(f"公司IPO详情已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取公司IPO详情失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取公司IPO详情失败: {str(e)}",
                code="COMPANY_IPO_ERROR"
            )

    # ===== 高级功能：高管薪酬数据 =====

    async def get_executive_compensation(
        self,
        ticker: str,
        years: int = 3,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取高管薪酬数据

        Args:
            ticker: 股票代码
            years: 查询年数
            use_cache: 是否使用缓存

        Returns:
            高管薪酬数据
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        if not (1 <= years <= 5):
            raise FinanceAPIException(
                message="查询年数必须在1-5之间",
                code="INVALID_YEARS"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:compensation:{ticker}:{years}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取高管薪酬数据: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取高管薪酬数据: {ticker}")
            result = await self.advanced_data_source.get_executive_compensation(
                ticker=ticker,
                years=years
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['compensation']['ttl']
                    )
                    logger.debug(f"高管薪酬数据已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取高管薪酬数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取高管薪酬数据失败: {str(e)}",
                code="EXECUTIVE_COMPENSATION_ERROR"
            )

    # ===== 高级功能：公司治理数据 =====

    async def get_company_governance(
        self,
        ticker: str,
        include_subsidiaries: bool = True,
        include_audit_fees: bool = True,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司治理信息

        Args:
            ticker: 股票代码
            include_subsidiaries: 是否包含子公司信息
            include_audit_fees: 是否包含审计费用
            use_cache: 是否使用缓存

        Returns:
            公司治理信息
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:governance:{ticker}:{include_subsidiaries}:{include_audit_fees}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取公司治理信息: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取公司治理信息: {ticker}")
            result = await self.advanced_data_source.get_company_governance(
                ticker=ticker,
                include_subsidiaries=include_subsidiaries,
                include_audit_fees=include_audit_fees
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['governance']['ttl']
                    )
                    logger.debug(f"公司治理信息已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取公司治理信息失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取公司治理信息失败: {str(e)}",
                code="COMPANY_GOVERNANCE_ERROR"
            )

    # ===== 高级功能：SEC执法数据 =====

    async def get_recent_enforcement_actions(
        self,
        days_back: int = 90,
        action_type: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取最近SEC执法行动

        Args:
            days_back: 查询天数
            action_type: 行动类型
            use_cache: 是否使用缓存

        Returns:
            SEC执法行动数据
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not (1 <= days_back <= 365):
            raise FinanceAPIException(
                message="查询天数必须在1-365之间",
                code="INVALID_DAYS_BACK"
            )

        # 构建缓存键
        cache_key = f"sec:enforcement:{days_back}:{action_type}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取SEC执法行动数据")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取SEC执法行动数据")
            result = await self.advanced_data_source.get_recent_enforcement_actions(
                days_back=days_back,
                action_type=action_type
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['enforcement']['ttl']
                    )
                    logger.debug(f"SEC执法行动数据已缓存")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取SEC执法行动数据失败, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取SEC执法行动数据失败: {str(e)}",
                code="ENFORCEMENT_ACTIONS_ERROR"
            )

    # ===== 高级功能：映射和实体数据 =====

    async def get_ticker_to_cik_mapping(
        self,
        ticker: str,
        include_historical: bool = False,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取股票代码到CIK映射

        Args:
            ticker: 股票代码
            include_historical: 是否包含历史映射
            use_cache: 是否使用缓存

        Returns:
            映射数据
        """
        if not self.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用",
                code="SEC_ADVANCED_UNAVAILABLE"
            )

        if not ticker or not ticker.strip():
            raise FinanceAPIException(
                message="股票代码不能为空",
                code="INVALID_TICKER"
            )

        ticker = ticker.upper().strip()

        # 构建缓存键
        cache_key = f"sec:mapping:{ticker}:{include_historical}"

        # 尝试从缓存获取
        if use_cache:
            try:
                cached_data = await get_cache_value(cache_key)
                if cached_data:
                    logger.info(f"从缓存获取CIK映射: {ticker}")
                    return cached_data
            except Exception as e:
                logger.warning(f"获取缓存失败: {e}")

        try:
            # 从数据源获取数据
            logger.info(f"从SEC数据源获取CIK映射: {ticker}")
            result = await self.advanced_data_source.get_ticker_to_cik_mapping(
                ticker=ticker,
                include_historical=include_historical
            )

            # 缓存结果
            if use_cache:
                try:
                    await set_cache_value(
                        cache_key,
                        result,
                        ttl=self.cache_config['mapping']['ttl']
                    )
                    logger.debug(f"CIK映射已缓存: {ticker}")
                except Exception as e:
                    logger.warning(f"缓存设置失败: {e}")

            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise

            logger.error(f"获取CIK映射失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取CIK映射失败: {str(e)}",
                code="CIK_MAPPING_ERROR"
            )

    async def get_health_status(self) -> Dict[str, Any]:
        """获取SEC服务健康状态"""
        try:
            # 检查基础数据源状态
            basic_status = await self.data_source.get_health_status()

            # 检查高级数据源状态（如果可用）
            advanced_status = None
            if self.advanced_available and self.advanced_data_source:
                try:
                    advanced_status = await self.advanced_data_source.get_health_status()
                except Exception as e:
                    logger.warning(f"高级数据源健康检查失败: {e}")
                    advanced_status = {"status": "unhealthy", "error": str(e)}

            return {
                'service': 'sec_service',
                'status': basic_status.get('status', 'unknown'),
                'basic_data_source_status': basic_status,
                'advanced_available': self.advanced_available,
                'advanced_data_source_status': advanced_status,
                'cache_enabled': True,
                'last_checked': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'service': 'sec_service',
                'status': 'unhealthy',
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }

    async def shutdown(self):
        """关闭服务"""
        try:
            await self.data_source.shutdown()
            if self.advanced_available and self.advanced_data_source:
                await self.advanced_data_source.shutdown()
            logger.info("SEC服务已关闭")
        except Exception as e:
            logger.error(f"关闭SEC服务失败: {e}")


# 全局服务实例
_sec_service: Optional[SecService] = None


def get_sec_service() -> SecService:
    """获取SEC服务实例（单例模式）"""
    global _sec_service
    if _sec_service is None:
        try:
            # 尝试使用配置的API密钥，如果没有则使用免费API
            api_key = getattr(settings, 'sec_api_key', None)
            _sec_service = SecService(api_key=api_key)

            if api_key:
                logger.info("SEC服务已初始化（使用API密钥）")
            else:
                logger.info("SEC服务已初始化（使用免费API）")

        except Exception as e:
            logger.error(f"SEC服务初始化失败: {e}")
            raise FinanceAPIException(
                message=f"SEC服务不可用: {str(e)}",
                code="SEC_SERVICE_UNAVAILABLE"
            )
    return _sec_service


async def initialize_sec_service(api_key: Optional[str] = None):
    """初始化SEC服务"""
    global _sec_service
    try:
        _sec_service = SecService(api_key=api_key)
        logger.info("SEC服务已初始化")
    except Exception as e:
        logger.error(f"SEC服务初始化失败: {e}")
        # 不抛出异常，允许应用继续启动，但服务不可用
        _sec_service = None


async def shutdown_sec_service():
    """关闭SEC服务"""
    global _sec_service
    if _sec_service:
        await _sec_service.shutdown()
        _sec_service = None
