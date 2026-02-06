#!/usr/bin/env python3
"""
测试YAML迁移后的角色生成功能
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from novel_ai_agent.agents.character_agent import CharacterAgent
from novel_ai_agent.models.outline import Outline, PlotPoint


async def test_character_generation():
    """测试角色生成（使用YAML格式）"""
    print("=" * 80)
    print("测试 YAML 格式的角色生成")
    print("=" * 80)

    # 创建测试大纲
    outline = Outline(
        title="智治纪元",
        genre="科幻",
        summary="在AI全面管理的未来，主角面临人类进化的抉择",
        theme="人性与科技的平衡",
        plot_points=[
            PlotPoint(
                name="父亲离去",
                description="父亲选择离开适应区前往遗民区",
                chapter_range="第1-3章",
                importance="高"
            )
        ],
        chapters_plan=[],
        target_words=100000,
        version=1
    )

    # 创建Agent
    print("\n📝 创建 CharacterAgent...")
    agent = CharacterAgent()

    print("🤖 使用的LLM配置:")
    print(f"  - Provider: {agent.settings.llm_provider}")
    print(f"  - Model: {agent.settings.get_model_name()}")

    # 生成角色
    print("\n🎭 开始生成角色（使用YAML格式）...")
    print("  这可能需要几秒钟...\n")

    try:
        result = await agent.generate_characters(
            outline=outline,
            character_requirements="创建2-3个主要角色，包含主角和配角"
        )

        if result["status"] == "success":
            print("✅ 角色生成成功！\n")
            print(f"📊 生成了 {result['count']} 个角色:\n")

            for i, char in enumerate(result["characters"], 1):
                print(f"{i}. {char.name} ({char.role})")
                print(f"   性格: {char.personality[:60]}...")
                print(f"   背景: {char.background[:60]}...")
                if char.relationships:
                    print(f"   关系: {len(char.relationships)} 个人物关系")
                print()

            print("=" * 80)
            print("✅ 测试完成！YAML格式工作正常")
            print("=" * 80)

        else:
            print(f"❌ 生成失败: {result.get('message')}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """主函数"""
    print("\n🚀 YAML迁移测试脚本\n")

    # 运行异步测试
    success = asyncio.run(test_character_generation())

    if success:
        print("\n✅ 所有测试通过！")
        print("\n💡 提示: 如果您看到这条消息，说明YAML格式迁移成功。")
        print("   现在可以启动服务测试完整功能：")
        print("   ./start_all.sh")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
