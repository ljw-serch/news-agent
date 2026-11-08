"""AI 对话记录持久化。"""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import PageData
from app.models.interaction import AIChat
from app.schemas.ai import ChatHistoryItem


async def save_chat(
    db: AsyncSession, user_id: int, message: str, response: str
) -> AIChat:
    record = AIChat(user_id=user_id, message=message[:6000], response=response[:12000])
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_chat_page(
    db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
) -> PageData[ChatHistoryItem]:
    page = max(page, 1)
    page_size = max(min(page_size, 50), 1)
    total = int(
        await db.scalar(
            select(func.count(AIChat.id)).where(AIChat.user_id == user_id)
        )
        or 0
    )
    stmt = (
        select(AIChat)
        .where(AIChat.user_id == user_id)
        .order_by(AIChat.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.scalars(stmt)).all()
    items = [
        ChatHistoryItem(
            id=row.id,
            message=row.message,
            response=row.response,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return PageData(
        list=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


async def clear_chat(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(delete(AIChat).where(AIChat.user_id == user_id))
    await db.commit()
    return int(result.rowcount or 0)
