"""收藏业务。"""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.response import PageData
from app.models.interaction import Favorite
from app.models.news import News
from app.schemas.favorite import FavoriteItem
from app.services.news_service import _to_list_item
from app.utils.cache import cache_delete_prefix


async def is_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    return (
        await db.scalar(
            select(Favorite.id).where(
                Favorite.user_id == user_id, Favorite.news_id == news_id
            )
        )
        is not None
    )


async def add_favorite(
    db: AsyncSession, user_id: int, news_id: int
) -> FavoriteItem:
    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)
    if await is_favorite(db, user_id, news_id):
        raise BusinessException(message="已经收藏过该新闻")

    favorite = Favorite(user_id=user_id, news_id=news_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    await cache_delete_prefix("news:hot:")
    await cache_delete_prefix("stats:")
    return FavoriteItem(
        favorite_id=favorite.id,
        favorite_time=favorite.created_at,
        news=_to_list_item(news),
    )


async def remove_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    result = await db.execute(
        delete(Favorite).where(
            Favorite.user_id == user_id, Favorite.news_id == news_id
        )
    )
    await db.commit()
    await cache_delete_prefix("news:hot:")
    await cache_delete_prefix("stats:")
    return bool(result.rowcount)


async def clear_favorites(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(delete(Favorite).where(Favorite.user_id == user_id))
    await db.commit()
    await cache_delete_prefix("news:hot:")
    await cache_delete_prefix("stats:")
    return int(result.rowcount or 0)


async def get_favorite_page(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
) -> PageData[FavoriteItem]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    total = int(
        await db.scalar(
            select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
        )
        or 0
    )
    stmt = (
        select(Favorite)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.scalars(stmt)).all()
    items = [
        FavoriteItem(
            favorite_id=row.id,
            favorite_time=row.created_at,
            news=_to_list_item(row.news),
        )
        for row in rows
        if row.news is not None
    ]
    return PageData(
        list=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )
