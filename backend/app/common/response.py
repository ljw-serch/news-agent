"""统一响应结构。"""

from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Response(BaseModel):
    """统一封装的返回格式。"""

    code: int = 200
    message: str = "请求成功"
    data: Any = None

    @classmethod
    def success(cls, message: str = "请求成功", data: Any = None):
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int = 500, message: str = "请求失败"):
        return cls(code=code, message=message, data=None)


class PageData(BaseModel, Generic[T]):
    """分页数据。"""

    list: List[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 10
    has_more: bool = False
