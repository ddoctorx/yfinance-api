"""
缓存工具模块
提供基于aiocache的缓存装饰器和配置
"""

import functools
import hashlib
import json
from typing import Any, Callable, Optional, Union
from datetime import datetime
import pandas as pd

from aiocache import Cache, cached
from aiocache.serializers import BaseSerializer
from aiocache.backends.memory import SimpleMemoryCache
from aiocache.backends.redis import RedisCache
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import CacheError

logger = get_logger(__name__)


class CustomJsonSerializer(BaseSerializer):
    """自定义JSON序列化器，支持Pydantic模型和Timestamp"""

    def dumps(self, value: Any) -> str:
        """序列化数据"""
        def convert_value(obj):
            if isinstance(obj, BaseModel):
                # Pydantic模型转换为字典
                return obj.model_dump()
            elif isinstance(obj, pd.Timestamp):
                # Pandas时间戳转换为ISO字符串
                return obj.isoformat()
            elif isinstance(obj, datetime):
                # datetime对象转换为ISO字符串
                return obj.isoformat()
            elif isinstance(obj, dict):
                # 递归处理字典
                return {k: convert_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                # 递归处理列表
                return [convert_value(item) for item in obj]
            else:
                return obj

        converted_value = convert_value(value)
        return json.dumps(converted_value, ensure_ascii=False)

    def loads(self, value: Union[str, bytes, None]) -> Any:
        """反序列化数据"""
        if value is None:
            return None

        # 确保value是字符串类型
        if isinstance(value, bytes):
            value = value.decode('utf-8')

        if not value:  # 空字符串
            return None

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("缓存反序列化失败", value=value, error=str(e))
            return None


def get_cache_backend():
    """获取缓存后端类"""
    if settings.redis_url:
        logger.info("使用Redis作为缓存后端", redis_url=settings.redis_url)
        return RedisCache
    else:
        logger.info("使用内存作为缓存后端")
        return SimpleMemoryCache


def get_cache() -> Cache:
    """获取配置的缓存实例"""
    cache_backend = get_cache_backend()

    if settings.redis_url:
        # 使用 Redis 作为缓存后端
        cache = Cache(Cache.REDIS, endpoint=settings.redis_url,
                      serializer=CustomJsonSerializer())
    else:
        # 使用内存作为缓存后端
        cache = Cache(Cache.MEMORY, serializer=CustomJsonSerializer())

    return cache


def create_cache_key(prefix: str, *args, **kwargs) -> str:
    """创建缓存键"""
    # 将参数转换为字符串
    key_parts = [prefix]

    # 添加位置参数
    for arg in args:
        if isinstance(arg, (dict, list)):
            key_parts.append(json.dumps(arg, sort_keys=True))
        else:
            key_parts.append(str(arg))

    # 添加关键字参数
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.append(json.dumps(sorted_kwargs, sort_keys=True))

    # 创建完整的键
    full_key = "|".join(key_parts)

    # 如果键太长，使用哈希
    if len(full_key) > 200:
        hash_obj = hashlib.md5(full_key.encode())
        return f"{prefix}:hash:{hash_obj.hexdigest()}"

    return full_key


def cache_key_builder(func: Callable, *args, **kwargs) -> str:
    """为缓存装饰器构建键"""
    func_name = f"{func.__module__}.{func.__qualname__}"
    return create_cache_key(func_name, *args, **kwargs)


def finance_cached(ttl: Optional[int] = None) -> Callable:
    """
    财务数据缓存装饰器

    Args:
        ttl: 缓存过期时间(秒)，默认使用配置中的值
    """
    actual_ttl = ttl or settings.cache_ttl_seconds
    cache_backend = get_cache_backend()

    kwargs = {
        "ttl": actual_ttl,
        "cache": cache_backend,
        "serializer": CustomJsonSerializer(),
        "key_builder": cache_key_builder,
    }

    # 如果使用Redis，添加连接参数
    if settings.redis_url and cache_backend == RedisCache:
        kwargs["endpoint"] = settings.redis_url

    return cached(**kwargs)


async def clear_cache_pattern(pattern: str) -> int:
    """
    清除匹配模式的缓存

    Args:
        pattern: 要清除的缓存键模式

    Returns:
        清除的键数量
    """
    try:
        cache_instance = get_cache()

        if hasattr(cache_instance, 'clear'):
            # 对于内存缓存，清除所有
            await cache_instance.clear()
            logger.info("清除所有内存缓存")
            return 1
        else:
            # 对于Redis，需要使用具体的实现
            logger.warning("Redis缓存清除需要额外实现", pattern=pattern)
            return 0

    except Exception as e:
        logger.error("清除缓存失败", pattern=pattern, error=str(e))
        raise CacheError(f"清除缓存失败: {str(e)}")


async def get_cache_info() -> dict:
    """获取缓存信息"""
    try:
        info = {
            "backend": "redis" if settings.redis_url else "memory",
            "ttl_seconds": settings.cache_ttl_seconds,
        }

        if settings.redis_url:
            info["redis_url"] = settings.redis_url

        return info

    except Exception as e:
        logger.error("获取缓存信息失败", error=str(e))
        raise CacheError(f"获取缓存信息失败: {str(e)}")


async def get_cache_value(key: str) -> Any:
    """
    从缓存获取数据

    Args:
        key: 缓存键

    Returns:
        缓存的数据，如果不存在返回None
    """
    try:
        cache_instance = get_cache()
        result = await cache_instance.get(key)
        return result
    except Exception as e:
        logger.warning("获取缓存失败", key=key, error=str(e))
        return None


async def set_cache_value(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    设置缓存数据

    Args:
        key: 缓存键
        value: 要缓存的数据
        ttl: 过期时间(秒)，默认使用配置中的值

    Returns:
        是否设置成功
    """
    try:
        cache_instance = get_cache()
        actual_ttl = ttl or settings.cache_ttl_seconds
        await cache_instance.set(key, value, ttl=actual_ttl)
        return True
    except Exception as e:
        logger.warning("设置缓存失败", key=key, error=str(e))
        return False


# 预配置的缓存装饰器
quote_cache = finance_cached(ttl=60)  # 报价缓存1分钟
history_cache = finance_cached(ttl=3600)  # 历史数据缓存1小时
financial_cache = finance_cached(ttl=86400)  # 财务数据缓存1天
news_cache = finance_cached(ttl=1800)  # 新闻缓存30分钟
