"""
自定义异常类和异常处理器
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
    HTTP_503_SERVICE_UNAVAILABLE,
    HTTP_504_GATEWAY_TIMEOUT,
)
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class FinanceAPIException(Exception):
    """财务API基础异常类"""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class TickerNotFoundError(FinanceAPIException):
    """股票代码未找到异常"""

    def __init__(self, symbol: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"未找到股票代码: {symbol}",
            code="TICKER_NOT_FOUND",
            status_code=HTTP_404_NOT_FOUND,
            details=details,
        )


class InvalidParameterError(FinanceAPIException):
    """无效参数异常"""

    def __init__(self, parameter: str, value: Any, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"无效参数 {parameter}: {value}",
            code="INVALID_PARAM",
            status_code=HTTP_400_BAD_REQUEST,
            details=details,
        )


class YahooAPIError(FinanceAPIException):
    """Yahoo API调用异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Yahoo API错误: {message}",
            code="YAHOO_API_ERROR",
            status_code=HTTP_502_BAD_GATEWAY,
            details=details,
        )


class ServiceUnavailableError(FinanceAPIException):
    """服务不可用异常"""

    def __init__(self, message: str = "服务暂时不可用", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class CacheError(FinanceAPIException):
    """缓存异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"缓存错误: {message}",
            code="CACHE_ERROR",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


async def finance_api_exception_handler(request: Request, exc: FinanceAPIException) -> JSONResponse:
    """财务API异常处理器"""

    # 根据错误代码映射到合适的HTTP状态码
    status_code_mapping = {
        "INVALID_SYMBOL": HTTP_400_BAD_REQUEST,
        "TICKER_NOT_FOUND": HTTP_404_NOT_FOUND,
        "INVALID_PARAM": HTTP_400_BAD_REQUEST,
        "INSUFFICIENT_PERMISSIONS": HTTP_403_FORBIDDEN,
        "TIMEOUT_ERROR": HTTP_504_GATEWAY_TIMEOUT,
        "SERVICE_UNAVAILABLE": HTTP_503_SERVICE_UNAVAILABLE,
        "YAHOO_API_ERROR": HTTP_502_BAD_GATEWAY,
        "CACHE_ERROR": HTTP_500_INTERNAL_SERVER_ERROR,
    }

    # 使用映射的状态码，或者使用异常自带的状态码
    final_status_code = status_code_mapping.get(exc.code, exc.status_code)

    logger.error(
        "API异常",
        exception_type=exc.__class__.__name__,
        message=exc.message,
        code=exc.code,
        status_code=final_status_code,
        details=exc.details,
        url=str(request.url),
        method=request.method,
    )

    return JSONResponse(
        status_code=final_status_code,
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "detail": exc.message,
            "timestamp": datetime.now().isoformat(),
            "details": exc.details,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(
        "未处理的异常",
        exception_type=exc.__class__.__name__,
        message=str(exc),
        url=str(request.url),
        method=request.method,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": "INTERNAL_ERROR",
            "message": "内部服务器错误",
            "detail": "服务器内部错误，请稍后重试",
            "timestamp": datetime.now().isoformat(),
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(
        "HTTP异常",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method,
    )

    # 根据状态码确定错误代码
    code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    error_code = code_mapping.get(exc.status_code, "HTTP_ERROR")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": error_code,
            "message": str(exc.detail),
            "detail": str(exc.detail),
            "timestamp": datetime.now().isoformat(),
        },
    )
