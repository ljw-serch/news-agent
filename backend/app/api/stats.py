"""新闻统计数据接口。"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/overview")
async def overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await stats_service.get_overview(db, is_admin=current_user.is_admin)
    return Response.success(data=data)


@router.get("/trend")
async def trend(
    days: int = Query(7, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await stats_service.get_trend(db, days=days)
    return Response.success(data=data)


@router.get("/categories")
async def category_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await stats_service.get_category_stats(db)
    return Response.success(data=data)


@router.get("/authors")
async def author_stats(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await stats_service.get_author_stats(db, limit=limit)
    return Response.success(data=data)


@router.get("/publish-range")
async def publish_range(
    start_date: date | None = None,
    end_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=6))
    if start > end:
        start, end = end, start
    data = await stats_service.get_publish_range(db, start, end)
    return Response.success(data=data)
