import asyncio
from novel_ai_agent.agents.dialogue_agent import DialogueAgent

async def main():
    agent = DialogueAgent("novel_a9f69e79")
    ctx = {"novel_title": "测试小说"}
    # Test 1: Local edit
    res1 = await agent.chat("把第1章的最后一段修改一下，加一点环境描写", context=ctx)
    print("Test 1 (Local):", res1["actions"])
    
    # Test 2: Full rewrite
    res2 = await agent.chat("第1章整体节奏太慢了，帮我重写一遍", context=ctx)
    print("Test 2 (Rewrite):", res2["actions"])

if __name__ == "__main__":
    asyncio.run(main())
