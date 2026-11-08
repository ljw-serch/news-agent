"""新闻 Agent：工具调用 + SSE 流式输出 + 无 Key 的本地降级。"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.ai import ChatMessage, ChatRequest
from app.services import (
    agent_tools,
    ai_service,
    chat_service,
    hotspot_service,
    news_service,
    stats_service,
    summary_service,
)

logger = logging.getLogger("news-app.agent")

MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """你是「AI 新闻资讯平台」的新闻智能助手，面向普通读者提供新闻问答、摘要、热榜与数据统计服务。

## 工作原则
1. **所有回答只能使用从数据库查询到的内容，严禁使用外部知识、记忆、模型自带知识编造任何新闻、数字、事实。**
2. 任何涉及新闻、列表、热榜、数量、趋势、摘要等问题，必须调用工具查询数据库。
3. 如果数据库/工具没有返回结果，直接如实回复：「数据库中没有找到相关新闻」，不要自己补充、不要猜测。
4. 引用新闻时写出：「标题（发布日期）」，必要时附上新闻 ID，站内详情页为 /manager/news/{id}。
5. 摘要忠于原文，不能添加原文不存在的内容。
6. 普通用户只可查询。
7. 使用中文 Markdown 回答，先给结论，再给要点，不要输出 JSON。

## 降级说明
如果工具没有返回结果，如实说明「数据库中没有找到相关新闻」，并给出可执行的搜索建议，不要编造。
"""


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _build_history(data: ChatRequest) -> list[dict]:
    history: list[dict] = []
    for message in (data.messages or [])[-16:]:
        content = (message.content or "").strip()
        if message.role in ("user", "assistant") and content:
            history.append({"role": message.role, "content": content})
    if not history:
        raise BusinessException(message="请输入您要对话的内容")
    return history


def _system_message(user: User) -> dict:
    role_label = "管理员" if user.is_admin else "普通用户"
    return {
        "role": "system",
        "content": (
            SYSTEM_PROMPT
            + f"\n当前用户：{user.nickname or user.username}（{role_label}）"
            + f"\n当前时间：{_now_text()}"
            + "\n数据库覆盖的新闻时间可能早于当前时间，统计时请以工具返回的真实数据为准。"
        ),
    }


async def _persist(db: AsyncSession, user: User, question: str, answer: str) -> None:
    if not question.strip() or not answer.strip():
        return
    try:
        await chat_service.save_chat(db, user.id, question, answer.strip())
    except Exception as exc:  # 聊天记录失败不影响回答
        logger.warning("save chat failed: %s", exc)


def _last_question(history: list[dict]) -> str:
    for item in reversed(history):
        if item["role"] == "user":
            return item["content"]
    return ""


# ---------------------------------------------------------------------------
# 本地降级：不依赖大模型也能查库、汇总热榜、统计与摘要
# ---------------------------------------------------------------------------


def _format_hot(hot) -> str:
    if not hot.list:
        return "当前时间窗口内没有可汇总的新闻，试试放宽时间范围。"
    lines = [f"## {('近 ' + str(hot.days) + ' 天') if hot.days else '全部时间'}热榜 TOP {len(hot.list)}", ""]
    for item in hot.list:
        lines.append(
            f"{item.rank}. **{item.title}**（{item.category_name or '未分类'}）"
        )
        lines.append(
            f"   阅读 {item.views:,} · 收藏 {item.favorite_count} · 热度 {item.score} · "
            f"{item.publish_time.strftime('%Y-%m-%d') if item.publish_time else '未知日期'}"
        )
    lines.append("")
    lines.append("> 热度 = 阅读量 × 0.6 + 收藏数 × 40 + 时效加成。")
    return "\n".join(lines)


def _format_stats(overview, trend) -> str:
    lines = [
        "## 新闻数据总览",
        f"- 新闻总量：**{overview.total_news:,}** 条",
        f"- 今日新发布：**{overview.today_news}** 条",
        f"- 近 7 天新发布：**{overview.week_news}** 条",
        f"- 近 30 天新发布：**{overview.month_news}** 条",
        f"- 累计阅读：**{overview.total_views:,}**",
        f"- 今日阅读：**{overview.today_views:,}**",
        f"- 累计收藏：**{overview.total_favorites:,}**",
        f"- 已生成 AI 摘要：**{overview.total_summaries:,}** 条",
    ]
    if overview.total_users is not None:
        lines.append(f"- 注册用户：**{overview.total_users}**（正常 {overview.active_users}）")
    if overview.latest_publish_time:
        lines.append(f"- 最新发布时间：{overview.latest_publish_time}")
    lines.append("")
    lines.append(f"## 最近 {trend.days} 天发布趋势")
    for point in trend.points[-10:]:
        bar = "█" * min(point.news_count, 20)
        lines.append(f"- {point.date}：{point.news_count} 条 {bar}".rstrip())
    if trend.total_news == 0:
        lines.append("")
        lines.append("> 当前区间没有新发布新闻，以上统计为真实数据库结果。")
    return "\n".join(lines)


def _format_news_rows(rows: list[dict], title: str = "检索结果") -> str:
    if not rows:
        return "数据库中没有找到相关新闻，可以换个关键词，或直接问「最近的热榜」。"
    lines = [f"## {title}（{len(rows)} 条）", ""]
    for item in rows:
        lines.append(f"### {item['title']}")
        meta = f"{item.get('publish_time') or ''} · {item.get('category') or '未分类'} · 阅读 {item.get('views', 0):,}"
        lines.append(meta)
        desc = item.get("summary") or item.get("description") or item.get("content_excerpt") or ""
        desc = re.sub(r"\s+", " ", desc)[:220]
        if desc:
            lines.append(desc)
        lines.append("")
    return "\n".join(lines)


def _extract_keywords(question: str) -> str:
    stopwords = {
        "帮我", "请问", "一下", "最近", "新闻", "有什么", "哪些", "关于", "怎么",
        "如何", "可以", "给我", "看看", "总结", "摘要", "汇总", "统计", "多少",
        "今天", "昨日", "本周", "这个", "那个", "以及", "还有", "相关", "内容",
        "搜索", "查找", "检索", "介绍", "关注", "值得", "一些", "最新", "生成",
        "报道", "消息", "资讯", "信息",
    }
    cleaned = question
    # 中文没有空格，先把常见动词/虚词替换掉，避免整句被当成一个关键词
    for word in sorted(stopwords, key=len, reverse=True):
        cleaned = cleaned.replace(word, " ")
    tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fa5]{2,}", cleaned)
    kept = []
    for token in tokens:
        if token in stopwords:
            continue
        if any(stop in token for stop in ("什么", "怎么", "如何", "多少", "一下")):
            continue
        kept.append(token.rstrip("的"))
    return " ".join(kept[:3])


async def _fallback_compose(
    db: AsyncSession, user: User, question: str
) -> tuple[str, list[dict]]:
    """返回 (markdown 文本, 工具步骤)。"""
    text = question.strip()
    steps: list[dict] = []
    lowered = text.lower()

    # 1) 指定新闻 ID 的摘要
    id_match = re.search(r"(?:新闻|id|ID|第)\s*(\d{1,6})", text)
    if id_match and any(word in text for word in ("摘要", "总结", "概括", "看点")):
        news_id = int(id_match.group(1))
        steps.append({"name": "summarize_news", "label": "生成 AI 摘要"})
        result = await summary_service.summarize_news(db, news_id)
        steps[-1]["preview"] = f"新闻 {news_id} 摘要已生成"
        content = (
            f"## 新闻 {news_id} 摘要\n\n{result.summary}\n\n"
            f"**一句话看点**：{result.highlight or '—'}"
        )
        return content, steps

    # 2) 热榜
    if any(word in text for word in ("热榜", "热门", "排行", "榜单", "最火")):
        steps.append({"name": "get_hot_news", "label": "汇总热榜"})
        days = 0
        if "7天" in text or "一周" in text or "本周" in text:
            days = 7
        elif "30天" in text or "一个月" in text:
            days = 30
        hot = await hotspot_service.get_hot_news(db, days=days, limit=10)
        steps[-1]["preview"] = f"汇总 {hot.total} 条热榜"
        return _format_hot(hot), steps

    # 3) 发布统计 / 趋势
    if any(
        word in text
        for word in ("统计", "多少", "新增", "发布量", "趋势", "数据", "总量", "用户数")
    ):
        days = 7
        if "30天" in text or "一个月" in text:
            days = 30
        elif "90天" in text or "三个月" in text:
            days = 90
        steps.append({"name": "get_news_stats", "label": "统计新闻数据"})
        overview = await stats_service.get_overview(db, is_admin=user.is_admin)
        trend = await stats_service.get_trend(db, days)
        steps[-1]["preview"] = f"统计 {overview.total_news} 条新闻"
        return _format_stats(overview, trend), steps

    # 4) 简报 / 日报
    if any(word in text for word in ("简报", "日报", "汇总一下", "新闻综述", "今日新闻")):
        steps.append({"name": "get_daily_digest", "label": "生成新闻简报"})
        result = await summary_service.daily_digest(db, days=0, limit=8)
        steps[-1]["preview"] = "新闻简报已生成"
        return result.content, steps

    # 5) 分类
    if "分类" in text or "频道" in text:
        steps.append({"name": "list_categories", "label": "读取新闻分类"})
        categories = await news_service.get_categories(db)
        steps[-1]["preview"] = f"读取 {len(categories)} 个分类"
        lines = ["## 新闻分类"]
        for item in categories:
            lines.append(f"- **{item.name}**：{item.news_count} 条")
        return "\n".join(lines), steps

    # 6) 默认：关键词检索
    keywords = _extract_keywords(text)
    steps.append({"name": "search_news", "label": "检索新闻数据库"})
    rows = await news_service.search_news_for_ai(db, keywords=keywords, limit=8)
    steps[-1]["preview"] = f"命中 {len(rows)} 条新闻"
    if not rows and keywords:
        rows = await news_service.search_news_for_ai(db, limit=8)
        intro = f"没有找到「{keywords}」的直接结果，以下是数据库中的最新新闻"
    elif rows:
        intro = f"关键词「{keywords}」的检索结果" if keywords else "数据库中的最新新闻"
    else:
        intro = "数据库中的最新新闻"
    return _format_news_rows(rows, intro), steps


async def _fallback_answer(
    db: AsyncSession, user: User, question: str
) -> str:
    content, _ = await _fallback_compose(db, user, question)
    return content


# ---------------------------------------------------------------------------
# 非流式 Agent
# ---------------------------------------------------------------------------


async def run_agent(db: AsyncSession, user: User, data: ChatRequest) -> str:
    history = _build_history(data)
    question = _last_question(history)

    if not ai_service.is_enabled():
        answer = await _fallback_answer(db, user, question)
        await _persist(db, user, question, answer)
        return answer

    messages: list[dict] = [_system_message(user), *history]
    try:
        for _ in range(MAX_TOOL_ROUNDS):
            message = await ai_service.complete(messages, tools=agent_tools.TOOL_DEFINITIONS)
            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                answer = ai_service.text_of(getattr(message, "content", "")).strip()
                if answer:
                    await _persist(db, user, question, answer)
                    return answer
                break

            messages.append(
                {
                    "role": "assistant",
                    "content": ai_service.text_of(getattr(message, "content", "")) or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments or "{}",
                            },
                        }
                        for call in tool_calls
                    ],
                }
            )
            for call in tool_calls:
                result = await agent_tools.execute_tool(
                    db, user, call.function.name, call.function.arguments
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )
    except (ai_service.AIUnavailable, ai_service.AIError) as exc:
        logger.warning("agent failed, fallback: %s", exc)

    answer = await _fallback_answer(db, user, question)
    await _persist(db, user, question, answer)
    return answer


# ---------------------------------------------------------------------------
# 流式 Agent（SSE）
# ---------------------------------------------------------------------------


def _tool_preview(result: str, limit: int = 240) -> str:
    text = result if isinstance(result, str) else str(result)
    return text if len(text) <= limit else text[:limit] + "…"


def _chunks(text: str, size: int = 14) -> list[str]:
    return [text[index : index + size] for index in range(0, len(text), size)]


async def _emit_fallback(
    db: AsyncSession, user: User, question: str
) -> AsyncGenerator[dict, None]:
    yield {"type": "status", "message": "大模型未配置，使用本地新闻引擎…"}
    try:
        content, steps = await _fallback_compose(db, user, question)
    except BusinessException as exc:
        yield {"type": "error", "message": exc.message}
        return
    except Exception as exc:
        logger.exception("fallback compose failed: %s", exc)
        yield {"type": "error", "message": "本地新闻引擎执行失败"}
        return

    for step in steps:
        yield {
            "type": "tool_start",
            "name": step["name"],
            "label": step["label"],
        }
        yield {
            "type": "tool_end",
            "name": step["name"],
            "label": step["label"],
            "preview": step.get("preview", ""),
        }

    for piece in _chunks(content):
        yield {"type": "token", "content": piece}
        await asyncio.sleep(0)

    yield {"type": "done"}
    await _persist(db, user, question, content)


async def stream_agent(
    db: AsyncSession, user: User, data: ChatRequest
) -> AsyncGenerator[dict, None]:
    """SSE 事件：status / tool_start / tool_end / token / done / error。"""
    try:
        history = _build_history(data)
    except BusinessException as exc:
        yield {"type": "error", "message": exc.message}
        return

    question = _last_question(history)

    if not ai_service.is_enabled():
        async for event in _emit_fallback(db, user, question):
            yield event
        return

    yield {"type": "status", "message": "正在思考…"}
    messages: list[dict] = [_system_message(user), *history]
    visible_parts: list[str] = []
    final_answer = ""

    try:
        for round_index in range(MAX_TOOL_ROUNDS):
            tool_calls: dict[int, dict] = {}
            round_parts: list[str] = []

            try:
                async for chunk in ai_service.stream_complete(
                    messages, tools=agent_tools.TOOL_DEFINITIONS
                ):
                    choice = chunk.choices[0] if chunk.choices else None
                    if choice is None:
                        continue
                    delta = choice.delta
                    content = ai_service.text_of(getattr(delta, "content", ""))
                    if content:
                        round_parts.append(content)
                        visible_parts.append(content)
                        yield {"type": "token", "content": content}
                    for call in getattr(delta, "tool_calls", None) or []:
                        index = getattr(call, "index", 0) or 0
                        entry = tool_calls.setdefault(
                            index, {"id": "", "name": "", "arguments": ""}
                        )
                        if getattr(call, "id", None):
                            entry["id"] = call.id
                        function = getattr(call, "function", None)
                        if function is not None:
                            if getattr(function, "name", None):
                                entry["name"] = function.name
                            if getattr(function, "arguments", None):
                                entry["arguments"] += function.arguments
            except ai_service.AIUnavailable:
                async for event in _emit_fallback(db, user, question):
                    yield event
                return
            except ai_service.AIError as exc:
                logger.warning("stream llm error: %s", exc)
                if not visible_parts:
                    async for event in _emit_fallback(db, user, question):
                        yield event
                    return
                yield {"type": "error", "message": "大模型连接中断，请稍后重试"}
                return

            if not tool_calls:
                final_answer = "".join(visible_parts).strip()
                if final_answer:
                    break
                async for event in _emit_fallback(db, user, question):
                    yield event
                return

            calls = list(tool_calls.values())
            messages.append(
                {
                    "role": "assistant",
                    "content": "".join(round_parts),
                    "tool_calls": [
                        {
                            "id": call["id"] or f"call_{round_index}_{index}",
                            "type": "function",
                            "function": {
                                "name": call["name"],
                                "arguments": call["arguments"] or "{}",
                            },
                        }
                        for index, call in enumerate(calls)
                    ],
                }
            )

            for index, call in enumerate(calls):
                call_id = call["id"] or f"call_{round_index}_{index}"
                label = agent_tools.TOOL_LABELS.get(call["name"], call["name"])
                yield {
                    "type": "tool_start",
                    "name": call["name"],
                    "label": label,
                }
                result = await agent_tools.execute_tool(
                    db, user, call["name"], call["arguments"]
                )
                yield {
                    "type": "tool_end",
                    "name": call["name"],
                    "label": label,
                    "preview": _tool_preview(result),
                }
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result,
                    }
                )

            yield {"type": "status", "message": "正在整理结果…"}

        if not final_answer:
            final_answer = "".join(visible_parts).strip()
        if not final_answer:
            async for event in _emit_fallback(db, user, question):
                yield event
            return

        await _persist(db, user, question, final_answer)
        yield {"type": "done"}
    except BusinessException as exc:
        yield {"type": "error", "message": exc.message}
    except Exception as exc:
        logger.exception("stream_agent failed: %s", exc)
        yield {"type": "error", "message": "AI 服务暂时不可用，请稍后重试"}
