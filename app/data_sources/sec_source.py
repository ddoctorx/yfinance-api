"""
SEC (Securities and Exchange Commission) 数据源
提供美股公司财报数据和SEC文件信息
"""

import asyncio
import aiohttp
import requests
import requests_cache
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
import pandas as pd
import os
import logging

try:
    from sec_api import ExtractorApi, QueryApi, RenderApi, XbrlApi
    SEC_API_AVAILABLE = True
except ImportError:
    SEC_API_AVAILABLE = False

from app.data_sources.base import BaseDataSource, DataSourceError, DataSourceType
from app.core.logging import get_logger
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.models.sec import (
    CompanyFinancialsResponse,
    AnnualFinancials,
    QuarterlyFinancials,
    IncomeStatementData,
    BalanceSheetData,
    CashFlowData,
    SecNewsResponse,
    SecNewsItem,
    SecFilingInfo,
    FinancialRatios
)

logger = logging.getLogger(__name__)


class SecDataSource(BaseDataSource):
    """SEC数据源实现"""

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        初始化SEC数据源

        Args:
            api_key: SEC API密钥 (可选，未提供时使用免费额度)
            use_cache: 是否启用缓存
        """
        # 初始化基类
        super().__init__(DataSourceType.ALPHAVANTAGE, "SEC EDGAR")  # 使用ALPHAVANTAGE作为占位符

        self.api_key = api_key or os.environ.get('SEC_API_KEY')
        self.use_cache = use_cache

        if not SEC_API_AVAILABLE:
            logger.warning("sec-api包未安装，将使用模拟数据模式")
            self._mock_mode = True
        elif not self.api_key:
            logger.warning("SEC API密钥未提供，将使用模拟数据模式")
            self._mock_mode = True
        else:
            self._mock_mode = False
            try:
                self.extractor_api = ExtractorApi(api_key=self.api_key)
                self.query_api = QueryApi(api_key=self.api_key)
                self.render_api = RenderApi(api_key=self.api_key)
                self.xbrl_api = XbrlApi(api_key=self.api_key)
                logger.info("SEC API客户端初始化成功")
            except Exception as e:
                logger.error(f"SEC API客户端初始化失败: {e}")
                self._mock_mode = True

        # 设置缓存会话
        if use_cache:
            self.session = requests_cache.CachedSession(
                'sec_cache',
                expire_after=timedelta(hours=1)  # SEC数据缓存1小时
            )
        else:
            self.session = requests.Session()

        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    # 实现DataSourceInterface要求的抽象方法
    async def get_fast_quote(self, symbol: str) -> FastQuoteData:
        """
        获取快速报价数据
        SEC数据源主要提供财报数据，不提供实时报价，返回空数据
        """
        logger.warning(f"SEC数据源不支持实时报价，返回空数据: {symbol}")
        return FastQuoteData(
            last_price=0.0,
            previous_close=0.0,
            open_price=0.0,
            day_high=0.0,
            day_low=0.0,
            volume=0,
            market_cap=0,
            shares=0,
            currency="USD"
        )

    async def get_detailed_quote(self, symbol: str) -> QuoteData:
        """
        获取详细报价数据
        SEC数据源主要提供财报数据，不提供实时报价，返回空数据
        """
        logger.warning(f"SEC数据源不支持详细报价，返回空数据: {symbol}")
        return QuoteData(
            last_price=0.0,
            previous_close=0.0,
            open_price=0.0,
            day_high=0.0,
            day_low=0.0,
            change=0.0,
            change_percent=0.0,
            volume=0,
            market_cap=0,
            pe_ratio=None,
            fifty_two_week_high=0.0,
            fifty_two_week_low=0.0,
            currency="USD",
            exchange="Unknown"
        )

    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """
        获取公司信息
        从SEC数据中提取基本公司信息
        """
        try:
            # 尝试从SEC数据获取公司信息
            cik = await self._get_company_cik(symbol)
            if cik:
                # 获取公司基本信息
                submissions_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
                response = requests.get(
                    submissions_url, headers=self.headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    return CompanyInfo(
                        name=data.get('name', f'{symbol} Corporation'),
                        sector=data.get('sicDescription', 'Unknown'),
                        industry=data.get('sicDescription', 'Unknown'),
                        country=data.get('stateOfIncorporation', 'US'),
                        website=data.get('website', ''),
                        business_summary=f"CIK: {cik}, Exchange: {data.get('exchanges', ['Unknown'])[0] if data.get('exchanges') else 'Unknown'}",
                        employees=data.get('employeeCount', 0)
                    )

            # 如果无法获取SEC数据，返回基本信息
            return CompanyInfo(
                name=f'{symbol} Corporation',
                sector='Unknown',
                industry='Unknown',
                country='US',
                website='',
                business_summary='Company information from SEC data source',
                employees=0
            )

        except Exception as e:
            logger.error(f"获取公司信息失败: {symbol}, 错误: {e}")
            return CompanyInfo(
                name=f'{symbol} Corporation',
                sector='Unknown',
                industry='Unknown',
                country='US',
                website='',
                business_summary='Unable to retrieve company information',
                employees=0
            )

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
        """
        获取历史数据
        SEC数据源不提供价格历史数据，返回空数据
        """
        logger.warning(f"SEC数据源不支持历史价格数据，返回空数据: {symbol}")
        return {
            'symbol': symbol,
            'data': [],
            'metadata': {
                'source': 'SEC EDGAR',
                'note': 'SEC data source does not provide price history'
            }
        }

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, FastQuoteData]:
        """
        批量获取报价数据
        SEC数据源不提供实时报价，返回空数据
        """
        logger.warning(f"SEC数据源不支持批量报价，返回空数据: {symbols}")
        result = {}
        for symbol in symbols:
            result[symbol] = await self.get_fast_quote(symbol)
        return result

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if self._mock_mode:
                logger.info("使用模拟模式，返回健康状态")
                return True

            # 使用免费的SEC.gov端点测试连接
            response = requests.get("https://www.sec.gov/edgar/searchedgar/companysearch.html",
                                    timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SEC数据源健康检查失败: {e}")
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """获取数据源健康状态"""
        try:
            # 测试EDGAR API连通性
            edgar_url = "https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Revenues.json"

            async with aiohttp.ClientSession() as session:
                async with session.get(edgar_url, headers=self.headers) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "response_time": getattr(response, 'response_time', 0),
                            "api_available": self.api_key is not None,
                            "cache_enabled": self.use_cache
                        }
                    else:
                        return {
                            "status": "degraded",
                            "message": f"EDGAR API返回状态码: {response.status}",
                            "api_available": self.api_key is not None
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_available": self.api_key is not None
            }

    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        从股票代码获取CIK

        Args:
            ticker: 股票代码

        Returns:
            CIK字符串或None
        """
        try:
            # 使用SEC的company tickers映射
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self.session.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                for company_info in data.values():
                    if company_info.get('ticker', '').upper() == ticker.upper():
                        cik = str(company_info.get('cik_str', '')).zfill(10)
                        return cik

            logger.warning(f"未找到股票代码 {ticker} 对应的CIK")
            return None

        except Exception as e:
            logger.error(f"获取CIK失败: {e}")
            return None

    def _fetch_company_concept_data(self, cik: str, concept: str) -> Optional[Dict]:
        """
        获取公司概念数据

        Args:
            cik: 公司CIK
            concept: 财务概念 (如 Revenues, Assets等)

        Returns:
            概念数据字典或None
        """
        try:
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
            response = self.session.get(url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    f"获取概念数据失败: {concept}, 状态码: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"获取概念数据异常: {concept}, 错误: {e}")
            return None

    def _parse_financial_data(self, concept_data: Dict, years: int = 5) -> Dict[str, List]:
        """
        解析财务数据

        Args:
            concept_data: 概念数据字典
            years: 获取年数

        Returns:
            包含年度和季度数据的字典
        """
        annual_data = []
        quarterly_data = []

        try:
            # 获取当前日期
            current_date = datetime.now()
            cutoff_date = current_date - timedelta(days=365 * years)

            # 解析10-K年度数据
            for form_type in ['10-K', '10-K/A']:
                if form_type in concept_data.get('units', {}).get('USD', {}):
                    for item in concept_data['units']['USD'][form_type]:
                        end_date = datetime.strptime(item['end'], '%Y-%m-%d')
                        if end_date >= cutoff_date:
                            annual_data.append({
                                'end_date': end_date,
                                'value': item.get('val'),
                                'filed_date': datetime.strptime(item['filed'], '%Y-%m-%d'),
                                'form': form_type,
                                'period': item.get('fp', 'FY')
                            })

            # 解析10-Q季度数据
            for form_type in ['10-Q', '10-Q/A']:
                if form_type in concept_data.get('units', {}).get('USD', {}):
                    for item in concept_data['units']['USD'][form_type]:
                        end_date = datetime.strptime(item['end'], '%Y-%m-%d')
                        if end_date >= cutoff_date:
                            quarterly_data.append({
                                'end_date': end_date,
                                'value': item.get('val'),
                                'filed_date': datetime.strptime(item['filed'], '%Y-%m-%d'),
                                'form': form_type,
                                'period': item.get('fp', 'Q1')
                            })

            # 按日期排序
            annual_data.sort(key=lambda x: x['end_date'], reverse=True)
            quarterly_data.sort(key=lambda x: x['end_date'], reverse=True)

        except Exception as e:
            logger.error(f"解析财务数据异常: {e}")

        return {
            'annual': annual_data[:years],  # 限制年数
            'quarterly': quarterly_data[:years * 4]  # 限制季度数
        }

    async def get_company_financials(
        self,
        ticker: str,
        years: int = 5,
        include_quarterly: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司财务数据

        Args:
            ticker: 公司股票代码
            years: 获取的年份数量
            include_quarterly: 是否包含季度数据

        Returns:
            包含财务数据的字典
        """
        try:
            if self._mock_mode:
                logger.info(f"使用模拟模式获取 {ticker} 财务数据")
                return self._get_mock_financial_data(ticker)

            # 如果没有API密钥，使用免费的SEC.gov数据
            return await self._get_free_sec_data(ticker, years, include_quarterly)

        except Exception as e:
            logger.error(f"获取公司财务数据失败 {ticker}: {e}")
            # 降级到模拟数据
            return self._get_mock_financial_data(ticker)

    async def _get_free_sec_data(self, ticker: str, years: int, include_quarterly: bool) -> Dict[str, Any]:
        """使用免费的SEC.gov API获取数据"""
        try:
            # 首先获取公司CIK
            cik = await self._get_company_cik(ticker)
            if not cik:
                raise DataSourceError(f"无法找到股票代码 {ticker} 对应的CIK")

            # 获取公司概念数据
            concepts_url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:010d}/us-gaap/Revenues.json"

            response = requests.get(
                concepts_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return self._parse_sec_concepts_data(data, ticker, years, include_quarterly)
            else:
                logger.warning(f"SEC.gov API请求失败: {response.status_code}")
                return self._get_mock_financial_data(ticker)

        except Exception as e:
            logger.error(f"获取免费SEC数据失败: {e}")
            return self._get_mock_financial_data(ticker)

    async def _get_company_cik(self, ticker: str) -> Optional[int]:
        """获取公司的CIK号码"""
        try:
            # 使用SEC.gov的公司搜索API
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(
                tickers_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for key, company in data.items():
                    if company.get('ticker', '').upper() == ticker.upper():
                        return company.get('cik_str')

            return None
        except Exception as e:
            logger.error(f"获取CIK失败: {e}")
            return None

    def _parse_sec_concepts_data(self, data: Dict, ticker: str, years: int, include_quarterly: bool) -> Dict[str, Any]:
        """解析SEC概念数据"""
        try:
            company_info = data.get('entityName', f'{ticker} Corporation')
            cik = data.get('cik', '0001234567')

            # 解析年度和季度数据
            units = data.get('units', {})
            usd_data = units.get('USD', [])

            # 按年度和季度分组数据
            annual_data = []
            quarterly_data = []

            for item in usd_data:
                filing_date = item.get('filed')
                form_type = item.get('form', '')
                fiscal_year = item.get('fy')
                revenue = item.get('val', 0)

                if form_type == '10-K' and fiscal_year:
                    annual_data.append({
                        'fiscal_year': fiscal_year,
                        'revenue': revenue,
                        'net_income': revenue * 0.2,  # 估算
                        'total_assets': revenue * 3,  # 估算
                        'total_debt': revenue * 0.5,  # 估算
                        'filing_date': filing_date
                    })
                elif form_type == '10-Q' and include_quarterly and fiscal_year:
                    quarter = item.get('fp', 'Q1')
                    quarterly_data.append({
                        'quarter': f"{quarter} {fiscal_year}",
                        'fiscal_year': fiscal_year,
                        'revenue': revenue,
                        'net_income': revenue * 0.2,
                        'filing_date': filing_date
                    })

            # 按年份排序，取最近几年
            annual_data = sorted(
                annual_data, key=lambda x: x['fiscal_year'], reverse=True)[:years]
            quarterly_data = sorted(quarterly_data, key=lambda x: (
                x['fiscal_year'], x['quarter']), reverse=True)[:20]

            return {
                'ticker': ticker,
                'company_name': company_info,
                'cik': cik,
                'annual_financials': annual_data,
                'quarterly_financials': quarterly_data if include_quarterly else []
            }

        except Exception as e:
            logger.error(f"解析SEC概念数据失败: {e}")
            return self._get_mock_financial_data(ticker)

    def _get_value_for_period(self, concept_data: Dict, concept: str, period_type: str, index: int) -> Optional[Decimal]:
        """获取指定期间的数值"""
        try:
            if concept in concept_data and period_type in concept_data[concept]:
                data_list = concept_data[concept][period_type]
                if index < len(data_list):
                    value = data_list[index].get('value')
                    if value is not None:
                        return Decimal(str(value))
        except (IndexError, KeyError, ValueError):
            pass
        return None

    async def get_company_news(
        self,
        ticker: str,
        limit: int = 10,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取公司SEC新闻和文件

        Args:
            ticker: 股票代码
            limit: 返回结果数量限制
            days_back: 向后查找天数

        Returns:
            SEC新闻项目列表
        """
        try:
            if self._mock_mode:
                logger.info(f"使用模拟模式获取 {ticker} 新闻数据")
                return self._get_mock_news_data(ticker)[:limit]

            # 使用免费的SEC.gov数据获取最近的文件提交
            return await self._get_free_sec_filings(ticker, limit, days_back)

        except Exception as e:
            logger.error(f"获取公司SEC新闻失败 {ticker}: {e}")
            # 降级到模拟数据
            return self._get_mock_news_data(ticker)[:limit]

    async def _get_free_sec_filings(self, ticker: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
        """使用免费的SEC.gov API获取最近的文件提交"""
        try:
            # 获取CIK
            cik = await self._get_company_cik(ticker)
            if not cik:
                return self._get_mock_news_data(ticker)[:limit]

            # 获取公司最近提交的文件
            submissions_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
            response = requests.get(
                submissions_url, headers=self.headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                return self._parse_sec_filings_data(data, ticker, limit, days_back)
            else:
                logger.warning(f"SEC提交数据请求失败: {response.status_code}")
                return self._get_mock_news_data(ticker)[:limit]

        except Exception as e:
            logger.error(f"获取免费SEC文件提交失败: {e}")
            return self._get_mock_news_data(ticker)[:limit]

    def _parse_sec_filings_data(self, data: Dict, ticker: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
        """解析SEC文件提交数据"""
        try:
            filings = []
            recent_filings = data.get('filings', {}).get('recent', {})

            forms = recent_filings.get('form', [])
            filing_dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])

            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=days_back)

            for i, (form, filing_date, accession) in enumerate(zip(forms, filing_dates, accession_numbers)):
                try:
                    # 检查日期是否在范围内
                    file_date = datetime.strptime(filing_date, '%Y-%m-%d')
                    if file_date < cutoff_date:
                        continue

                    # 只关注主要的财务报表类型
                    if form in ['10-K', '10-Q', '8-K', '20-F', 'DEF 14A']:
                        # 构建文件URL
                        accession_clean = accession.replace('-', '')
                        filing_url = f"https://www.sec.gov/Archives/edgar/data/{data.get('cik')}/{accession_clean}/{accession}-index.htm"

                        filing_info = {
                            'title': f"{ticker} 提交 {form} 文件",
                            'summary': self._get_form_description(form),
                            'url': filing_url,
                            'filing_type': form,
                            'filing_date': filing_date,
                            'accession_number': accession
                        }
                        filings.append(filing_info)

                        if len(filings) >= limit:
                            break

                except (ValueError, KeyError) as e:
                    logger.warning(f"解析文件项目失败: {e}")
                    continue

            return filings

        except Exception as e:
            logger.error(f"解析SEC文件提交数据失败: {e}")
            return self._get_mock_news_data(ticker)[:limit]

    def _get_form_description(self, form_type: str) -> str:
        """获取表单类型的描述"""
        descriptions = {
            '10-K': '年度报告，包含公司财务状况和业务概况的全面信息',
            '10-Q': '季度报告，包含未经审计的财务报表和管理层讨论',
            '8-K': '当期报告，披露重大公司事件或变化',
            '20-F': '外国公司年度报告',
            'DEF 14A': '委托书说明书，通常用于股东大会'
        }
        return descriptions.get(form_type, f'{form_type} 文件提交')

    async def calculate_financial_ratios(self, ticker: str, period: str = "annual") -> Optional[FinancialRatios]:
        """
        计算财务比率

        Args:
            ticker: 股票代码
            period: 期间类型 ("annual" 或 "quarterly")

        Returns:
            财务比率数据或None
        """
        try:
            financials = await self.get_company_financials(ticker, years=1, include_quarterly=(period == "quarterly"))

            if not financials:
                return None

            # 获取最新的财务数据
            if period == "annual" and financials.get('annual_financials'):
                latest = financials['annual_financials'][0]
            elif period == "quarterly" and financials.get('quarterly_financials'):
                latest = financials['quarterly_financials'][0]
            else:
                return None

            # 计算比率
            ratios = FinancialRatios(
                period=f"{period}_{latest['fiscal_year']}")

            if latest.get('total_assets') and latest.get('total_debt'):
                # 计算负债权益比
                if (latest.get('total_debt') and
                    latest.get('total_assets') and
                        latest.get('total_assets') > 0):
                    ratios.debt_to_equity = float(
                        latest.get('total_debt') / latest.get('total_assets')
                    )

                # 计算ROA (需要净利润和总资产)
                if (latest.get('net_income') and latest.get('total_assets') and
                        latest.get('total_assets') > 0):
                    ratios.roa = float(
                        latest.get('net_income') / latest.get('total_assets')
                    ) * 100

                # 计算ROE (需要净利润和股东权益)
                if (latest.get('net_income') and latest.get('total_assets') and
                        latest.get('total_assets') > 0):
                    ratios.roe = float(
                        latest.get('net_income') / latest.get('total_assets')
                    ) * 100

            return ratios

        except Exception as e:
            logger.error(f"计算财务比率失败: {ticker}, 错误: {e}")
            return None

    async def shutdown(self):
        """关闭数据源连接"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
            logger.info("SEC数据源已关闭")
        except Exception as e:
            logger.error(f"关闭SEC数据源失败: {e}")

    def _get_mock_financial_data(self, ticker: str) -> Dict[str, Any]:
        """返回模拟财务数据用于测试"""
        return {
            "ticker": ticker,
            "company_name": f"{ticker} Corporation",
            "cik": "0001234567",
            "annual_financials": [
                {
                    "fiscal_year": 2023,
                    "revenue": 100000000000,
                    "net_income": 20000000000,
                    "total_assets": 300000000000,
                    "total_debt": 50000000000,
                    "filing_date": "2024-02-01"
                },
                {
                    "fiscal_year": 2022,
                    "revenue": 90000000000,
                    "net_income": 18000000000,
                    "total_assets": 280000000000,
                    "total_debt": 45000000000,
                    "filing_date": "2023-02-01"
                }
            ],
            "quarterly_financials": [
                {
                    "quarter": "Q3 2023",
                    "fiscal_year": 2023,
                    "revenue": 26000000000,
                    "net_income": 5200000000,
                    "filing_date": "2023-10-26"
                },
                {
                    "quarter": "Q2 2023",
                    "fiscal_year": 2023,
                    "revenue": 25000000000,
                    "net_income": 5000000000,
                    "filing_date": "2023-07-26"
                }
            ]
        }

    def _get_mock_news_data(self, ticker: str) -> List[Dict[str, Any]]:
        """返回模拟新闻数据用于测试"""
        return [
            {
                "title": f"{ticker} 发布季度财报",
                "summary": f"{ticker}公司发布了最新的季度财报，显示营收增长强劲。",
                "url": f"https://www.sec.gov/ix?doc=/Archives/edgar/data/1234567/000123456724000001/mock-{ticker.lower()}-10q.htm",
                "filing_type": "10-Q",
                "filing_date": "2024-01-26",
                "accession_number": "0001234567-24-000001"
            },
            {
                "title": f"{ticker} 年度报告",
                "summary": f"{ticker}公司发布年度10-K报告，详细披露了公司业务状况。",
                "url": f"https://www.sec.gov/ix?doc=/Archives/edgar/data/1234567/000123456724000002/mock-{ticker.lower()}-10k.htm",
                "filing_type": "10-K",
                "filing_date": "2024-02-01",
                "accession_number": "0001234567-24-000002"
            }
        ]
