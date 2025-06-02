"""
降级管理器
实现多数据源的智能降级和切换逻辑
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Type, Callable
from enum import Enum

from .base import DataSourceInterface, DataSourceStatus, DataSourceType
from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FallbackTrigger(Enum):
    """降级触发原因"""
    CONSECUTIVE_FAILURES = "consecutive_failures"
    TIMEOUT = "timeout"
    ERROR_RATE = "error_rate"
    MANUAL = "manual"


class FallbackEvent:
    """降级事件记录"""

    def __init__(self, trigger: FallbackTrigger, primary_source: str, fallback_source: str, error: str = None):
        self.trigger = trigger
        self.primary_source = primary_source
        self.fallback_source = fallback_source
        self.error = error
        self.timestamp = time.time()
        self.operation = None


class FallbackManager:
    """降级管理器"""

    def __init__(
        self,
        primary_source: DataSourceInterface,
        fallback_sources: List[DataSourceInterface]
    ):
        """
        初始化降级管理器

        Args:
            primary_source: 主数据源
            fallback_sources: 降级数据源列表
        """
        self.primary_source = primary_source
        self.fallback_sources = fallback_sources
        self.all_sources = [primary_source] + fallback_sources

        # 配置参数
        self.enabled = settings.fallback_enabled
        self.timeout = settings.fallback_timeout
        self.max_failures = settings.primary_source_max_failures
        self.cooldown_period = settings.fallback_cooldown_period

        # 状态追踪
        self.consecutive_failures = 0
        self.last_failure_time = None
        self.fallback_events = []
        self.health_check_task = None
        self._is_initialized = False

        logger.info(
            "降级管理器初始化完成",
            primary=primary_source.name,
            fallback_count=len(fallback_sources)
        )

    async def initialize(self) -> None:
        """初始化异步组件"""
        if not self._is_initialized:
            self._start_health_check()
            self._is_initialized = True

    async def get_fast_quote(self, symbol: str) -> FastQuoteData:
        """获取快速报价（带降级）"""
        return await self._execute_with_fallback("get_fast_quote", symbol=symbol)

    async def get_detailed_quote(self, symbol: str) -> QuoteData:
        """获取详细报价（带降级）"""
        return await self._execute_with_fallback("get_detailed_quote", symbol=symbol)

    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """获取公司信息（带降级）"""
        return await self._execute_with_fallback("get_company_info", symbol=symbol)

    async def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        start: Optional[str] = None,
        end: Optional[str] = None,
        auto_adjust: bool = True,
        prepost: bool = True,
        actions: bool = True
    ) -> Dict[str, Any]:
        """获取历史数据（带降级）"""
        return await self._execute_with_fallback(
            "get_history",
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
        """批量获取报价（带降级）"""
        return await self._execute_with_fallback("get_batch_quotes", symbols=symbols)

    async def _execute_with_fallback(self, method_name: str, **kwargs) -> Any:
        """执行操作，失败时自动降级"""
        if not self.enabled:
            # 降级未启用，直接使用主数据源
            method = getattr(self.primary_source, method_name)
            return await method(**kwargs)

        # 检查是否需要直接使用降级源
        if self._should_use_fallback():
            logger.info(
                "主数据源状态不佳，直接使用降级数据源",
                consecutive_failures=self.consecutive_failures,
                primary_status=self.primary_source.get_status().value
            )
            return await self._try_fallback_sources(method_name, **kwargs)

        # 尝试主数据源
        try:
            method = getattr(self.primary_source, method_name)
            result = await asyncio.wait_for(method(**kwargs), timeout=self.timeout)

            # 主数据源成功，重置失败计数
            self._reset_failure_count()

            # 在结果中标记数据源
            if hasattr(result, '__dict__') and isinstance(result, dict):
                result["data_source"] = self.primary_source.get_source_type().value

            return result

        except Exception as e:
            self._record_failure(str(e))

            logger.warning(
                "主数据源操作失败，尝试降级",
                method=method_name,
                error=str(e),
                consecutive_failures=self.consecutive_failures,
                source=self.primary_source.name
            )

            # 尝试降级数据源
            return await self._try_fallback_sources(method_name, **kwargs)

    async def _try_fallback_sources(self, method_name: str, **kwargs) -> Any:
        """尝试降级数据源"""
        last_error = None

        for fallback_source in self.fallback_sources:
            try:
                if fallback_source.get_status() == DataSourceStatus.UNHEALTHY:
                    logger.debug(f"跳过不健康的降级数据源: {fallback_source.name}")
                    continue

                method = getattr(fallback_source, method_name)
                result = await asyncio.wait_for(method(**kwargs), timeout=self.timeout)

                # 记录降级事件
                self._record_fallback_event(
                    FallbackTrigger.CONSECUTIVE_FAILURES,
                    self.primary_source.name,
                    fallback_source.name
                )

                logger.info(
                    "降级数据源操作成功",
                    method=method_name,
                    fallback_source=fallback_source.name,
                    consecutive_failures=self.consecutive_failures
                )

                # 在结果中标记数据源
                if hasattr(result, '__dict__') and isinstance(result, dict):
                    result["data_source"] = fallback_source.get_source_type().value
                    result["is_fallback"] = True

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    "降级数据源操作失败",
                    method=method_name,
                    fallback_source=fallback_source.name,
                    error=str(e)
                )
                continue

        # 所有数据源都失败了
        raise Exception(f"所有数据源都不可用，最后错误: {str(last_error)}")

    def _should_use_fallback(self) -> bool:
        """判断是否应该直接使用降级源"""
        # 检查连续失败次数
        if self.consecutive_failures >= self.max_failures:
            return True

        # 检查主数据源状态
        if self.primary_source.get_status() == DataSourceStatus.UNHEALTHY:
            return True

        # 检查是否在冷却期内
        if self.last_failure_time:
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure < self.cooldown_period:
                return True

        return False

    def _record_failure(self, error: str):
        """记录失败"""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        logger.error(
            "数据源操作失败",
            source=self.primary_source.name,
            consecutive_failures=self.consecutive_failures,
            error=error
        )

    def _reset_failure_count(self):
        """重置失败计数"""
        if self.consecutive_failures > 0:
            logger.info(
                "主数据源恢复正常，重置失败计数",
                previous_failures=self.consecutive_failures,
                source=self.primary_source.name
            )
            self.consecutive_failures = 0
            self.last_failure_time = None

    def _record_fallback_event(self, trigger: FallbackTrigger, primary: str, fallback: str, error: str = None):
        """记录降级事件"""
        event = FallbackEvent(trigger, primary, fallback, error)
        self.fallback_events.append(event)

        # 保留最近100个事件
        if len(self.fallback_events) > 100:
            self.fallback_events = self.fallback_events[-100:]

        logger.warning(
            "数据源降级事件",
            trigger=trigger.value,
            primary_source=primary,
            fallback_source=fallback,
            error=error
        )

    def _start_health_check(self):
        """启动健康检查任务"""
        async def health_check_loop():
            while True:
                try:
                    await asyncio.sleep(settings.health_check_interval)
                    await self._perform_health_checks()
                except Exception as e:
                    logger.error("健康检查任务异常", error=str(e))

        self.health_check_task = asyncio.create_task(health_check_loop())

    async def _perform_health_checks(self):
        """执行健康检查"""
        tasks = []
        for source in self.all_sources:
            tasks.append(self._check_single_source(source))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_single_source(self, source: DataSourceInterface):
        """检查单个数据源"""
        try:
            is_healthy = await source.health_check()
            logger.debug(
                "数据源健康检查",
                source=source.name,
                healthy=is_healthy,
                status=source.get_status().value
            )
        except Exception as e:
            logger.warning(
                "数据源健康检查失败",
                source=source.name,
                error=str(e)
            )

    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        sources_status = []
        for source in self.all_sources:
            sources_status.append({
                "name": source.name,
                "type": source.get_source_type().value,
                "status": source.get_status().value,
                "metrics": source.get_metrics()
            })

        recent_events = [
            {
                "trigger": event.trigger.value,
                "primary_source": event.primary_source,
                "fallback_source": event.fallback_source,
                "timestamp": event.timestamp,
                "error": event.error
            }
            for event in self.fallback_events[-10:]  # 最近10个事件
        ]

        return {
            "fallback_enabled": self.enabled,
            "consecutive_failures": self.consecutive_failures,
            "last_failure_time": self.last_failure_time,
            "should_use_fallback": self._should_use_fallback(),
            "sources": sources_status,
            "recent_events": recent_events,
            "config": {
                "max_failures": self.max_failures,
                "timeout": self.timeout,
                "cooldown_period": self.cooldown_period
            }
        }

    async def force_fallback(self, reason: str = "manual"):
        """手动触发降级"""
        self.consecutive_failures = self.max_failures
        self.last_failure_time = time.time()

        self._record_fallback_event(
            FallbackTrigger.MANUAL,
            self.primary_source.name,
            self.fallback_sources[0].name if self.fallback_sources else "none",
            reason
        )

        logger.warning("手动触发数据源降级", reason=reason)

    async def reset_fallback(self):
        """重置降级状态"""
        self._reset_failure_count()
        logger.info("降级状态已重置")

    def __del__(self):
        """清理资源"""
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
