"""
测试API路由
提供直接测试各数据源的接口，用于调试和验证
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Depends

from app.core.logging import get_logger
from app.core.config import settings
from app.models.base import BaseResponse
from app.data_sources import YFinanceDataSource, PolygonDataSource
from app.services.data_source_manager import DataSourceManager
from app.utils.exceptions import InvalidParameterError

logger = get_logger(__name__)
router = APIRouter()


def get_data_source_manager() -> DataSourceManager:
    """获取数据源管理器实例"""
    from app.main import get_data_source_manager
    return get_data_source_manager()


@router.get("/polygon/{symbol}/raw", tags=["测试"])
async def test_polygon_raw(symbol: str):
    """
    直接测试 Polygon.io 数据源（原始响应）

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回 Polygon.io 的原始 API 响应，用于调试接口
    """
    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    logger.info("直接测试Polygon.io原始响应", symbol=symbol)

    # 创建Polygon数据源实例
    polygon_source = PolygonDataSource()

    try:
        # 直接调用内部方法获取原始数据
        raw_snapshot = await polygon_source.get_raw_snapshot(symbol)
        raw_ticker_details = await polygon_source.get_raw_ticker_details(symbol)

        return {
            "symbol": symbol,
            "polygon_snapshot": raw_snapshot,
            "polygon_ticker_details": raw_ticker_details,
            "api_status": "success",
            "message": "Polygon.io 原始数据获取成功"
        }

    except Exception as e:
        logger.error("Polygon.io原始数据获取失败", symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Polygon.io 原始数据获取失败: {str(e)}"
        )


@router.get("/polygon/{symbol}/quote", tags=["测试"])
async def test_polygon_quote(symbol: str):
    """
    直接测试 Polygon.io 数据源（转换后的报价数据）

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回经过适配器转换的 Polygon.io 报价数据
    """
    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    logger.info("直接测试Polygon.io转换后报价", symbol=symbol)

    # 创建Polygon数据源实例
    polygon_source = PolygonDataSource()

    try:
        # 获取快速报价数据
        quote_data = await polygon_source.get_fast_quote(symbol)

        return BaseResponse(
            symbol=symbol,
            data=quote_data,
            data_source="polygon",
            is_fallback=False
        )

    except Exception as e:
        logger.error("Polygon.io报价数据获取失败", symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Polygon.io 报价数据获取失败: {str(e)}"
        )


@router.get("/polygon/{symbol}/company", tags=["测试"])
async def test_polygon_company(symbol: str):
    """
    直接测试 Polygon.io 公司信息

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回 Polygon.io 的公司信息数据
    """
    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    logger.info("直接测试Polygon.io公司信息", symbol=symbol)

    # 创建Polygon数据源实例
    polygon_source = PolygonDataSource()

    try:
        # 获取公司信息
        company_info = await polygon_source.get_company_info(symbol)

        return BaseResponse(
            symbol=symbol,
            data=company_info,
            data_source="polygon",
            is_fallback=False
        )

    except Exception as e:
        logger.error("Polygon.io公司信息获取失败", symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Polygon.io 公司信息获取失败: {str(e)}"
        )


@router.get("/yfinance/{symbol}/quote", tags=["测试"])
async def test_yfinance_quote(symbol: str):
    """
    直接测试 Yahoo Finance 数据源

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回 Yahoo Finance 的报价数据
    """
    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    logger.info("直接测试Yahoo Finance报价", symbol=symbol)

    # 创建Yahoo Finance数据源实例
    yfinance_source = YFinanceDataSource()

    try:
        # 获取快速报价数据
        quote_data = await yfinance_source.get_fast_quote(symbol)

        return BaseResponse(
            symbol=symbol,
            data=quote_data,
            data_source="yfinance",
            is_fallback=False
        )

    except Exception as e:
        logger.error("Yahoo Finance报价数据获取失败", symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Yahoo Finance 报价数据获取失败: {str(e)}"
        )


@router.get("/compare/{symbol}", tags=["测试"])
async def test_compare_sources(
    symbol: str,
    manager: DataSourceManager = Depends(get_data_source_manager)
):
    """
    比较所有数据源的数据差异

    - **symbol**: 股票代码 (例如: AAPL, MSFT, TSLA)

    返回不同数据源的数据对比结果

    注意：仅在调试模式下可用
    """
    if not settings.debug:
        raise HTTPException(
            status_code=403,
            detail="数据源比较功能仅在调试模式下可用"
        )

    if not symbol or len(symbol.strip()) == 0:
        raise InvalidParameterError("symbol", symbol)

    symbol = symbol.upper().strip()
    logger.info("比较数据源差异", symbol=symbol)

    try:
        comparison_result = await manager.compare_data_sources(symbol)
        return comparison_result

    except Exception as e:
        logger.error("数据源比较失败", symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"数据源比较失败: {str(e)}"
        )


@router.get("/health-check", tags=["测试"])
async def test_all_sources_health():
    """
    测试所有数据源的健康状态

    直接调用各个数据源的健康检查方法
    """
    logger.info("测试所有数据源健康状态")

    results = {}

    # 测试Yahoo Finance
    try:
        yfinance_source = YFinanceDataSource()
        yf_health = await yfinance_source.health_check()
        results["yfinance"] = {
            "healthy": yf_health,
            "status": yfinance_source.get_status().value,
            "metrics": yfinance_source.get_metrics()
        }
    except Exception as e:
        results["yfinance"] = {
            "healthy": False,
            "error": str(e)
        }

    # 测试Polygon.io
    try:
        polygon_source = PolygonDataSource()
        polygon_health = await polygon_source.health_check()
        results["polygon"] = {
            "healthy": polygon_health,
            "status": polygon_source.get_status().value,
            "metrics": polygon_source.get_metrics()
        }
    except Exception as e:
        results["polygon"] = {
            "healthy": False,
            "error": str(e)
        }

    return {
        "overall_healthy": any(source.get("healthy", False) for source in results.values()),
        "sources": results,
        "message": "数据源健康检查完成"
    }


@router.get("/api-limits", tags=["测试"])
async def test_api_limits():
    """
    测试 API 限制和配置信息

    返回当前 API 配置和限制信息
    """
    return {
        "polygon_config": {
            "api_key_configured": bool(settings.polygon_api_key),
            "api_key_prefix": settings.polygon_api_key[:8] + "..." if settings.polygon_api_key else None,
            "base_url": "https://api.polygon.io"
        },
        "fallback_config": {
            "enabled": settings.fallback_enabled,
            "max_failures": settings.primary_source_max_failures,
            "timeout": settings.fallback_timeout,
            "cooldown_period": settings.fallback_cooldown_period
        },
        "cache_config": {
            "redis_url": bool(settings.redis_url),
            "ttl_seconds": settings.cache_ttl_seconds
        },
        "debug_mode": settings.debug
    }
