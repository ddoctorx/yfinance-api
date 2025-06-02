"""
Finance API 主应用
基于 FastAPI + yfinance 的金融数据API服务
支持多数据源降级机制 (yfinance -> Polygon.io)
"""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.logging import configure_logging, get_logger, log_request_response
from app.models.base import HealthResponse, CacheInfo
from app.utils.exceptions import (
    FinanceAPIException,
    finance_api_exception_handler,
    general_exception_handler,
    http_exception_handler,
)
from app.utils.cache import get_cache_info

# 导入数据源管理器
from app.services.data_source_manager import DataSourceManager
from app.services.sec_service import initialize_sec_service, shutdown_sec_service

# 导入路由
from app.api.v1 import (
    quote_router,
    history_router,
    test_router,
    sec_router,
    sec_advanced_router
)

# 配置日志
configure_logging()
logger = get_logger(__name__)

# 全局数据源管理器实例
data_source_manager: DataSourceManager = None

# 配置 Sentry (如果提供了 DSN)
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment="production" if not settings.debug else "development",
    )
    logger.info("Sentry监控已启用")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global data_source_manager

    # 启动时执行
    logger.info("Finance API 启动中...", version=settings.app_version)

    # 初始化数据源管理器
    try:
        data_source_manager = DataSourceManager()
        logger.info("数据源管理器初始化成功",
                    fallback_enabled=settings.fallback_enabled)
    except Exception as e:
        logger.error("数据源管理器初始化失败", error=str(e))
        # 不阻止应用启动，但记录错误

    # 初始化SEC服务
    try:
        # 使用配置文件中的API key
        await initialize_sec_service(api_key=settings.sec_api_key)
        logger.info("SEC服务初始化成功")
    except Exception as e:
        logger.error("SEC服务初始化失败", error=str(e))
        # 不阻止应用启动，但记录错误

    yield

    # 关闭时执行
    logger.info("Finance API 关闭中...")

    # 清理数据源管理器
    if data_source_manager:
        try:
            await data_source_manager.shutdown()
            logger.info("数据源管理器已关闭")
        except Exception as e:
            logger.error("数据源管理器关闭失败", error=str(e))

    # 关闭SEC服务
    try:
        await shutdown_sec_service()
        logger.info("SEC服务已关闭")
    except Exception as e:
        logger.error("SEC服务关闭失败", error=str(e))


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Finance API

    基于 yfinance 和 SEC EDGAR 的金融数据API服务，提供：

    * **实时报价** - 获取股票实时价格和基本信息
    * **历史数据** - 获取K线数据、股息、拆股等历史信息
    * **公司信息** - 获取公司基本资料和财务指标
    * **SEC财报数据** - 获取美股公司官方财务报表 (NEW!)
    * **批量查询** - 支持多个股票代码的批量查询

    ### 数据来源
    - **股价数据**: Yahoo Finance
    - **财报数据**: SEC EDGAR API + XBRL (官方数据源)

    ### 主要功能
    #### SEC财报模块 🆕
    - 年度和季度财务报表 (10-K, 10-Q)
    - 损益表、资产负债表、现金流量表
    - 季度收入趋势和同比增长分析
    - 年度财务数据对比
    - SEC文件和新闻动态
    - 主要财务比率计算

    ### 缓存策略
    - 实时报价：缓存1分钟
    - 历史数据：缓存1小时
    - 公司信息：缓存1天
    - SEC财报数据：缓存1小时
    - SEC新闻：缓存30分钟

    ### 限流
    - 每分钟最多100次请求
    - 批量查询最多支持10个股票代码

    ### API版本
    - v1: `/v1/` - 当前稳定版本
    - SEC模块: `/v1/sec/` - 财报数据专用接口
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()

    # 执行请求
    response = await call_next(request)

    # 计算响应时间
    process_time = time.time() - start_time

    # 记录日志
    log_request_response(
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        response_time=process_time,
        user_agent=request.headers.get("user-agent"),
        client_ip=request.client.host if request.client else None,
    )

    # 添加响应时间头
    response.headers["X-Process-Time"] = str(process_time)

    return response


# 注册异常处理器
app.add_exception_handler(FinanceAPIException, finance_api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# 健康检查端点
@app.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """
    健康检查

    检查API服务状态和依赖服务状态
    """
    dependencies = {}
    overall_healthy = True

    # 检查缓存状态
    try:
        cache_info = await get_cache_info()
        dependencies["cache"] = "healthy"
    except Exception as e:
        dependencies["cache"] = f"error: {str(e)}"
        overall_healthy = False
        logger.warning("缓存健康检查失败", error=str(e))

    # 检查数据源状态
    try:
        if data_source_manager:
            # 获取详细的数据源状态
            status_summary = data_source_manager.get_status()
            primary_healthy = any(
                source["status"] == "healthy"
                for source in status_summary["sources"]
            )
            dependencies["data_sources"] = "healthy" if primary_healthy else "degraded"
            dependencies["fallback_enabled"] = status_summary["fallback_enabled"]

            if not primary_healthy:
                overall_healthy = False
        else:
            dependencies["data_sources"] = "not_initialized"
            overall_healthy = False
    except Exception as e:
        dependencies["data_sources"] = f"error: {str(e)}"
        overall_healthy = False
        logger.warning("数据源健康检查失败", error=str(e))

    # 确定响应状态
    if overall_healthy:
        return HealthResponse(
            success=True,
            code="HEALTHY",
            message="服务运行正常",
            status="healthy",
            version=settings.app_version,
            dependencies=dependencies
        )
    else:
        return HealthResponse(
            success=False,
            code="DEGRADED",
            message="服务运行异常或降级",
            status="degraded",
            version=settings.app_version,
            dependencies=dependencies
        )


# 数据源状态端点
@app.get("/data-sources/status", tags=["系统"])
async def get_data_source_status():
    """
    获取数据源详细状态

    返回所有数据源的状态、指标和降级信息
    """
    if not data_source_manager:
        return {"error": "数据源管理器未初始化"}

    try:
        return data_source_manager.get_status()
    except Exception as e:
        logger.error("获取数据源状态失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取数据源状态失败: {str(e)}")


# 数据源健康检查端点
@app.get("/data-sources/health", tags=["系统"])
async def check_data_source_health():
    """
    执行数据源健康检查

    主动检查所有数据源的健康状态
    """
    if not data_source_manager:
        return {"error": "数据源管理器未初始化"}

    try:
        health_results = await data_source_manager.health_check()
        return health_results
    except Exception as e:
        logger.error("数据源健康检查失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"数据源健康检查失败: {str(e)}")


# 手动降级控制端点
@app.post("/data-sources/fallback", tags=["系统"])
async def force_fallback(reason: str = "manual"):
    """
    手动触发数据源降级

    Args:
        reason: 降级原因
    """
    if not data_source_manager:
        raise HTTPException(status_code=500, detail="数据源管理器未初始化")

    try:
        await data_source_manager.force_fallback(reason)
        return {"message": "降级已触发", "reason": reason}
    except Exception as e:
        logger.error("手动触发降级失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"触发降级失败: {str(e)}")


# 重置降级状态端点
@app.post("/data-sources/reset", tags=["系统"])
async def reset_fallback():
    """
    重置数据源降级状态

    恢复使用主数据源
    """
    if not data_source_manager:
        raise HTTPException(status_code=500, detail="数据源管理器未初始化")

    try:
        await data_source_manager.reset_fallback()
        return {"message": "降级状态已重置"}
    except Exception as e:
        logger.error("重置降级状态失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"重置降级状态失败: {str(e)}")


# 缓存信息端点
@app.get("/cache/info", response_model=CacheInfo, tags=["系统"])
async def get_cache_status():
    """
    获取缓存配置信息

    返回当前缓存后端类型和配置
    """
    return await get_cache_info()


# 注册API路由
app.include_router(quote_router, prefix="/api/v1/quote", tags=["股价查询"])
app.include_router(history_router, prefix="/api/v1/history", tags=["历史数据"])
app.include_router(test_router, prefix="/api/v1/test", tags=["测试"])
app.include_router(sec_router, prefix="/api/v1/sec", tags=["SEC数据"])
app.include_router(sec_advanced_router,
                   prefix="/api/v1/sec-advanced", tags=["SEC高级功能"])


# 根路径重定向到文档
@app.get("/", include_in_schema=False)
async def root():
    """根路径重定向到API文档"""
    return JSONResponse({
        "message": "欢迎使用 Finance API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    })


def get_data_source_manager() -> DataSourceManager:
    """
    获取数据源管理器实例
    用于依赖注入
    """
    if not data_source_manager:
        raise HTTPException(status_code=500, detail="数据源管理器未初始化")
    return data_source_manager


if __name__ == "__main__":
    import uvicorn

    logger.info("启动开发服务器", host=settings.host, port=settings.port)

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
