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
def interactive():
    """启动交互式创作模式"""
    console.print(Panel("[bold cyan]交互式创作模式[/bold cyan]"))
    console.print("在此模式下,您可以与AI进行多轮对话来创作小说\n")

    # TODO: 实现交互式对话循环
    console.print("[yellow]功能开发中...[/yellow]")
    console.print("该功能将在Phase 3完成")


@app.command()
def version():
    """显示版本信息"""
    console.print(Panel("[bold cyan]小说AI Agent[/bold cyan]"))
    console.print("版本: [yellow]0.1.0[/yellow] (Phase 1 - 基础框架)")
    console.print("作者: Keith Xi")
    console.print("\n基于:")
    console.print("- LangChain & LangGraph")
    console.print("- Claude 4 Sonnet")
    console.print("- 多Agent协作架构")


if __name__ == "__main__":
    app()
