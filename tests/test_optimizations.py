#!/usr/bin/env python3
"""
针对本轮优化的回归测试。

运行方式:
    PYTHONPATH=. python3 tests/test_optimizations.py
"""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from novel_ai_agent.agents.base_agent import _content_to_text
from novel_ai_agent.agents.writer_agent import WriterAgent
from novel_ai_agent.models.chapter import Chapter
from novel_ai_agent.models.outline import Outline, PlotPoint, ChapterPlan
from novel_ai_agent.utils.logger import NovelCreationLogger, WorkflowStep
from novel_ai_agent.utils.text_utils import strip_generated_chapter_title


class TextUtilsTest(unittest.TestCase):
    def test_strip_generated_title(self):
        self.assertEqual(
            strip_generated_chapter_title("# 第1章 初见\n\n正文开始"),
            "正文开始",
        )
        self.assertEqual(
            strip_generated_chapter_title("## 第12章 转折\n正文开始"),
            "正文开始",
        )
        self.assertEqual(
            strip_generated_chapter_title("正文本来就没有标题"),
            "正文本来就没有标题",
        )

    def test_strip_does_not_touch_body_heading(self):
        text = "正文第一段\n\n## 场景二\n内容"
        self.assertEqual(strip_generated_chapter_title(text), text)


class ContentBlockTest(unittest.TestCase):
    def test_content_to_text(self):
        self.assertEqual(_content_to_text("abc"), "abc")
        self.assertEqual(
            _content_to_text([{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]),
            "ab",
        )
        self.assertEqual(_content_to_text(None), "")


class PreviousContextTest(unittest.TestCase):
    def _make_agent(self, full_context_mode=True, budget=80000):
        settings = SimpleNamespace(
            default_chapter_words=4000,
            full_context_mode=full_context_mode,
            max_previous_context_chars=budget,
        )
        with patch("novel_ai_agent.agents.base_agent.get_settings", return_value=settings), \
             patch("novel_ai_agent.agents.base_agent.BaseAgent._create_llm"):
            agent = WriterAgent()
        agent.logger = MagicMock()
        return agent

    @staticmethod
    def _chapters():
        return [
            Chapter(
                number=1,
                title="第一章",
                summary="开篇",
                content="长" * 80,
                hooks_planted=["神秘信件"],
                character_states={"主角": "受伤"},
            ),
            Chapter(
                number=2,
                title="第二章",
                summary="发展",
                content="长" * 80,
                character_states={"主角": "康复", "配角": "已死亡"},
            ),
        ]

    def test_full_context_under_budget(self):
        agent = self._make_agent(budget=10000)
        result = agent._prepare_previous_content(self._chapters(), current_chapter_num=3)
        self.assertIn("【前文完整内容】", result)
        self.assertIn("【待回收的伏笔】", result)
        self.assertIn("⚠️ 配角", result)

    def test_auto_fallback_over_budget(self):
        agent = self._make_agent(budget=100)
        result = agent._prepare_previous_content(self._chapters(), current_chapter_num=3)
        self.assertIn("【故事进展】", result)
        self.assertNotIn("【前文完整内容】", result)
        self.assertIn("【最近章节详情】", result)
        self.assertIn("⚠️ 配角", result)
        agent.logger.log.assert_called_once()

    def test_summary_mode(self):
        agent = self._make_agent(full_context_mode=False)
        result = agent._prepare_previous_content(self._chapters(), current_chapter_num=3)
        self.assertIn("【故事进展】", result)
        self.assertNotIn("【前文完整内容】", result)

    def test_plot_point_filtering(self):
        agent = self._make_agent()
        outline = Outline(
            title="测试",
            genre="科幻",
            summary="简介",
            theme="主题",
            plot_points=[
                PlotPoint(name="早期", description="已发生", chapter_range="第1-2章", importance="高"),
                PlotPoint(name="后期", description="未发生", chapter_range="第8-10章", importance="高"),
            ],
        )
        result = agent._prepare_previous_content(
            self._chapters(), outline=outline, current_chapter_num=3
        )
        self.assertIn("早期", result)
        self.assertNotIn("后期", result)


class LoggerFlushTest(unittest.TestCase):
    def test_flush_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = NovelCreationLogger("test_flush", log_dir=tmpdir)
            logger.step_start(WorkflowStep.CHAPTER_WRITING, "开始")
            logger.complete("完成")

            json_file = Path(tmpdir) / "test_flush.json"
            self.assertTrue(json_file.exists())
            data = json.loads(json_file.read_text(encoding="utf-8"))
            self.assertEqual(data["workflow_status"]["status"], "completed")
            self.assertGreaterEqual(len(data["logs"]), 3)
            self.assertFalse((Path(tmpdir) / "test_flush.json.tmp").exists())


class WriterFlowTest(unittest.IsolatedAsyncioTestCase):
    async def test_write_chapter_strips_title_and_uses_settings(self):
        settings = SimpleNamespace(
            default_chapter_words=3210,
            full_context_mode=True,
            max_previous_context_chars=80000,
            temperature=0.7,
            max_tokens=8192,
            llm_provider="openai",
        )
        with patch("novel_ai_agent.agents.base_agent.get_settings", return_value=settings), \
             patch("novel_ai_agent.agents.base_agent.BaseAgent._create_llm"), \
             patch("novel_ai_agent.agents.writer_agent.get_logger", return_value=MagicMock()):
            agent = WriterAgent()

        prompts = []
        body = "这是正文。" * 120

        async def fake_stream_invoke(llm, messages, on_token=None):
            prompts.append(messages[1].content)
            if len(prompts) == 1:
                return f"# 第1章 初见\n\n{body}"
            return json.dumps({
                "actual_summary": "主角登场",
                "hooks_planted": [],
                "hooks_resolved": [],
                "character_states": {},
                "key_items": [],
                "emotional_tone": "平静",
            })

        agent._stream_invoke = fake_stream_invoke
        agent._get_json_llm = MagicMock()

        outline = Outline(
            title="测试小说",
            genre="科幻",
            summary="简介",
            theme="主题",
        )
        plan = ChapterPlan(
            chapter_number=1,
            title="初见",
            summary="主角登场",
            key_events=["登场"],
            characters_involved=[],
        )

        result = await agent.write_chapter(chapter_plan=plan, outline=outline, characters=[])

        self.assertEqual(result["status"], "success", result)
        self.assertEqual(result["chapter"].content, body)
        self.assertEqual(result["target_words"], 3210)
        self.assertIn("3210", prompts[0])

    async def test_digest_includes_chapter_ending(self):
        settings = SimpleNamespace(
            default_chapter_words=4000,
            full_context_mode=True,
            max_previous_context_chars=80000,
            temperature=0.7,
            max_tokens=8192,
            llm_provider="openai",
        )
        with patch("novel_ai_agent.agents.base_agent.get_settings", return_value=settings), \
             patch("novel_ai_agent.agents.base_agent.BaseAgent._create_llm"), \
             patch("novel_ai_agent.agents.writer_agent.get_logger", return_value=MagicMock()):
            agent = WriterAgent()

        captured = {}

        async def fake_stream_invoke(llm, messages, on_token=None):
            captured["prompt"] = messages[1].content
            return json.dumps({
                "actual_summary": "主角死亡",
                "hooks_planted": [],
                "hooks_resolved": [],
                "character_states": {"主角": "已死亡"},
                "key_items": [],
                "emotional_tone": "悲怆",
            })

        agent._stream_invoke = fake_stream_invoke
        agent._get_json_llm = MagicMock()

        content = "开头" + "中段" * 3000 + "结尾关键事件：主角死亡"
        plan = ChapterPlan(
            chapter_number=1,
            title="测试",
            summary="测试",
            key_events=[],
            characters_involved=[],
        )

        digest = await agent._extract_chapter_digest(content, plan)

        self.assertIn("结尾关键事件：主角死亡", captured["prompt"])
        self.assertEqual(digest["actual_summary"], "主角死亡")
        self.assertEqual(digest["character_states"]["主角"], "已死亡")


class StreamRetryTest(unittest.IsolatedAsyncioTestCase):
    def _make_agent(self):
        settings = SimpleNamespace(
            default_chapter_words=4000,
            full_context_mode=True,
            max_previous_context_chars=80000,
            temperature=0.7,
            max_tokens=8192,
            llm_provider="openai",
        )
        with patch("novel_ai_agent.agents.base_agent.get_settings", return_value=settings), \
             patch("novel_ai_agent.agents.base_agent.BaseAgent._create_llm"), \
             patch("novel_ai_agent.agents.writer_agent.get_logger", return_value=MagicMock()):
            return WriterAgent()

    async def test_retry_on_empty_response(self):
        agent = self._make_agent()

        class FlakyLLM:
            def __init__(self):
                self.calls = 0

            async def astream(self, messages):
                self.calls += 1
                if self.calls == 1:
                    return
                yield SimpleNamespace(content="恢复了")

        llm = FlakyLLM()
        result = await agent._stream_invoke(llm, [], retries=1)

        self.assertEqual(result, "恢复了")
        self.assertEqual(llm.calls, 2)

    async def test_empty_response_stays_empty_after_retries(self):
        agent = self._make_agent()

        class EmptyLLM:
            def __init__(self):
                self.calls = 0

            async def astream(self, messages):
                self.calls += 1
                if False:
                    yield None

        llm = EmptyLLM()
        result = await agent._stream_invoke(llm, [], retries=0)

        self.assertEqual(result, "")
        self.assertEqual(llm.calls, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
