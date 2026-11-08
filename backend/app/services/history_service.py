"""浏览历史业务。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.response import PageData
from app.models.interaction import History
from app.models.news import News
from app.schemas.history import HistoryItem
from app.services.news_service import _to_list_item


async def add_history(db: AsyncSession, user_id: int, news_id: int) -> HistoryItem:
    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)

    record = await db.scalar(
        select(History).where(History.user_id == user_id, History.news_id == news_id)
    )
    if record is None:
        record = History(user_id=user_id, news_id=news_id)
        db.add(record)
    else:
        record.view_time = datetime.now()
    await db.commit()
    await db.refresh(record)
    return HistoryItem(
        history_id=record.id,
        view_time=record.view_time,
        news=_to_list_item(news),
    )


async def get_history_page(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
) -> PageData[HistoryItem]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    total = int(
        await db.scalar(
            select(func.count(History.id)).where(History.user_id == user_id)
        )
        or 0
    )
    stmt = (
        select(History)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.scalars(stmt)).all()
    items = [
        HistoryItem(
            history_id=row.id,
            view_time=row.view_time,
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


async def delete_history(db: AsyncSession, user_id: int, history_id: int) -> bool:
    result = await db.execute(
        delete(History).where(History.id == history_id, History.user_id == user_id)
    )
    await db.commit()
    return bool(result.rowcount)


async def clear_history(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(delete(History).where(History.user_id == user_id))
    await db.commit()
    return int(result.rowcount or 0)
