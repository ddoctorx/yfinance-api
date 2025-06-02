"""
SEC高级API路由
基于SEC API的丰富功能提供高级数据查询
包括XBRL转换、全文搜索、内幕交易、IPO等功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, Depends, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.models.base import BaseResponse
from app.services.sec_service import get_sec_service, SecService
from app.core.logging import get_logger
from app.utils.exceptions import FinanceAPIException

logger = get_logger(__name__)

# 创建路由器
router = APIRouter(tags=["SEC高级功能"])


def get_service() -> SecService:
    """依赖注入：获取SEC服务实例"""
    try:
        service = get_sec_service()
        if not service.advanced_available:
            raise FinanceAPIException(
                message="SEC高级功能不可用，请检查API密钥配置",
                code="SEC_ADVANCED_UNAVAILABLE"
            )
        return service
    except FinanceAPIException as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SEC高级服务不可用",
                "message": str(e),
                "solution": "请检查SEC API密钥配置"
            }
        )


# ===== XBRL数据转换功能 =====

@router.get(
    "/xbrl/convert/{filing_url}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="XBRL到JSON转换",
    description="""
    将SEC XBRL财务报表转换为JSON格式，便于数据分析。
    
    **功能特点**:
    - 支持所有XBRL格式的SEC文件
    - 自动解析财务概念和数值
    - 标准化输出格式
    
    **应用场景**:
    - 自动化财务数据提取
    - 批量处理XBRL文件
    - 财务数据标准化
    """
)
async def convert_xbrl_to_json(
    filing_url: str = Path(..., description="SEC XBRL文件URL"),
    include_dimensions: bool = Query(True, description="是否包含维度信息"),
    service: SecService = Depends(get_service)
):
    """
    将XBRL文件转换为JSON格式

    - **filing_url**: SEC XBRL文件的完整URL
    - **include_dimensions**: 是否包含XBRL维度信息
    """
    try:
        result = await service.convert_xbrl_to_json(
            filing_url=filing_url,
            include_dimensions=include_dimensions
        )

        return BaseResponse(
            symbol="XBRL",
            data=result,
            data_source="sec_xbrl_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"XBRL转换失败: {filing_url}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"XBRL转换失败: {str(e)}")


@router.get(
    "/xbrl/company/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="获取公司XBRL数据",
    description="""
    获取公司最新的XBRL格式财务数据。
    
    **数据内容**:
    - 损益表数据
    - 资产负债表数据
    - 现金流量表数据
    - 股东权益变动表
    """
)
async def get_company_xbrl_data(
    ticker: str,
    form_type: str = Query("10-K", description="报表类型 (10-K, 10-Q)"),
    fiscal_year: Optional[int] = Query(None, description="财政年度"),
    service: SecService = Depends(get_service)
):
    """获取公司XBRL数据"""
    try:
        result = await service.get_company_xbrl_data(
            ticker=ticker,
            form_type=form_type,
            fiscal_year=fiscal_year
        )

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_xbrl_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取XBRL数据失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取XBRL数据失败: {str(e)}")


# ===== 全文搜索功能 =====

@router.get(
    "/search/full-text",
    response_model=BaseResponse[Dict[str, Any]],
    summary="SEC文件全文搜索",
    description="""
    在SEC文件中进行全文搜索，支持复杂查询语法。
    
    **搜索功能**:
    - 关键词搜索
    - 短语搜索 ("exact phrase")
    - 布尔操作符 (AND, OR, NOT)
    - 字段特定搜索
    
    **搜索范围**:
    - 10-K, 10-Q年报季报
    - 8-K重大事件报告
    - 其他SEC文件类型
    """
)
async def full_text_search(
    query: str = Query(..., description="搜索查询语句"),
    form_types: Optional[str] = Query(
        "10-K,10-Q,8-K", description="文件类型，逗号分隔"),
    date_from: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200, description="结果数量限制"),
    service: SecService = Depends(get_service)
):
    """SEC文件全文搜索"""
    try:
        result = await service.full_text_search(
            query=query,
            form_types=form_types.split(',') if form_types else None,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )

        return BaseResponse(
            symbol="SEARCH",
            data=result,
            data_source="sec_fulltext_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"全文搜索失败: {query}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"全文搜索失败: {str(e)}")


@router.get(
    "/search/company/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="公司特定文件搜索",
    description="""
    在特定公司的SEC文件中搜索内容。
    
    **搜索特点**:
    - 限定在特定公司文件范围内
    - 支持关键词高亮
    - 按相关性排序
    """
)
async def search_company_filings(
    ticker: str,
    query: str = Query(..., description="搜索查询"),
    form_types: Optional[str] = Query("10-K,10-Q", description="文件类型"),
    years: int = Query(3, ge=1, le=10, description="搜索年数"),
    service: SecService = Depends(get_service)
):
    """在公司文件中搜索"""
    try:
        result = await service.search_company_filings(
            ticker=ticker,
            query=query,
            form_types=form_types.split(',') if form_types else None,
            years=years
        )

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_fulltext_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"公司文件搜索失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"公司文件搜索失败: {str(e)}")


# ===== 内幕交易数据 =====

@router.get(
    "/insider-trading/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="内幕交易数据",
    description="""
    获取公司内幕交易数据 (Form 3/4/5)。
    
    **包含信息**:
    - 高管买卖记录
    - 交易时间和价格
    - 持股变化情况
    - 交易后持股数量
    
    **Form类型**:
    - Form 3: 初始持股报告
    - Form 4: 持股变动报告  
    - Form 5: 年度持股报告
    """
)
async def get_insider_trading(
    ticker: str,
    days_back: int = Query(90, ge=1, le=365, description="查询天数"),
    include_derivatives: bool = Query(True, description="是否包含衍生品交易"),
    service: SecService = Depends(get_service)
):
    """获取内幕交易数据"""
    try:
        result = await service.get_insider_trading(
            ticker=ticker,
            days_back=days_back,
            include_derivatives=include_derivatives
        )

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_forms345_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取内幕交易数据失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取内幕交易数据失败: {str(e)}")


# ===== 机构持股数据 =====

@router.get(
    "/institutional-holdings/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="机构持股数据",
    description="""
    获取机构投资者持股数据 (Form 13F)。
    
    **数据内容**:
    - 机构持股数量和比例
    - 持股变化趋势
    - 主要机构投资者名单
    - 持股集中度分析
    
    **更新频率**: 季度更新
    """
)
async def get_institutional_holdings(
    ticker: str,
    quarters: int = Query(4, ge=1, le=8, description="查询季度数"),
    min_value: Optional[int] = Query(None, description="最小持股价值 (美元)"),
    service: SecService = Depends(get_service)
):
    """获取机构持股数据"""
    try:
        result = await service.get_institutional_holdings(
            ticker=ticker,
            quarters=quarters,
            min_value=min_value
        )

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_form13f_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取机构持股数据失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取机构持股数据失败: {str(e)}")


# ===== IPO数据 =====

@router.get(
    "/ipo/recent",
    response_model=BaseResponse[Dict[str, Any]],
    summary="最近IPO数据",
    description="""
    获取最近的IPO和股票发行数据 (Form S-1/424B4)。
    
    **包含信息**:
    - IPO公司基本信息
    - 发行价格和数量
    - 承销商信息
    - 募资用途
    
    **数据来源**: Form S-1, 424B4等IPO相关文件
    """
)
async def get_recent_ipos(
    days_back: int = Query(30, ge=1, le=365, description="查询天数"),
    min_offering_amount: Optional[int] = Query(
        None, description="最小募资金额 (美元)"),
    service: SecService = Depends(get_service)
):
    """获取最近IPO数据"""
    try:
        result = await service.get_recent_ipos(
            days_back=days_back,
            min_offering_amount=min_offering_amount
        )

        return BaseResponse(
            symbol="IPO",
            data=result,
            data_source="sec_ipo_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取IPO数据失败, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取IPO数据失败: {str(e)}")


@router.get(
    "/ipo/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="公司IPO详情",
    description="""
    获取特定公司的IPO详细信息。
    
    **详细信息**:
    - IPO时间和价格
    - 发行数量和募资总额
    - 承销商详情
    - 业务描述和风险因素
    """
)
async def get_company_ipo_details(
    ticker: str,
    service: SecService = Depends(get_service)
):
    """获取公司IPO详情"""
    try:
        result = await service.get_company_ipo_details(ticker=ticker)

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_ipo_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取公司IPO详情失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取公司IPO详情失败: {str(e)}")


# ===== 高管薪酬数据 =====

@router.get(
    "/executive-compensation/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="高管薪酬数据",
    description="""
    获取公司高管薪酬信息。
    
    **薪酬组成**:
    - 基本工资
    - 奖金
    - 股票期权
    - 其他福利
    
    **数据来源**: DEF 14A代理权声明书
    """
)
async def get_executive_compensation(
    ticker: str,
    years: int = Query(3, ge=1, le=5, description="查询年数"),
    service: SecService = Depends(get_service)
):
    """获取高管薪酬数据"""
    try:
        result = await service.get_executive_compensation(
            ticker=ticker,
            years=years
        )

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_compensation_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取高管薪酬数据失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取高管薪酬数据失败: {str(e)}")


# ===== 公司治理数据 =====

@router.get(
    "/governance/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="公司治理信息",
    description="""
    获取公司治理相关信息。
    
    **包含内容**:
    - 董事会成员信息
    - 审计费用
    - 公司子公司
    - 流通股和公众持股
    """
)
async def get_company_governance(
    ticker: str,
    include_subsidiaries: bool = Query(True, description="是否包含子公司信息"),
    include_audit_fees: bool = Query(True, description="是否包含审计费用"),
    service: SecService = Depends(get_service)
):
    """获取公司治理信息"""
    try:
        result = await service.get_company_governance(
            ticker=ticker,
            include_subsidiaries=include_subsidiaries,
            include_audit_fees=include_audit_fees
        )

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_governance_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取公司治理信息失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取公司治理信息失败: {str(e)}")


# ===== SEC执法数据 =====

@router.get(
    "/enforcement/recent",
    response_model=BaseResponse[Dict[str, Any]],
    summary="最近SEC执法行动",
    description="""
    获取最近的SEC执法行动信息。
    
    **包含信息**:
    - 执法行动类型
    - 涉及公司或个人
    - 违规行为描述
    - 处罚金额
    """
)
async def get_recent_enforcement_actions(
    days_back: int = Query(90, ge=1, le=365, description="查询天数"),
    action_type: Optional[str] = Query(None, description="行动类型"),
    service: SecService = Depends(get_service)
):
    """获取最近SEC执法行动"""
    try:
        result = await service.get_recent_enforcement_actions(
            days_back=days_back,
            action_type=action_type
        )

        return BaseResponse(
            symbol="ENFORCEMENT",
            data=result,
            data_source="sec_enforcement_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取SEC执法行动失败, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取SEC执法行动失败: {str(e)}")


# ===== 映射和实体数据 =====

@router.get(
    "/mapping/ticker-to-cik/{ticker}",
    response_model=BaseResponse[Dict[str, Any]],
    summary="股票代码到CIK映射",
    description="""
    获取股票代码到SEC CIK的映射关系。
    
    **应用场景**:
    - API调用准备
    - 数据关联分析
    - 公司标识符转换
    """
)
async def get_ticker_to_cik_mapping(
    ticker: str,
    include_historical: bool = Query(False, description="是否包含历史映射"),
    service: SecService = Depends(get_service)
):
    """获取股票代码到CIK映射"""
    try:
        result = await service.get_ticker_to_cik_mapping(
            ticker=ticker,
            include_historical=include_historical
        )

        return BaseResponse(
            symbol=ticker,
            data=result,
            data_source="sec_mapping_api",
            is_fallback=False
        )
    except Exception as e:
        logger.error(f"获取CIK映射失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取CIK映射失败: {str(e)}")


# ===== 健康检查 =====

@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="SEC高级服务健康检查",
    description="检查SEC高级功能服务的健康状态"
)
async def health_check(service: SecService = Depends(get_service)):
    """SEC高级服务健康检查"""
    try:
        status = await service.get_health_status()
        return {
            "status": "healthy" if status.get("all_services_available", False) else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": status
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# ===== API概览 =====

@router.get(
    "/",
    summary="SEC高级API概览",
    description="获取SEC高级API的功能概览和使用说明"
)
async def sec_advanced_api_overview():
    """SEC高级API概览"""
    return {
        "service": "SEC高级API",
        "version": "1.0",
        "description": "基于SEC API提供的高级数据查询功能",
        "capabilities": {
            "xbrl_conversion": {
                "description": "XBRL到JSON转换",
                "endpoints": ["/xbrl/convert/{filing_url}", "/xbrl/company/{ticker}"]
            },
            "full_text_search": {
                "description": "SEC文件全文搜索",
                "endpoints": ["/search/full-text", "/search/company/{ticker}"]
            },
            "insider_trading": {
                "description": "内幕交易数据 (Form 3/4/5)",
                "endpoints": ["/insider-trading/{ticker}"]
            },
            "institutional_holdings": {
                "description": "机构持股数据 (Form 13F)",
                "endpoints": ["/institutional-holdings/{ticker}"]
            },
            "ipo_data": {
                "description": "IPO和股票发行数据",
                "endpoints": ["/ipo/recent", "/ipo/{ticker}"]
            },
            "executive_compensation": {
                "description": "高管薪酬数据",
                "endpoints": ["/executive-compensation/{ticker}"]
            },
            "governance": {
                "description": "公司治理信息",
                "endpoints": ["/governance/{ticker}"]
            },
            "enforcement": {
                "description": "SEC执法行动",
                "endpoints": ["/enforcement/recent"]
            },
            "mapping": {
                "description": "数据映射和实体信息",
                "endpoints": ["/mapping/ticker-to-cik/{ticker}"]
            }
        },
        "documentation": "https://sec-api.io/docs",
        "supported_features": [
            "XBRL-to-JSON转换",
            "全文搜索",
            "内幕交易监控",
            "机构持股分析",
            "IPO数据追踪",
            "高管薪酬分析",
            "公司治理信息",
            "执法行动监控",
            "实体映射服务"
        ]
    }
