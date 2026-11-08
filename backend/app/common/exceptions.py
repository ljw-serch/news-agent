"""业务异常与全局异常处理器。"""

from __future__ import annotations

import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.common.response import Response

logger = logging.getLogger("news-app")


class BusinessException(Exception):
    """可预期的业务异常。"""

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)


async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content=Response.error(code=exc.code, message=exc.message).model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=Response.error(code=exc.status_code, message=str(exc.detail)).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        first = errors[0]
        location = ".".join(str(item) for item in first.get("loc", []) if item != "body")
        message = f"请求参数错误：{location} {first.get('msg', '')}".strip()
    else:
        message = "请求参数校验错误"
    return JSONResponse(
        status_code=422,
        content=Response.error(code=422, message=message).model_dump(),
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("integrity error: %s", exc)
    message = "数据约束冲突，请检查输入"
    detail = str(exc.orig)
    if "username_UNIQUE" in detail or "Duplicate entry" in detail:
        if "username" in detail:
            message = "用户名已存在"
        elif "phone" in detail:
            message = "手机号已存在"
        elif "user_news_unique" in detail:
            message = "已经收藏过该新闻"
    return JSONResponse(
        status_code=400,
        content=Response.error(code=400, message=message).model_dump(),
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("database error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=Response.error(code=500, message="数据库操作失败，请稍后重试").model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=Response.error(code=500, message="服务器内部错误").model_dump(),
    )


def register_exception_handlers(app):
    """注册异常处理器：具体在前，兜底在后。"""
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)
