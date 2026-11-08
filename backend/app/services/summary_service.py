"""新闻摘要、日报、热榜解读（含无 Key 时的本地降级）。"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.config import settings
from app.models.news import News
from app.schemas.ai import AIResultResponse, SummaryResponse
from app.services import ai_service, hotspot_service
from app.utils.cache import (
    cache_get_json,
    cache_set_json,
    invalidate_news_cache,
)

logger = logging.getLogger("news-app.summary")


def _extractive_summary(title: str, content: str) -> tuple[str, str]:
    """不依赖大模型的抽取式摘要。"""
    clean = re.sub(r"\s+", " ", content or "").strip()
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[。！？!?])", clean)
        if len(item.strip()) >= 8
    ]
    if not sentences:
        sentences = [clean[:160] or title]

    core = "".join(sentences[:3])[:280]
    highlight = sentences[0][:60]
    keys = [item[:80] for item in sentences[1:4]]
    summary = f"**核心内容**：{core}"
    if keys:
        summary += "\n\n**关键信息**：\n" + "\n".join(f"- {item}" for item in keys)
    return summary, highlight


async def summarize_news(
    db: AsyncSession, news_id: int, force: bool = False
) -> SummaryResponse:
    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)

    if news.summary and not force:
        return SummaryResponse(
            news_id=news.id,
            summary=news.summary,
            highlight=news.highlight,
            summary_time=news.summary_time,
            cached=True,
        )

    summary, highlight = "", ""
    if ai_service.is_enabled():
        try:
            summary, highlight = await ai_service.summarize_text(
                news.title, news.content
            )
        except (ai_service.AIUnavailable, ai_service.AIError) as exc:
            logger.warning("AI summary failed, fallback to extractive: %s", exc)
    if not summary:
        summary, highlight = _extractive_summary(news.title, news.content)

    news.summary = summary
    news.highlight = highlight
    news.summary_time = datetime.now()
    await db.commit()
    await invalidate_news_cache()

    return SummaryResponse(
        news_id=news.id,
        summary=summary,
        highlight=highlight,
        summary_time=news.summary_time,
        cached=False,
    )


async def batch_summarize(
    db: AsyncSession, limit: int = 5, force: bool = False
) -> dict:
    limit = max(min(limit, 30), 1)
    stmt = select(News)
    if not force:
        stmt = stmt.where(News.summary.is_(None))
    stmt = stmt.order_by(News.publish_time.desc()).limit(limit)
    rows = (await db.scalars(stmt)).all()

    success, failed = [], []
    for news in rows:
        try:
            result = await summarize_news(db, news.id, force=force)
            success.append({"news_id": news.id, "title": news.title, "summary": result.summary})
        except Exception as exc:  # 单条失败不影响其他新闻
            logger.warning("batch summary failed for %s: %s", news.id, exc)
            failed.append({"news_id": news.id, "title": news.title, "error": str(exc)})

    return {
        "requested": len(rows),
        "success_count": len(success),
        "failed_count": len(failed),
        "success": success,
        "failed": failed,
    }


def _digest_fallback(news_items: list[dict], note: str = "") -> str:
    if not news_items:
        return "## 暂无新闻\n\n当前数据库还没有可汇总的新闻，请管理员先在「新闻管理」中新增。"

    category_count: dict[str, int] = {}
    for item in news_items:
        category = item.get("category") or "未分类"
        category_count[category] = category_count.get(category, 0) + 1
    category_text = "、".join(
        f"{name} {count} 条"
        for name, count in sorted(category_count.items(), key=lambda x: -x[1])
    )

    lines = ["## 今日速览"]
    if note:
        lines.append(note)
    lines.append(
        f"本次汇总覆盖 {len(news_items)} 条新闻，分布在 {len(category_count)} 个分类（{category_text}）。"
    )

    lines.append("\n## 重点新闻")
    for index, item in enumerate(news_items[:5], start=1):
        summary = (item.get("summary") or item.get("description") or "").strip()
        summary = re.sub(r"\s+", " ", summary)[:180]
        lines.append(
            f"{index}. **{item.get('title')}**"
            f"（{item.get('publish_time') or ''} / {item.get('category') or '未分类'}）"
            f"—— {summary}"
        )

    lines.append("\n## 趋势观察")
    top_category = max(category_count.items(), key=lambda x: x[1])[0]
    lines.append(f"- 报道最集中的分类是「{top_category}」。")
    views = sum(int(item.get("views") or 0) for item in news_items)
    lines.append(f"- 汇总新闻累计阅读量约 {views:,}。")
    lines.append("- 以上为本地规则摘要；配置 LLM_API_KEY 后可获得更具洞察力的 AI 综述。")
    return "\n".join(lines)


async def daily_digest(
    db: AsyncSession, days: int = 0, limit: int = 8
) -> AIResultResponse:
    days = max(min(days, 3650), 0)
    limit = max(min(limit, 20), 1)
    cache_key = f"news:digest:{date.today()}:{days}:{limit}"
    cached = await cache_get_json(cache_key)
    if cached:
        return AIResultResponse(content=cached.get("content", ""), cached=True)

    stmt = select(News)
    note = ""
    if days > 0:
        stmt = stmt.where(News.publish_time >= datetime.now() - timedelta(days=days))
    rows = (
        await db.scalars(stmt.order_by(News.publish_time.desc()).limit(limit))
    ).all()

    if not rows and days > 0:
        rows = (
            await db.scalars(
                select(News).order_by(News.publish_time.desc()).limit(limit)
            )
        ).all()
        note = f"近 {days} 天暂无新发布的新闻，以下为数据库中最近的 {len(rows)} 条。"

    items = [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "summary": item.summary,
            "content": item.content,
            "category": item.category.name if item.category else None,
            "author": item.author,
            "views": item.views,
            "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M")
            if item.publish_time
            else None,
        }
        for item in rows
    ]

    content = ""
    if items and ai_service.is_enabled():
        try:
            content = await ai_service.digest_text(items)
        except (ai_service.AIUnavailable, ai_service.AIError) as exc:
            logger.warning("AI digest failed, fallback: %s", exc)
    if not content:
        content = _digest_fallback(items, note)

    await cache_set_json(
        cache_key, {"content": content}, settings.CACHE_TTL_DIGEST
    )
    return AIResultResponse(content=content, cached=False)


def _hot_fallback(items: list[dict], days: int) -> str:
    if not items:
        return "## 暂无热榜数据\n\n当前时间窗口内没有新闻，试着扩大统计范围或先发布新闻。"

    window = f"近 {days} 天" if days else "全部时间"
    total_views = sum(int(item.get("views") or 0) for item in items)
    total_fav = sum(int(item.get("favorite_count") or 0) for item in items)
    category_count: dict[str, int] = {}
    for item in items:
        category = item.get("category_name") or "未分类"
        category_count[category] = category_count.get(category, 0) + 1

    lines = ["## 热榜概览"]
    lines.append(
        f"{window}内共 {len(items)} 条新闻上榜，累计阅读 {total_views:,}，收藏 {total_fav}。"
    )
    lines.append("\n## 榜单解读")
    for item in items[:10]:
        lines.append(
            f"{item.get('rank')}. **{item.get('title')}**"
            f"（{item.get('category_name') or '未分类'}）"
            f"—— 阅读 {item.get('views', 0):,}，收藏 {item.get('favorite_count', 0)}，"
            f"热度 {item.get('score', 0)}"
        )
    lines.append("\n## 话题聚类")
    for name, count in sorted(category_count.items(), key=lambda x: -x[1]):
        lines.append(f"- {name}：{count} 条上榜")
    lines.append("\n## 阅读建议")
    lines.append("- 优先阅读榜首新闻，并结合同一分类下的相关报道交叉验证。")
    lines.append("- 配置 LLM_API_KEY 后，可获得 AI 对热榜话题与趋势的深度解读。")
    return "\n".join(lines)


async def hot_analysis(
    db: AsyncSession, days: int = 0, limit: int = 10
) -> AIResultResponse:
    days = max(min(days, 3650), 0)
    limit = max(min(limit, 20), 1)
    cache_key = f"news:hot-analysis:{days}:{limit}"
    cached = await cache_get_json(cache_key)
    if cached:
        return AIResultResponse(content=cached.get("content", ""), cached=True)

    hot = await hotspot_service.get_hot_news(db, days=days, limit=limit)
    items = [item.model_dump(mode="json") for item in hot.list]

    content = ""
    if items and ai_service.is_enabled():
        try:
            content = await ai_service.hot_analysis_text(items, days)
        except (ai_service.AIUnavailable, ai_service.AIError) as exc:
            logger.warning("AI hot analysis failed, fallback: %s", exc)
    if not content:
        content = _hot_fallback(items, days)

    await cache_set_json(
        cache_key, {"content": content}, settings.CACHE_TTL_DIGEST
    )
    return AIResultResponse(content=content, cached=False)
