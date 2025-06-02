"""
数据源管理服务
整合所有数据源，提供统一的接口和降级管理
"""

from typing import Dict, List, Optional, Any
import asyncio

from app.data_sources import (
    YFinanceDataSource,
    PolygonDataSource,
    FallbackManager
)
from app.adapters.polygon_adapter import PolygonDataAdapter
from app.adapters.data_normalizer import DataNormalizer
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        """初始化数据源管理器"""
        # 创建数据源实例 - Yahoo Finance为主，Polygon.io为降级
        self.primary_source = YFinanceDataSource()
        self.fallback_sources = [PolygonDataSource()]

        # 创建降级管理器
        self.fallback_manager = FallbackManager(
            primary_source=self.primary_source,
            fallback_sources=self.fallback_sources
        )

        # 数据适配器
        self.polygon_adapter = PolygonDataAdapter()
        self.normalizer = DataNormalizer()

        # 状态
        self._is_initialized = False

        logger.info("数据源管理器初始化完成")

    async def _ensure_initialized(self) -> None:
        """确保管理器已初始化"""
        if not self._is_initialized:
            await self.fallback_manager.initialize()
            self._is_initialized = True

    async def get_fast_quote(self, symbol: str) -> FastQuoteData:
        """获取快速报价"""
        await self._ensure_initialized()
        return await self.fallback_manager.get_fast_quote(symbol)

    async def get_detailed_quote(self, symbol: str) -> QuoteData:
        """获取详细报价"""
        await self._ensure_initialized()
        return await self.fallback_manager.get_detailed_quote(symbol)

    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """获取公司信息"""
        await self._ensure_initialized()
        return await self.fallback_manager.get_company_info(symbol)

    async def get_history(
        self,
        symbol: str,
        period: Optional[str] = "1y",
        interval: Optional[str] = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        auto_adjust: bool = True,
        prepost: bool = False,
        actions: bool = True
    ) -> dict:
        """获取历史数据"""
        await self._ensure_initialized()
        return await self.fallback_manager.get_history(
            symbol=symbol,
            period=period,
            interval=interval,
            start=start,
            end=end,
            auto_adjust=auto_adjust,
            prepost=prepost,
            actions=actions
        )

    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, FastQuoteData]:
        """批量获取报价"""
        await self._ensure_initialized()
        return await self.fallback_manager.get_batch_quotes(symbols)

    async def compare_data_sources(self, symbol: str) -> Dict[str, Any]:
        """比较不同数据源的数据（用于测试和验证）"""
        if not settings.debug:
            raise ValueError("数据源比较功能仅在调试模式下可用")

        results = {}
        errors = {}

        # 获取所有数据源的数据
        for source in [self.primary_source] + self.fallback_sources:
            try:
                quote = await source.get_fast_quote(symbol)
                results[source.name] = quote
            except Exception as e:
                errors[source.name] = str(e)

        # 比较数据差异
        comparisons = {}
        source_names = list(results.keys())

        for i, source1 in enumerate(source_names):
            for source2 in source_names[i+1:]:
                if source1 in results and source2 in results:
                    diff = self.normalizer.compare_sources(
                        results[source1],
                        results[source2],
                        source1,
                        source2
                    )
                    if diff:
                        comparisons[f"{source1}_vs_{source2}"] = diff

        return {
            "symbol": symbol,
            "results": results,
            "errors": errors,
            "comparisons": comparisons,
            "timestamp": asyncio.get_event_loop().time()
        }

    def get_status(self) -> Dict[str, Any]:
        """获取数据源管理器状态"""
        return {
            "manager": {
                "primary_source": self.primary_source.name,
                "fallback_sources": [source.name for source in self.fallback_sources],
                "fallback_enabled": settings.fallback_enabled
            },
            "fallback_manager": self.fallback_manager.get_status_summary()
        }

    async def health_check(self) -> Dict[str, Any]:
        """全面健康检查"""
        health_status = {}

        # 检查所有数据源
        for source in [self.primary_source] + self.fallback_sources:
            try:
                is_healthy = await source.health_check()
                health_status[source.name] = {
                    "healthy": is_healthy,
                    "status": source.get_status().value,
                    "metrics": source.get_metrics()
                }
            except Exception as e:
                health_status[source.name] = {
                    "healthy": False,
                    "error": str(e)
                }

        # 检查降级管理器状态
        fallback_status = self.fallback_manager.get_status_summary()

        overall_health = any(
            status.get("healthy", False)
            for status in health_status.values()
        )

        return {
            "overall_healthy": overall_health,
            "sources": health_status,
            "fallback": fallback_status,
            "timestamp": asyncio.get_event_loop().time()
        }

    async def force_fallback(self, reason: str = "manual"):
        """手动触发降级"""
        await self.fallback_manager.force_fallback(reason)
        logger.warning("手动触发数据源降级", reason=reason)

    async def reset_fallback(self):
        """重置降级状态"""
        await self.fallback_manager.reset_fallback()
        logger.info("数据源降级状态已重置")

    async def shutdown(self):
        """关闭数据源管理器"""
        logger.info("正在关闭数据源管理器...")

        # 清理资源
        if hasattr(self.fallback_manager, '__del__'):
            self.fallback_manager.__del__()


# 创建全局实例
data_source_manager = DataSourceManager()
