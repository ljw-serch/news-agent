"""API 路由汇总。"""

from fastapi import APIRouter

from app.api import ai, auth, favorite, files, history, news, stats, user

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(user.router)
api_router.include_router(news.router)
api_router.include_router(favorite.router)
api_router.include_router(history.router)
api_router.include_router(stats.router)
api_router.include_router(ai.router)
api_router.include_router(files.router)
