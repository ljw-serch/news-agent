"""AI Agent 可调用的数据库工具。"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.models.user import User
from app.services import (
    hotspot_service,
    news_service,
    stats_service,
    summary_service,
)

logger = logging.getLogger("news-app.tools")

TOOL_LABELS = {
    "search_news": "检索新闻数据库",
    "get_hot_news": "汇总热榜",
    "get_news_detail": "读取新闻详情",
    "summarize_news": "生成 AI 摘要",
    "get_news_stats": "统计新闻数据",
    "get_publish_trend": "统计发布趋势",
    "list_categories": "读取新闻分类",
    "get_category_stats": "统计分类分布",
    "get_daily_digest": "生成新闻简报",
}

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "按关键词、分类、时间范围检索新闻数据库，返回标题、摘要、日期、阅读量。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "搜索关键词，可为空；为空时返回最新新闻",
                    },
                    "category_id": {
                        "type": "integer",
                        "description": "分类 ID，0 表示不限；可先调用 list_categories 获取",
                    },
                    "days": {
                        "type": "integer",
                        "description": "最近多少天内，0 表示不限",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回条数，1-10",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hot_news",
            "description": "汇总热榜，按阅读量、收藏数、发布时间综合计算热度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计窗口天数，0 表示全部时间",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "榜单条数，1-20",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_detail",
            "description": "根据新闻 ID 读取完整正文和已有摘要。",
            "parameters": {
                "type": "object",
                "properties": {
                    "news_id": {"type": "integer", "description": "新闻 ID"},
                },
                "required": ["news_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_news",
            "description": "对指定新闻生成/读取 AI 摘要与一句话看点。",
            "parameters": {
                "type": "object",
                "properties": {
                    "news_id": {"type": "integer", "description": "新闻 ID"},
                },
                "required": ["news_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news_stats",
            "description": "统计新闻总量、今日/近7天/近30天新发布数量、总阅读、收藏等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "趋势区间天数，默认 7",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_publish_trend",
            "description": "获取最近 N 天每天的新发布新闻数与阅读数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "天数，1-90",
                    },
                },
                "required": ["days"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "列出新闻分类及每个分类的新闻数量。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_stats",
            "description": "统计各分类的新闻数、阅读量与收藏量。",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_digest",
            "description": "汇总最近新闻并生成新闻简报（含重点新闻与趋势观察）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "统计窗口天数，0 表示最近新闻",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "汇总条数，1-20",
                    },
                },
            },
        },
    },
]


async def _tool_search_news(db: AsyncSession, args: dict) -> Any:
    rows = await news_service.search_news_for_ai(
        db,
        keywords=str(args.get("keywords") or ""),
        category_id=int(args.get("category_id") or 0) or None,
        days=int(args.get("days") or 0),
        limit=int(args.get("limit") or 5),
    )
    return {"count": len(rows), "news": rows}


async def _tool_hot_news(db: AsyncSession, args: dict) -> Any:
    hot = await hotspot_service.get_hot_news(
        db,
        days=int(args.get("days") or 0),
        limit=int(args.get("limit") or 10),
    )
    return {
        "days": hot.days,
        "items": [
            {
                "rank": item.rank,
                "id": item.id,
                "title": item.title,
                "category": item.category_name,
                "views": item.views,
                "favorite_count": item.favorite_count,
                "score": item.score,
                "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M")
                if item.publish_time
                else None,
                "summary": item.summary or item.description,
            }
            for item in hot.list
        ],
    }


async def _tool_news_detail(db: AsyncSession, args: dict) -> Any:
    detail = await news_service.get_news_brief(db, int(args.get("news_id") or 0))
    if detail is None:
        raise BusinessException(message="新闻不存在", code=404)
    return detail


async def _tool_summarize(db: AsyncSession, args: dict) -> Any:
    result = await summary_service.summarize_news(
        db, int(args.get("news_id") or 0)
    )
    return {
        "news_id": result.news_id,
        "summary": result.summary,
        "highlight": result.highlight,
        "cached": result.cached,
    }


async def _tool_stats(db: AsyncSession, user: User, args: dict) -> Any:
    overview = await stats_service.get_overview(db, is_admin=user.is_admin)
    trend = await stats_service.get_trend(db, int(args.get("days") or 7))
    return {
        "overview": overview.model_dump(mode="json"),
        "trend": {
            "days": trend.days,
            "total_news": trend.total_news,
            "total_views": trend.total_views,
            "points": [point.model_dump() for point in trend.points],
        },
    }


async def _tool_trend(db: AsyncSession, args: dict) -> Any:
    trend = await stats_service.get_trend(db, int(args.get("days") or 7))
    return trend.model_dump(mode="json")


async def _tool_categories(db: AsyncSession, args: dict) -> Any:
    items = await news_service.get_categories(db)
    return {
        "categories": [
            {
                "id": item.id,
                "name": item.name,
                "news_count": item.news_count,
            }
            for item in items
        ]
    }


async def _tool_category_stats(db: AsyncSession, args: dict) -> Any:
    items = await stats_service.get_category_stats(db)
    return {"categories": [item.model_dump() for item in items]}


async def _tool_digest(db: AsyncSession, args: dict) -> Any:
    result = await summary_service.daily_digest(
        db,
        days=int(args.get("days") or 0),
        limit=int(args.get("limit") or 8),
    )
    return {"content": result.content[:4000]}


async def execute_tool(
    db: AsyncSession, user: User, name: str, arguments: str | dict
) -> str:
    """执行工具，返回给模型看的 JSON 字符串。"""
    try:
        if isinstance(arguments, str):
            args = json.loads(arguments or "{}")
        else:
            args = arguments or {}
        if not isinstance(args, dict):
            raise ValueError("参数必须是对象")

        if name == "search_news":
            data = await _tool_search_news(db, args)
        elif name == "get_hot_news":
            data = await _tool_hot_news(db, args)
        elif name == "get_news_detail":
            data = await _tool_news_detail(db, args)
        elif name == "summarize_news":
            data = await _tool_summarize(db, args)
        elif name == "get_news_stats":
            data = await _tool_stats(db, user, args)
        elif name == "get_publish_trend":
            data = await _tool_trend(db, args)
        elif name == "list_categories":
            data = await _tool_categories(db, args)
        elif name == "get_category_stats":
            data = await _tool_category_stats(db, args)
        elif name == "get_daily_digest":
            data = await _tool_digest(db, args)
        else:
            return json.dumps(
                {"error": f"未知工具：{name}"}, ensure_ascii=False
            )

        return json.dumps(data, ensure_ascii=False, default=str)
    except BusinessException as exc:
        return json.dumps({"error": exc.message}, ensure_ascii=False)
    except Exception as exc:
        logger.exception("tool %s failed: %s", name, exc)
        return json.dumps(
            {"error": f"工具执行失败：{exc}"}, ensure_ascii=False
        )
