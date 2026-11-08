"""AI 对话 / 摘要 / 热榜解读模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = []


class SummaryRequest(BaseModel):
    news_id: int
    force: bool = False


class BatchSummaryRequest(BaseModel):
    limit: int = Field(5, ge=1, le=30)
    force: bool = False


class DigestRequest(BaseModel):
    days: int = Field(0, ge=0, le=3650)
    limit: int = Field(8, ge=1, le=20)


class HotAnalysisRequest(BaseModel):
    days: int = Field(0, ge=0, le=3650)
    limit: int = Field(10, ge=1, le=20)


class SummaryResponse(BaseModel):
    news_id: int
    summary: str
    highlight: str | None = None
    summary_time: datetime | None = None
    cached: bool = False


class ChatHistoryItem(BaseModel):
    id: int
    message: str
    response: str
    created_at: datetime


class AIStatusResponse(BaseModel):
    enabled: bool
    model: str
    mode: str
    base_url: str


class AIResultResponse(BaseModel):
    content: str
    cached: bool = False
