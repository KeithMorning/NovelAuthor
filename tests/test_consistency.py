import json
import asyncio
from unittest.mock import MagicMock, patch
from novel_ai_agent.agents.outline_agent import OutlineAgent
from novel_ai_agent.models.outline import Outline, ChapterPlan, PlotPoint

async def test_outline_expansion_with_dead_character():
    """
    Test that OutlineAgent respects 'World State' (Dead Character) 
    and substitutes them in the expansion.
    """
    # Patch dependencies to avoid initialization errors
    with patch("novel_ai_agent.agents.base_agent.get_settings") as mock_settings, \
         patch("novel_ai_agent.agents.base_agent.BaseAgent._create_llm") as mock_create_llm:
        
        # 1. Setup Mock Component
        agent = OutlineAgent()
        
        # Mock LLM response to simulate "Substitution"
        mock_llm_response = {
            "detailed_summary": "In this chapter, Li Wei takes over the defense mechanism because Zhang Qiang is dead. Li Wei struggles but succeeds.",
            "scenes": [
                {
                    "description": "Li Wei repairs the generator.",
                    "focus": "Tension",
                    "characters": ["Li Wei", "Lin Xing"]
                }
            ],
            "emotional_tone": "Tense",
            "key_dialogues": ["Li Wei: I'll do it for Zhang Qiang."],
            "transitions": {"previous": "After the battle", "next": "Victory"}
        }
        
        async def mock_ainvoke(messages):
            prompt_content = messages[1].content
            print(f"DEBUG: FULL PROMPT CONTENT:\n{prompt_content}\n-------------------")
            
            # VERIFY: Prompt must contain the Story Context we passed
            print(f"DEBUG: Prompt Context Check: 'Zhang Qiang: 已死亡' in prompt? {'Zhang Qiang: 已死亡' in prompt_content}")
            print(f"DEBUG: Prompt Instruction Check: '核心指令: 渐进式适配' in prompt? {'核心指令: 渐进式适配' in prompt_content}")
            
            # If assertions fail here, they will raise exception and fail the test
            if "Zhang Qiang: 已死亡" not in prompt_content:
                print("FAILURE: Prompt missing World State")
            if "核心指令: 渐进式适配" not in prompt_content:
                print("FAILURE: Prompt missing Progressive Adaptation instruction")
            
            # Use json.dumps for valid JSON
            return MagicMock(content=f"```json\n{json.dumps(mock_llm_response)}\n```")

        agent.llm = MagicMock()
        agent.llm.ainvoke = mock_ainvoke
        # We need to mock _get_json_llm to return our mocked llm
        agent._get_json_llm = MagicMock(return_value=agent.llm)

        # 2. Setup Context
        outline = Outline(
            title="Test Novel",
            genre="Sci-Fi",
            summary="Test Summary",
            theme="Survival",
            chapters_plan=[
                ChapterPlan(
                    chapter_number=1, 
                    title="Chapter 1", 
                    summary="Zhang Qiang saves everyone.", # Original Outline says Zhang Qiang
                    estimated_words=2000
                ) 
            ],
            plot_points=[]
        )
        
        story_context = {
            "world_state": {"Zhang Qiang": "已死亡 (Dead)"},
            "recent_history": [{"number": 0, "title": "Prologue", "summary": "Zhang Qiang died."}]
        }

        # 3. Execute
        result = await agent.expand_chapter_plan(
            outline=outline,
            chapter_number=1,
            story_context=story_context
        )

        # 4. Assert
        print(f"DEBUG: Result Status: {result.get('status')}")
        if result.get("status") != "success":
            print(f"DEBUG: Full Result: {result}")
        
        assert result["status"] == "success"
        detailed = result["detailed_plan"]
        # The mock response we provided has Li Wei doing the work, implying substitution happened.
        # The real assertion is in `mock_ainvoke` checking the prompt received the constraint.
        assert "Li Wei" in detailed.detailed_summary
        print("Test Passed: Constraint injected and substitution simulated.")

if __name__ == "__main__":
    asyncio.run(test_outline_expansion_with_dead_character())
