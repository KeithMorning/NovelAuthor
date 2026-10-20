import asyncio
from unittest.mock import MagicMock, patch
from novel_ai_agent.agents.writer_agent import WriterAgent
from novel_ai_agent.agents.editor_agent import EditorAgent
from novel_ai_agent.models.chapter import Chapter

async def test_writer_agent_edit_chapter_style():
    """Test that WriterAgent.edit_chapter includes the style prompt for local edits."""
    with patch("novel_ai_agent.agents.base_agent.get_settings"), \
         patch("novel_ai_agent.agents.base_agent.BaseAgent._create_llm"):
        agent = WriterAgent(style_name="刘慈欣")
        
        async def mock_stream_invoke(llm, messages, on_token=None):
            system_msg = messages[0].content
            user_msg = messages[1].content
            full_prompt = system_msg + "\n" + user_msg
            
            # Assert negative constraints are present
            assert "好莱坞式" in full_prompt, "Style constraint '好莱坞式' missing in edit_chapter prompt"
            assert "刘慈欣" in full_prompt, "Style name missing in edit_chapter prompt"
            print("WriterAgent edit_chapter style injection checked OK.")
            
            return '```json\n{"summary": "Test", "edits": [{"action": "replace", "anchor": "Original content", "content": "New content"}]}\n```'
            
        agent._stream_invoke = mock_stream_invoke
        agent._get_json_llm = MagicMock()
        
        chapter = Chapter(number=1, title="Test", summary="Test summary", content="Original content")
        result = await agent.edit_chapter(chapter=chapter, revision_requirements="test edit")
        
        assert "chapter" in result or result.get("status") == "success", f"Unexpected result: {result}"
        print("WriterAgent edit_chapter test passed.\n")

async def test_editor_agent_polish_chapter_style():
    """Test that EditorAgent.polish_chapter includes the full style prompt constraints."""
    with patch("novel_ai_agent.agents.base_agent.get_settings"), \
         patch("novel_ai_agent.agents.base_agent.BaseAgent._create_llm"):
        agent = EditorAgent()
        
        async def mock_stream_invoke(llm, messages, on_token=None):
            system_msg = messages[0].content
            user_msg = messages[1].content
            full_prompt = system_msg + "\n" + user_msg
            
            # Assert negative constraints are present
            assert "好莱坞式" in full_prompt, "Style constraint '好莱坞式' missing in polish_chapter prompt"
            assert "刘慈欣" in full_prompt, "Style name missing in polish_chapter prompt"
            print("EditorAgent polish_chapter style injection checked OK.")
            
            return "这是润色后的内容。" * 100
            
        agent._stream_invoke = mock_stream_invoke
        
        chapter = Chapter(number=1, title="Test", summary="Test summary", content="Original content")
        result = await agent.polish_chapter(chapter=chapter, style="刘慈欣")
        
        assert result.get("status") == "success", f"Unexpected result: {result}"
        print("EditorAgent polish_chapter test passed.\n")

if __name__ == "__main__":
    print("Testing Style Injection...\n")
    asyncio.run(test_writer_agent_edit_chapter_style())
    asyncio.run(test_editor_agent_polish_chapter_style())
    print("All tests passed successfully.")
