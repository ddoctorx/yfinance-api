# API Version 1 Package

"""
API v1 路由模块
"""

from .quote import router as quote_router
from .history import router as history_router
from .test import router as test_router
from .sec import router as sec_router

__all__ = ["quote_router", "history_router", "test_router", "sec_router"]
