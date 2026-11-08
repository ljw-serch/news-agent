"""大模型调用（OpenAI 兼容协议）。

后端统一持有 API Key，前端不再暴露任何密钥。
未配置 Key 或调用失败时，由上层降级为本地规则引擎。
"""

from __future__ import annotations

import logging
import re
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger("news-app.ai")

_client: AsyncOpenAI | None = None


class AIUnavailable(Exception):
    """未配置大模型或初始化失败。"""


class AIError(Exception):
    """大模型调用失败。"""


def is_enabled() -> bool:
    return bool(settings.LLM_API_KEY and settings.LLM_API_KEY.strip())


def get_client() -> AsyncOpenAI:
    global _client
    if not is_enabled():
        raise AIUnavailable("未配置 LLM_API_KEY")
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
            max_retries=1,
        )
    return _client


def text_of(content: Any) -> str:
    """把模型返回的 content 统一成字符串。"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                parts.append(item)
            else:
                parts.append(getattr(item, "text", "") or "")
        return "".join(parts)
    return str(content)


async def complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.3,
) -> Any:
    """非流式调用，返回 assistant message 对象。"""
    try:
        client = get_client()
    except AIUnavailable:
        raise
    kwargs: dict[str, Any] = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    try:
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message
    except Exception as exc:
        logger.exception("llm completion failed: %s", exc)
        raise AIError(str(exc)) from exc


async def stream_complete(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.3,
) -> AsyncGenerator[Any, None]:
    """流式调用，逐个 chunk 产出。"""
    try:
        client = get_client()
    except AIUnavailable:
        raise
    kwargs: dict[str, Any] = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    try:
        stream = await client.chat.completions.create(**kwargs)
    except Exception as exc:
        logger.exception("llm stream failed: %s", exc)
        raise AIError(str(exc)) from exc

    try:
        async for chunk in stream:
            yield chunk
    finally:
        try:
            await stream.close()
        except Exception:
            pass


SUMMARY_PROMPT = """你是专业新闻编辑。请阅读下面的新闻，提炼客观、准确的信息。
要求：
1. 摘要 100-180 字，只保留事实，不要编造。
2. 看点不超过 40 字，一句话点出最重要的信息。
3. 严格按下面两行输出，不要输出其他内容：
摘要：...
看点：..."""

DIGEST_PROMPT = """你是新闻主编。请根据给出的新闻列表，生成一份中文新闻简报。
格式要求（Markdown）：
## 今日速览
用 2-3 句话概括整体信息面。
## 重点新闻
挑选 3-5 条，每条格式：**标题**（日期 / 分类）—— 2 句话要点 + 可能影响。
## 趋势观察
用 3-4 条概括当前新闻热点与共同主题。
只依据给出的素材，不要编造事实；总字数控制在 400-700 字。"""

HOT_PROMPT = """你是新闻运营分析师。请根据给出的热榜数据，输出中文 Markdown 分析：
## 热榜概览
说明热榜的整体特征与热度依据。
## 话题聚类
把上榜新闻归为 2-4 个话题，并说明各自代表新闻。
## 值得关注
指出 2-3 条最值得继续追踪的新闻及原因。
## 阅读建议
给普通读者 2-3 条建议。
只依据给出数据，不要编造；总字数 400-600 字。"""


def clean_model_text(text: str) -> str:
    """清理模型偶发输出的引用标记（如 :cite[1]）。"""
    text = re.sub(r"\s*:?cite\[[^\]]*\]", "", text or "", flags=re.I)
    text = re.sub(r"\s*\[citation[^\]]*\]", "", text, flags=re.I)
    return text.strip()


def _split_summary(text: str) -> tuple[str, str]:
    text = clean_model_text(text)
    if not text:
        return "", ""
    summary = ""
    highlight = ""
    match_summary = re.search(r"摘要[:：]\s*(.+?)(?=\n\s*看点[:：]|\Z)", text, re.S)
    match_highlight = re.search(r"看点[:：]\s*(.+?)\Z", text, re.S)
    if match_summary:
        summary = match_summary.group(1).strip()
    if match_highlight:
        highlight = match_highlight.group(1).strip().replace("\n", " ")
    if not summary:
        # 没有按格式输出时，去掉标题行，最多保留 400 字
        summary = re.sub(r"^(摘要|看点)[:：].*$", "", text, flags=re.M).strip()
        summary = summary[:400]
    summary = re.sub(r"\s+", " ", summary).strip()
    highlight = re.sub(r"\s+", " ", highlight).strip()[:80]
    if not highlight:
        first = re.split(r"[。！？!?]", summary, maxsplit=1)[0]
        highlight = first[:40]
    return summary, highlight


async def summarize_text(title: str, content: str) -> tuple[str, str]:
    messages = [
        {"role": "system", "content": SUMMARY_PROMPT},
        {
            "role": "user",
            "content": f"标题：{title}\n\n正文：\n{content[:6000]}",
        },
    ]
    message = await complete(messages, temperature=0.2)
    return _split_summary(text_of(message.content))


async def digest_text(news_items: list[dict]) -> str:
    lines = []
    for index, item in enumerate(news_items, start=1):
        lines.append(
            f"{index}. [{item.get('publish_time')}] 《{item.get('title')}》 "
            f"分类：{item.get('category')} 作者：{item.get('author')} 阅读：{item.get('views')}\n"
            f"   摘要：{item.get('summary') or item.get('description') or ''}\n"
            f"   正文节选：{(item.get('content') or '')[:400]}"
        )
    messages = [
        {"role": "system", "content": DIGEST_PROMPT},
        {"role": "user", "content": "新闻素材：\n" + "\n".join(lines)},
    ]
    message = await complete(messages, temperature=0.35)
    return clean_model_text(text_of(message.content))


async def hot_analysis_text(hot_items: list[dict], days: int) -> str:
    lines = []
    for item in hot_items:
        lines.append(
            f"#{item.get('rank')} 《{item.get('title')}》 "
            f"分类：{item.get('category_name')} 阅读：{item.get('views')} "
            f"收藏：{item.get('favorite_count')} 发布：{item.get('publish_time')} "
            f"热度：{item.get('score')}"
        )
    window = f"近 {days} 天" if days else "全部时间"
    messages = [
        {"role": "system", "content": HOT_PROMPT},
        {
            "role": "user",
            "content": f"统计窗口：{window}\n热榜数据：\n" + "\n".join(lines),
        },
    ]
    message = await complete(messages, temperature=0.35)
    return clean_model_text(text_of(message.content))
