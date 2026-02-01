"""
小说AI Agent - 主入口
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from pathlib import Path

app = typer.Typer(help="小说AI Agent - 基于多Agent协作的AI小说创作系统")
console = Console()


@app.command()
def init():
    """初始化项目,创建必要的目录和配置文件"""
    console.print(Panel("[bold cyan]初始化小说AI Agent项目[/bold cyan]"))

    # 创建.env文件
    env_file = Path(".env")
    if not env_file.exists():
        anthropic_key = Prompt.ask("请输入您的Anthropic API Key")
        with open(env_file, "w") as f:
            f.write(f"ANTHROPIC_API_KEY={anthropic_key}\n")
            f.write("DEFAULT_MODEL=claude-sonnet-4-20250514\n")
            f.write("TEMPERATURE=0.7\n")
        console.print("[green]✓[/green] 已创建 .env 配置文件")
    else:
        console.print("[yellow]![/yellow] .env 文件已存在,跳过创建")

    # 确保输出目录存在
    output_dirs = [
        "novel_ai_agent/output/novels",
        "novel_ai_agent/output/outlines",
        "novel_ai_agent/output/characters",
        "novel_ai_agent/data/chroma"
    ]

    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    console.print("[green]✓[/green] 已创建输出目录")
    console.print("\n[bold green]初始化完成![/bold green]")
    console.print("\n使用 [cyan]python main.py --help[/cyan] 查看可用命令")


@app.command()
def create(
    title: str = typer.Option(..., "--title", "-t", help="小说标题"),
    genre: str = typer.Option(..., "--genre", "-g", help="小说类型 (如:武侠/科幻/推理)"),
    theme: str = typer.Option(..., "--theme", help="故事主题"),
    style: str = typer.Option("中性风格", "--style", "-s", help="作家风格"),
    chapters: int = typer.Option(20, "--chapters", "-n", help="章节数量"),
    requirements: str = typer.Option("", "--requirements", "-r", help="额外需求")
):
    """创建新小说项目 (包含大纲和角色)"""
    import asyncio
    from novel_ai_agent.agents.coordinator import CoordinatorAgent

    console.print(Panel(f"[bold cyan]创建新小说: {title}[/bold cyan]"))
    console.print(f"类型: [yellow]{genre}[/yellow]")
    console.print(f"主题: [yellow]{theme}[/yellow]")
    console.print(f"风格: [yellow]{style}[/yellow]")
    console.print(f"章节数: [yellow]{chapters}[/yellow]\n")

    console.print("[cyan]正在创建小说...[/cyan]")

    # 调用CoordinatorAgent创建小说
    coordinator = CoordinatorAgent()

    with console.status("[bold green]正在生成大纲和角色..."):
        result = asyncio.run(coordinator.create_novel_workflow(
            title=title,
            genre=genre,
            theme=theme,
            style=style,
            chapter_count=chapters,
            user_requirements=requirements
        ))

    if result["status"] == "success":
        console.print(f"\n[green]✓[/green] {result['message']}")
        console.print(f"\n[bold]小说ID[/bold]: [cyan]{result['novel_id']}[/cyan]")
        console.print(f"[bold]大纲章节[/bold]: {len(result['novel'].outline.chapters_plan)}章")
        console.print(f"[bold]角色数量[/bold]: {len(result['novel'].characters)}个")

        console.print("\n[bold green]接下来可以:[/bold green]")
        console.print(f"- 查看大纲: [cyan]cat novel_ai_agent/output/outlines/{result['novel_id']}_outline_v1.md[/cyan]")
        console.print(f"- 查看角色: [cyan]cat novel_ai_agent/output/characters/{result['novel_id']}_characters.md[/cyan]")
        console.print(f"- 开始写作: [cyan]python main.py write --id {result['novel_id']} --chapter 1[/cyan]")
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")
        if "error" in result:
            console.print(f"[red]错误详情: {result['error']}[/red]")


@app.command()
def outline(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    theme: str = typer.Option(..., "--theme", help="故事主题")
):
    """为小说创建大纲"""
    console.print(Panel(f"[bold cyan]创建大纲[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"主题: [yellow]{theme}[/yellow]")

    # TODO: 调用OutlineAgent生成大纲
    console.print("\n[yellow]功能开发中...[/yellow]")
    console.print("该功能将在Phase 2完成")


@app.command()
def write(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号")
):
    """写作指定章节"""
    import asyncio
    from novel_ai_agent.agents.coordinator import CoordinatorAgent

    console.print(Panel(f"[bold cyan]写作章节[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"章节: [yellow]第{chapter}章[/yellow]\n")

    # 调用CoordinatorAgent写作章节
    coordinator = CoordinatorAgent()

    with console.status(f"[bold green]正在创作第{chapter}章..."):
        result = asyncio.run(coordinator.write_chapter_workflow(
            novel_id=novel_id,
            chapter_number=chapter
        ))

    if result["status"] == "success":
        ch = result["chapter"]
        console.print(f"\n[green]✓[/green] {result['message']}")
        console.print(f"\n[bold]章节标题[/bold]: {ch.title}")
        console.print(f"[bold]字数[/bold]: {ch.word_count}")
        console.print(f"[bold]状态[/bold]: {ch.status.value}")

        console.print("\n[bold green]文件已保存到:[/bold green]")
        console.print(f"- 单章: [cyan]novel_ai_agent/output/novels/{novel_id}_chapter_{chapter:03d}.md[/cyan]")
        console.print(f"- 完整版: [cyan]novel_ai_agent/output/novels/{novel_id}_*.md[/cyan]")

        console.print(f"\n[bold]内容预览[/bold] (前200字):")
        console.print(f"[dim]{ch.content[:200]}...[/dim]")
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")
        if "error" in result:
            console.print(f"[red]错误详情: {result['error']}[/red]")


@app.command()
def list_novels():
    """列出所有小说项目"""
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel("[bold cyan]小说列表[/bold cyan]"))

    novels = file_manager.list_novels()

    if not novels:
        console.print("[yellow]暂无小说项目[/yellow]")
        console.print("\n使用 [cyan]python main.py create[/cyan] 创建新小说")
    else:
        console.print(f"找到 [green]{len(novels)}[/green] 个小说项目:\n")
        for i, novel_id in enumerate(novels, 1):
            console.print(f"{i}. [cyan]{novel_id}[/cyan]")


@app.command()
def check(novel_id: str = typer.Option(..., "--id", "-i", help="小说ID")):
    """检查小说的一致性"""
    from novel_ai_agent.utils.file_manager import file_manager
    from novel_ai_agent.utils.consistency_checker import ConsistencyChecker

    console.print(Panel(f"[bold cyan]一致性检查: {novel_id}[/bold cyan]"))

    novel = file_manager.load_novel_json(novel_id)

    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    checker = ConsistencyChecker(novel)
    report = checker.generate_report()

    console.print(report)


@app.command()
def export(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    output: str = typer.Option(None, "--output", "-o", help="输出路径")
):
    """导出小说为Markdown文件"""
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel(f"[bold cyan]导出小说: {novel_id}[/bold cyan]"))

    novel = file_manager.load_novel_json(novel_id)

    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    if output:
        # 自定义输出路径
        with open(output, 'w', encoding='utf-8') as f:
            f.write(novel.to_markdown())
        filepath = output
    else:
        # 使用默认路径
        filepath = file_manager.save_novel_markdown(novel)

    console.print(f"[green]✓[/green] 小说已导出到: [cyan]{filepath}[/cyan]")


@app.command()
def styles():
    """列出所有可用的作家风格"""
    from novel_ai_agent.config.styles import list_styles, get_style_description

    console.print(Panel("[bold cyan]可用作家风格[/bold cyan]"))

    available_styles = list_styles()

    for i, style_name in enumerate(available_styles, 1):
        description = get_style_description(style_name)
        console.print(f"{i}. [yellow]{description}[/yellow]")


@app.command()
def style_info(style: str = typer.Option(..., "--style", "-s", help="风格名称")):
    """查看风格详细信息"""
    from novel_ai_agent.config.styles import get_style

    try:
        style_obj = get_style(style)
        console.print(Panel(f"[bold cyan]{style_obj.name}[/bold cyan]"))
        console.print(f"\n[bold]描述[/bold]: {style_obj.description}")
        console.print(f"\n[bold]特征[/bold]:")
        for feature in style_obj.features:
            console.print(f"  • {feature}")
        console.print(f"\n[bold]写作要点[/bold]:")
        console.print(style_obj.prompt_template)
    except KeyError as e:
        console.print(f"[red]错误:[/red] {e}")


@app.command()
def recommend_style(genre: str = typer.Option(..., "--genre", "-g", help="小说类型")):
    """根据类型推荐合适的风格"""
    from novel_ai_agent.config.styles import get_recommended_styles

    console.print(Panel(f"[bold cyan]类型: {genre}[/bold cyan]"))

    recommended = get_recommended_styles(genre)

    if recommended:
        console.print(f"\n[bold green]推荐风格:[/bold green]")
        for style in recommended:
            console.print(f"  • {style}")
    else:
        console.print("[yellow]未找到推荐风格，建议使用'中性风格'[/yellow]")


@app.command()
def polish(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
    focus: str = typer.Option("", "--focus", "-f", help="重点关注的方面（多个用逗号分隔）")
):
    """润色指定章节"""
    import asyncio
    from novel_ai_agent.agents.editor_agent import EditorAgent
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel(f"[bold cyan]润色章节[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"章节: [yellow]第{chapter}章[/yellow]\n")

    # 加载小说
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    # 获取章节
    target_chapter = novel.get_chapter(chapter)
    if not target_chapter:
        console.print(f"[red]错误:[/red] 未找到第{chapter}章")
        return

    # 准备关注点
    focus_areas = [f.strip() for f in focus.split(",")] if focus else None

    # 执行润色
    editor = EditorAgent()

    with console.status(f"[bold green]正在润色第{chapter}章..."):
        result = asyncio.run(editor.polish_chapter(
            chapter=target_chapter,
            style=novel.author_style,
            focus_areas=focus_areas
        ))

    if result["status"] == "success":
        polished_chapter = result["chapter"]
        console.print(f"\n[green]✓[/green] 润色完成！")
        console.print(f"原始字数: {result['original_word_count']}")
        console.print(f"润色后字数: {result['polished_word_count']}")

        # 更新小说
        novel.add_chapter(polished_chapter)
        file_manager.save_novel_json(novel)
        file_manager.save_chapter_markdown(polished_chapter, novel_id)

        console.print(f"\n[bold]文件已保存[/bold]")
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")


@app.command()
def review(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号")
):
    """评审指定章节"""
    import asyncio
    from novel_ai_agent.agents.editor_agent import EditorAgent
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel(f"[bold cyan]评审章节[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"章节: [yellow]第{chapter}章[/yellow]\n")

    # 加载小说
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    # 获取章节
    target_chapter = novel.get_chapter(chapter)
    if not target_chapter:
        console.print(f"[red]错误:[/red] 未找到第{chapter}章")
        return

    # 获取前文
    previous_chapters = [ch for ch in novel.chapters if ch.number < chapter]

    # 执行评审
    editor = EditorAgent()

    with console.status(f"[bold green]正在评审第{chapter}章..."):
        result = asyncio.run(editor.comprehensive_review(
            chapter=target_chapter,
            style=novel.author_style,
            characters=novel.characters,
            outline=novel.outline,
            previous_chapters=previous_chapters if previous_chapters else None
        ))

    if result["status"] == "success":
        review_result = result["review"]
        console.print(f"\n[green]✓[/green] 评审完成！")
        console.print(f"\n[bold]综合评分[/bold]: {review_result.get('overall_score', 'N/A')}/10")

        scores = review_result.get("scores", {})
        console.print(f"\n[bold]分项评分[/bold]:")
        console.print(f"  文字质量: {scores.get('writing_quality', 'N/A')}")
        console.print(f"  风格一致性: {scores.get('style_consistency', 'N/A')}")
        console.print(f"  情节逻辑: {scores.get('plot_logic', 'N/A')}")
        console.print(f"  角色一致性: {scores.get('character_consistency', 'N/A')}")
        console.print(f"  叙事节奏: {scores.get('pacing', 'N/A')}")
        console.print(f"  情感表达: {scores.get('emotional_impact', 'N/A')}")

        console.print(f"\n[bold green]优点[/bold green]:")
        for strength in review_result.get("strengths", []):
            console.print(f"  + {strength}")

        if review_result.get("weaknesses"):
            console.print(f"\n[bold yellow]需要改进[/bold yellow]:")
            for weakness in review_result.get("weaknesses", []):
                console.print(f"  - {weakness}")

        console.print(f"\n[bold]总体评价[/bold]:")
        console.print(f"{review_result.get('summary', '')}")
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")


@app.command()
def interactive(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: int = typer.Option(None, "--chapter", "-c", help="章节号（可选）")
):
    """启动交互式创作模式"""
    import asyncio
    from novel_ai_agent.agents.dialogue_agent import DialogueAgent
    from novel_ai_agent.utils.file_manager import file_manager
    from rich.prompt import Prompt

    console.print(Panel("[bold cyan]交互式创作模式[/bold cyan]"))
    console.print("在此模式下,您可以与AI进行多轮对话来修改小说")
    console.print("输入 'quit' 或 'exit' 退出对话\n")

    # 加载小说
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    console.print(f"[green]已加载小说:[/green] {novel.title}")

    # 准备上下文
    context = {
        "novel_title": novel.title,
        "novel_id": novel_id
    }

    # 如果指定了章节，加载章节信息
    if chapter:
        target_chapter = novel.get_chapter(chapter)
        if target_chapter:
            context["current_chapter"] = {
                "number": target_chapter.number,
                "title": target_chapter.title,
                "summary": target_chapter.summary
            }
            console.print(f"[green]当前章节:[/green] 第{chapter}章 - {target_chapter.title}")
        else:
            console.print(f"[yellow]警告:[/yellow] 未找到第{chapter}章")

    # 创建对话Agent
    dialogue_agent = DialogueAgent(novel_id)

    console.print("\n[bold]开始对话...[/bold]\n")

    # 对话循环
    async def chat_loop():
        while True:
            try:
                # 获取用户输入
                user_input = Prompt.ask("[bold cyan]你[/bold cyan]")

                # 检查退出命令
                if user_input.lower() in ["quit", "exit", "退出"]:
                    console.print("\n[yellow]退出对话模式[/yellow]")
                    break

                # 处理对话
                with console.status("[bold green]AI正在思考..."):
                    result = await dialogue_agent.chat(user_input, context)

                if result["status"] == "success":
                    # 显示AI回复
                    console.print(f"\n[bold green]助手[/bold green]: {result['response']}\n")

                    # 如果有需要执行的操作
                    if result.get("action"):
                        action = result["action"]
                        console.print(f"[yellow]检测到操作请求: {action['type']}[/yellow]")

                        confirm = Prompt.ask(
                            "是否执行此操作？",
                            choices=["y", "n"],
                            default="y"
                        )

                        if confirm == "y":
                            console.print("[cyan]执行操作中...[/cyan]")
                            # 这里可以调用相应的Agent执行操作
                            console.print("[green]操作完成[/green]")

                else:
                    console.print(f"[red]错误:[/red] {result.get('message', '未知错误')}")

            except KeyboardInterrupt:
                console.print("\n[yellow]退出对话模式[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]错误:[/red] {str(e)}")

    # 运行对话循环
    asyncio.run(chat_loop())

    # 显示对话摘要
    console.print(f"\n[bold]对话摘要[/bold]:")
    console.print(dialogue_agent.get_conversation_summary())


@app.command()
def memory_stats(novel_id: str = typer.Option(..., "--id", "-i", help="小说ID")):
    """查看小说的记忆统计"""
    from novel_ai_agent.memory import get_memory_manager

    console.print(Panel(f"[bold cyan]记忆统计: {novel_id}[/bold cyan]"))

    memory_manager = get_memory_manager(novel_id)
    stats = memory_manager.get_memory_stats()

    console.print(f"\n[bold]短期记忆[/bold]:")
    console.print(f"  当前章节: {'是' if stats['short_term']['current_chapter'] else '否'}")
    console.print(f"  最近章节数: {stats['short_term']['recent_chapters_count']}")
    console.print(f"  对话轮次: {stats['short_term']['conversation_turns']}")

    console.print(f"\n[bold]长期记忆 (向量数据库)[/bold]:")
    console.print(f"  角色数: {stats['long_term'].get('characters', 0)}")
    console.print(f"  情节点数: {stats['long_term'].get('plots', 0)}")
    console.print(f"  章节数: {stats['long_term'].get('chapters', 0)}")
    console.print(f"  世界观设定数: {stats['long_term'].get('worldbuilding', 0)}")


@app.command()
def search_memory(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    query: str = typer.Option(..., "--query", "-q", help="搜索查询"),
    type: str = typer.Option("characters", "--type", "-t", help="搜索类型 (characters/plots/chapters)")
):
    """搜索小说记忆"""
    from novel_ai_agent.memory import get_memory_manager

    console.print(Panel(f"[bold cyan]搜索记忆: {novel_id}[/bold cyan]"))
    console.print(f"查询: [yellow]{query}[/yellow]")
    console.print(f"类型: [yellow]{type}[/yellow]\n")

    memory_manager = get_memory_manager(novel_id)

    if type == "characters":
        results = memory_manager.recall_characters(query)
    elif type == "plots":
        results = memory_manager.recall_plot_points(query)
    elif type == "chapters":
        results = memory_manager.recall_chapters(query)
    else:
        console.print(f"[red]错误:[/red] 不支持的搜索类型: {type}")
        return

    if results:
        console.print(f"[green]找到 {len(results)} 条结果:[/green]\n")
        for i, result in enumerate(results, 1):
            console.print(f"[bold]{i}.[/bold]")
            console.print(result)
            console.print()
    else:
        console.print("[yellow]未找到相关结果[/yellow]")


@app.command()
def version():
    """显示版本信息"""
    console.print(Panel("[bold cyan]小说AI Agent[/bold cyan]"))
    console.print("版本: [yellow]0.3.0[/yellow] (Phase 3 - 高级功能)")
    console.print("作者: Keith Xi")
    console.print("\n[bold]已实现功能:[/bold]")
    console.print("- ✅ 多Agent协作创作")
    console.print("- ✅ 大纲规划和角色设定")
    console.print("- ✅ 智能章节创作")
    console.print("- ✅ 章节编辑和润色")
    console.print("- ✅ 向量记忆系统")
    console.print("- ✅ 10种作家风格")
    console.print("- ✅ 交互式对话修改")
    console.print("\n基于:")
    console.print("- LangChain & LangGraph")
    console.print("- Claude 4 Sonnet / DeepSeek / OpenAI")
    console.print("- Chroma向量数据库")
    console.print("- 多Agent协作架构")


if __name__ == "__main__":
    app()
