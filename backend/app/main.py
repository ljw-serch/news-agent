"""FastAPI 应用入口。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.common.exceptions import register_exception_handlers
from app.config import UPLOAD_DIR, settings
from app.database import engine, init_db
from app.utils.cache import close_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("news-app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("initializing database ...")
    await init_db()
    logger.info("database ready: %s", settings.DATABASE_URL.split("@")[-1])
    logger.info(
        "AI mode: %s (%s)",
        "LLM" if settings.LLM_API_KEY else "local fallback",
        settings.LLM_MODEL,
    )
    yield
    await close_cache()
    await engine.dispose()
    logger.info("application shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 新闻资讯平台：新闻浏览、AI 摘要、热榜、发布统计、用户与新闻管理",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传图片静态访问
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(api_router)

register_exception_handlers(app)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "api": "/api",
    }


@app.get("/health")
async def health():
    from sqlalchemy import text

    from app.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # pragma: no cover
        logger.warning("health db check failed: %s", exc)
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "ai": bool(settings.LLM_API_KEY),
    }
