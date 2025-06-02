"""
日志配置模块
配置结构化日志记录
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import FilteringBoundLogger

from .config import settings


def configure_logging() -> None:
    """配置应用日志"""

    # 配置标准库日志
    logging.basicConfig(
        format=settings.log_format,
        level=getattr(logging, settings.log_level.upper()),
        stream=sys.stdout,
    )

    # 配置 structlog
    structlog.configure(
        processors=[
            # 添加日志级别
            structlog.stdlib.add_log_level,
            # 添加时间戳
            structlog.processors.TimeStamper(fmt="iso"),
            # 在开发模式下使用更友好的格式
            structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> FilteringBoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


def log_request_response(
    method: str,
    url: str,
    status_code: int,
    response_time: float,
    **kwargs: Any
) -> None:
    """记录请求响应日志"""
    logger = get_logger("api")

    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "response_time_ms": round(response_time * 1000, 2),
        **kwargs
    }

    if status_code >= 400:
        logger.error("API请求失败", **log_data)
    else:
        logger.info("API请求成功", **log_data)


def log_yfinance_call(
    symbol: str,
    operation: str,
    success: bool,
    response_time: float = None,
    error: str = None,
    **kwargs: Any
) -> None:
    """记录yfinance调用日志"""
    logger = get_logger("yfinance")

    log_data = {
        "symbol": symbol,
        "operation": operation,
        "success": success,
        **kwargs
    }

    if response_time is not None:
        log_data["response_time_ms"] = round(response_time * 1000, 2)

    if success:
        logger.info("yfinance调用成功", **log_data)
    else:
        log_data["error"] = error
        logger.error("yfinance调用失败", **log_data)
