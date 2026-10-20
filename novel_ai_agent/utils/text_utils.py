"""
文本处理工具

集中存放多个 Agent 共用的文本清洗逻辑，避免同一段正则在各处复制粘贴。
"""
from __future__ import annotations

import re

# LLM 有时会在正文开头重复输出章节标题（如 "# 第1章 标题"）。
# 标题由 FileManager 统一生成，因此这里只移除正文开头的一行标题。
_CHAPTER_TITLE_RE = re.compile(
    r"^\s*#{1,2}\s*第[0-9一二三四五六七八九十百]+[章节].*?\n+",
    flags=re.MULTILINE,
)


def strip_generated_chapter_title(text: str) -> str:
    """
    移除 LLM 正文开头多余的章节标题行。

    Args:
        text: LLM 生成的原始文本

    Returns:
        str: 去掉开头标题并去除左侧空白后的正文
    """
    if not text:
        return ""
    return _CHAPTER_TITLE_RE.sub("", text, count=1).lstrip()


def estimate_tokens(text: str) -> int:
    """
    粗略估算 token 数（中文场景按 1 token ≈ 1.5 字符）。

    仅用于日志和预算判断，不追求精确。
    """
    return len(text) // 3 if text else 0
