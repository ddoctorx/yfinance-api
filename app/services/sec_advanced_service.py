"""
SEC高级数据服务
基于SEC API提供的高级功能实现
包括XBRL转换、全文搜索、内幕交易、机构持股等
"""

import asyncio
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote

from app.data_sources.sec_advanced_source import SecAdvancedDataSource
from app.utils.cache import get_cache_value, set_cache_value
from app.core.logging import get_logger
from app.utils.exceptions import FinanceAPIException
from app.core.config import settings

logger = get_logger(__name__)


class SecAdvancedService:
    """SEC高级数据服务"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化SEC高级服务

        Args:
            api_key: SEC API密钥（必需）

        Raises:
            FinanceAPIException: 当SEC API不可用时抛出
        """
        try:
            self.data_source = SecAdvancedDataSource(api_key=api_key)
        except Exception as e:
            logger.error(f"SEC高级数据源初始化失败: {e}")
            raise FinanceAPIException(
                message=f"SEC高级服务不可用: {str(e)}",
                code="SEC_ADVANCED_SERVICE_UNAVAILABLE"
            )

        # 缓存配置
        self.cache_config = {
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

    # ===== XBRL转换功能 =====

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
            result = await self.data_source.convert_xbrl_to_json(
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
            result = await self.data_source.get_company_xbrl_data(
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

    # ===== 全文搜索功能 =====

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
            result = await self.data_source.full_text_search(
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
            result = await self.data_source.search_company_filings(
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

    # ===== 内幕交易数据 =====

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
            result = await self.data_source.get_insider_trading(
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

    # ===== 机构持股数据 =====

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
            result = await self.data_source.get_institutional_holdings(
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

    # ===== IPO数据 =====

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
            result = await self.data_source.get_recent_ipos(
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
            result = await self.data_source.get_company_ipo_details(ticker=ticker)

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

    # ===== 高管薪酬数据 =====

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
            result = await self.data_source.get_executive_compensation(
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

    # ===== 公司治理数据 =====

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
            result = await self.data_source.get_company_governance(
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

    # ===== SEC执法数据 =====

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
            result = await self.data_source.get_recent_enforcement_actions(
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

    # ===== 映射和实体数据 =====

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
            result = await self.data_source.get_ticker_to_cik_mapping(
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

    # ===== 健康检查 =====

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取服务健康状态

        Returns:
            健康状态信息
        """
        try:
            status = await self.data_source.get_health_status()
            return {
                **status,
                "cache_status": "healthy",
                "service_name": "sec_advanced_service"
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "service_name": "sec_advanced_service"
            }

    async def shutdown(self):
        """关闭服务"""
        try:
            if hasattr(self.data_source, 'shutdown'):
                await self.data_source.shutdown()
            logger.info("SEC高级服务已关闭")
        except Exception as e:
            logger.error(f"关闭SEC高级服务失败: {e}")


# ===== 服务实例管理 =====

_sec_advanced_service: Optional[SecAdvancedService] = None


def get_sec_advanced_service() -> SecAdvancedService:
    """
    获取SEC高级服务单例

    Returns:
        SecAdvancedService实例

    Raises:
        FinanceAPIException: 服务不可用时抛出
    """
    global _sec_advanced_service

    if _sec_advanced_service is None:
        api_key = getattr(settings, 'sec_api_key', None)
        _sec_advanced_service = SecAdvancedService(api_key=api_key)

    return _sec_advanced_service


async def initialize_sec_advanced_service(api_key: Optional[str] = None):
    """
    初始化SEC高级服务

    Args:
        api_key: SEC API密钥，如果不提供则从配置获取
    """
    global _sec_advanced_service

    try:
        if api_key is None:
            api_key = getattr(settings, 'sec_api_key', None)

        _sec_advanced_service = SecAdvancedService(api_key=api_key)
        logger.info("SEC高级服务初始化成功")
    except Exception as e:
        logger.error(f"SEC高级服务初始化失败: {e}")
        raise


async def shutdown_sec_advanced_service():
    """关闭SEC高级服务"""
    global _sec_advanced_service

    if _sec_advanced_service:
        try:
            await _sec_advanced_service.shutdown()
            _sec_advanced_service = None
            logger.info("SEC高级服务已关闭")
        except Exception as e:
            logger.error(f"关闭SEC高级服务失败: {e}")
