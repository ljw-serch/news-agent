"""统计 / 热榜 / 趋势模型。"""

from __future__ import annotations

from pydantic import BaseModel

from typing import List

from app.schemas.news import NewsListItem


class OverviewResponse(BaseModel):
    total_news: int = 0
    today_news: int = 0
    week_news: int = 0
    month_news: int = 0
    total_views: int = 0
    today_views: int = 0
    total_favorites: int = 0
    total_categories: int = 0
    total_summaries: int = 0
    total_users: int | None = None
    active_users: int | None = None
    latest_publish_time: str | None = None
    latest_publish_title: str | None = None
    coverage_start: str | None = None


class TrendPoint(BaseModel):
    date: str
    news_count: int = 0
    view_count: int = 0


class TrendResponse(BaseModel):
    days: int
    points: list[TrendPoint]
    total_news: int = 0
    total_views: int = 0


class CategoryStat(BaseModel):
    id: int
    name: str
    news_count: int = 0
    total_views: int = 0
    favorite_count: int = 0


class AuthorStat(BaseModel):
    author: str
    news_count: int
    total_views: int


class PublishRangeResponse(BaseModel):
    start_date: str
    end_date: str
    count: int
    list: List[NewsListItem] = []
