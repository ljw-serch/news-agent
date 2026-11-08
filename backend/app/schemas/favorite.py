"""收藏模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.news import NewsListItem


class FavoriteCheckResponse(BaseModel):
    is_favorite: bool


class FavoriteAddRequest(BaseModel):
    news_id: int


class FavoriteItem(BaseModel):
    favorite_id: int
    favorite_time: datetime
    news: NewsListItem
