"""
示例使用脚本
演示如何使用小说AI Agent的核心功能
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from novel_ai_agent.agents.coordinator import CoordinatorAgent
from novel_ai_agent.utils.file_manager import file_manager


async def example_create_novel():
    """示例: 创建一个科幻小说"""
    print("=" * 60)
    print("示例 1: 创建科幻小说")
    print("=" * 60)

    coordinator = CoordinatorAgent()

    result = await coordinator.create_novel_workflow(
        title="三体回响",
        genre="科幻",
        theme="人类与外星文明的首次接触",
        style="刘慈欣",
        chapter_count=10,  # 为了演示，只创建10章
        user_requirements="希望故事有紧张的悬疑感，包含科学理论和哲学思考"
    )

    if result["status"] == "success":
        print(f"\n✓ {result['message']}")
        print(f"小说ID: {result['novel_id']}")
        print(f"大纲章节: {len(result['novel'].outline.chapters_plan)}章")
        print(f"角色数量: {len(result['novel'].characters)}个")

        # 打印大纲摘要
        print("\n【大纲摘要】")
        print(result['novel'].outline.summary)

        # 打印角色列表
        print("\n【主要角色】")
        for char in result['novel'].characters[:3]:  # 只显示前3个
            print(f"- {char.name} ({char.role}): {char.personality[:30]}...")

        return result['novel_id']
    else:
        print(f"\n✗ 创建失败: {result['message']}")
        return None


async def example_write_chapter(novel_id: str):
    """示例: 创作第一章"""
    print("\n" + "=" * 60)
    print(f"示例 2: 创作第1章")
    print("=" * 60)

    coordinator = CoordinatorAgent()

    result = await coordinator.write_chapter_workflow(
        novel_id=novel_id,
        chapter_number=1
    )

    if result["status"] == "success":
        print(f"\n✓ {result['message']}")
        chapter = result['chapter']
        print(f"章节标题: {chapter.title}")
        print(f"字数: {chapter.word_count}")

        # 打印内容预览
        print("\n【内容预览】(前300字)")
        print(chapter.content[:300] + "...")
    else:
        print(f"\n✗ 创作失败: {result['message']}")


async def example_武侠_novel():
    """示例: 创建武侠小说"""
    print("\n" + "=" * 60)
    print("示例 3: 创建武侠小说")
    print("=" * 60)

    coordinator = CoordinatorAgent()

    result = await coordinator.create_novel_workflow(
        title="江湖夜雨",
        genre="武侠",
        theme="江湖恩怨与侠义精神",
        style="金庸",
        chapter_count=15,
        user_requirements="主角是一个隐世高手，被迫卷入江湖纷争"
    )

    if result["status"] == "success":
        print(f"\n✓ {result['message']}")
        print(f"小说ID: {result['novel_id']}")

        # 打印章节标题列表
        print("\n【章节列表】")
        for cp in result['novel'].outline.chapters_plan[:5]:  # 前5章
            print(f"第{cp.chapter_number}章: {cp.title}")
            print(f"  梗概: {cp.summary[:50]}...")

        return result['novel_id']
    else:
        print(f"\n✗ 创建失败: {result['message']}")
        return None


async def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║           小说AI Agent - 示例演示                          ║
║                                                           ║
║  本示例将演示:                                             ║
║  1. 创建科幻小说(刘慈欣风格)                                ║
║  2. 创作第一章                                             ║
║  3. 创建武侠小说(金庸风格)                                  ║
╚═══════════════════════════════════════════════════════════╝
    """)

    try:
        # 示例1: 创建科幻小说
        novel_id_scifi = await example_create_novel()

        if novel_id_scifi:
            # 示例2: 创作第一章
            await example_write_chapter(novel_id_scifi)

        # 示例3: 创建武侠小说
        novel_id_wuxia = await example_武侠_novel()

        print("\n" + "=" * 60)
        print("示例演示完成!")
        print("=" * 60)

        print("\n生成的文件:")
        print("- 大纲: novel_ai_agent/output/outlines/")
        print("- 角色: novel_ai_agent/output/characters/")
        print("- 小说: novel_ai_agent/output/novels/")

        # 列出所有小说
        novels = file_manager.list_novels()
        print(f"\n当前共有 {len(novels)} 个小说项目:")
        for nid in novels:
            print(f"  - {nid}")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
