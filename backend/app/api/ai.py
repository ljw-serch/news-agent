"""AI 对话、摘要、简报、热榜解读接口。"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.ai import (
    AIStatusResponse,
    ChatMessage,
    ChatRequest,
    DigestRequest,
    HotAnalysisRequest,
    SummaryRequest,
)
from app.services import agent_service, ai_service, chat_service, summary_service

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/status")
async def ai_status():
    enabled = ai_service.is_enabled()
    data = AIStatusResponse(
        enabled=enabled,
        model=settings.LLM_MODEL,
        mode="llm" if enabled else "local",
        base_url=settings.LLM_BASE_URL,
    )
    return Response.success(data=data)


@router.post("/chat")
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await agent_service.run_agent(db, current_user, data)
    return Response.success(
        data=ChatMessage(role="assistant", content=content)
    )


def _sse_line(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async def event_gen():
        async for event in agent_service.stream_agent(db, current_user, data):
            yield _sse_line(event)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def chat_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await chat_service.get_chat_page(
        db, current_user.id, page, page_size
    )
    return Response.success(data=data)


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await chat_service.clear_chat(db, current_user.id)
    return Response.success(message=f"已清空 {count} 条对话记录")


@router.post("/digest")
async def digest(
    data: DigestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await summary_service.daily_digest(
        db, days=data.days, limit=data.limit
    )
    return Response.success(data=result)


@router.post("/hot-analysis")
async def hot_analysis(
    data: HotAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await summary_service.hot_analysis(
        db, days=data.days, limit=data.limit
    )
    return Response.success(data=result)


@router.post("/summary")
async def summarize(
    data: SummaryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await summary_service.summarize_news(
        db, data.news_id, force=data.force
    )
    return Response.success(message="摘要生成成功", data=result)


@router.post("/batch-summary")
async def batch_summary(
    limit: int = Query(5, ge=1, le=30),
    force: bool = False,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await summary_service.batch_summarize(
        db, limit=limit, force=force
    )
    return Response.success(message="批量摘要完成", data=result)
