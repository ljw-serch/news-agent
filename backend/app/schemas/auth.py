"""登录 / 注册模型。"""

from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=3, max_length=72)
    nickname: str | None = Field(None, max_length=50)


class LoginResponse(BaseModel):
    token: str
    user: UserResponse
