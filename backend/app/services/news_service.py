"""新闻、分类业务（含 Redis 分类缓存）。"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.response import PageData
from app.config import settings
from app.models.interaction import Favorite
from app.models.news import Category, News
from app.models.user import User
from app.schemas.news import (
    CategoryResponse,
    NewsCreateRequest,
    NewsDetailResponse,
    NewsListItem,
    NewsUpdateRequest,
)
from app.utils.cache import cache_get_json, cache_set_json, invalidate_news_cache


def _to_list_item(news: News) -> NewsListItem:
    category = getattr(news, "category", None)
    return NewsListItem(
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
    )


async def get_categories(db: AsyncSession) -> list[CategoryResponse]:
    cached = await cache_get_json("news:categories")
    if cached:
        return [CategoryResponse(**item) for item in cached]

    stmt = (
        select(Category, func.count(News.id).label("news_count"))
        .outerjoin(News, News.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.sort_order.asc(), Category.id.asc())
    )
    rows = (await db.execute(stmt)).all()
    items = [
        CategoryResponse(
            id=category.id,
            name=category.name,
            sort_order=category.sort_order,
            news_count=int(news_count or 0),
        )
        for category, news_count in rows
    ]
    if items:
        await cache_set_json(
            "news:categories",
            [item.model_dump() for item in items],
            settings.CACHE_TTL_CATEGORY,
        )
    return items


async def get_news_page(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    category_id: int | None = None,
    keywords: str | None = None,
    author: str | None = None,
    order: str = "latest",
) -> PageData[NewsListItem]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)

    conditions = []
    if category_id:
        conditions.append(News.category_id == category_id)
    if keywords and keywords.strip():
        like = f"%{keywords.strip()}%"
        conditions.append(
            or_(
                News.title.ilike(like),
                News.description.ilike(like),
                News.content.ilike(like),
            )
        )
    if author and author.strip():
        conditions.append(News.author.ilike(f"%{author.strip()}%"))

    count_stmt = select(func.count(News.id))
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
    total = int(await db.scalar(count_stmt) or 0)

    stmt = select(News)
    for condition in conditions:
        stmt = stmt.where(condition)
    if order == "hot":
        stmt = stmt.order_by(News.views.desc(), News.publish_time.desc())
    else:
        stmt = stmt.order_by(News.publish_time.desc(), News.id.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    news_list = (await db.scalars(stmt)).all()
    items = [_to_list_item(item) for item in news_list]
    return PageData(
        list=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


async def _build_detail(
    db: AsyncSession,
    news_id: int,
    current_user: User | None = None,
    increment_views: bool = True,
) -> NewsDetailResponse:
    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)

    if increment_views:
        news.views = (news.views or 0) + 1
        await db.commit()
        # 重新查询，确保 joined 的 category 已加载（异步下避免惰性加载）
        news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)

    favorite_count = int(
        await db.scalar(
            select(func.count(Favorite.id)).where(Favorite.news_id == news_id)
        )
        or 0
    )
    is_favorite = False
    if current_user is not None:
        is_favorite = (
            await db.scalar(
                select(Favorite.id).where(
                    Favorite.user_id == current_user.id,
                    Favorite.news_id == news_id,
                )
            )
            is not None
        )

    related_stmt = (
        select(News)
        .where(News.category_id == news.category_id, News.id != news.id)
        .order_by(News.views.desc(), News.publish_time.desc())
        .limit(5)
    )
    related = [_to_list_item(item) for item in (await db.scalars(related_stmt)).all()]

    base = _to_list_item(news)
    return NewsDetailResponse(
        **base.model_dump(),
        content=news.content,
        summary_time=news.summary_time,
        favorite_count=favorite_count,
        is_favorite=is_favorite,
        related=related,
    )


async def get_news_detail(
    db: AsyncSession, news_id: int, current_user: User | None = None
) -> NewsDetailResponse:
    return await _build_detail(
        db, news_id, current_user=current_user, increment_views=True
    )


async def _ensure_category(db: AsyncSession, category_id: int) -> Category:
    category = await db.get(Category, category_id)
    if category is None:
        raise BusinessException(message="新闻分类不存在")
    return category


async def create_news(db: AsyncSession, data: NewsCreateRequest) -> NewsDetailResponse:
    await _ensure_category(db, data.category_id)
    content = data.content.strip()
    description = (data.description or "").strip() or (
        content[:120] + ("…" if len(content) > 120 else "")
    )
    news = News(
        title=data.title.strip(),
        description=description,
        content=content,
        image=(data.image or "").strip() or None,
        author=(data.author or "").strip() or "平台编辑",
        category_id=data.category_id,
        views=max(data.views or 0, 0),
        publish_time=data.publish_time or datetime.now(),
    )
    db.add(news)
    await db.commit()
    await db.refresh(news)
    await invalidate_news_cache()
    return await _build_detail(db, news.id, increment_views=False)


async def update_news(
    db: AsyncSession, news_id: int, data: NewsUpdateRequest
) -> NewsDetailResponse:
    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)

    payload = data.model_dump(exclude_unset=True)
    if "category_id" in payload and payload["category_id"] is not None:
        await _ensure_category(db, payload["category_id"])

    content_changed = False
    for field in ("title", "content", "description", "image", "author", "views"):
        if field in payload and payload[field] is not None:
            value = payload[field]
            if isinstance(value, str):
                value = value.strip()
            setattr(news, field, value)
            if field in ("title", "content"):
                content_changed = True
    if "category_id" in payload and payload["category_id"] is not None:
        news.category_id = payload["category_id"]
    if "publish_time" in payload and payload["publish_time"] is not None:
        news.publish_time = payload["publish_time"]

    if content_changed:
        # 正文变化后旧摘要失效，等待重新生成
        news.summary = None
        news.highlight = None
        news.summary_time = None

    await db.commit()
    await db.refresh(news)
    await invalidate_news_cache()
    return await _build_detail(db, news_id, increment_views=False)


async def delete_news(db: AsyncSession, news_id: int) -> None:
    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)
    await db.delete(news)
    await db.commit()
    await invalidate_news_cache()


async def search_news_for_ai(
    db: AsyncSession,
    keywords: str = "",
    category_id: int | None = None,
    days: int = 0,
    limit: int = 5,
) -> list[dict]:
    """供 AI 工具调用：返回紧凑的新闻数据。"""
    limit = max(min(limit, 20), 1)
    stmt = select(News)
    if keywords.strip():
        like = f"%{keywords.strip()}%"
        stmt = stmt.where(
            or_(
                News.title.ilike(like),
                News.description.ilike(like),
                News.content.ilike(like),
                News.author.ilike(like),
            )
        )
    if category_id:
        stmt = stmt.where(News.category_id == category_id)
    if days > 0:
        stmt = stmt.where(News.publish_time >= datetime.now() - timedelta(days=days))
    stmt = stmt.order_by(News.publish_time.desc()).limit(limit)

    rows = (await db.scalars(stmt)).all()
    result = []
    for item in rows:
        result.append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "summary": item.summary,
                "category": item.category.name if item.category else None,
                "author": item.author,
                "views": item.views,
                "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M")
                if item.publish_time
                else None,
                "content_excerpt": (item.content or "")[:500],
            }
        )
    return result


async def get_news_brief(db: AsyncSession, news_id: int) -> dict | None:
    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        return None
    return {
        "id": news.id,
        "title": news.title,
        "description": news.description,
        "content": news.content,
        "category": news.category.name if news.category else None,
        "author": news.author,
        "views": news.views,
        "publish_time": news.publish_time.strftime("%Y-%m-%d %H:%M")
        if news.publish_time
        else None,
        "summary": news.summary,
        "highlight": news.highlight,
    }
