"""新闻、分类、热榜模型。"""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int = 0
    news_count: int = 0


class NewsListItem(BaseModel):
    id: int
    title: str
    description: str | None = None
    image: str | None = None
    author: str | None = None
    category_id: int
    category_name: str | None = None
    views: int = 0
    publish_time: datetime | None = None
    summary: str | None = None
    highlight: str | None = None


class NewsDetailResponse(NewsListItem):
    content: str
    summary_time: datetime | None = None
    favorite_count: int = 0
    is_favorite: bool = False
    related: list[NewsListItem] = []


class NewsCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=2)
    description: str | None = Field(None, max_length=500)
    image: str | None = Field(None, max_length=255)
    author: str | None = Field(None, max_length=50)
    category_id: int
    publish_time: datetime | None = None
    views: int = 0


class NewsUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=255)
    content: str | None = Field(None, min_length=2)
    description: str | None = Field(None, max_length=500)
    image: str | None = Field(None, max_length=255)
    author: str | None = Field(None, max_length=50)
    category_id: int | None = None
    publish_time: datetime | None = None
    views: int | None = None


class HotNewsItem(NewsListItem):
    rank: int
    score: float
    favorite_count: int = 0
    hot_reason: str | None = None


class HotNewsResponse(BaseModel):
    days: int
    total: int
    list: List[HotNewsItem]
