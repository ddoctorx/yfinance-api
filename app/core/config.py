"""
全局配置模块
使用 pydantic BaseSettings 管理环境变量和配置
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置设置"""

    # 应用基本信息
    app_name: str = "Finance API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")

    # API 配置
    api_v1_prefix: str = "/api/v1"
    allowed_origins: List[str] = Field(
        default=["*"],
        env="ALLOWED_ORIGINS",
        description="CORS允许的来源，生产环境应该设置具体域名"
    )

    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # 缓存配置
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl_seconds: int = Field(
        default=300, env="CACHE_TTL", description="缓存过期时间(秒)")

    # yfinance 配置
    yf_session_timeout: int = Field(
        default=30, env="YF_TIMEOUT", description="yfinance请求超时时间")
    yf_max_retries: int = Field(
        default=5, env="YF_MAX_RETRIES", description="yfinance最大重试次数")

    # Polygon.io 配置
    polygon_api_key: Optional[str] = Field(
        default=None,
        env="POLYGON_API_KEY",
        description="Polygon.io API密钥"
    )
    polygon_base_url: str = Field(
        default="https://api.polygon.io",
        env="POLYGON_BASE_URL",
        description="Polygon.io API基础URL"
    )
    polygon_timeout: int = Field(
        default=30, env="POLYGON_TIMEOUT", description="Polygon API请求超时时间")
    polygon_max_retries: int = Field(
        default=3, env="POLYGON_MAX_RETRIES", description="Polygon API最大重试次数")

    # 降级策略配置
    fallback_enabled: bool = Field(
        default=True, env="FALLBACK_ENABLED", description="是否启用降级机制")
    fallback_timeout: int = Field(
        default=10, env="FALLBACK_TIMEOUT", description="降级操作超时时间")
    primary_source_max_failures: int = Field(
        default=5, env="PRIMARY_SOURCE_MAX_FAILURES",
        description="主数据源连续失败多少次后触发降级")
    health_check_interval: int = Field(
        default=60, env="HEALTH_CHECK_INTERVAL",
        description="数据源健康检查间隔(秒)")
    fallback_cooldown_period: int = Field(
        default=300, env="FALLBACK_COOLDOWN_PERIOD",
        description="降级冷却期(秒)")

    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )

    # 限流配置
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")

    # 安全配置
    secret_key: str = Field(
        default="your-secret-key-change-in-production", env="SECRET_KEY")

    # Sentry监控 (可选)
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")

    # SEC API 配置
    sec_api_key: Optional[str] = Field(
        default=None,
        env="SEC_API_KEY",
        description="SEC API密钥，用于获取财务报表数据"
    )
    sec_api_timeout: int = Field(
        default=30, env="SEC_API_TIMEOUT", description="SEC API请求超时时间")
    sec_api_max_retries: int = Field(
        default=3, env="SEC_API_MAX_RETRIES", description="SEC API最大重试次数")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取应用配置实例"""
    return settings
