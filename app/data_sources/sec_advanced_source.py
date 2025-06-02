"""
SEC高级数据源
基于SEC API实现高级功能的数据获取
包括XBRL转换、全文搜索、内幕交易、机构持股等
"""

import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
import os
import logging
from urllib.parse import quote, urlencode

try:
    from sec_api import (
        ExtractorApi, QueryApi, RenderApi, XbrlApi,
        FullTextSearchApi, InsiderTradingApi,
        Form13FHoldingsApi, Form_S1_424B4_Api, ExecCompApi,
        DirectorsBoardMembersApi, SecEnforcementActionsApi,
        MappingApi, SubsidiaryApi
    )
    SEC_API_AVAILABLE = True
except ImportError:
    SEC_API_AVAILABLE = False

from app.core.logging import get_logger
from app.utils.exceptions import FinanceAPIException

logger = get_logger(__name__)


class SecAdvancedDataSource:
    """SEC高级数据源实现"""

    def __init__(self, api_key: str = None):
        """初始化SEC高级数据源"""
        self.api_key = api_key or os.environ.get('SEC_API_KEY')

        if not self.api_key:
            raise FinanceAPIException(
                message="SEC API密钥是必需的",
                code="SEC_API_KEY_REQUIRED"
            )

        # 检查SEC API可用性
        if not SEC_API_AVAILABLE:
            raise FinanceAPIException(
                message="SEC API库不可用，请安装sec-api包",
                code="SEC_API_LIBRARY_UNAVAILABLE"
            )

        try:
            # 初始化各种API客户端
            self.query_api = QueryApi(api_key=self.api_key)
            self.extractor_api = ExtractorApi(api_key=self.api_key)
            self.render_api = RenderApi(api_key=self.api_key)
            self.xbrl_api = XbrlApi(api_key=self.api_key)

            # 高级功能API
            self.fulltext_api = FullTextSearchApi(api_key=self.api_key)
            self.insider_api = InsiderTradingApi(api_key=self.api_key)
            self.form13f_api = Form13FHoldingsApi(api_key=self.api_key)
            self.ipo_api = Form_S1_424B4_Api(api_key=self.api_key)
            self.compensation_api = ExecCompApi(api_key=self.api_key)
            self.governance_api = DirectorsBoardMembersApi(
                api_key=self.api_key)
            self.enforcement_api = SecEnforcementActionsApi(
                api_key=self.api_key)
            self.mapping_api = MappingApi(api_key=self.api_key)

            logger.info("SEC高级API已初始化")

        except Exception as e:
            logger.error(f"SEC高级API初始化失败: {e}")
            raise FinanceAPIException(
                message=f"SEC高级API初始化失败: {str(e)}",
                code="SEC_ADVANCED_API_INIT_FAILED"
            )

        # 配置请求头
        self.headers = {
            'User-Agent': 'YFinance-API/1.0 (https://example.com/contact)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Authorization': f'Bearer {self.api_key}'
        }

    # ===== XBRL转换功能 =====

    async def convert_xbrl_to_json(
        self,
        filing_url: str,
        include_dimensions: bool = True
    ) -> Dict[str, Any]:
        """
        将XBRL文件转换为JSON格式

        Args:
            filing_url: SEC XBRL文件URL
            include_dimensions: 是否包含维度信息

        Returns:
            转换后的JSON数据
        """
        try:
            logger.info(f"转换XBRL文件: {filing_url}")

            # 使用XBRL API转换文件 - 移除不支持的参数
            xbrl_json = self.xbrl_api.xbrl_to_json(
                xbrl_url=filing_url
            )

            # 处理和标准化数据
            result = {
                "source_url": filing_url,
                "conversion_timestamp": datetime.now().isoformat(),
                "include_dimensions": include_dimensions,
                "data": xbrl_json,
                "financial_concepts": self._extract_financial_concepts(xbrl_json) if xbrl_json else {}
            }

            logger.info(
                f"XBRL转换完成，概念数量: {len(result.get('financial_concepts', {}))}")
            return result

        except Exception as e:
            logger.error(f"XBRL转换失败: {str(e)}")
            raise FinanceAPIException(f"XBRL转换失败: {str(e)}")

    async def get_company_xbrl_data(
        self,
        ticker: str,
        form_type: str = "10-K",
        fiscal_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取公司XBRL数据

        Args:
            ticker: 股票代码
            form_type: 报表类型
            fiscal_year: 财政年度

        Returns:
            公司XBRL数据
        """
        try:
            logger.info(f"获取公司XBRL数据: {ticker}, 类型: {form_type}")

            # 构建查询
            query = {
                "query": f'ticker:"{ticker}" AND formType:"{form_type}"',
                "from": "0",
                "size": "1",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            if fiscal_year:
                query["query"] += f' AND fiscalYear:"{fiscal_year}"'

            # 查询最新的XBRL文件
            filings = self.query_api.get_filings(query)

            if not filings or not filings.get("filings"):
                raise FinanceAPIException(
                    message=f"未找到 {ticker} 的 {form_type} XBRL文件",
                    code="XBRL_FILE_NOT_FOUND"
                )

            filing = filings["filings"][0]

            # 获取XBRL文件URL
            xbrl_url = None
            for doc in filing.get("dataFiles", []):
                if doc.get("description", "").upper().endswith("XBRL INSTANCE DOCUMENT"):
                    xbrl_url = doc.get("documentUrl")
                    break

            if not xbrl_url:
                raise FinanceAPIException(
                    message=f"未找到 {ticker} 的XBRL实例文档",
                    code="XBRL_INSTANCE_NOT_FOUND"
                )

            # 转换XBRL数据
            xbrl_data = await self.convert_xbrl_to_json(xbrl_url, include_dimensions=True)

            # 添加公司和文件信息
            result = {
                "ticker": ticker,
                "form_type": form_type,
                "fiscal_year": fiscal_year or filing.get("fiscalYear"),
                "filing_date": filing.get("filedAt"),
                "period_end": filing.get("periodOfReport"),
                "company_name": filing.get("companyName"),
                "cik": filing.get("cik"),
                "accession_number": filing.get("accessionNumber"),
                "xbrl_data": xbrl_data,
                "filing_url": filing.get("linkToFilingDetails"),
                "processed_at": datetime.now().isoformat()
            }

            logger.info(f"成功获取 {ticker} 的XBRL数据")
            return result

        except Exception as e:
            if isinstance(e, FinanceAPIException):
                raise
            logger.error(f"获取公司XBRL数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取公司XBRL数据失败: {str(e)}",
                code="COMPANY_XBRL_ERROR"
            )

    def _extract_financial_concepts(self, xbrl_json: Dict[str, Any]) -> Dict[str, Any]:
        """从XBRL JSON中提取主要财务概念"""
        concepts = {}
        facts = xbrl_json.get("facts", {})

        # 主要财务概念映射
        concept_mapping = {
            "Revenues": ["Revenues", "Revenue", "SalesRevenueNet"],
            "NetIncome": ["NetIncomeLoss", "NetIncome", "ProfitLoss"],
            "TotalAssets": ["Assets", "AssetsCurrent", "AssetsTotal"],
            "TotalLiabilities": ["Liabilities", "LiabilitiesTotal"],
            "StockholdersEquity": ["StockholdersEquity", "StockholdersEquityTotal"],
            "OperatingCashFlow": ["NetCashProvidedByUsedInOperatingActivities"],
            "FreeCashFlow": ["NetCashProvidedByUsedInOperatingActivities"]
        }

        for standard_name, possible_names in concept_mapping.items():
            for concept_name in possible_names:
                if concept_name in facts:
                    concepts[standard_name] = facts[concept_name]
                    break

        return concepts

    # ===== 全文搜索功能 =====

    async def full_text_search(
        self,
        query: str,
        form_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        执行SEC文件全文搜索

        Args:
            query: 搜索查询字符串
            form_types: 报表类型列表（如 ["10-K", "10-Q"]）
            date_from: 开始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
            limit: 结果数量限制

        Returns:
            搜索结果
        """
        try:
            logger.info(f"执行全文搜索: {query}")

            # 构建搜索查询
            search_query = {
                "query": query,
                "from": "0",
                "size": str(limit),
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 添加表单类型过滤
            if form_types:
                form_filter = " OR ".join(
                    [f'formType:"{ft}"' for ft in form_types])
                search_query["query"] += f" AND ({form_filter})"

            # 添加日期过滤
            if date_from:
                search_query["query"] += f' AND filedAt:[{date_from} TO *]'
            if date_to:
                search_query["query"] += f' AND filedAt:[* TO {date_to}]'

            # 执行搜索
            results = self.fulltext_api.get_filings(search_query)

            # 处理和标准化结果
            processed_results = {
                "query": query,
                "parameters": {
                    "form_types": form_types,
                    "date_from": date_from,
                    "date_to": date_to,
                    "limit": limit
                },
                "results": {
                    "total": results.get("total", 0),
                    "filings": []
                },
                "timestamp": datetime.now().isoformat()
            }

            # 处理每个结果
            for filing in results.get("filings", []):
                processed_filing = {
                    "form_type": filing.get("formType"),
                    "company_name": filing.get("companyName"),
                    "ticker": filing.get("ticker"),
                    "cik": filing.get("cik"),
                    "filed_at": filing.get("filedAt"),
                    "report_date": filing.get("reportDate"),
                    "document_url": filing.get("linkToFilingDetails"),
                    "description": filing.get("description"),
                    "relevance_score": filing.get("score", 0)
                }
                processed_results["results"]["filings"].append(
                    processed_filing)

            logger.info(
                f"全文搜索完成，找到 {processed_results['results']['total']} 个结果")
            return processed_results

        except Exception as e:
            logger.error(f"全文搜索失败: {query}, 错误: {e}")
            raise FinanceAPIException(
                message=f"全文搜索失败: {str(e)}",
                code="FULLTEXT_SEARCH_FAILED"
            )

    async def search_company_filings(
        self,
        ticker: str,
        query: str,
        form_types: Optional[List[str]] = None,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        在公司文件中搜索

        Args:
            ticker: 股票代码
            query: 搜索查询
            form_types: 文件类型列表
            years: 搜索年数

        Returns:
            搜索结果
        """
        try:
            logger.info(f"在公司文件中搜索: {ticker}, 查询: {query}")

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)

            # 构建限定公司的搜索查询
            company_query = f'ticker:"{ticker}" AND ({query})'

            # 执行搜索
            search_results = await self.full_text_search(
                query=company_query,
                form_types=form_types,
                date_from=start_date.strftime("%Y-%m-%d"),
                date_to=end_date.strftime("%Y-%m-%d"),
                limit=100
            )

            # 添加公司特定信息
            result = {
                **search_results,
                "ticker": ticker,
                "years_searched": years,
                "form_types": form_types or ["10-K", "10-Q"],
                "company_specific": True
            }

            logger.info(f"公司文件搜索完成: {ticker}")
            return result

        except Exception as e:
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
        include_derivatives: bool = True
    ) -> Dict[str, Any]:
        """
        获取内幕交易数据

        Args:
            ticker: 股票代码
            days_back: 回溯天数
            include_derivatives: 是否包含衍生工具交易

        Returns:
            内幕交易数据
        """
        try:
            logger.info(f"获取内幕交易数据: {ticker}")

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # 构建查询参数
            query = {
                "query": f'ticker:"{ticker}"',
                "from": "0",
                "size": "50",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 添加日期过滤
            query["query"] += f' AND filedAt:[{start_date.strftime("%Y-%m-%d")} TO {end_date.strftime("%Y-%m-%d")}]'

            # 添加表单类型过滤（内幕交易相关表单）
            if include_derivatives:
                query["query"] += ' AND (formType:"3" OR formType:"4" OR formType:"5")'
            else:
                query["query"] += ' AND (formType:"3" OR formType:"4")'

            # 获取内幕交易数据
            trading_data = self.insider_api.get_data(query)

            # 处理和分析数据
            transactions = []
            total_value = 0
            transaction_counts = {"acquisitions": 0, "dispositions": 0}

            for filing in trading_data.get("data", []):
                for transaction in filing.get("transactions", []):
                    transaction_info = {
                        "filing_date": filing.get("filedAt"),
                        "insider_name": filing.get("issuerName", ""),
                        "insider_cik": filing.get("issuerCik", ""),
                        "transaction_date": transaction.get("transactionDate"),
                        "transaction_code": transaction.get("transactionCode"),
                        "transaction_type": self._get_transaction_type(transaction.get("transactionCode", "")),
                        "shares": transaction.get("transactionShares", 0),
                        "price_per_share": transaction.get("transactionPricePerShare", 0),
                        "total_value": transaction.get("transactionShares", 0) * transaction.get("transactionPricePerShare", 0),
                        "shares_owned_after": transaction.get("sharesOwnedFollowingTransaction", 0),
                        "direct_or_indirect": transaction.get("directOrIndirectOwnership", ""),
                        "form_type": filing.get("formType")
                    }

                    transactions.append(transaction_info)
                    total_value += transaction_info["total_value"]

                    # 统计交易类型
                    if transaction_info["transaction_type"] == "acquisition":
                        transaction_counts["acquisitions"] += 1
                    elif transaction_info["transaction_type"] == "disposition":
                        transaction_counts["dispositions"] += 1

            # 按日期排序
            transactions.sort(
                key=lambda x: x["transaction_date"] or "", reverse=True)

            result = {
                "ticker": ticker,
                "query_parameters": {
                    "days_back": days_back,
                    "include_derivatives": include_derivatives,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                "summary": {
                    "total_transactions": len(transactions),
                    "total_value": total_value,
                    "acquisitions": transaction_counts["acquisitions"],
                    "dispositions": transaction_counts["dispositions"],
                    "net_activity": transaction_counts["acquisitions"] - transaction_counts["dispositions"]
                },
                "transactions": transactions,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"内幕交易数据获取完成: {ticker}, 找到 {len(transactions)} 笔交易")
            return result

        except Exception as e:
            logger.error(f"获取内幕交易数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取内幕交易数据失败: {str(e)}",
                code="INSIDER_TRADING_FAILED"
            )

    # ===== 机构持股数据 =====

    async def get_institutional_holdings(
        self,
        ticker: str,
        quarters: int = 4,
        min_value: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取机构持股数据 (Form 13F)

        Args:
            ticker: 股票代码
            quarters: 查询季度数
            min_value: 最小持股价值（美元）

        Returns:
            机构持股数据
        """
        try:
            logger.info(f"获取机构持股数据: {ticker}")

            # 构建查询参数
            query = {
                "query": f'ticker:"{ticker}" AND formType:"13F-HR"',
                "from": "0",
                "size": str(quarters * 10),  # 每个季度可能有多个机构
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 获取13F持股数据
            holdings_data = self.form13f_api.get_data(query)

            # 处理持股数据
            institutions = {}
            quarterly_data = {}

            for filing in holdings_data.get("data", []):
                filing_date = filing.get("filedAt", "")
                quarter = self._get_quarter_from_date(filing_date)

                if quarter not in quarterly_data:
                    quarterly_data[quarter] = {
                        "total_institutions": 0,
                        "total_shares": 0,
                        "total_value": 0,
                        "holdings": []
                    }

                for holding in filing.get("holdings", []):
                    if holding.get("nameOfIssuer", "").upper() != ticker.upper():
                        continue

                    institution_name = filing.get("institutionName", "")
                    shares = int(holding.get(
                        "shrsOrPrnlAmt", {}).get("sshPrnlAmt", 0))
                    value = int(holding.get("value", 0)) * 1000  # 13F值以千美元为单位

                    # 应用最小价值过滤
                    if min_value and value < min_value:
                        continue

                    holding_info = {
                        "institution_name": institution_name,
                        "institution_cik": filing.get("cik", ""),
                        "shares": shares,
                        "value": value,
                        "investment_discretion": holding.get("investmentDiscretion", ""),
                        "voting_authority": {
                            "sole": int(holding.get("votingAuthority", {}).get("Sole", 0)),
                            "shared": int(holding.get("votingAuthority", {}).get("Shared", 0)),
                            "none": int(holding.get("votingAuthority", {}).get("None", 0))
                        },
                        "filing_date": filing_date,
                        "quarter": quarter
                    }

                    quarterly_data[quarter]["holdings"].append(holding_info)
                    quarterly_data[quarter]["total_institutions"] += 1
                    quarterly_data[quarter]["total_shares"] += shares
                    quarterly_data[quarter]["total_value"] += value

                    # 汇总机构信息
                    if institution_name not in institutions:
                        institutions[institution_name] = {
                            "name": institution_name,
                            "cik": filing.get("cik", ""),
                            "total_shares": 0,
                            "total_value": 0,
                            "quarters_held": 0,
                            "holdings_history": []
                        }

                    institutions[institution_name]["total_shares"] += shares
                    institutions[institution_name]["total_value"] += value
                    institutions[institution_name]["quarters_held"] += 1
                    institutions[institution_name]["holdings_history"].append(
                        holding_info)

            # 排序和分析
            top_institutions = sorted(
                institutions.values(),
                key=lambda x: x["total_value"],
                reverse=True
            )[:20]  # 取前20大机构

            quarterly_summary = []
            for quarter in sorted(quarterly_data.keys(), reverse=True):
                data = quarterly_data[quarter]
                quarterly_summary.append({
                    "quarter": quarter,
                    "total_institutions": len(set(h["institution_name"] for h in data["holdings"])),
                    "total_shares": data["total_shares"],
                    "total_value": data["total_value"],
                    "average_position_size": data["total_value"] / max(1, len(data["holdings"]))
                })

            result = {
                "ticker": ticker,
                "query_parameters": {
                    "quarters": quarters,
                    "min_value": min_value
                },
                "summary": {
                    "total_institutions": len(institutions),
                    "total_quarters": len(quarterly_data),
                    "latest_total_value": quarterly_summary[0]["total_value"] if quarterly_summary else 0,
                    "latest_total_shares": quarterly_summary[0]["total_shares"] if quarterly_summary else 0
                },
                "top_institutions": top_institutions,
                "quarterly_summary": quarterly_summary,
                "detailed_holdings": quarterly_data,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"机构持股数据获取完成: {ticker}, 找到 {len(institutions)} 个机构")
            return result

        except Exception as e:
            logger.error(f"获取机构持股数据失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取机构持股数据失败: {str(e)}",
                code="INSTITUTIONAL_HOLDINGS_FAILED"
            )

    # ===== IPO数据 =====

    async def get_recent_ipos(
        self,
        days_back: int = 30,
        min_offering_amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取最近IPO数据

        Args:
            days_back: 查询天数
            min_offering_amount: 最小募资金额

        Returns:
            IPO数据
        """
        try:
            logger.info(f"获取最近IPO数据，天数: {days_back}")

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # 构建查询参数
            query = {
                "query": f'formType:("S-1" OR "S-1/A" OR "424B4") AND filedAt:[{start_date.strftime("%Y-%m-%d")} TO {end_date.strftime("%Y-%m-%d")}]',
                "from": "0",
                "size": "50",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 获取IPO数据
            ipo_data = self.ipo_api.get_data(query)

            # 处理IPO数据
            ipos = []
            for ipo in ipo_data.get("filings", []):
                # 提取基本信息
                company_name = ipo.get("companyName", "")
                ticker = ipo.get("ticker", "")
                form_type = ipo.get("formType", "")

                # 跳过不符合条件的记录
                if not company_name or form_type not in ["S-1", "S-1/A", "424B4"]:
                    continue

                ipo_info = {
                    "company_name": company_name,
                    "ticker": ticker,
                    "ipo_date": ipo.get("reportDate"),
                    "filing_date": ipo.get("filedAt"),
                    "form_type": form_type,
                    "cik": ipo.get("cik"),
                    "filing_url": ipo.get("linkToFilingDetails"),
                    "description": ipo.get("description", ""),
                    "industry": "",  # 需要从文件内容解析
                    "exchange": "",  # 需要从文件内容解析
                    "business_description": ipo.get("description", "")
                }
                ipos.append(ipo_info)

            # 应用最小募资金额过滤（如果指定）
            if min_offering_amount:
                # 这里需要从文件内容中解析募资金额，目前跳过
                pass

            result = {
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days_back": days_back
                },
                "filters": {
                    "min_offering_amount": min_offering_amount
                },
                "summary": {
                    "total_ipos": len(ipos),
                    "form_types_found": list(set(ipo["form_type"] for ipo in ipos))
                },
                "ipos": ipos,
                "retrieved_at": datetime.now().isoformat()
            }

            logger.info(f"获取到 {len(ipos)} 个IPO记录")
            return result

        except Exception as e:
            logger.error(f"获取最近IPO数据失败, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取最近IPO数据失败: {str(e)}",
                code="IPO_DATA_ERROR"
            )

    async def get_company_ipo_details(self, ticker: str) -> Dict[str, Any]:
        """
        获取公司IPO详情

        Args:
            ticker: 股票代码

        Returns:
            公司IPO详情
        """
        try:
            logger.info(f"获取公司IPO详情: {ticker}")

            # 构建查询参数
            query = {
                "query": f'ticker:"{ticker}" AND formType:("S-1" OR "S-1/A" OR "424B4")',
                "from": "0",
                "size": "10",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 获取公司IPO详情
            ipo_data = self.ipo_api.get_data(query)

            if not ipo_data.get("filings"):
                raise FinanceAPIException(
                    message=f"未找到 {ticker} 的IPO信息",
                    code="IPO_INFO_NOT_FOUND"
                )

            # 取最新的IPO文件
            latest_filing = ipo_data["filings"][0]

            result = {
                "ticker": ticker,
                "company_name": latest_filing.get("companyName"),
                "filing_date": latest_filing.get("filedAt"),
                "form_type": latest_filing.get("formType"),
                "cik": latest_filing.get("cik"),
                "filing_url": latest_filing.get("linkToFilingDetails"),
                "description": latest_filing.get("description"),
                "report_date": latest_filing.get("reportDate"),
                "period_of_report": latest_filing.get("periodOfReport"),
                "retrieved_at": datetime.now().isoformat()
            }

            logger.info(f"成功获取 {ticker} 的IPO详情")
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
        years: int = 3
    ) -> Dict[str, Any]:
        """
        获取高管薪酬数据

        Args:
            ticker: 股票代码
            years: 查询年数

        Returns:
            高管薪酬数据
        """
        try:
            logger.info(f"获取高管薪酬数据: {ticker}")

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)

            # 构建查询参数 - 查找代理声明书(DEF 14A)和10-K中的薪酬信息
            query = {
                "query": f'ticker:"{ticker}" AND (formType:"DEF 14A" OR formType:"10-K") AND filedAt:[{start_date.strftime("%Y-%m-%d")} TO {end_date.strftime("%Y-%m-%d")}]',
                "from": "0",
                "size": "20",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 获取薪酬数据
            compensation_data = self.compensation_api.get_data(query)

            # 处理薪酬数据
            executives = []
            filings_found = compensation_data.get("filings", [])

            for filing in filings_found:
                # 这里应该解析文件内容来提取薪酬数据
                # 目前返回基本文件信息
                exec_data = {
                    "filing_date": filing.get("filedAt"),
                    "form_type": filing.get("formType"),
                    "fiscal_year": filing.get("fiscalYear"),
                    "filing_url": filing.get("linkToFilingDetails"),
                    "description": filing.get("description")
                }
                executives.append(exec_data)

            result = {
                "ticker": ticker,
                "years_covered": years,
                "query_period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                "summary": {
                    "total_filings": len(executives),
                    "def_14a_filings": len([e for e in executives if e.get("form_type") == "DEF 14A"]),
                    "10k_filings": len([e for e in executives if e.get("form_type") == "10-K"])
                },
                "filings": executives,
                "retrieved_at": datetime.now().isoformat()
            }

            logger.info(f"获取到 {len(executives)} 条薪酬相关文件: {ticker}")
            return result

        except Exception as e:
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
        include_audit_fees: bool = True
    ) -> Dict[str, Any]:
        """
        获取公司治理信息

        Args:
            ticker: 股票代码
            include_subsidiaries: 是否包含子公司信息
            include_audit_fees: 是否包含审计费用

        Returns:
            公司治理信息
        """
        try:
            logger.info(f"获取公司治理信息: {ticker}")

            # 构建查询参数 - 查找代理声明书和10-K
            query = {
                "query": f'ticker:"{ticker}" AND (formType:"DEF 14A" OR formType:"10-K")',
                "from": "0",
                "size": "5",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 获取治理数据
            governance_data = self.governance_api.get_data(query)

            filings = governance_data.get("filings", [])

            result = {
                "ticker": ticker,
                "company_name": filings[0].get("companyName") if filings else "",
                "cik": filings[0].get("cik") if filings else "",
                "query_parameters": {
                    "include_subsidiaries": include_subsidiaries,
                    "include_audit_fees": include_audit_fees
                },
                "governance_filings": [
                    {
                        "form_type": filing.get("formType"),
                        "filing_date": filing.get("filedAt"),
                        "description": filing.get("description"),
                        "filing_url": filing.get("linkToFilingDetails")
                    }
                    for filing in filings
                ],
                "summary": {
                    "total_filings": len(filings),
                    "def_14a_count": len([f for f in filings if f.get("formType") == "DEF 14A"]),
                    "10k_count": len([f for f in filings if f.get("formType") == "10-K"])
                },
                "retrieved_at": datetime.now().isoformat()
            }

            logger.info(f"成功获取 {ticker} 的公司治理信息")
            return result

        except Exception as e:
            logger.error(f"获取公司治理信息失败: {ticker}, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取公司治理信息失败: {str(e)}",
                code="COMPANY_GOVERNANCE_ERROR"
            )

    # ===== SEC执法数据 =====

    async def get_recent_enforcement_actions(
        self,
        days_back: int = 90,
        action_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取最近SEC执法行动

        Args:
            days_back: 查询天数
            action_type: 行动类型

        Returns:
            SEC执法行动数据
        """
        try:
            logger.info(f"获取最近SEC执法行动，天数: {days_back}")

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # 构建查询参数
            query = {
                "query": f'filedAt:[{start_date.strftime("%Y-%m-%d")} TO {end_date.strftime("%Y-%m-%d")}]',
                "from": "0",
                "size": "50",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            # 添加行动类型过滤
            if action_type:
                query["query"] += f' AND description:"{action_type}"'

            # 获取执法行动数据
            enforcement_data = self.enforcement_api.get_data(query)

            # 处理执法行动数据
            actions = []
            for action in enforcement_data.get("filings", []):
                actions.append({
                    "action_date": action.get("filedAt"),
                    "form_type": action.get("formType"),
                    "company_name": action.get("companyName"),
                    "ticker": action.get("ticker"),
                    "cik": action.get("cik"),
                    "description": action.get("description"),
                    "filing_url": action.get("linkToFilingDetails"),
                    "period_of_report": action.get("periodOfReport")
                })

            result = {
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days_back": days_back
                },
                "filter": {
                    "action_type": action_type
                },
                "summary": {
                    "total_actions": len(actions),
                    "form_types": list(set(a["form_type"] for a in actions if a["form_type"]))
                },
                "actions": actions,
                "retrieved_at": datetime.now().isoformat()
            }

            logger.info(f"获取到 {len(actions)} 个SEC执法行动")
            return result

        except Exception as e:
            logger.error(f"获取SEC执法行动失败, 错误: {e}")
            raise FinanceAPIException(
                message=f"获取SEC执法行动失败: {str(e)}",
                code="ENFORCEMENT_ACTIONS_ERROR"
            )

    # ===== 映射和实体数据 =====

    async def get_ticker_to_cik_mapping(
        self,
        ticker: str,
        include_historical: bool = False
    ) -> Dict[str, Any]:
        """
        获取股票代码到CIK映射

        Args:
            ticker: 股票代码
            include_historical: 是否包含历史映射

        Returns:
            映射数据
        """
        try:
            logger.info(f"获取CIK映射: {ticker}")

            # 使用resolve方法获取映射数据
            mapping_result = self.mapping_api.resolve(
                parameter="ticker", value=ticker)

            if not mapping_result:
                # 如果resolve失败，尝试通过查询API获取
                query = {
                    "query": f'ticker:"{ticker}"',
                    "from": "0",
                    "size": "1",
                    "sort": [{"filedAt": {"order": "desc"}}]
                }

                query_result = self.query_api.get_filings(query)
                filings = query_result.get("filings", [])

                if not filings:
                    raise FinanceAPIException(
                        message=f"未找到 {ticker} 的CIK映射",
                        code="CIK_MAPPING_NOT_FOUND"
                    )

                # 从查询结果构建映射
                filing = filings[0]
                current_mapping = {
                    "cik": filing.get("cik"),
                    "company_name": filing.get("companyName"),
                    "ticker": filing.get("ticker"),
                    "latest_filing_date": filing.get("filedAt"),
                    "latest_form_type": filing.get("formType")
                }
            else:
                # 使用resolve方法的结果
                current_mapping = {
                    "cik": mapping_result.get("cik"),
                    "company_name": mapping_result.get("entityName"),
                    "ticker": ticker,
                    "resolved_via": "mapping_api"
                }

            result = {
                "ticker": ticker,
                "current_mapping": current_mapping,
                "historical_mappings": [],  # MappingApi resolve方法不支持历史数据
                "metadata": {
                    "resolution_method": "mapping_api_resolve" if mapping_result else "query_api_fallback",
                    "query_included_historical": include_historical
                },
                "retrieved_at": datetime.now().isoformat()
            }

            logger.info(f"成功获取 {ticker} 的CIK映射")
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
        获取数据源健康状态

        Returns:
            健康状态信息
        """
        try:
            # 测试各个API的可用性
            api_status = {}

            # 测试基础查询API
            try:
                test_query = {"query": "formType:\"10-K\"",
                              "from": "0", "size": "1"}
                self.query_api.get_filings(test_query)
                api_status["query_api"] = "healthy"
            except Exception as e:
                api_status["query_api"] = f"unhealthy: {str(e)}"

            # 测试其他API
            apis_to_test = [
                ("xbrl_api", self.xbrl_api),
                ("fulltext_api", self.fulltext_api),
                ("insider_api", self.insider_api),
                ("form13f_api", self.form13f_api),
                ("ipo_api", self.ipo_api),
                ("compensation_api", self.compensation_api),
                ("governance_api", self.governance_api),
                ("enforcement_api", self.enforcement_api),
                ("mapping_api", self.mapping_api)
            ]

            for api_name, api_instance in apis_to_test:
                try:
                    # 简单的健康检查，可以根据具体API调整
                    if hasattr(api_instance, 'health_check'):
                        api_instance.health_check()
                    api_status[api_name] = "healthy"
                except Exception as e:
                    api_status[api_name] = f"unhealthy: {str(e)}"

            # 计算总体状态
            healthy_apis = sum(
                1 for status in api_status.values() if status == "healthy")
            total_apis = len(api_status)
            overall_healthy = healthy_apis == total_apis

            return {
                "status": "healthy" if overall_healthy else "degraded",
                "api_status": api_status,
                "api_availability": f"{healthy_apis}/{total_apis}",
                "availability_percentage": (healthy_apis / total_apis) * 100,
                "all_services_available": overall_healthy,
                "timestamp": datetime.now().isoformat(),
                "data_source": "sec_advanced"
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "data_source": "sec_advanced"
            }

    # ===== 辅助方法 =====

    def _get_transaction_type(self, transaction_code: str) -> str:
        """解析交易代码为交易类型"""
        acquisition_codes = ["P", "A", "F", "I",
                             "J", "U"]  # Purchase, Award, etc.
        # Sale, Disposal, etc.
        disposition_codes = ["S", "D", "G", "L", "W", "Z"]

        if transaction_code in acquisition_codes:
            return "acquisition"
        elif transaction_code in disposition_codes:
            return "disposition"
        else:
            return "other"

    def _get_quarter_from_date(self, date_str: str) -> str:
        """从日期字符串获取季度"""
        try:
            if not date_str:
                return "unknown"

            # 解析日期字符串
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            year = date_obj.year
            month = date_obj.month

            # 确定季度
            if month <= 3:
                quarter = 1
            elif month <= 6:
                quarter = 2
            elif month <= 9:
                quarter = 3
            else:
                quarter = 4

            return f"{year}-Q{quarter}"
        except Exception:
            return "unknown"

    async def shutdown(self):
        """关闭数据源连接"""
        try:
            logger.info("关闭SEC高级数据源连接")
            # 这里可以添加任何清理代码
        except Exception as e:
            logger.error(f"关闭SEC高级数据源时出错: {e}")
