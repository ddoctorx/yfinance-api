"""
数据源抽象基类
定义所有数据源必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
import time

from app.models.quote import QuoteData, FastQuoteData, CompanyInfo
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataSourceError(Exception):
    """数据源相关异常"""
    pass


class DataSourceType(Enum):
    """数据源类型枚举"""
    YFINANCE = "yfinance"
    POLYGON = "polygon"
    ALPHAVANTAGE = "alphavantage"


class DataSourceStatus(Enum):
    """数据源状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  # 性能下降但可用
    UNHEALTHY = "unhealthy"  # 不可用


class DataSourceInterface(ABC):
    """数据源接口定义"""

    @abstractmethod
    async def get_fast_quote(self, symbol: str) -> FastQuoteData:
        """获取快速报价数据"""
        pass

    @abstractmethod
    async def get_detailed_quote(self, symbol: str) -> QuoteData:
        """获取详细报价数据"""
        pass

    @abstractmethod
    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """获取公司信息"""
        pass

    @abstractmethod
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
        """获取历史数据"""
        pass

    @abstractmethod
    async def get_batch_quotes(self, symbols: List[str]) -> Dict[str, FastQuoteData]:
        """批量获取报价数据"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    @abstractmethod
    def get_source_type(self) -> DataSourceType:
        """获取数据源类型"""
        pass


class BaseDataSource(DataSourceInterface):
    """数据源基类，提供通用功能"""

    def __init__(self, source_type: DataSourceType, name: str = None):
        self.source_type = source_type
        self.name = name or source_type.value
        self.status = DataSourceStatus.HEALTHY
        self.last_error = None
        self.last_health_check = None
        self.total_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0

    def get_source_type(self) -> DataSourceType:
        """获取数据源类型"""
        return self.source_type

    def get_status(self) -> DataSourceStatus:
        """获取数据源状态"""
        return self.status

    def _update_status(self, success: bool, response_time: float = None, error: str = None):
        """更新数据源状态"""
        self.total_requests += 1

        if response_time:
            self.total_response_time += response_time

        if success:
            # 成功时重置错误计数
            self.failed_requests = max(0, self.failed_requests - 1)
            self.last_error = None

            # 根据性能更新状态
            if self.status == DataSourceStatus.UNHEALTHY:
                self.status = DataSourceStatus.DEGRADED
            elif self.status == DataSourceStatus.DEGRADED:
                # 连续成功则恢复健康状态
                success_rate = (self.total_requests -
                                self.failed_requests) / self.total_requests
                if success_rate > 0.9:  # 成功率>90%时恢复健康
                    self.status = DataSourceStatus.HEALTHY
        else:
            self.failed_requests += 1
            self.last_error = error

            # 根据失败率更新状态
            failure_rate = self.failed_requests / self.total_requests
            if failure_rate > 0.5:  # 失败率>50%标记为不健康
                self.status = DataSourceStatus.UNHEALTHY
            elif failure_rate > 0.2:  # 失败率>20%标记为性能下降
                self.status = DataSourceStatus.DEGRADED

    def get_metrics(self) -> Dict[str, Any]:
        """获取数据源指标"""
        avg_response_time = (
            self.total_response_time / self.total_requests
            if self.total_requests > 0 else 0
        )

        success_rate = (
            (self.total_requests - self.failed_requests) / self.total_requests
            if self.total_requests > 0 else 1.0
        )

        return {
            "source_type": self.source_type.value,
            "name": self.name,
            "status": self.status.value,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "average_response_time": avg_response_time,
            "last_error": self.last_error,
            "last_health_check": self.last_health_check
        }

    async def execute_with_metrics(self, operation_name: str, operation_func):
        """带指标记录的操作执行"""
        start_time = time.time()
        try:
            result = await operation_func()
            response_time = time.time() - start_time
            self._update_status(True, response_time)

            logger.debug(
                f"{self.name} 操作成功",
                operation=operation_name,
                response_time=response_time,
                source=self.name
            )

            return result

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            self._update_status(False, response_time, error_msg)

            logger.error(
                f"{self.name} 操作失败",
                operation=operation_name,
                response_time=response_time,
                error=error_msg,
                source=self.name
            )

            raise

    async def health_check(self) -> bool:
        """默认健康检查实现"""
        try:
            # 尝试获取一个测试股票的快速报价
            await self.get_fast_quote("AAPL")
            self.last_health_check = time.time()
            return True
        except Exception as e:
            logger.warning(f"{self.name} 健康检查失败", error=str(e))
            return False
