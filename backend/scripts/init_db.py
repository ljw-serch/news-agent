"""初始化 / 迁移数据库。

用法（在 backend 目录下）：
    .venv/bin/python -m scripts.init_db
或：
    .venv/bin/python scripts/init_db.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select  # noqa: E402

from app.database import AsyncSessionLocal, init_db  # noqa: E402
from app.models.news import Category, News  # noqa: E402
from app.models.user import User  # noqa: E402


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        news_count = await session.scalar(select(func.count(News.id)))
        user_count = await session.scalar(select(func.count(User.id)))
        category_count = await session.scalar(select(func.count(Category.id)))
    print("数据库初始化完成")
    print(f"  新闻：{news_count} 条")
    print(f"  用户：{user_count} 个")
    print(f"  分类：{category_count} 个")
    print("  管理员：admin / 123456")
    print("  普通用户：user / 123456")


if __name__ == "__main__":
    asyncio.run(main())
