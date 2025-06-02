"""
SEC财报数据API路由
提供美股公司SEC财报数据查询功能
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.models.sec import (
    CompanyFinancialsResponse,
    SecNewsResponse,
    FinancialRatios,
    SecErrorResponse
)
from app.models.base import BaseResponse
from app.services.sec_service import get_sec_service, SecService
from app.core.logging import get_logger
from app.utils.exceptions import FinanceAPIException

logger = get_logger(__name__)

# 创建路由器
router = APIRouter(tags=["SEC财报数据"])


def get_service() -> SecService:
    """依赖注入：获取SEC服务实例"""
    from app.services.sec_service import _sec_service
    if _sec_service is None:
        # 如果没有初始化，使用配置中的API key创建新实例
        from app.core.config import settings
        return SecService(api_key=settings.sec_api_key)
    return _sec_service


@router.get(
    "/financials/{ticker}",
    summary="获取公司财务数据",
    description="""
    获取美股公司的财务报表数据，包括损益表、资产负债表和现金流量表。
    
    **数据来源**: SEC EDGAR API + XBRL数据
    
    **支持的报表类型**:
    - 年度报告 (10-K)
    - 季度报告 (10-Q)
    
    **主要财务指标**:
    - 营业收入、净利润、毛利润
    - 总资产、总负债、股东权益
    - 经营现金流、投资现金流、筹资现金流
    
    **缓存策略**: 1小时
    """
)
async def get_company_financials(
    ticker: str,
    years: int = Query(5, ge=1, le=10, description="获取年数 (1-10年)"),
    include_quarterly: bool = Query(True, description="是否包含季度数据"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    service: SecService = Depends(get_service)
):
    """
    获取公司财务数据

    - **ticker**: 美股股票代码 (如: AAPL, MSFT, GOOGL)
    - **years**: 获取年数，默认5年
    - **include_quarterly**: 是否包含季度数据，默认True
    - **use_cache**: 是否使用缓存，默认True
    """
    try:
        logger.info(f"获取财务数据请求: {ticker}, 年数: {years}")

        result = await service.get_company_financials(
            ticker=ticker,
            years=years,
            include_quarterly=include_quarterly,
            use_cache=use_cache
        )

        logger.info(
            f"成功获取财务数据: {ticker}, 年度数据: {len(result.get('annual_financials', []))}, 季度数据: {len(result.get('quarterly_financials', []))}")
        return result

    except FinanceAPIException as e:
        logger.warning(f"财务数据请求失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"财务数据请求异常: {ticker}, 错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取财务数据失败: {str(e)}")


@router.get(
    "/quarterly-revenue/{ticker}",
    summary="获取季度收入数据",
    description="""
    获取公司最近若干季度的收入情况，包括同比增长率计算。
    
    **功能特点**:
    - 按季度展示收入趋势
    - 自动计算同比增长率
    - 支持最多20个季度数据
    
    **应用场景**:
    - 季度收入分析
    - 增长趋势判断
    - 同比对比分析
    """
)
async def get_quarterly_revenue(
    ticker: str,
    quarters: int = Query(8, ge=1, le=20, description="获取季度数 (1-20)"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    service: SecService = Depends(get_service)
):
    """
    获取季度收入数据

    - **ticker**: 美股股票代码
    - **quarters**: 获取季度数，默认8个季度
    - **use_cache**: 是否使用缓存
    """
    try:
        logger.info(f"获取季度收入请求: {ticker}, 季度数: {quarters}")

        result = await service.get_quarterly_revenue(
            ticker=ticker,
            quarters=quarters,
            use_cache=use_cache
        )

        logger.info(f"成功获取季度收入: {ticker}, 季度数: {result['total_quarters']}")
        return result

    except FinanceAPIException as e:
        logger.warning(f"季度收入请求失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"季度收入请求异常: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail="获取季度收入失败，请稍后重试")


@router.get(
    "/annual-comparison/{ticker}",
    summary="获取年度财务对比",
    description="""
    获取公司年度财务数据对比，包括收入、净利润、资产等关键指标的年度变化。
    
    **对比指标**:
    - 营业收入及增长率
    - 净利润及增长率  
    - 总资产及增长率
    - 股东权益
    
    **计算功能**:
    - 自动计算年度增长率
    - 多年趋势分析
    """
)
async def get_annual_comparison(
    ticker: str,
    years: int = Query(5, ge=1, le=10, description="对比年数 (1-10年)"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    service: SecService = Depends(get_service)
):
    """
    获取年度财务对比数据

    - **ticker**: 美股股票代码
    - **years**: 对比年数，默认5年
    - **use_cache**: 是否使用缓存
    """
    try:
        logger.info(f"获取年度对比请求: {ticker}, 年数: {years}")

        result = await service.get_annual_comparison(
            ticker=ticker,
            years=years,
            use_cache=use_cache
        )

        logger.info(f"成功获取年度对比: {ticker}, 年数: {result['years_covered']}")
        return result

    except FinanceAPIException as e:
        logger.warning(f"年度对比请求失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"年度对比请求异常: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail="获取年度对比失败，请稍后重试")


@router.get(
    "/news/{ticker}",
    summary="获取SEC新闻和文件",
    description="""
    获取公司最近提交的SEC文件和相关新闻。
    
    **包含内容**:
    - 10-K年度报告
    - 10-Q季度报告
    - 8-K重大事件报告
    - 其他SEC文件
    
    **信息字段**:
    - 文件类型和提交日期
    - 直接链接到SEC网站
    - 文件摘要信息
    
    **缓存策略**: 30分钟
    """
)
async def get_company_news(
    ticker: str,
    limit: int = Query(20, ge=1, le=100, description="新闻数量限制 (1-100)"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    service: SecService = Depends(get_service)
):
    """
    获取公司SEC新闻和文件

    - **ticker**: 美股股票代码
    - **limit**: 新闻数量限制，默认20条
    - **use_cache**: 是否使用缓存
    """
    try:
        logger.info(f"获取SEC新闻请求: {ticker}, 数量: {limit}")

        result = await service.get_company_news(
            ticker=ticker,
            limit=limit,
            use_cache=use_cache
        )

        logger.info(f"成功获取SEC新闻: {ticker}, 数量: {result.get('total_count', 0)}")
        return result

    except FinanceAPIException as e:
        logger.warning(f"SEC新闻请求失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"SEC新闻请求异常: {ticker}, 错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取SEC新闻失败: {str(e)}")


@router.get(
    "/ratios/{ticker}",
    summary="获取财务比率",
    description="""
    计算公司主要财务比率。
    
    **包含比率**:
    - 市盈率 (P/E Ratio)
    - 市净率 (P/B Ratio)  
    - 负债权益比 (Debt-to-Equity)
    - 流动比率 (Current Ratio)
    - 资产回报率 (ROA)
    - 净资产收益率 (ROE)
    
    **计算依据**:
    - 基于最新财务报表数据
    - 支持年度和季度数据
    
    **缓存策略**: 1小时
    """
)
async def get_financial_ratios(
    ticker: str,
    period: str = Query("annual", regex="^(annual|quarterly)$",
                        description="期间类型 (annual/quarterly)"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    service: SecService = Depends(get_service)
):
    """
    获取财务比率

    - **ticker**: 美股股票代码
    - **period**: 期间类型，annual(年度) 或 quarterly(季度)
    - **use_cache**: 是否使用缓存
    """
    try:
        logger.info(f"获取财务比率请求: {ticker}, 期间: {period}")

        result = await service.get_financial_ratios(
            ticker=ticker,
            period=period,
            use_cache=use_cache
        )

        if result:
            logger.info(f"成功获取财务比率: {ticker}")
        else:
            logger.info(f"未能计算财务比率: {ticker} (数据不足)")

        return result

    except FinanceAPIException as e:
        logger.warning(f"财务比率请求失败: {ticker}, 错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"财务比率请求异常: {ticker}, 错误: {e}")
        raise HTTPException(status_code=500, detail="获取财务比率失败，请稍后重试")


@router.get(
    "/health",
    summary="SEC服务健康检查",
    description="检查SEC数据源和服务的健康状态"
)
async def health_check(service: SecService = Depends(get_service)):
    """SEC服务健康检查"""
    try:
        status = await service.get_health_status()

        if status['status'] == 'healthy':
            return JSONResponse(
                status_code=200,
                content=status
            )
        else:
            return JSONResponse(
                status_code=503,
                content=status
            )

    except Exception as e:
        logger.error(f"SEC健康检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                'service': 'sec_service',
                'status': 'unhealthy',
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }
        )


@router.get(
    "/",
    summary="SEC API概览",
    description="获取SEC API的功能概览和使用说明"
)
async def sec_api_overview():
    """SEC API概览"""
    return {
        "name": "SEC财报数据API",
        "description": "基于SEC EDGAR API提供美股公司官方财报数据",
        "version": "1.0.0",
        "data_source": "SEC EDGAR + XBRL",
        "features": [
            "年度和季度财务报表 (10-K, 10-Q)",
            "损益表、资产负债表、现金流量表",
            "季度收入趋势和同比增长",
            "年度财务数据对比分析",
            "SEC文件和新闻动态",
            "主要财务比率计算"
        ],
        "endpoints": {
            "财务数据": "/financials/{ticker}",
            "季度收入": "/quarterly-revenue/{ticker}",
            "年度对比": "/annual-comparison/{ticker}",
            "SEC新闻": "/news/{ticker}",
            "财务比率": "/ratios/{ticker}",
            "健康检查": "/health"
        },
        "cache_strategy": {
            "财务数据": "1小时",
            "新闻数据": "30分钟",
            "财务比率": "1小时"
        },
        "rate_limits": {
            "免费用户": "每分钟10次请求",
            "API密钥用户": "每分钟100次请求"
        },
        "documentation": "https://api.edgarfiling.sec.gov/docs/index.html",
        "last_updated": datetime.now().isoformat()
    }
