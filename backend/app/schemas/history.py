"""浏览历史模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.news import NewsListItem


class HistoryAddRequest(BaseModel):
    news_id: int


class HistoryItem(BaseModel):
    history_id: int
    view_time: datetime
    news: NewsListItem
