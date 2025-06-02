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

    def __init__(self, api_key: str = None):
        """初始化SEC数据源"""
        super().__init__(DataSourceType.SEC)

        self.api_key = api_key or os.environ.get('SEC_API_KEY')

        # 设置SEC API可用性标志
        self.sec_api_available = SEC_API_AVAILABLE and bool(self.api_key)

        if self.sec_api_available:
            try:
                self.query_api = QueryApi(api_key=self.api_key)
                self.extractor_api = ExtractorApi(api_key=self.api_key)
                self.render_api = RenderApi(api_key=self.api_key)
                self.xbrl_api = XbrlApi(api_key=self.api_key)
                logger.info("SEC API已初始化")
            except Exception as e:
                logger.warning(f"SEC API初始化失败，将使用免费API: {e}")
                self.sec_api_available = False
        else:
            self.query_api = None
            self.extractor_api = None
            self.render_api = None
            self.xbrl_api = None
            if not self.api_key:
                logger.info("未配置SEC API密钥，将使用免费的SEC.gov API")
            else:
                logger.warning("SEC API库不可用，将使用免费的SEC.gov API")

        # 配置请求头
        self.headers = {
            'User-Agent': 'YFinance-API/1.0 (https://example.com/contact)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }

        # 设置缓存
        self.session = requests_cache.CachedSession(
            cache_name='sec_cache',
            expire_after=timedelta(hours=1),
            backend='memory'
        )

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
        SEC数据源不提供历史价格数据
        """
        logger.warning(f"SEC数据源不支持历史价格数据: {symbol}")
        return {
            'dates': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': [],
            'message': 'SEC数据源不提供历史价格数据'
        }

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, FastQuoteData]:
        """获取批量快速报价"""
        logger.warning("SEC数据源不支持批量报价")
        return {symbol: await self.get_fast_quote(symbol) for symbol in symbols}

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 执行一个简单的查询来测试API连接
            query = {
                "query": "formType:\"10-K\"",
                "from": "0",
                "size": "1",
                "sort": [{"filedAt": {"order": "desc"}}]
            }
            response = self.query_api.get_filings(query)
            return bool(response and 'filings' in response)
        except Exception as e:
            logger.error(f"SEC API健康检查失败: {e}")
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态详情"""
        try:
            is_healthy = await self.health_check()
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'source': 'SEC EDGAR',
                'api_key_configured': bool(self.api_key),
                'cache_enabled': True,
                'last_checked': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'source': 'SEC EDGAR',
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }

    def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        从股票代码获取CIK
        使用SEC.gov免费API
        """
        try:
            # 获取公司代码映射
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(
                tickers_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for key, company in data.items():
                    if company.get('ticker', '').upper() == ticker.upper():
                        return str(company.get('cik_str'))
            return None
        except Exception as e:
            logger.error(f"获取CIK失败: {ticker}, 错误: {e}")
            return None

    def _fetch_company_concept_data(self, cik: str, concept: str) -> Optional[Dict]:
        """获取公司概念数据（从SEC.gov免费API）"""
        try:
            # 格式化CIK（需要10位数字，前面补0）
            formatted_cik = f"{int(cik):010d}"

            # SEC.gov的公司概念API
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{formatted_cik}/us-gaap/{concept}.json"

            response = requests.get(url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.info(f"概念 {concept} 对CIK {cik} 不存在")
                return None
            else:
                logger.warning(f"获取概念数据失败: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"获取概念数据失败: {concept}, 错误: {e}")
            return None

    def _parse_financial_data(self, concept_data: Dict, years: int = 5) -> Dict[str, List]:
        """解析财务概念数据"""
        try:
            result = {
                'annual': [],
                'quarterly': []
            }

            # 解析年度数据
            if 'units' in concept_data and 'USD' in concept_data['units']:
                usd_data = concept_data['units']['USD']

                # 过滤年度数据（form为10-K）
                annual_items = [
                    item for item in usd_data
                    if item.get('form') == '10-K' and 'fy' in item
                ]

                # 按年度排序
                annual_items.sort(key=lambda x: x.get('fy', 0), reverse=True)

                for item in annual_items[:years]:
                    result['annual'].append({
                        'fiscal_year': item.get('fy'),
                        'value': item.get('val', 0),
                        'filing_date': item.get('filed', ''),
                        'start_date': item.get('start', ''),
                        'end_date': item.get('end', ''),
                        'accession_number': item.get('accn', ''),
                        'form_type': item.get('form', '')
                    })

                # 过滤季度数据（form为10-Q）
                quarterly_items = [
                    item for item in usd_data
                    if item.get('form') == '10-Q' and 'fy' in item and 'fp' in item
                ]

                # 按年度和季度排序
                quarterly_items.sort(
                    key=lambda x: (x.get('fy', 0), x.get('fp', '')),
                    reverse=True
                )

                for item in quarterly_items[:years*4]:  # 最多years*4个季度
                    result['quarterly'].append({
                        'fiscal_year': item.get('fy'),
                        'quarter': f"Q{item.get('fp', 'X')} {item.get('fy', '')}",
                        'value': item.get('val', 0),
                        'filing_date': item.get('filed', ''),
                        'start_date': item.get('start', ''),
                        'end_date': item.get('end', ''),
                        'accession_number': item.get('accn', ''),
                        'form_type': item.get('form', '')
                    })

            return result
        except Exception as e:
            logger.error(f"解析财务数据失败: {e}")
            return {'annual': [], 'quarterly': []}

    async def get_company_financials(
        self,
        ticker: str,
        years: int = 5,
        include_quarterly: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司财务数据

        Args:
            ticker: 股票代码
            years: 获取年数 (1-10)
            include_quarterly: 是否包含季度数据

        Returns:
            包含年度和季度财务数据的字典

        Raises:
            DataSourceError: 当获取数据失败时抛出
        """
        try:
            # 首先获取公司CIK
            cik = await self._get_company_cik(ticker)
            if not cik:
                # 尝试使用内置的CIK查找
                cik = self._get_cik_from_ticker(ticker)
                if not cik:
                    raise DataSourceError(f"无法找到股票代码 {ticker} 对应的CIK")

            if self.sec_api_available:
                # 使用SEC API获取文件信息，然后结合免费API获取数据
                return await self._get_hybrid_sec_data(ticker, cik, years, include_quarterly)
            else:
                # 仅使用免费的SEC.gov API
                return await self._get_free_sec_data(ticker, years, include_quarterly)

        except Exception as e:
            logger.error(f"获取SEC财务数据失败: {ticker}, 错误: {e}")
            raise DataSourceError(f"获取SEC财务数据失败: {str(e)}")

    async def _get_hybrid_sec_data(self, ticker: str, cik: str, years: int, include_quarterly: bool) -> Dict[str, Any]:
        """结合SEC API文件信息和免费API的财务数据"""
        try:
            # 1. 使用SEC API获取最新的文件信息
            query_payload = {
                "query": f"ticker:\"{ticker}\" AND (formType:\"10-K\" OR formType:\"10-Q\")",
                "from": "0",
                "size": "20",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }

            filing_info = {}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.sec-api.io',
                    json=query_payload,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        api_response = await response.json()
                        if api_response and 'filings' in api_response:
                            filings = api_response['filings']

                            # 组织文件信息以供后续使用
                            for filing in filings:
                                form_type = filing.get('formType')
                                fiscal_year = self._extract_fiscal_year(filing)
                                if fiscal_year and form_type:
                                    key = f"{form_type}_{fiscal_year}"
                                    filing_info[key] = {
                                        'filed_at': filing.get('filedAt'),
                                        'accession_no': filing.get('accessionNo'),
                                        'company_name': filing.get('companyName'),
                                        'link': filing.get('linkToFilingDetails')
                                    }

            # 2. 使用免费SEC.gov API获取实际财务数据
            financial_data = await self._get_free_sec_data(ticker, years, include_quarterly)

            # 3. 增强财务数据与文件信息
            if filing_info:
                company_name = next(iter(filing_info.values())).get(
                    'company_name', f'{ticker} Corporation')
                financial_data['company_name'] = company_name

                # 为年度数据添加文件信息
                for annual_item in financial_data.get('annual_financials', []):
                    fiscal_year = annual_item.get('fiscal_year')
                    file_key = f"10-K_{fiscal_year}"
                    if file_key in filing_info:
                        annual_item.update({
                            'sec_filing_url': filing_info[file_key].get('link'),
                            'accession_number': filing_info[file_key].get('accession_no')
                        })

                # 为季度数据添加文件信息
                for quarterly_item in financial_data.get('quarterly_financials', []):
                    fiscal_year = quarterly_item.get('fiscal_year')
                    file_key = f"10-Q_{fiscal_year}"
                    if file_key in filing_info:
                        quarterly_item.update({
                            'sec_filing_url': filing_info[file_key].get('link'),
                            'accession_number': filing_info[file_key].get('accession_no')
                        })

            return financial_data

        except Exception as e:
            logger.warning(f"混合模式获取失败，回退到免费API: {e}")
            return await self._get_free_sec_data(ticker, years, include_quarterly)

    def _extract_fiscal_year(self, filing: Dict) -> Optional[int]:
        """从filing中提取财政年度"""
        try:
            # 尝试从periodOfReport提取
            period_str = filing.get('periodOfReport', '')
            if period_str:
                # 格式通常是 YYYY-MM-DD
                return int(period_str.split('-')[0])

            # 尝试从filedAt提取
            filed_str = filing.get('filedAt', '')
            if filed_str:
                return int(filed_str.split('-')[0])

            return None
        except (ValueError, IndexError):
            return None

    async def _get_free_sec_data(self, ticker: str, years: int, include_quarterly: bool) -> Dict[str, Any]:
        """使用免费的SEC.gov API获取数据"""
        try:
            # 首先获取公司CIK
            cik = await self._get_company_cik(ticker)
            if not cik:
                raise DataSourceError(f"无法找到股票代码 {ticker} 对应的CIK")

            # 获取多个财务概念的数据
            financial_concepts = {
                'revenue': ['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
                'net_income': ['NetIncomeLoss', 'ProfitLoss', 'NetIncome'],
                'total_assets': ['Assets', 'AssetsCurrent'],
                'total_debt': ['DebtCurrent', 'LongTermDebt', 'Liabilities']
            }

            all_data = {}

            # 获取每个概念的数据
            for concept_name, concept_variations in financial_concepts.items():
                for concept in concept_variations:
                    data = self._fetch_company_concept_data(cik, concept)
                    if data:
                        all_data[concept_name] = self._parse_financial_data(
                            data, years)
                        break  # 找到数据就停止尝试其他变体

            # 组合所有财务数据
            result = {
                'ticker': ticker,
                'company_name': f'{ticker} Corporation',
                'cik': str(cik),
                'annual_financials': [],
                'quarterly_financials': []
            }

            # 构建年度财务数据
            if 'revenue' in all_data and all_data['revenue']['annual']:
                annual_revenue = all_data['revenue']['annual']

                for i, revenue_item in enumerate(annual_revenue):
                    fiscal_year = revenue_item['fiscal_year']

                    annual_financial = {
                        'fiscal_year': fiscal_year,
                        'revenue': revenue_item['value'],
                        'net_income': 0,
                        'total_assets': 0,
                        'total_debt': 0,
                        'filing_date': revenue_item['filing_date'],
                        'accession_number': revenue_item['accession_number'],
                        'form_type': revenue_item['form_type']
                    }

                    # 添加其他财务指标
                    for metric, data_dict in all_data.items():
                        if metric != 'revenue' and data_dict['annual']:
                            # 找到相同财年的数据
                            matching_item = next(
                                (item for item in data_dict['annual']
                                 if item['fiscal_year'] == fiscal_year),
                                None
                            )
                            if matching_item:
                                annual_financial[metric] = matching_item['value']

                    result['annual_financials'].append(annual_financial)

            # 构建季度财务数据
            if include_quarterly and 'revenue' in all_data and all_data['revenue']['quarterly']:
                quarterly_revenue = all_data['revenue']['quarterly']

                for revenue_item in quarterly_revenue:
                    fiscal_year = revenue_item['fiscal_year']
                    quarter = revenue_item['quarter']

                    quarterly_financial = {
                        'quarter': quarter,
                        'fiscal_year': fiscal_year,
                        'revenue': revenue_item['value'],
                        'net_income': 0,
                        'filing_date': revenue_item['filing_date'],
                        'accession_number': revenue_item['accession_number'],
                        'form_type': revenue_item['form_type']
                    }

                    # 添加净利润数据
                    if 'net_income' in all_data and all_data['net_income']['quarterly']:
                        matching_income = next(
                            (item for item in all_data['net_income']['quarterly']
                             if item['fiscal_year'] == fiscal_year and item['quarter'] == quarter),
                            None
                        )
                        if matching_income:
                            quarterly_financial['net_income'] = matching_income['value']

                    result['quarterly_financials'].append(quarterly_financial)

            return result

        except Exception as e:
            logger.error(f"获取免费SEC数据失败: {e}")
            raise DataSourceError(f"获取SEC数据失败: {str(e)}")

    async def _get_company_cik(self, ticker: str) -> Optional[str]:
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
                        return str(company.get('cik_str'))
            return None
        except Exception as e:
            logger.error(f"获取CIK失败: {ticker}, 错误: {e}")
            return None

    def _parse_sec_concepts_data(self, data: Dict, ticker: str, years: int, include_quarterly: bool) -> Dict[str, Any]:
        """解析SEC概念数据"""
        try:
            annual_data = []
            quarterly_data = []
            company_info = data.get('entityName', f'{ticker} Corporation')
            cik = data.get('cik')

            if 'units' in data and 'USD' in data['units']:
                usd_data = data['units']['USD']

                # 按年份分组年度数据
                annual_by_year = {}
                for item in usd_data:
                    if item.get('form') == '10-K' and item.get('fy'):
                        fiscal_year = item['fy']
                        if fiscal_year not in annual_by_year:
                            annual_by_year[fiscal_year] = []
                        annual_by_year[fiscal_year].append(item)

                # 处理年度数据
                sorted_years = sorted(
                    annual_by_year.keys(), reverse=True)[:years]
                for year in sorted_years:
                    items = annual_by_year[year]
                    # 取该年最新的数据
                    latest_item = max(items, key=lambda x: x.get('filed', ''))
                    revenue = latest_item.get('val', 0)
                    filing_date = latest_item.get('filed', '')

                    annual_data.append({
                        'fiscal_year': year,
                        'revenue': revenue,
                        'net_income': revenue * 0.2,  # 估算净利润
                        'filing_date': filing_date
                    })

                # 处理季度数据
                if include_quarterly:
                    quarterly_by_period = {}
                    for item in usd_data:
                        if item.get('form') == '10-Q' and item.get('fy') and item.get('fp'):
                            period_key = f"{item['fy']}-{item['fp']}"
                            if period_key not in quarterly_by_period:
                                quarterly_by_period[period_key] = []
                            quarterly_by_period[period_key].append(item)

                    sorted_periods = sorted(
                        quarterly_by_period.keys(), reverse=True)[:20]
                    for period in sorted_periods:
                        items = quarterly_by_period[period]
                        latest_item = max(
                            items, key=lambda x: x.get('filed', ''))
                        revenue = latest_item.get('val', 0)
                        filing_date = latest_item.get('filed', '')

                        quarterly_data.append({
                            'quarter': f"Q{latest_item.get('fp', 'Unknown')} {latest_item.get('fy', 'Unknown')}",
                            'fiscal_year': latest_item.get('fy'),
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
            raise DataSourceError(f"解析SEC概念数据失败: {str(e)}")

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

        Raises:
            DataSourceError: 当获取数据失败时抛出
        """
        try:
            # 使用正确的SEC API获取最近的文件提交
            return await self._get_sec_api_filings(ticker, limit, days_back)

        except Exception as e:
            logger.error(f"获取公司SEC新闻失败 {ticker}: {e}")
            raise DataSourceError(f"获取SEC新闻数据失败: {str(e)}")

    async def _get_sec_api_filings(self, ticker: str, limit: int, days_back: int) -> List[Dict[str, Any]]:
        """使用正确的SEC API获取最近的文件提交"""
        try:
            from datetime import datetime, timedelta

            # 计算查询日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # 根据官方文档构建正确的查询
            query_payload = {
                "query": f"ticker:\"{ticker}\" AND filedAt:[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]",
                "from": "0",
                "size": str(limit),
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 使用正确的认证方式
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }

            # 发送POST请求到正确的API端点
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.sec-api.io',
                    json=query_payload,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.warning(
                            f"SEC API调用失败: HTTP {response.status}, {error_text}")

                        # 如果ticker查询失败，尝试使用CIK
                        cik = await self._get_company_cik(ticker)
                        if cik:
                            query_payload[
                                "query"] = f"cik:\"{cik}\" AND filedAt:[{start_date.strftime('%Y-%m-%d')} TO {end_date.strftime('%Y-%m-%d')}]"

                            async with session.post(
                                'https://api.sec-api.io',
                                json=query_payload,
                                headers=headers,
                                timeout=30
                            ) as cik_response:
                                if cik_response.status == 200:
                                    api_response = await cik_response.json()
                                else:
                                    raise DataSourceError(
                                        f"SEC API查询失败: HTTP {cik_response.status}")
                        else:
                            raise DataSourceError(
                                f"SEC API查询失败: HTTP {response.status}")
                    else:
                        api_response = await response.json()

            if not api_response or 'filings' not in api_response:
                return []

            filings = api_response['filings']
            news_items = []

            for filing in filings:
                try:
                    news_item = {
                        'title': f"{filing.get('formType', 'Unknown')} - {filing.get('companyName', ticker)}",
                        'description': self._get_form_description(filing.get('formType', '')),
                        'url': filing.get('linkToFilingDetails', ''),
                        'published_at': filing.get('filedAt', ''),
                        'form_type': filing.get('formType', ''),
                        'company_name': filing.get('companyName', ''),
                        'cik': filing.get('cik', ''),
                        'accession_number': filing.get('accessionNo', ''),
                        'source': 'SEC EDGAR'
                    }
                    news_items.append(news_item)
                except Exception as e:
                    logger.warning(f"解析SEC文件失败: {e}")
                    continue

            return news_items

        except Exception as e:
            logger.error(f"SEC API获取文件提交失败: {e}")
            raise DataSourceError(f"SEC API数据获取失败: {str(e)}")

    def _get_form_description(self, form_type: str) -> str:
        """获取表单类型的描述"""
        descriptions = {
            '10-K': '年度报告，包含公司财务状况和业务概况的全面信息',
            '10-Q': '季度报告，包含未经审计的财务报表和管理层讨论',
            '8-K': '当期报告，披露重大公司事件或变化',
            '20-F': '外国公司年度报告',
            'DEF 14A': '委托书说明书，通常用于股东大会',
            'S-1': '首次公开发行注册声明',
            '424B4': '最终招股说明书',
            '13F-HR': '机构投资者持股报告',
            '4': '内部人交易报告',
            '3': '内部人初始持股报告',
            '5': '内部人年度持股声明'
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
        """已移除：不再提供模拟财务数据"""
        raise DataSourceError("SEC数据源不提供模拟数据。请配置有效的SEC API密钥。")

    def _get_mock_news_data(self, ticker: str) -> List[Dict[str, Any]]:
        """已移除：不再提供模拟新闻数据"""
        raise DataSourceError("SEC数据源不提供模拟数据。请配置有效的SEC API密钥。")
