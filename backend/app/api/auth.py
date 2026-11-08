"""认证接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.login(db, data)
    return Response.success(message="登录成功", data=result)


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.register(db, data)
    return Response.success(message="注册成功", data=result)


@router.post("/logout")
async def logout():
    return Response.success(message="退出成功")
