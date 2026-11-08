"""用户相关请求/响应模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    avatar: str | None = None
    gender: str | None = None
    bio: str | None = None
    phone: str | None = None
    role: str = "user"
    status: int = 1
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    nickname: str | None = Field(None, max_length=50)
    avatar: str | None = Field(None, max_length=255)
    gender: str | None = Field(None, max_length=10)
    bio: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=20)


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field("123456", min_length=3, max_length=72)
    nickname: str | None = Field(None, max_length=50)
    role: str = "user"
    status: int = 1
    phone: str | None = Field(None, max_length=20)
    avatar: str | None = Field(None, max_length=255)
    gender: str | None = Field(None, max_length=10)
    bio: str | None = Field(None, max_length=500)


class UserAdminUpdateRequest(BaseModel):
    nickname: str | None = Field(None, max_length=50)
    avatar: str | None = Field(None, max_length=255)
    gender: str | None = Field(None, max_length=10)
    bio: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=20)
    role: str | None = None
    status: int | None = None
    password: str | None = Field(None, min_length=3, max_length=72)


class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=3, max_length=72)
