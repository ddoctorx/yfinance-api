"""
Finance API 主应用
基于 FastAPI + yfinance 的金融数据API服务
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

# 导入路由
from app.api.v1.quote import router as quote_router
from app.api.v1.history import router as history_router

# 配置日志
configure_logging()
logger = get_logger(__name__)

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
    # 启动时执行
    logger.info("Finance API 启动中...", version=settings.app_version)

    # 这里可以添加启动时的初始化逻辑
    # 例如：数据库连接、缓存预热等

    yield

    # 关闭时执行
    logger.info("Finance API 关闭中...")

    # 这里可以添加清理逻辑
    # 例如：关闭数据库连接、清理缓存等


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Finance API
    
    基于 yfinance 的金融数据API服务，提供：
    
    * **实时报价** - 获取股票实时价格和基本信息
    * **历史数据** - 获取K线数据、股息、拆股等历史信息
    * **公司信息** - 获取公司基本资料和财务指标
    * **批量查询** - 支持多个股票代码的批量查询
    
    ### 数据来源
    所有数据来源于 Yahoo Finance，请遵守相关使用条款。
    
    ### 缓存策略
    - 实时报价：缓存1分钟
    - 历史数据：缓存1小时
    - 公司信息：缓存1天
    
    ### 限流
    - 每分钟最多100次请求
    - 批量查询最多支持10个股票代码
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

    # 检查缓存状态
    try:
        cache_info = await get_cache_info()
        dependencies["cache"] = "healthy"
    except Exception as e:
        dependencies["cache"] = f"error: {str(e)}"
        logger.warning("缓存健康检查失败", error=str(e))

    # 检查 yfinance 状态 (可以尝试获取一个简单的报价)
    try:
        from app.services.yfinance_service import yfinance_service
        # 这里可以添加一个简单的yfinance测试
        dependencies["yfinance"] = "healthy"
    except Exception as e:
        dependencies["yfinance"] = f"error: {str(e)}"
        logger.warning("yfinance健康检查失败", error=str(e))

    return HealthResponse(
        version=settings.app_version,
        dependencies=dependencies
    )


# 缓存信息端点
@app.get("/cache/info", response_model=CacheInfo, tags=["系统"])
async def get_cache_status():
    """
    获取缓存配置信息

    返回当前缓存后端类型和配置
    """
    return await get_cache_info()


# 注册API路由
app.include_router(
    quote_router,
    prefix=f"{settings.api_v1_prefix}/quote",
    tags=["报价"]
)

app.include_router(
    history_router,
    prefix=f"{settings.api_v1_prefix}/history",
    tags=["历史数据"]
)


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
