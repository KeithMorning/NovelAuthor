#!/usr/bin/env python3
"""调试脚本 - 用于测试角色生成"""

import asyncio
import sys
sys.path.insert(0, '/Users/keithxi/Documents/work/Nover')

from novel_ai_agent.agents.character_agent import CharacterAgent
from novel_ai_agent.prompts.character_prompts import CHARACTER_SYSTEM_PROMPT, get_character_generation_prompt
from langchain_core.messages import HumanMessage, SystemMessage

async def test():
    print("=" * 50)
    print("1. 创建 CharacterAgent...")
    agent = CharacterAgent()
    print(f"   LLM: {agent.llm}")
    print(f"   Model: {agent.llm.model_name}")

    print("\n2. 构建 prompt...")
    prompt = get_character_generation_prompt(
        title="测试小说",
        genre="科幻",
        summary="测试 summary",
        theme="AI 觉醒",
        outline_key_points="暂无大纲",
        character_requirements="",
        chapter_count=8
    )
    print(f"   Prompt 长度: {len(prompt)}")

    print("\n3. 调用 LLM...")
    messages = [
        SystemMessage(content=CHARACTER_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]

    try:
        response = await agent.llm.ainvoke(messages)
        content = response.content
        print(f"   响应长度: {len(content)}")
        print(f"   响应内容: {content[:500]}...")
    except Exception as e:
        print(f"   调用失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n4. 测试 CharacterAgent.generate_characters...")
    result = await agent.generate_characters(
        title="测试小说",
        genre="科幻",
        theme="AI 觉醒",
        chapter_count=8
    )
    print(f"   结果: {result}")

if __name__ == "__main__":
    asyncio.run(test())
