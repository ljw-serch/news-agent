"""登录 / 注册业务。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.user import UserResponse
from app.utils.jwt import create_access_token
from app.utils.password import hash_password, verify_password


async def login(db: AsyncSession, data: LoginRequest) -> LoginResponse:
    user = await db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password):
        raise BusinessException(message="账号或密码错误")

    if user.status != 1:
        raise BusinessException(message="账号已被禁用，请联系管理员", code=403)

    token = create_access_token(user)
    return LoginResponse(token=token, user=UserResponse.model_validate(user))


async def register(db: AsyncSession, data: RegisterRequest) -> LoginResponse:
    exists = await db.scalar(select(User.id).where(User.username == data.username))
    if exists:
        raise BusinessException(message="用户名已存在")

    user = User(
        username=data.username,
        password=hash_password(data.password),
        nickname=(data.nickname or data.username).strip(),
        role="user",
        status=1,
        gender="unknown",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user)
    return LoginResponse(token=token, user=UserResponse.model_validate(user))
