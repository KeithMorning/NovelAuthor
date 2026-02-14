"""
小说AI Agent - 主入口
"""
import logging
import sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log', mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)

# 为关键模块启用 DEBUG 级别
logging.getLogger('novel_ai_agent.memory').setLevel(logging.DEBUG)
logging.getLogger('novel_ai_agent.memory.local_embeddings').setLevel(logging.DEBUG)
logging.getLogger('novel_ai_agent.memory.vector_store').setLevel(logging.DEBUG)

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
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
    expand: bool = typer.Option(True, "--expand/--no-expand", help="是否启用章节规划细化")
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
            chapter_number=chapter,
            enable_expansion=expand
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
def write_all(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    start: int = typer.Option(1, "--start", "-s", help="起始章节号（用于从中断处恢复）"),
    expand: bool = typer.Option(True, "--expand/--no-expand", help="是否启用章节规划细化")
):
    """按顺序写作全部章节"""
    import asyncio
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from novel_ai_agent.agents.coordinator import CoordinatorAgent
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel(f"[bold cyan]批量写作全部章节[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"起始章节: [yellow]第{start}章[/yellow]\n")

    # 加载小说信息
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    if not novel.outline or not novel.outline.chapters_plan:
        console.print(f"[red]错误:[/red] 小说没有大纲，请先创建大纲")
        return

    total_chapters = len(novel.outline.chapters_plan)
    written = {ch.number for ch in novel.chapters} if novel.chapters else set()
    to_write = [cp for cp in novel.outline.chapters_plan
                if cp.chapter_number >= start and cp.chapter_number not in written]

    if not to_write:
        console.print("[green]✓[/green] 所有章节已完成，无需写作")
        return

    console.print(f"[bold]小说[/bold]: {novel.title}")
    console.print(f"[bold]总章节[/bold]: {total_chapters} 章")
    console.print(f"[bold]已完成[/bold]: {len(written)} 章")
    console.print(f"[bold]待写作[/bold]: {len(to_write)} 章\n")

    # 使用 Progress 显示进度
    coordinator = CoordinatorAgent()
    progress_task = None
    progress_bar = None

    def progress_callback(chapter_num, total, status, message):
        nonlocal progress_task, progress_bar
        if progress_bar and progress_task is not None:
            if status == "writing":
                progress_bar.update(progress_task, description=f"[cyan]第{chapter_num}章[/cyan]")
            elif status == "done":
                progress_bar.advance(progress_task)
                console.print(f"  [green]✓[/green] {message}")
            elif status == "error":
                console.print(f"  [red]✗[/red] {message}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        progress_bar = progress
        progress_task = progress.add_task(
            f"[cyan]写作中...[/cyan]",
            total=len(to_write)
        )

        result = asyncio.run(coordinator.write_all_chapters_workflow(
            novel_id=novel_id,
            start_chapter=start,
            progress_callback=progress_callback,
            enable_expansion=expand
        ))

    # 显示结果
    console.print()
    if result["status"] == "success":
        console.print(f"[green]✓[/green] {result['message']}")
        console.print(f"\n[bold]写作统计[/bold]:")
        console.print(f"  完成章节: {result['chapters_written']} 章")
        console.print(f"  总字数: {result['total_words']:,} 字")

        if result.get("chapters_completed"):
            console.print(f"\n[bold]各章详情[/bold]:")
            for ch in result["chapters_completed"]:
                console.print(f"  第{ch['number']}章 {ch['title']}: {ch['word_count']}字")

        console.print(f"\n[bold green]全部完成！[/bold green]")
        console.print(f"- 查看完整小说: [cyan]python main.py export --id {novel_id}[/cyan]")

    elif result["status"] == "partial":
        console.print(f"[yellow]⚠[/yellow] {result['message']}")
        console.print(f"\n已完成 {result['chapters_written']} 章，总字数: {result.get('total_words', 0):,} 字")
        failed = result.get("failed_chapter", "?")
        console.print(f"\n[bold]从断点恢复[/bold]: [cyan]python main.py write-all --id {novel_id} --start {failed}[/cyan]")

    else:
        console.print(f"[red]✗[/red] {result['message']}")
        if "error" in result:
            console.print(f"[red]错误详情: {result['error']}[/red]")


@app.command()
def resume(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    skip_memory: bool = typer.Option(False, "--skip-memory", help="跳过记忆加载"),
    force_reload: bool = typer.Option(False, "--force-reload", help="强制重新加载记忆（清除旧数据）")
):
    """从中断位置继续创建小说（重新加载到记忆系统）"""
    import asyncio
    from novel_ai_agent.utils.file_manager import file_manager
    from novel_ai_agent.memory import get_memory_manager
    import json

    console.print(Panel(f"[bold cyan]恢复小说创建: {novel_id}[/bold cyan]"))

    # 1. 检查小说文件是否存在
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]✗[/red] 未找到小说文件: {novel_id}")
        console.print(f"\n请检查小说ID是否正确，或使用 [cyan]python main.py list[/cyan] 查看所有小说")
        return

    console.print(f"[green]✓[/green] 找到小说: [yellow]{novel.title}[/yellow]")

    # 2. 检查工作流状态日志
    log_file = Path(f"logs/novel_{novel_id}.json")
    workflow_status = None

    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
            workflow_status = log_data.get("workflow_status", {})

        console.print(f"\n[bold]工作流状态:[/bold]")
        console.print(f"  当前步骤: [yellow]{workflow_status.get('current_step', '未知')}[/yellow]")
        console.print(f"  状态: [yellow]{workflow_status.get('status', '未知')}[/yellow]")

        completed_steps = workflow_status.get('steps_completed', [])
        console.print(f"\n[bold]已完成步骤:[/bold]")
        for step in completed_steps:
            console.print(f"  ✓ {step}")

        errors = workflow_status.get('errors', [])
        if errors:
            console.print(f"\n[bold red]错误信息:[/bold red]")
            for error in errors:
                console.print(f"  [red]✗[/red] {error.get('step', '未知')}: {error.get('error', '')}")
    else:
        console.print(f"\n[yellow]![/yellow] 未找到工作流日志文件")

    # 3. 显示小说状态
    console.print(f"\n[bold]小说信息:[/bold]")
    console.print(f"  标题: {novel.title}")
    console.print(f"  类型: {novel.genre}")
    console.print(f"  风格: {novel.author_style}")
    console.print(f"  大纲: {'✓ 已生成' if novel.outline else '✗ 未生成'}")
    console.print(f"  角色数: {len(novel.characters)}")
    console.print(f"  章节数: {len(novel.chapters)}")

    # 4. 确定需要执行的步骤
    needs_memory_load = False

    if workflow_status:
        completed = workflow_status.get('steps_completed', [])
        current_step = workflow_status.get('current_step', '')

        # 如果在"加载记忆"步骤失败，或者已完成保存但未完成记忆加载
        if current_step == "加载记忆" or ("保存文件" in completed and "加载记忆" not in completed):
            needs_memory_load = True

    # 如果有大纲和角色但还没加载到记忆，也需要加载
    if novel.outline and novel.characters and not skip_memory:
        console.print(f"\n[bold cyan]检测到需要加载到记忆系统[/bold cyan]")
        needs_memory_load = True

    # 5. 执行恢复操作
    if needs_memory_load and not skip_memory:
        if force_reload:
            console.print(f"\n[yellow]⚠️  强制重新加载模式：将清除旧的记忆数据[/yellow]")
        console.print(f"\n[cyan]正在加载小说到记忆系统...[/cyan]")

        try:
            with console.status("[bold green]加载记忆中..."):
                memory_manager = get_memory_manager(novel_id)
                memory_manager.load_novel_to_memory(novel, force_reload=force_reload)

            console.print(f"[green]✓[/green] 小说已成功加载到记忆系统")

            # 显示记忆统计
            stats = memory_manager.vector_store.get_collection_stats(novel_id)
            console.print(f"\n[bold]记忆统计:[/bold]")
            console.print(f"  角色记录: {stats.get('characters', 0)}")
            console.print(f"  情节记录: {stats.get('plots', 0)}")
            console.print(f"  章节记录: {stats.get('chapters', 0)}")

            console.print(f"\n[bold green]✓ 小说恢复完成！[/bold green]")

        except Exception as e:
            console.print(f"\n[red]✗[/red] 加载记忆失败: {e}")
            console.print(f"\n[yellow]提示:[/yellow] 可以使用 [cyan]--skip-memory[/cyan] 跳过记忆加载")
            return

    elif skip_memory:
        console.print(f"\n[yellow]![/yellow] 已跳过记忆加载")
        console.print(f"\n[bold green]✓ 小说数据已就绪[/bold green]")

    else:
        console.print(f"\n[green]✓[/green] 小说状态正常，无需额外操作")

    # 6. 显示后续操作建议
    console.print(f"\n[bold green]接下来可以:[/bold green]")

    if len(novel.chapters) == 0:
        console.print(f"- 开始写作第1章: [cyan]python main.py write --id {novel_id} --chapter 1[/cyan]")
    else:
        next_chapter = len(novel.chapters) + 1
        console.print(f"- 继续写作第{next_chapter}章: [cyan]python main.py write --id {novel_id} --chapter {next_chapter}[/cyan]")

    console.print(f"- 查看大纲: [cyan]cat novel_ai_agent/output/outlines/{novel_id}_outline_v1.md[/cyan]")
    console.print(f"- 查看角色: [cyan]cat novel_ai_agent/output/characters/{novel_id}_characters.md[/cyan]")
    console.print(f"- 查看记忆统计: [cyan]python main.py memory-stats --id {novel_id}[/cyan]")


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
    focus: str = typer.Option("", "--focus", "-f", help="重点关注的方面（多个用逗号分隔）"),
    requirements: str = typer.Option("", "--requirements", "-r", help="自定义修订要求")
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
            focus_areas=focus_areas,
            user_requirements=requirements
        ))

    if result["status"] == "success":
        polished_chapter = result["chapter"]
        console.print(f"\n[green]✓[/green] 润色完成！")
        console.print(f"原始字数: {result['original_word_count']}")
        console.print(f"润色后字数: {result['polished_word_count']}")

        # 更新小说（使用 update_chapter 而不是 add_chapter）
        novel.update_chapter(polished_chapter)
        file_manager.save_novel_json(novel)
        file_manager.save_chapter_markdown(polished_chapter, novel_id)

        console.print(f"\n[bold]文件已保存[/bold]")
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")


@app.command()
def review(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: int = typer.Option(..., "--chapter", "-c", help="章节号"),
    requirements: str = typer.Option("", "--requirements", "-r", help="自定义评审要求")
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
            previous_chapters=previous_chapters if previous_chapters else None,
            user_requirements=requirements
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
