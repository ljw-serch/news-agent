"""热榜：结合浏览量、收藏数、发布时间计算热度。"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.interaction import Favorite
from app.models.news import News
from app.schemas.news import HotNewsItem, HotNewsResponse
from app.utils.cache import cache_get_json, cache_set_json


def _hot_score(news: News, favorite_count: int, now: datetime, days: int) -> float:
    views = news.views or 0
    score = views * 0.6 + favorite_count * 40

    age_days = 0
    if news.publish_time:
        age_days = max((now - news.publish_time).days, 0)
    # 越新越有加成；旧闻仅靠阅读/收藏
    score += max(0, 30 - age_days) * 3
    # 指定时间窗口时，窗口内再给一点权重
    if days and age_days <= days:
        score += 20
    return round(score, 2)


def _hot_reason(news: News, favorite_count: int, days: int) -> str:
    parts = [f"阅读 {news.views or 0}"]
    if favorite_count:
        parts.append(f"收藏 {favorite_count}")
    if news.publish_time:
        parts.append(news.publish_time.strftime("%m-%d 发布"))
    if days:
        parts.append(f"近 {days} 天")
    return " · ".join(parts)


async def get_hot_news(
    db: AsyncSession,
    days: int = 0,
    limit: int = 10,
    category_id: int | None = None,
) -> HotNewsResponse:
    days = max(min(days, 3650), 0)
    limit = max(min(limit, 50), 1)
    cache_key = f"news:hot:{days}:{limit}:{category_id or 0}"
    cached = await cache_get_json(cache_key)
    if cached:
        return HotNewsResponse(**cached)

    stmt = select(News)
    if days > 0:
        stmt = stmt.where(
            News.publish_time >= datetime.now() - timedelta(days=days)
        )
    if category_id:
        stmt = stmt.where(News.category_id == category_id)
    # 先按浏览量取候选集，再在 Python 里综合收藏/时效计算
    stmt = stmt.order_by(News.views.desc(), News.publish_time.desc()).limit(
        max(limit * 6, 60)
    )
    candidates = (await db.scalars(stmt)).all()

    favorite_map: dict[int, int] = {}
    if candidates:
        ids = [news.id for news in candidates]
        fav_rows = (
            await db.execute(
                select(Favorite.news_id, func.count(Favorite.id))
                .where(Favorite.news_id.in_(ids))
                .group_by(Favorite.news_id)
            )
        ).all()
        favorite_map = {news_id: int(count) for news_id, count in fav_rows}

    now = datetime.now()
    scored = []
    for news in candidates:
        favorite_count = favorite_map.get(news.id, 0)
        scored.append(
            (
                _hot_score(news, favorite_count, now, days),
                favorite_count,
                news,
            )
        )
    scored.sort(key=lambda item: item[0], reverse=True)

    items: list[HotNewsItem] = []
    for rank, (score, favorite_count, news) in enumerate(scored[:limit], start=1):
        category = getattr(news, "category", None)
        items.append(
            HotNewsItem(
                id=news.id,
                title=news.title,
                description=news.description,
                image=news.image,
                author=news.author,
                category_id=news.category_id,
                category_name=category.name if category is not None else None,
                views=news.views or 0,
                publish_time=news.publish_time,
                summary=news.summary,
                highlight=news.highlight,
                rank=rank,
                score=score,
                favorite_count=favorite_count,
                hot_reason=_hot_reason(news, favorite_count, days),
            )
        )

    data = HotNewsResponse(days=days, total=len(items), list=items)
    await cache_set_json(
        cache_key, data.model_dump(mode="json"), settings.CACHE_TTL_HOT
    )
    return data
