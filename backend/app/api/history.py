"""浏览历史接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.history import HistoryAddRequest
from app.services import history_service

router = APIRouter(prefix="/history", tags=["浏览历史"])


@router.post("/add")
async def add_history(
    data: HistoryAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await history_service.add_history(db, current_user.id, data.news_id)
    return Response.success(message="已记录浏览历史", data=result)


@router.get("/list")
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await history_service.get_history_page(
        db, current_user.id, page, page_size
    )
    return Response.success(data=data)


@router.delete("/delete/{history_id}")
async def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    removed = await history_service.delete_history(db, current_user.id, history_id)
    if not removed:
        return Response.error(code=404, message="浏览记录不存在")
    return Response.success(message="删除成功")


@router.delete("/clear")
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await history_service.clear_history(db, current_user.id)
    return Response.success(message=f"已清空 {count} 条浏览记录")
