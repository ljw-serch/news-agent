"""用户接口：个人资料 + 管理员用户管理。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.user import (
    PasswordUpdateRequest,
    UserAdminUpdateRequest,
    UserCreateRequest,
    UserUpdateRequest,
)
from app.services import user_service

router = APIRouter(prefix="/user", tags=["用户"])


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return Response.success(data=await user_service.get_user_info(current_user))


@router.put("/me")
async def update_me(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await user_service.update_user_info(db, current_user, data)
    return Response.success(message="资料已更新", data=result)


@router.put("/password")
async def update_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await user_service.update_password(db, current_user, data)
    return Response.success(message="密码修改成功")


@router.get("/list")
async def get_user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keywords: str | None = None,
    role: str | None = None,
    status: int | None = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await user_service.get_user_page_list(
        db, page, page_size, keywords, role, status
    )
    return Response.success(data=result)


@router.post("")
async def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await user_service.create_user(db, data)
    return Response.success(message="用户创建成功", data=result)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserAdminUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await user_service.update_user(db, user_id, data, current_user)
    return Response.success(message="用户信息已更新", data=result)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await user_service.delete_user(db, user_id, current_user)
    return Response.success(message="用户已删除")
