"""新闻发布统计、趋势、分类与作者统计。"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.interaction import Favorite, History
from app.models.news import Category, News
from app.models.user import User
from app.schemas.news import NewsListItem
from app.schemas.stats import (
    AuthorStat,
    CategoryStat,
    OverviewResponse,
    PublishRangeResponse,
    TrendPoint,
    TrendResponse,
)
from app.services.news_service import _to_list_item
from app.utils.cache import cache_get_json, cache_set_json


def _today_start() -> datetime:
    return datetime.combine(date.today(), time.min)


async def get_overview(
    db: AsyncSession, is_admin: bool = False
) -> OverviewResponse:
    cache_key = f"stats:overview:{'admin' if is_admin else 'user'}"
    cached = await cache_get_json(cache_key)
    if cached:
        return OverviewResponse(**cached)

    today_start = _today_start()
    week_start = today_start - timedelta(days=6)
    month_start = today_start - timedelta(days=29)

    total_news = int(await db.scalar(select(func.count(News.id))) or 0)
    total_views = int(await db.scalar(select(func.coalesce(func.sum(News.views), 0))) or 0)
    total_favorites = int(await db.scalar(select(func.count(Favorite.id))) or 0)
    total_categories = int(await db.scalar(select(func.count(Category.id))) or 0)
    total_summaries = int(
        await db.scalar(
            select(func.count(News.id)).where(News.summary.is_not(None))
        )
        or 0
    )
    today_news = int(
        await db.scalar(
            select(func.count(News.id)).where(News.publish_time >= today_start)
        )
        or 0
    )
    week_news = int(
        await db.scalar(
            select(func.count(News.id)).where(News.publish_time >= week_start)
        )
        or 0
    )
    month_news = int(
        await db.scalar(
            select(func.count(News.id)).where(News.publish_time >= month_start)
        )
        or 0
    )
    today_views = int(
        await db.scalar(
            select(func.count(History.id)).where(History.view_time >= today_start)
        )
        or 0
    )

    latest_news = await db.scalar(
        select(News).order_by(News.publish_time.desc()).limit(1)
    )
    coverage_start = await db.scalar(select(func.min(News.publish_time)))

    data = OverviewResponse(
        total_news=total_news,
        today_news=today_news,
        week_news=week_news,
        month_news=month_news,
        total_views=total_views,
        today_views=today_views,
        total_favorites=total_favorites,
        total_categories=total_categories,
        total_summaries=total_summaries,
        latest_publish_time=latest_news.publish_time.isoformat(sep=" ", timespec="minutes")
        if latest_news and latest_news.publish_time
        else None,
        latest_publish_title=latest_news.title if latest_news else None,
        coverage_start=str(coverage_start) if coverage_start else None,
    )

    if is_admin:
        data.total_users = int(await db.scalar(select(func.count(User.id))) or 0)
        data.active_users = int(
            await db.scalar(
                select(func.count(User.id)).where(User.status == 1)
            )
            or 0
        )

    await cache_set_json(cache_key, data.model_dump(), settings.CACHE_TTL_STATS)
    return data


async def get_trend(db: AsyncSession, days: int = 7) -> TrendResponse:
    days = max(min(days, 365), 1)
    cache_key = f"stats:trend:{days}"
    cached = await cache_get_json(cache_key)
    if cached:
        return TrendResponse(**cached)

    start = _today_start() - timedelta(days=days - 1)

    news_stmt = (
        select(func.date(News.publish_time).label("day"), func.count(News.id))
        .where(News.publish_time >= start)
        .group_by(func.date(News.publish_time))
    )
    news_rows = (await db.execute(news_stmt)).all()
    news_map = {str(day): int(count) for day, count in news_rows}

    view_stmt = (
        select(func.date(History.view_time).label("day"), func.count(History.id))
        .where(History.view_time >= start)
        .group_by(func.date(History.view_time))
    )
    view_rows = (await db.execute(view_stmt)).all()
    view_map = {str(day): int(count) for day, count in view_rows}

    points: list[TrendPoint] = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).date()
        key = str(day)
        points.append(
            TrendPoint(
                date=key,
                news_count=news_map.get(key, 0),
                view_count=view_map.get(key, 0),
            )
        )

    data = TrendResponse(
        days=days,
        points=points,
        total_news=sum(point.news_count for point in points),
        total_views=sum(point.view_count for point in points),
    )
    await cache_set_json(cache_key, data.model_dump(), settings.CACHE_TTL_STATS)
    return data


async def get_category_stats(db: AsyncSession) -> list[CategoryStat]:
    cached = await cache_get_json("stats:categories")
    if cached:
        return [CategoryStat(**item) for item in cached]

    news_stmt = (
        select(
            News.category_id,
            func.count(News.id),
            func.coalesce(func.sum(News.views), 0),
        )
        .group_by(News.category_id)
    )
    news_rows = (await db.execute(news_stmt)).all()
    news_map = {
        category_id: (int(count), int(views))
        for category_id, count, views in news_rows
    }

    favorite_stmt = (
        select(News.category_id, func.count(Favorite.id))
        .join(Favorite, Favorite.news_id == News.id)
        .group_by(News.category_id)
    )
    favorite_rows = (await db.execute(favorite_stmt)).all()
    favorite_map = {category_id: int(count) for category_id, count in favorite_rows}

    categories = (
        await db.scalars(select(Category).order_by(Category.sort_order.asc()))
    ).all()
    items = []
    for category in categories:
        count, views = news_map.get(category.id, (0, 0))
        items.append(
            CategoryStat(
                id=category.id,
                name=category.name,
                news_count=count,
                total_views=views,
                favorite_count=favorite_map.get(category.id, 0),
            )
        )
    await cache_set_json(
        "stats:categories", [item.model_dump() for item in items], settings.CACHE_TTL_STATS
    )
    return items


async def get_author_stats(db: AsyncSession, limit: int = 10) -> list[AuthorStat]:
    limit = max(min(limit, 50), 1)
    stmt = (
        select(
            func.coalesce(News.author, "未知作者").label("author"),
            func.count(News.id).label("news_count"),
            func.coalesce(func.sum(News.views), 0).label("total_views"),
        )
        .group_by(func.coalesce(News.author, "未知作者"))
        .order_by(func.count(News.id).desc(), func.sum(News.views).desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [
        AuthorStat(
            author=author,
            news_count=int(news_count),
            total_views=int(total_views),
        )
        for author, news_count, total_views in rows
    ]


async def get_publish_range(
    db: AsyncSession, start_date: date, end_date: date
) -> PublishRangeResponse:
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date + timedelta(days=1), time.min)
    count = int(
        await db.scalar(
            select(func.count(News.id)).where(
                News.publish_time >= start_dt, News.publish_time < end_dt
            )
        )
        or 0
    )
    rows = (
        await db.scalars(
            select(News)
            .where(News.publish_time >= start_dt, News.publish_time < end_dt)
            .order_by(News.publish_time.desc())
            .limit(20)
        )
    ).all()
    items: list[NewsListItem] = [_to_list_item(item) for item in rows]
    return PublishRangeResponse(
        start_date=str(start_date),
        end_date=str(end_date),
        count=count,
        list=items,
    )
