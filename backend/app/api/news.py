"""新闻接口：公开浏览 + 管理员增删改 + AI 摘要。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user, get_optional_user
from app.models.user import User
from app.schemas.news import NewsCreateRequest, NewsUpdateRequest
from app.services import hotspot_service, news_service, summary_service

router = APIRouter(prefix="/news", tags=["新闻"])


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    data = await news_service.get_categories(db)
    return Response.success(message="获取分类成功", data=data)


@router.get("/list")
async def get_news_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category_id: int | None = None,
    keywords: str | None = None,
    author: str | None = None,
    order: str = Query("latest", pattern="^(latest|hot)$"),
    db: AsyncSession = Depends(get_db),
):
    data = await news_service.get_news_page(
        db,
        page=page,
        page_size=page_size,
        category_id=category_id,
        keywords=keywords,
        author=author,
        order=order,
    )
    return Response.success(message="获取新闻列表成功", data=data)


@router.get("/hot")
async def get_hot_news(
    days: int = Query(0, ge=0, le=3650),
    limit: int = Query(10, ge=1, le=50),
    category_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    data = await hotspot_service.get_hot_news(
        db, days=days, limit=limit, category_id=category_id
    )
    return Response.success(message="获取热榜成功", data=data)


@router.get("/search")
async def search_news(
    keywords: str = Query("", max_length=50),
    category_id: int | None = None,
    days: int = Query(0, ge=0, le=3650),
    limit: int = Query(10, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    data = await news_service.search_news_for_ai(
        db, keywords=keywords, category_id=category_id, days=days, limit=limit
    )
    return Response.success(message="搜索成功", data=data)


@router.post("/summaries/batch")
async def batch_summaries(
    limit: int = Query(5, ge=1, le=30),
    force: bool = False,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await summary_service.batch_summarize(db, limit=limit, force=force)
    return Response.success(message="批量摘要完成", data=data)


@router.get("/{news_id}")
async def get_news_detail(
    news_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    data = await news_service.get_news_detail(db, news_id, current_user=current_user)
    return Response.success(data=data)


@router.get("/{news_id}/summary")
async def get_news_summary(
    news_id: int,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    from app.common.exceptions import BusinessException
    from app.models.news import News

    news = await db.scalar(select(News).where(News.id == news_id))
    if news is None:
        raise BusinessException(message="新闻不存在", code=404)
    return Response.success(
        data={
            "news_id": news.id,
            "summary": news.summary,
            "highlight": news.highlight,
            "summary_time": news.summary_time,
        }
    )


@router.post("/{news_id}/summary")
async def generate_news_summary(
    news_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await summary_service.summarize_news(db, news_id, force=force)
    return Response.success(message="摘要生成成功", data=data)


@router.post("")
async def create_news(
    data: NewsCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await news_service.create_news(db, data)
    return Response.success(message="新闻创建成功", data=result)


@router.put("/{news_id}")
async def update_news(
    news_id: int,
    data: NewsUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await news_service.update_news(db, news_id, data)
    return Response.success(message="新闻已更新", data=result)


@router.delete("/{news_id}")
async def delete_news(
    news_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await news_service.delete_news(db, news_id)
    return Response.success(message="新闻已删除")
