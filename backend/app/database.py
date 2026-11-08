"""异步数据库连接、建表、轻量迁移与演示数据初始化。"""

from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型共享的声明式基类。"""


async def get_db():
    """FastAPI 依赖：每个请求一个 AsyncSession。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """建表 -> 轻量迁移 -> 初始化演示账号/分类。

    项目已经存在 news_app 数据库时，不会破坏原有新闻数据；
    只会补齐 role / status / summary 等新字段。
    """
    # 确保模型已注册到 Base.metadata
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.begin() as conn:
        await _migrate(conn)

    async with AsyncSessionLocal() as session:
        await _seed(session)


async def _column_names(conn, table: str) -> list[str]:
    def _inspect(sync_conn):
        return [column["name"] for column in inspect(sync_conn).get_columns(table)]

    return await conn.run_sync(_inspect)


async def _migrate(conn) -> None:
    """给旧库补充新字段。"""
    user_columns = await _column_names(conn, "user")
    if "role" not in user_columns:
        await conn.execute(
            text(
                "ALTER TABLE `user` ADD COLUMN `role` VARCHAR(20) NOT NULL "
                "DEFAULT 'user' COMMENT '角色：admin-管理员，user-普通用户' AFTER `phone`"
            )
        )
    if "status" not in user_columns:
        await conn.execute(
            text(
                "ALTER TABLE `user` ADD COLUMN `status` TINYINT NOT NULL "
                "DEFAULT 1 COMMENT '状态：0-禁用，1-正常' AFTER `role`"
            )
        )

    news_columns = await _column_names(conn, "news")
    if "summary" not in news_columns:
        await conn.execute(
            text(
                "ALTER TABLE `news` ADD COLUMN `summary` TEXT NULL "
                "COMMENT 'AI 摘要' AFTER `content`"
            )
        )
    if "summary_time" not in news_columns:
        await conn.execute(
            text(
                "ALTER TABLE `news` ADD COLUMN `summary_time` DATETIME NULL "
                "COMMENT '摘要生成时间' AFTER `summary`"
            )
        )
    if "highlight" not in news_columns:
        await conn.execute(
            text(
                "ALTER TABLE `news` ADD COLUMN `highlight` VARCHAR(255) NULL "
                "COMMENT 'AI 提炼的一句话看点' AFTER `summary_time`"
            )
        )


async def _seed(session: AsyncSession) -> None:
    from app.models.news import Category
    from app.models.user import User
    from app.utils.password import hash_password, verify_password

    categories = [
        ("头条", 1),
        ("社会", 2),
        ("国内", 3),
        ("国际", 4),
        ("娱乐", 5),
        ("体育", 6),
        ("科技", 7),
        ("财经", 8),
    ]
    count = await session.scalar(select(Category.id).limit(1))
    if count is None:
        for name, sort_order in categories:
            session.add(Category(name=name, sort_order=sort_order))
        await session.commit()

    # 管理员账号
    admin = await session.scalar(select(User).where(User.username == "admin"))
    if admin is None:
        session.add(
            User(
                username="admin",
                password=hash_password("123456"),
                nickname="平台管理员",
                role="admin",
                status=1,
                bio="负责新闻与用户管理",
                gender="unknown",
            )
        )
    else:
        changed = False
        if admin.role != "admin":
            admin.role = "admin"
            changed = True
        if admin.status != 1:
            admin.status = 1
            changed = True
        # 兼容旧演示库：旧库 admin 密码是 123，统一成文档中的 123456
        try:
            if verify_password("123", admin.password):
                admin.password = hash_password("123456")
                changed = True
        except Exception:
            pass
        if changed:
            await session.commit()

    # 普通用户演示账号
    demo = await session.scalar(select(User).where(User.username == "user"))
    if demo is None:
        session.add(
            User(
                username="user",
                password=hash_password("123456"),
                nickname="新闻读者",
                role="user",
                status=1,
                bio="关注科技与财经资讯",
                gender="unknown",
            )
        )

    if session.new:
        await session.commit()


async def reset_db() -> None:
    """危险操作：仅供测试脚本清空并重建表。"""
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await init_db()


if __name__ == "__main__":
    asyncio.run(init_db())
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] database initialized")
