"""集中注册所有 ORM 模型，确保 Base.metadata 完整。"""

from app.models.interaction import AIChat, Favorite, History
from app.models.news import Category, News
from app.models.user import User, UserToken

__all__ = [
    "User",
    "UserToken",
    "Category",
    "News",
    "Favorite",
    "History",
    "AIChat",
]
