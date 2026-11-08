"""收藏接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.favorite import FavoriteAddRequest
from app.services import favorite_service

router = APIRouter(prefix="/favorite", tags=["收藏"])


@router.get("/check")
async def check_favorite(
    news_id: int = Query(..., alias="newsId"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    value = await favorite_service.is_favorite(db, current_user.id, news_id)
    return Response.success(message="检查收藏状态成功", data={"is_favorite": value})


@router.post("/add")
async def add_favorite(
    data: FavoriteAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await favorite_service.add_favorite(db, current_user.id, data.news_id)
    return Response.success(message="收藏成功", data=result)


@router.delete("/remove")
async def remove_favorite(
    news_id: int = Query(..., alias="newsId"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    removed = await favorite_service.remove_favorite(db, current_user.id, news_id)
    if not removed:
        return Response.error(code=404, message="收藏记录不存在")
    return Response.success(message="已取消收藏")


@router.get("/list")
async def get_favorite_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await favorite_service.get_favorite_page(
        db, current_user.id, page, page_size
    )
    return Response.success(data=data)


@router.delete("/clear")
async def clear_favorite(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await favorite_service.clear_favorites(db, current_user.id)
    return Response.success(message=f"已清空 {count} 条收藏")
