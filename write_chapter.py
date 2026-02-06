#!/usr/bin/env python3
"""
直接调用后台功能写章节
无需启动服务
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from novel_ai_agent.agents.writer_agent import WriterAgent
from novel_ai_agent.utils.file_manager import file_manager


async def write_chapter(novel_id: str, chapter_number: int):
    """
    写作指定章节

    Args:
        novel_id: 小说ID
        chapter_number: 章节号
    """
    print(f"=" * 80)
    print(f"开始写作章节 - 小说ID: {novel_id}, 第{chapter_number}章")
    print(f"=" * 80)

    # 1. 加载小说
    print(f"\n📚 正在加载小说...")
    novel = file_manager.load_novel_json(novel_id)

    if not novel:
        print(f"❌ 错误: 未找到小说 {novel_id}")
        return False

    print(f"✅ 小说加载成功")
    print(f"   标题: {novel.title}")
    print(f"   类型: {novel.genre}")
    print(f"   风格: {novel.author_style}")
    print(f"   大纲章节数: {len(novel.outline.chapters_plan)}")
    print(f"   已完成章节: {len(novel.chapters)}")

    # 2. 检查章节是否存在
    if chapter_number > len(novel.outline.chapters_plan):
        print(f"❌ 错误: 章节号 {chapter_number} 超出大纲范围 (1-{len(novel.outline.chapters_plan)})")
        return False

    # 检查是否已经写过
    existing_chapter = next((c for c in novel.chapters if c.number == chapter_number), None)
    if existing_chapter:
        print(f"⚠️  警告: 第{chapter_number}章已存在，将重新生成")

    # 3. 创建WriterAgent
    print(f"\n🤖 初始化写作Agent...")
    writer = WriterAgent()

    # 4. 开始写作
    print(f"\n✍️  开始生成第{chapter_number}章内容...")
    print(f"   这可能需要几分钟，请耐心等待...\n")

    try:
        result = await writer.write_chapter(
            novel_id=novel_id,
            chapter_number=chapter_number
        )

        if result["status"] == "success":
            chapter = result["chapter"]
            print(f"\n" + "=" * 80)
            print(f"✅ 章节生成成功！")
            print(f"=" * 80)
            print(f"章节号: {chapter.number}")
            print(f"标题: {chapter.title}")
            print(f"字数: {len(chapter.content)} 字")
            print(f"生成时间: {chapter.created_at}")
            print(f"\n章节内容预览:")
            print("-" * 80)
            preview = chapter.content[:500] + "..." if len(chapter.content) > 500 else chapter.content
            print(preview)
            print("-" * 80)

            # 显示保存位置
            chapter_file = Path(f"novel_ai_agent/output/chapters/{novel_id}_chapter_{chapter_number}.md")
            if chapter_file.exists():
                print(f"\n📄 章节已保存到: {chapter_file}")

            return True
        else:
            print(f"\n❌ 生成失败: {result.get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def write_all_chapters(novel_id: str):
    """
    写作所有章节

    Args:
        novel_id: 小说ID
    """
    print(f"=" * 80)
    print(f"开始写作所有章节 - 小说ID: {novel_id}")
    print(f"=" * 80)

    # 加载小说
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        print(f"❌ 错误: 未找到小说 {novel_id}")
        return

    total_chapters = len(novel.outline.chapters_plan)
    print(f"\n总共需要写作 {total_chapters} 章")

    success_count = 0
    for i in range(1, total_chapters + 1):
        print(f"\n{'=' * 80}")
        print(f"进度: {i}/{total_chapters}")
        print(f"{'=' * 80}")

        success = await write_chapter(novel_id, i)
        if success:
            success_count += 1
        else:
            print(f"\n⚠️  第{i}章生成失败，是否继续？")
            response = input("继续 (y/n): ").lower()
            if response != 'y':
                break

    print(f"\n" + "=" * 80)
    print(f"写作完成！")
    print(f"=" * 80)
    print(f"成功: {success_count}/{total_chapters} 章")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="直接写作小说章节")
    parser.add_argument("novel_id", help="小说ID (例如: novel_87c32361)")
    parser.add_argument("-c", "--chapter", type=int, help="章节号 (不指定则写所有章节)")

    args = parser.parse_args()

    if args.chapter:
        # 写单个章节
        success = asyncio.run(write_chapter(args.novel_id, args.chapter))
        sys.exit(0 if success else 1)
    else:
        # 写所有章节
        asyncio.run(write_all_chapters(args.novel_id))


if __name__ == "__main__":
    main()
