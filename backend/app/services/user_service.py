"""用户管理业务。"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.common.response import PageData
from app.models.user import User
from app.schemas.user import (
    PasswordUpdateRequest,
    UserAdminUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.cache import cache_delete_prefix
from app.utils.password import hash_password, verify_password

VALID_ROLES = {"admin", "user"}


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


async def _count_admins(db: AsyncSession) -> int:
    return int(
        await db.scalar(select(func.count(User.id)).where(User.role == "admin")) or 0
    )


async def get_user_info(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


async def update_user_info(
    db: AsyncSession, user: User, data: UserUpdateRequest
) -> UserResponse:
    payload = data.model_dump(exclude_unset=True, exclude_none=True)
    for field in ("nickname", "avatar", "gender", "bio", "phone"):
        if field in payload:
            setattr(user, field, _clean(payload[field]))
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


async def update_password(
    db: AsyncSession, user: User, data: PasswordUpdateRequest
) -> None:
    if not verify_password(data.old_password, user.password):
        raise BusinessException(message="原密码错误")
    if data.old_password == data.new_password:
        raise BusinessException(message="新密码不能与原密码相同")
    user.password = hash_password(data.new_password)
    await db.commit()


async def get_user_page_list(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    role: str | None = None,
    status: int | None = None,
) -> PageData[UserResponse]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)

    conditions = []
    if keywords:
        like = f"%{keywords.strip()}%"
        conditions.append(or_(User.username.ilike(like), User.nickname.ilike(like)))
    if role in VALID_ROLES:
        conditions.append(User.role == role)
    if status in (0, 1):
        conditions.append(User.status == status)

    base = select(User)
    count_stmt = select(func.count(User.id))
    for condition in conditions:
        base = base.where(condition)
        count_stmt = count_stmt.where(condition)

    total = int(await db.scalar(count_stmt) or 0)
    result = await db.scalars(
        base.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [UserResponse.model_validate(item) for item in result.all()]
    return PageData(
        list=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


async def create_user(db: AsyncSession, data: UserCreateRequest) -> UserResponse:
    if data.role not in VALID_ROLES:
        raise BusinessException(message="角色只能是 admin 或 user")
    username = data.username.strip()
    exists = await db.scalar(select(User.id).where(User.username == username))
    if exists:
        raise BusinessException(message="账号已存在")
    phone = _clean(data.phone)
    if phone:
        phone_exists = await db.scalar(select(User.id).where(User.phone == phone))
        if phone_exists:
            raise BusinessException(message="手机号已被使用")

    user = User(
        username=username,
        password=hash_password(data.password or "123456"),
        nickname=_clean(data.nickname) or username,
        role=data.role,
        status=1 if data.status not in (0, 1) else data.status,
        phone=phone,
        avatar=_clean(data.avatar),
        gender=_clean(data.gender) or "unknown",
        bio=_clean(data.bio),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await cache_delete_prefix("stats:")
    return UserResponse.model_validate(user)


async def update_user(
    db: AsyncSession,
    user_id: int,
    data: UserAdminUpdateRequest,
    current_user: User,
) -> UserResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise BusinessException(message="用户不存在", code=404)

    payload = data.model_dump(exclude_unset=True, exclude_none=True)

    new_role = payload.get("role")
    new_status = payload.get("status")
    if new_role is not None and new_role not in VALID_ROLES:
        raise BusinessException(message="角色只能是 admin 或 user")
    if new_status is not None and new_status not in (0, 1):
        raise BusinessException(message="状态只能是 0 或 1")

    if user.id == current_user.id:
        if new_status == 0:
            raise BusinessException(message="不能禁用当前登录的账号")
        if new_role is not None and new_role != "admin":
            raise BusinessException(message="不能取消当前登录账号的管理员身份")

    if user.role == "admin" and (
        (new_role is not None and new_role != "admin") or new_status == 0
    ):
        if await _count_admins(db) <= 1:
            raise BusinessException(message="系统至少需要保留一名管理员")

    if "password" in payload and payload["password"]:
        user.password = hash_password(payload.pop("password"))
    else:
        payload.pop("password", None)

    for field in ("nickname", "avatar", "gender", "bio", "phone"):
        if field in payload:
            setattr(user, field, _clean(payload[field]))
    if new_role is not None:
        user.role = new_role
    if new_status is not None:
        user.status = new_status

    await db.commit()
    await db.refresh(user)
    await cache_delete_prefix("stats:")
    return UserResponse.model_validate(user)


async def delete_user(db: AsyncSession, user_id: int, current_user: User) -> None:
    if user_id == current_user.id:
        raise BusinessException(message="不能删除当前登录的账号")
    user = await db.get(User, user_id)
    if user is None:
        raise BusinessException(message="用户不存在", code=404)
    if user.role == "admin" and await _count_admins(db) <= 1:
        raise BusinessException(message="系统至少需要保留一名管理员")
    await db.delete(user)
    await db.commit()
    await cache_delete_prefix("stats:")
