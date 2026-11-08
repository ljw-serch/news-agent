"""Redis 异步缓存。

设计原则：缓存是加速项，不是单点依赖。
Redis 未启动或连接失败时自动降级为「无缓存」，接口仍可正常返回。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger("news-app.cache")

_client: aioredis.Redis | None = None
_disabled = False
_lock = asyncio.Lock()


async def get_redis() -> aioredis.Redis | None:
    global _client, _disabled
    if not settings.REDIS_ENABLED or _disabled:
        return None
    if _client is not None:
        return _client
    async with _lock:
        if _client is not None:
            return _client
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            await client.ping()
            _client = client
            logger.info("redis connected: %s", settings.REDIS_URL)
        except Exception as exc:  # pragma: no cover - 取决于本地环境
            _disabled = True
            logger.warning("redis unavailable, cache disabled: %s", exc)
            return None
    return _client


async def close_cache() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:
            pass
        _client = None


async def cache_get_json(key: str) -> Any | None:
    client = await get_redis()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("cache get failed [%s]: %s", key, exc)
        return None


async def cache_set_json(key: str, value: Any, expire: int = 300) -> None:
    client = await get_redis()
    if client is None:
        return
    try:
        await client.setex(key, expire, json.dumps(value, ensure_ascii=False, default=str))
    except Exception as exc:
        logger.debug("cache set failed [%s]: %s", key, exc)


async def cache_delete(*keys: str) -> None:
    client = await get_redis()
    if client is None or not keys:
        return
    try:
        await client.delete(*keys)
    except Exception as exc:
        logger.debug("cache delete failed: %s", exc)


async def cache_delete_prefix(prefix: str) -> None:
    """删除某个前缀下的缓存（新闻增删改后失效热榜/统计）。"""
    client = await get_redis()
    if client is None:
        return
    try:
        keys = [key async for key in client.scan_iter(match=f"{prefix}*", count=200)]
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.debug("cache delete prefix failed [%s]: %s", prefix, exc)


async def invalidate_news_cache() -> None:
    """新闻数据变更后统一清理相关缓存。"""
    await cache_delete_prefix("news:")
    await cache_delete_prefix("stats:")
