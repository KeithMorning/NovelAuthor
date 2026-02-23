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
from prompt_toolkit import PromptSession as _PTSession
_pt_session = _PTSession()

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

app = typer.Typer(help="小说AI Agent - 基于多Agent协作的AI小说创作系统")
console = Console()

# 工具名 → 语义化中文映射
_TOOL_LABELS = {
    "expand_chapter":    "细化章节规划",
    "polish_chapter":    "润色章节内容",
    "revise_chapter":    "修改章节内容",
    "modify_outline":    "修改小说大纲",
    "modify_character":  "修改角色设定",
    "redesign_characters": "重新设计角色",
}


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
    requirements: str = typer.Option("", "--requirements", "-r", help="额外需求"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="创建后进入交互式对话模式进行修改"),
    auto: bool = typer.Option(False, "--auto", "-a", help="创建后自动按顺序写完所有章节")
):
    """创建新小说项目 (包含大纲和角色)"""
    import asyncio
    from novel_ai_agent.agents.coordinator import CoordinatorAgent
    from novel_ai_agent.utils.file_manager import file_manager

    # 支持从本地文件读取主题内容
    theme_path = Path(theme)
    if theme_path.exists() and theme_path.is_file():
        theme = theme_path.read_text(encoding="utf-8").strip()
        console.print(f"[dim]从文件读取主题: {theme_path}[/dim]")

    console.print(Panel(f"[bold cyan]创建新小说: {title}[/bold cyan]"))
    console.print(f"类型: [yellow]{genre}[/yellow]")
    console.print(f"主题: [yellow]{theme[:80]}{'...' if len(theme) > 80 else ''}[/yellow]")
    console.print(f"风格: [yellow]{style}[/yellow]")
    console.print(f"章节数: [yellow]{chapters}[/yellow]\n")


    console.print("[cyan]正在创建小说...[/cyan]")

    # 调用CoordinatorAgent创建小说
    coordinator = CoordinatorAgent()

    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    # 定义创建流程的步骤列表（按顺序）
    STEPS = ["角色生成", "大纲生成", "保存文件"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        step_tasks = {
            step: progress.add_task(f"[dim]  {step}[/dim]", total=1, start=False)
            for step in STEPS
        }

        def progress_callback(step_name: str, status: str, message: str):
            task_id = step_tasks.get(step_name)
            if task_id is None:
                return
            if status == "start":
                progress.start_task(task_id)
                progress.update(task_id, description=f"[cyan]⏳ {step_name}[/cyan]  {message}")
            elif status == "done":
                progress.update(task_id, completed=1,
                                description=f"[green]✓  {step_name}[/green]  {message}")
                progress.stop_task(task_id)
            elif status == "error":
                progress.update(task_id, description=f"[red]✗  {step_name}[/red]  {message}")
                progress.stop_task(task_id)

        result = asyncio.run(coordinator.create_novel_workflow(
            title=title,
            genre=genre,
            theme=theme,
            style=style,
            chapter_count=chapters,
            user_requirements=requirements,
            progress_callback=progress_callback
        ))

    if result["status"] == "success":
        console.print(f"\n[green]✓[/green] {result['message']}")
        console.print(f"\n[bold]小说ID[/bold]: [cyan]{result['novel_id']}[/cyan]")
        console.print(f"[bold]大纲章节[/bold]: {len(result['novel'].outline.chapters_plan)}章")
        console.print(f"[bold]角色数量[/bold]: {len(result['novel'].characters)}个")

        # 如果启用了自动写作模式
        if auto:
            novel_id = result['novel_id']
            total_chapters = len(result['novel'].outline.chapters_plan)

            console.print(Panel(f"[bold cyan]自动写作模式 - 共{total_chapters}章[/bold cyan]"))

            # 按顺序写作每一章
            from rich.live import Live
            from rich.text import Text

            for ch in range(1, total_chapters + 1):
                _chars = [0]   # 用列表绕开闭包 nonlocal 限制
                _live_ref2 = [None]

                def _make_on_token(chapter_num, chars_ref, live_ref):
                    def _on_token(token: str):
                        chars_ref[0] += len(token)
                        if live_ref[0]:
                            live_ref[0].update(Text(
                                f"✍  正在写作第{chapter_num}章...  已生成 {chars_ref[0]} 字",
                                style="cyan"
                            ))
                    return _on_token

                _on_token = _make_on_token(ch, _chars, _live_ref2)
                _wr_holder = {}

                async def _do_write(chapter_num=ch):
                    _wr_holder["result"] = await coordinator.write_chapter_workflow(
                        novel_id=novel_id,
                        chapter_number=chapter_num,
                        enable_expansion=True,
                        force=False,
                        on_token=_on_token
                    )

                with Live(Text(f"✍  正在写作第{ch}章...  已生成 0 字", style="cyan"),
                          console=console, refresh_per_second=4) as live2:
                    _live_ref2[0] = live2
                    asyncio.run(_do_write())

                write_result = _wr_holder.get("result", {"status": "error", "message": "未知错误"})


                if write_result["status"] == "success":
                    ch_obj = write_result["chapter"]
                    console.print(f"[green]✓[/green] 第{ch}章完成: {ch_obj.title} ({ch_obj.word_count}字)")
                else:
                    console.print(f"[red]✗[/red] 第{ch}章写作失败: {write_result.get('message', '未知错误')}")
                    break
            else:
                # 所有章节写作完成
                console.print(Panel(f"[bold green]✓ 所有{total_chapters}章写作完成！[/bold green]"))

                # 重新加载小说获取最新信息
                novel = file_manager.load_novel_json(novel_id)
                total_words = sum(c.word_count for c in novel.chapters) if novel.chapters else 0

                console.print(f"\n[bold]小说ID[/bold]: [cyan]{novel_id}[/cyan]")
                console.print(f"[bold]完成章节[/bold]: {len(novel.chapters) if novel.chapters else 0}/{total_chapters}")
                console.print(f"[bold]总字数[/bold]: {total_words}字")
                console.print(f"\n[bold green]文件已保存到:[/bold green]")
                console.print(f"- 完整版: [cyan]novel_ai_agent/output/novels/{novel_id}_*.md[/cyan]")
                return  # 自动完成后直接返回，不进入交互模式

        console.print("\n[bold green]接下来可以:[/bold green]")
        console.print(f"- 查看大纲: [cyan]cat novel_ai_agent/output/outlines/{result['novel_id']}_outline_v1.md[/cyan]")
        console.print(f"- 查看角色: [cyan]cat novel_ai_agent/output/characters/{result['novel_id']}_characters.md[/cyan]")
        console.print(f"- 开始写作: [cyan]python main.py write --id {result['novel_id']} --chapter 1[/cyan]")

        # 如果启用了交互模式，进入对话
        if interactive:
            from novel_ai_agent.agents.dialogue_agent import DialogueAgent
            from rich.prompt import Prompt

            novel_id = result['novel_id']
            novel = result['novel']

            console.print(Panel("[bold cyan]交互式对话模式[/bold cyan]"))
            console.print("您可以对生成的大纲和角色进行修改")
            console.print("输入 'quit' 或 'exit' 退出对话\n")

            # 准备上下文
            context = {
                "novel_title": novel.title,
                "novel_id": novel_id,
                "novel": novel
            }

            # 创建对话Agent
            dialogue_agent = DialogueAgent(novel_id)

            # 对话循环
            async def chat_loop():
                nonlocal novel, dialogue_agent
                console.print(f"\n[dim]大纲概览: {novel.outline.summary[:100]}...[/dim]")
                console.print(f"[dim]角色数: {len(novel.characters)}[/dim]")
                console.print(f"[dim]章节数: {len(novel.outline.chapters_plan)}[/dim]")

                console.print("\n[bold cyan]你可以:[/bold cyan]")
                console.print("  - 细化某章节（如：'细化第3章'）")
                console.print("  - 修改大纲（如：'修改大纲，调整故事走向'）")
                console.print("  - 修改角色（如：'修改角色，让反派更聪明'）")
                console.print("  - 输入 'quit' 或 'exit' 退出\n")

                exec_context = {"novel_id": novel_id, "novel": novel}

                while True:
                    try:
                        user_input = (await _pt_session.prompt_async("你> ")).strip()

                        if user_input.lower() in ["quit", "exit", "退出"]:
                            console.print("\n[yellow]退出对话模式[/yellow]")
                            break

                        if not user_input:
                            continue

                        # 规则路由
                        action = dialogue_agent.fast_route(user_input)
                        if action:
                            console.print(f"[dim]→ {action['reason']}，执行中...[/dim]")
                            exec_context["novel"] = novel
                            with console.status("[bold green]执行中..."):
                                exec_result = await dialogue_agent.execute_action(action, exec_context)
                            if exec_result.get("status") == "success":
                                console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                novel = file_manager.load_novel_json(novel_id)
                                context["novel"] = novel
                            else:
                                console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                        else:
                            with console.status("[bold green]AI正在思考..."):
                                chat_result = await dialogue_agent.chat(user_input, context)
                            if chat_result["status"] == "success":
                                console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")
                                if chat_result.get("action"):
                                    action = chat_result["action"]
                                    console.print(f"[dim]→ {_TOOL_LABELS.get(action['tool'], action.get('reason', action['tool']))}...[/dim]")
                                    exec_context["novel"] = novel
                                    with console.status("[bold green]执行中..."):
                                        exec_result = await dialogue_agent.execute_action(action, exec_context)
                                    if exec_result.get("status") == "success":
                                        console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                        novel = file_manager.load_novel_json(novel_id)
                                        context["novel"] = novel
                                    else:
                                        console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                            else:
                                console.print(f"[red]错误: {chat_result.get('message', '未知错误')}[/red]")

                    except Exception as e:
                        console.print(f"[red]错误: {e}[/red]")


            asyncio.run(chat_loop())
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
    expand: bool = typer.Option(True, "--expand/--no-expand", help="是否启用章节规划细化"),
    review: bool = typer.Option(False, "--review/--no-review", help="写完后自动评审"),
    force: bool = typer.Option(False, "--force", "-f", help="强制重写已存在的章节"),
    interactive: bool = typer.Option(False, "--interactive", help="写完后进入交互式对话模式进行修改")
):
    """写作指定章节"""
    import asyncio
    from novel_ai_agent.agents.coordinator import CoordinatorAgent
    from novel_ai_agent.agents.editor_agent import EditorAgent
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel(f"[bold cyan]写作章节[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"章节: [yellow]第{chapter}章[/yellow]")
    if force:
        console.print(f"[red]模式: 强制重写[/red]\n")
    else:
        console.print()

    # 检查章节是否已存在
    novel = file_manager.load_novel_json(novel_id)
    if novel and novel.chapters:
        existing = [c for c in novel.chapters if c.number == chapter]
        if existing and not force:
            console.print(f"[yellow]⚠️ 第{chapter}章已存在，使用 --force 强制重写[/yellow]")
            return

    # 调用CoordinatorAgent写作章节（流式，单行显示进度）
    coordinator = CoordinatorAgent()

    from rich.live import Live
    from rich.text import Text

    received_chars = 0
    _live_ref = None

    def on_token(token: str):
        nonlocal received_chars
        received_chars += len(token)
        if _live_ref:
            _live_ref.update(Text(f"✍  正在创作第{chapter}章...  已生成 {received_chars} 字", style="cyan"))

    result_holder = {}

    async def _write():
        result_holder["result"] = await coordinator.write_chapter_workflow(
            novel_id=novel_id,
            chapter_number=chapter,
            enable_expansion=expand,
            force=force,
            on_token=on_token
        )

    with Live(Text(f"✍  正在创作第{chapter}章...  已生成 0 字", style="cyan"),
              console=console, refresh_per_second=4) as live:
        _live_ref = live
        asyncio.run(_write())

    result = result_holder.get("result", {"status": "error", "message": "未知错误"})



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

        # 如果启用了自动评审
        if review:
            console.print(f"\n[bold cyan]--- 自动评审 ---[/bold cyan]")

            # 加载小说获取角色和大纲
            novel = file_manager.load_novel_json(novel_id)
            previous_chapters = [c for c in novel.chapters if c.number < chapter] if novel.chapters else []

            editor = EditorAgent()
            with console.status(f"[bold green]正在评审第{chapter}章..."):
                review_result = asyncio.run(editor.comprehensive_review(
                    chapter=ch,
                    style=novel.author_style,
                    characters=novel.characters,
                    outline=novel.outline,
                    previous_chapters=previous_chapters if previous_chapters else None,
                    user_requirements=""
                ))

            if review_result["status"] == "success":
                review_data = review_result["review"]
                console.print(f"\n[bold]评分: {review_data.get('overall_score', 'N/A')}/10[/bold]")

                # 重点显示情节问题
                plot_issues = review_data.get("plot_issues", {})
                if plot_issues:
                    has_jumps = plot_issues.get("has_jumps", False)
                    has_contradictions = plot_issues.get("has_contradictions", False)

                    if has_jumps or has_contradictions:
                        console.print(f"\n[bold red]⚠️ 情节问题检测:[/bold red]")

                        if has_jumps:
                            console.print(f"[yellow]发现情节跳跃:[/yellow]")
                            for jump in plot_issues.get("jump_details", []):
                                console.print(f"  • {jump}")

                        if has_contradictions:
                            console.print(f"[red]发现情节矛盾:[/red]")
                            for contr in plot_issues.get("contradiction_details", []):
                                console.print(f"  • {contr}")

                        console.print(f"\n[bold]使用以下命令查看完整评审:[/bold]")
                        console.print(f"  python main.py review --id {novel_id} --chapter {chapter}")
                    else:
                        console.print(f"\n[green]✓ 未发现情节跳跃或矛盾[/green]")

                # 显示修改建议
                suggestions = review_data.get("revision_suggestions", [])
                if suggestions:
                    high_priority = [s for s in suggestions if s.get("priority") == "高"]
                    if high_priority:
                        console.print(f"\n[bold yellow]高优先级修改建议:[/bold yellow]")
                        for s in high_priority:
                            console.print(f"  • {s.get('area')}: {s.get('suggestion')}")

        # 如果启用了交互模式，进入对话
        if interactive:
            from novel_ai_agent.agents.dialogue_agent import DialogueAgent
            from rich.prompt import Prompt

            # 重新加载最新章节
            novel = file_manager.load_novel_json(novel_id)
            current_ch = novel.get_chapter(chapter) if novel else None

            console.print(Panel("[bold cyan]交互式对话模式[/bold cyan]"))
            console.print("您可以对本章进行修改")
            console.print("输入 'quit' 或 'exit' 退出对话\n")

            # 准备上下文
            context = {
                "novel_title": novel.title,
                "novel_id": novel_id,
                "novel": novel,
                "current_chapter": {
                    "number": chapter,
                    "title": current_ch.title if current_ch else "",
                    "summary": current_ch.summary if current_ch else ""
                }
            }

            # 创建对话Agent
            dialogue_agent = DialogueAgent(novel_id)

            # 对话循环
            async def chat_loop():
                nonlocal novel, current_ch, dialogue_agent
                console.print(f"\n[dim]当前章节: 第{chapter}章 - {current_ch.title if current_ch else ''}[/dim]")
                console.print(f"[dim]本章字数: {current_ch.word_count if current_ch else 0}[/dim]")

                console.print("\n[bold cyan]你可以:[/bold cyan]")
                console.print("  - 修改本章（如：'修改第N章，让对话更自然'）")
                console.print("  - 润色本章（如：'润色第N章'）")
                console.print("  - 细化章节规划（如：'细化第X章'）")
                console.print("  - 修改大纲（如：'修改大纲'）")
                console.print("  - 输入 'quit' 或 'exit' 退出\n")

                exec_context = {"novel_id": novel_id, "novel": novel}

                while True:
                    try:
                        user_input = (await _pt_session.prompt_async("你> ")).strip()

                        if user_input.lower() in ["quit", "exit", "退出"]:
                            console.print("\n[yellow]退出对话模式[/yellow]")
                            break

                        if not user_input:
                            continue

                        # 规则路由
                        action = dialogue_agent.fast_route(user_input)
                        if action:
                            console.print(f"[dim]→ {action['reason']}，执行中...[/dim]")
                            exec_context["novel"] = novel
                            with console.status("[bold green]执行中..."):
                                exec_result = await dialogue_agent.execute_action(action, exec_context)
                            if exec_result.get("status") == "success":
                                console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                novel = file_manager.load_novel_json(novel_id)
                                current_ch = novel.get_chapter(chapter) if novel else None
                                context["novel"] = novel
                                if current_ch:
                                    console.print(f"\n[bold]内容预览[/bold] (前200字):")
                                    console.print(f"[dim]{current_ch.content[:200]}...[/dim]")
                            else:
                                console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                        else:
                            with console.status("[bold green]AI正在思考..."):
                                chat_result = await dialogue_agent.chat(user_input, context)
                            if chat_result["status"] == "success":
                                console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")
                                if chat_result.get("action"):
                                    action = chat_result["action"]
                                    console.print(f"[dim]→ {_TOOL_LABELS.get(action['tool'], action.get('reason', action['tool']))}...[/dim]")
                                    exec_context["novel"] = novel
                                    with console.status("[bold green]执行中..."):
                                        exec_result = await dialogue_agent.execute_action(action, exec_context)
                                    if exec_result.get("status") == "success":
                                        console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                        novel = file_manager.load_novel_json(novel_id)
                                        current_ch = novel.get_chapter(chapter) if novel else None
                                        context["novel"] = novel
                                        if current_ch:
                                            console.print(f"\n[bold]内容预览[/bold] (前200字):")
                                            console.print(f"[dim]{current_ch.content[:200]}...[/dim]")
                                    else:
                                        console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                            else:
                                console.print(f"[red]错误: {chat_result.get('message', '未知错误')}[/red]")

                    except Exception as e:
                        console.print(f"[red]错误: {e}[/red]")


            asyncio.run(chat_loop())
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")
        if "error" in result:
            console.print(f"[red]错误详情: {result['error']}[/red]")


@app.command()
def write_all(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    start: int = typer.Option(1, "--start", "-s", help="起始章节号（用于从中断处恢复）"),
    expand: bool = typer.Option(True, "--expand/--no-expand", help="是否启用章节规划细化"),
    force: bool = typer.Option(False, "--force", "-f", help="强制重写已存在的章节"),
    interactive: bool = typer.Option(False, "--interactive", help="写完后进入交互式对话模式进行修改")
):
    """按顺序写作全部章节"""
    import asyncio
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from novel_ai_agent.agents.coordinator import CoordinatorAgent
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel(f"[bold cyan]批量写作全部章节[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"起始章节: [yellow]第{start}章[/yellow]")
    if force:
        console.print(f"[red]模式: [bold]强制重写[/bold]（将覆盖已存在的章节）[/red]\n")
    else:
        console.print()

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

    if force:
        # force=True: 重写所有从 start 开始的章节
        to_write = [cp for cp in novel.outline.chapters_plan
                    if cp.chapter_number >= start]
    else:
        # force=False: 跳过已存在的章节
        to_write = [cp for cp in novel.outline.chapters_plan
                    if cp.chapter_number >= start and cp.chapter_number not in written]

    if not to_write:
        action = "重写" if force else "写作"
        console.print(f"[green]✓[/green] 所有章节已完成，无需{action}")
        return

    console.print(f"[bold]小说[/bold]: {novel.title}")
    console.print(f"[bold]总章节[/bold]: {total_chapters} 章")
    console.print(f"[bold]已完成[/bold]: {len(written)} 章")
    console.print(f"[bold]待写作[/bold]: {len(to_write)} 章")
    if force:
        console.print(f"[yellow]⚠️  将重写 {len([cp for cp in to_write if cp.chapter_number in written])} 个已存在章节[/yellow]\n")
    else:
        console.print()

    # 逐章写作，用 Progress.update(description) 显示实时字数
    coordinator = CoordinatorAgent()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task(
            f"[cyan]第{to_write[0].chapter_number}章[/cyan]",
            total=len(to_write)
        )

        chapters_completed = []
        total_words = 0
        failed = False

        for cp in to_write:
            ch_num = cp.chapter_number
            chars = [0]  # 用列表在闭包里计数

            def make_on_token(n, c):
                def on_token(token: str):
                    c[0] += len(token)
                    progress.update(
                        task,
                        description=f"[cyan]第{n}章[/cyan]  [dim]已生成 {c[0]} 字[/dim]"
                    )
                return on_token

            _on_token = make_on_token(ch_num, chars)
            _holder = {}

            async def _do(chapter_num=ch_num, tok=_on_token):
                _holder["r"] = await coordinator.write_chapter_workflow(
                    novel_id=novel_id,
                    chapter_number=chapter_num,
                    enable_expansion=expand,
                    force=force,
                    on_token=tok
                )

            asyncio.run(_do())
            result = _holder.get("r", {"status": "error", "message": "未知错误"})

            if result["status"] == "success":
                ch_obj = result["chapter"]
                chapters_completed.append({
                    "number": ch_obj.number,
                    "title": ch_obj.title,
                    "word_count": ch_obj.word_count
                })
                total_words += ch_obj.word_count
                progress.advance(task)
                progress.print(
                    f"  [green]✓[/green] 第{ch_num}章完成: {ch_obj.title} ({ch_obj.word_count}字)"
                )
                # 更新下一章的描述
                next_chapters = [c for c in to_write if c.chapter_number > ch_num]
                if next_chapters:
                    progress.update(
                        task,
                        description=f"[cyan]第{next_chapters[0].chapter_number}章[/cyan]"
                    )
            else:
                progress.print(
                    f"  [red]✗[/red] 第{ch_num}章写作失败: {result.get('message', '未知错误')}"
                )
                failed = True
                break

    result = {
        "status": "error" if failed else "success",
        "message": f"完成 {len(chapters_completed)}/{len(to_write)} 章" if failed
                   else f"✓ 全部 {len(chapters_completed)} 章创作完成！总字数: {total_words:,}",
        "chapters_written": len(chapters_completed),
        "total_words": total_words,
        "chapters_completed": chapters_completed
    }

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

        # 如果启用了交互模式，进入对话
        if interactive:
            from novel_ai_agent.agents.dialogue_agent import DialogueAgent
            from rich.prompt import Prompt

            # 重新加载最新小说
            novel = file_manager.load_novel_json(novel_id)

            console.print(Panel("[bold cyan]交互式对话模式[/bold cyan]"))
            console.print("您可以对小说进行修改")
            console.print("输入 'quit' 或 'exit' 退出对话\n")

            # 准备上下文
            context = {
                "novel_title": novel.title,
                "novel_id": novel_id,
                "novel": novel
            }

            # 创建对话Agent
            dialogue_agent = DialogueAgent(novel_id)

            # 对话循环
            async def chat_loop():
                nonlocal novel, dialogue_agent
                console.print(f"\n[dim]小说: {novel.title}[/dim]")
                console.print(f"[dim]已写章节: {len(novel.chapters) if novel.chapters else 0}[/dim]")
                console.print(f"[dim]大纲章节: {len(novel.outline.chapters_plan) if novel.outline else 0}[/dim]")

                console.print("\n[bold cyan]你可以:[/bold cyan]")
                console.print("  - 修改某章节（如：'修改第3章'）")
                console.print("  - 细化章节规划（如：'细化第5章'）")
                console.print("  - 修改大纲（如：'修改大纲'）")
                console.print("  - 修改角色（如：'修改角色'）")
                console.print("  - 输入 'quit' 或 'exit' 退出\n")

                exec_context = {"novel_id": novel_id, "novel": novel}

                while True:
                    try:
                        user_input = (await _pt_session.prompt_async("你> ")).strip()

                        if user_input.lower() in ["quit", "exit", "退出"]:
                            console.print("\n[yellow]退出对话模式[/yellow]")
                            break

                        if not user_input:
                            continue

                        # 规则路由
                        action = dialogue_agent.fast_route(user_input)
                        if action:
                            console.print(f"[dim]→ {action['reason']}，执行中...[/dim]")
                            exec_context["novel"] = novel
                            with console.status("[bold green]执行中..."):
                                exec_result = await dialogue_agent.execute_action(action, exec_context)
                            if exec_result.get("status") == "success":
                                console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                novel = file_manager.load_novel_json(novel_id)
                                context["novel"] = novel
                            else:
                                console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                        else:
                            with console.status("[bold green]AI正在思考..."):
                                chat_result = await dialogue_agent.chat(user_input, context)
                            if chat_result["status"] == "success":
                                console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")
                                if chat_result.get("action"):
                                    action = chat_result["action"]
                                    console.print(f"[dim]→ {_TOOL_LABELS.get(action['tool'], action.get('reason', action['tool']))}...[/dim]")
                                    exec_context["novel"] = novel
                                    with console.status("[bold green]执行中..."):
                                        exec_result = await dialogue_agent.execute_action(action, exec_context)
                                    if exec_result.get("status") == "success":
                                        console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                        novel = file_manager.load_novel_json(novel_id)
                                        context["novel"] = novel
                                    else:
                                        console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                            else:
                                console.print(f"[red]错误: {chat_result.get('message', '未知错误')}[/red]")

                    except Exception as e:
                        console.print(f"[red]错误: {e}[/red]")


            asyncio.run(chat_loop())

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
        console.print(f"\n[cyan]正在初始化记忆系统...[/cyan]")

        try:
            memory_manager = get_memory_manager(novel_id)
            stats = memory_manager.get_memory_stats()
            console.print(f"\n[bold]记忆统计:[/bold]")
            console.print(f"  最近章节: {stats.get('recent_chapters_count', 0)}")
            console.print(f"  对话轮次: {stats.get('conversation_turns', 0)}")
            console.print(f"\n[bold green]✓ 小说恢复完成！[/bold green]")

        except Exception as e:
            console.print(f"\n[red]✗[/red] 加载失败: {e}")
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

        # 重点显示情节跳跃和矛盾
        plot_issues = review_result.get("plot_issues", {})
        if plot_issues:
            has_jumps = plot_issues.get("has_jumps", False)
            has_contradictions = plot_issues.get("has_contradictions", False)

            if has_jumps or has_contradictions:
                console.print(f"\n[bold red]⚠️ 情节问题检测[/bold red]:")

                if has_jumps:
                    console.print(f"\n[bold yellow]发现情节跳跃:[/bold yellow]")
                    for jump in plot_issues.get("jump_details", []):
                        console.print(f"  • {jump}")

                if has_contradictions:
                    console.print(f"\n[bold red]发现情节矛盾:[/bold red]")
                    for contr in plot_issues.get("contradiction_details", []):
                        console.print(f"  • {contr}")

                inconsistencies = plot_issues.get("inconsistencies", [])
                if inconsistencies:
                    console.print(f"\n[bold yellow]前后不一致:[/bold yellow]")
                    for inc in inconsistencies:
                        console.print(f"  • {inc}")

                console.print(f"\n[bold]建议操作:[/bold]")
                console.print("  1. 使用 --fix 参数自动修复")
                console.print("  2. 使用 edit-outline 修改大纲")
                console.print("  3. 手动调整章节内容")

        console.print(f"\n[bold green]优点[/bold green]:")
        for strength in review_result.get("strengths", []):
            console.print(f"  + {strength}")

        if review_result.get("weaknesses"):
            console.print(f"\n[bold yellow]需要改进[/bold yellow]:")
            for weakness in review_result.get("weaknesses", []):
                console.print(f"  - {weakness}")

        # 显示修改建议
        revision_suggestions = review_result.get("revision_suggestions", [])
        if revision_suggestions:
            console.print(f"\n[bold cyan]修改建议[/bold cyan]:")
            for i, sug in enumerate(revision_suggestions, 1):
                priority = sug.get("priority", "")
                area = sug.get("area", "")
                suggestion = sug.get("suggestion", "")
                priority_color = "red" if priority == "高" else "yellow" if priority == "中" else "green"
                console.print(f"  {i}. [{priority_color}]{priority}[/{priority_color}] {area}: {suggestion}")

        console.print(f"\n[bold]总体评价[/bold]:")
        console.print(f"{review_result.get('summary', '')}")
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")


@app.command()
def chat(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: int = typer.Option(None, "--chapter", "-c", help="章节号（可选）")
):
    """启动交互式创作对话模式（别名: chat）"""
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
        "novel_id": novel_id,
        "novel": novel
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
        nonlocal novel, dialogue_agent
        # 显示当前上下文信息
        if novel.outline:
            console.print(f"\n[dim]大纲概览: {novel.outline.summary[:100]}...[/dim]")
        if novel.characters:
            console.print(f"[dim]角色数: {len(novel.characters)}[/dim]")
        if novel.outline and novel.outline.chapters_plan:
            console.print(f"[dim]章节数: {len(novel.outline.chapters_plan)}[/dim]")

        console.print("\n[bold cyan]你可以:[/bold cyan]")
        console.print("  - 询问当前大纲或章节的情况")
        console.print("  - 提出修改意见（如：'把反派改得更聪明一点'）")
        console.print("  - 让AI细化某章节（如：'细化第3章'）")
        console.print("  - 输入 'quit' 或 'exit' 退出\n")

        exec_context = {"novel_id": novel_id, "novel": novel}

        while True:
            try:
                user_input = (await _pt_session.prompt_async("你> ")).strip()

                if user_input.lower() in ["quit", "exit", "退出"]:
                    console.print("\n[yellow]退出对话模式[/yellow]")
                    break

                if not user_input:
                    continue

                # ── 第一步：规则路由（零延迟）──────────────────
                action = dialogue_agent.fast_route(user_input)

                if action:
                    # 命中规则，直接执行，无需 LLM 意图解析
                    console.print(f"[dim]→ {action['reason']}，执行中...[/dim]")
                    exec_context["novel"] = novel
                    with console.status("[bold green]执行中..."):
                        exec_result = await dialogue_agent.execute_action(action, exec_context)

                    if exec_result.get("status") == "success":
                        console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                        novel = file_manager.load_novel_json(novel_id)
                    else:
                        console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")

                else:
                    # ── 第二步：LLM 调用理解意图，自动执行结果 ──
                    with console.status("[bold green]AI正在思考..."):
                        chat_result = await dialogue_agent.chat(user_input, context)

                    if chat_result["status"] == "success":
                        console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")

                        # 有 action 则自动执行（无需确认）
                        if chat_result.get("action"):
                            action = chat_result["action"]
                            console.print(f"[dim]→ {_TOOL_LABELS.get(action['tool'], action.get('reason', action['tool']))}...[/dim]")
                            exec_context["novel"] = novel
                            with console.status("[bold green]执行中..."):
                                exec_result = await dialogue_agent.execute_action(action, exec_context)

                            if exec_result.get("status") == "success":
                                console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                novel = file_manager.load_novel_json(novel_id)
                                exec_context["novel"] = novel
                            else:
                                console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                    else:
                        console.print(f"[red]错误:[/red] {chat_result.get('message', '未知错误')}")

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
def edit_outline(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    feedback: str = typer.Option(..., "--feedback", "-f", help="修改意见"),
    chapter: int = typer.Option(None, "--chapter", "-c", help="可选：指定修改某一章")
):
    """修改小说大纲"""
    import asyncio
    from novel_ai_agent.agents.coordinator import CoordinatorAgent

    console.print(Panel(f"[bold cyan]修改大纲[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    if chapter:
        console.print(f"修改章节: [yellow]第{chapter}章[/yellow]")
    console.print(f"修改意见: [yellow]{feedback}[/yellow]\n")

    coordinator = CoordinatorAgent()

    with console.status(f"[bold green]正在修改大纲..."):
        result = asyncio.run(coordinator.edit_outline_workflow(
            novel_id=novel_id,
            feedback=feedback,
            chapter_number=chapter
        ))

    if result["status"] == "success":
        console.print(f"\n[green]✓[/green] {result['message']}")
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")
        if "error" in result:
            console.print(f"[red]错误详情: {result['error']}[red]")


@app.command()
def edit_character(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    name: str = typer.Option(None, "--name", "-n", help="角色名（可选，不指定则从反馈中分析）"),
    feedback: str = typer.Option(..., "--feedback", "-f", help="修改意见")
):
    """修改角色设定（自动展示修改前后对比）"""
    import asyncio
    from novel_ai_agent.agents.coordinator import CoordinatorAgent
    from novel_ai_agent.utils.file_manager import file_manager
    from rich.table import Table

    console.print(Panel(f"[bold cyan]修改角色[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")
    console.print(f"修改意见: [yellow]{feedback}[/yellow]\n")

    # 加载小说
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]✗ 未找到小说 {novel_id}[/red]")
        return

    # 分析角色名
    target_name = name
    if not target_name:
        # 从反馈中尝试提取角色名
        for char in novel.characters:
            if char.name in feedback:
                target_name = char.name
                break
            # 也匹配名字的一部分
            if len(char.name) >= 2:
                given_name = char.name[1:]
                if len(given_name) >= 2 and given_name in feedback:
                    target_name = char.name
                    break

    if not target_name:
        console.print(f"[yellow]⚠️ 无法从反馈中识别角色名[/yellow]")
        console.print(f"[yellow]可用角色: {', '.join(c.name for c in novel.characters)}[/yellow]")
        console.print(f"[yellow]请使用 --name 指定角色名[/yellow]")
        return

    # 查找角色
    target_char = None
    for char in novel.characters:
        if char.name == target_name:
            target_char = char
            break

    if not target_char:
        console.print(f"[red]✗ 未找到角色: {target_name}[/red]")
        console.print(f"[yellow]可用角色: {', '.join(c.name for c in novel.characters)}[/red]")
        return

    # 保存修改前的状态
    before_char = target_char.model_copy()

    # 调用CoordinatorAgent修改角色
    coordinator = CoordinatorAgent()

    with console.status(f"[bold green]正在修改角色 {target_name}..."):
        result = asyncio.run(coordinator.edit_character_workflow(
            novel_id=novel_id,
            character_name=target_name,
            feedback=feedback
        ))

    if result["status"] != "success":
        console.print(f"\n[red]✗[/red] {result.get('message', '修改失败')}")
        return

    # 重新加载小说获取修改后的角色
    novel = file_manager.load_novel_json(novel_id)
    after_char = None
    for char in novel.characters:
        if char.name == target_name:
            after_char = char
            break

    # 显示修改前后对比
    console.print("\n[bold]修改对比:[/bold]\n")

    fields = ["personality", "background", "motivation", "quirk", "skills"]
    field_names = {
        "personality": "性格",
        "background": "背景",
        "motivation": "动机",
        "quirk": "个人特点",
        "skills": "技能"
    }

    for field in fields:
        before_val = getattr(before_char, field, "") or "(无)"
        after_val = getattr(after_char, field, "") or "(无)"

        if before_val != after_val:
            console.print(f"[bold cyan]{field_names.get(field, field)}:[/bold cyan]")
            console.print(f"  [red]前:[/red] {before_val}")
            console.print(f"  [green]后:[/green] {after_val}")
            console.print()

    console.print(f"\n[green]✓[/green] 角色 {target_name} 已修改")
    console.print(f"[dim]文件已保存到: novel_ai_agent/output/characters/{novel_id}_characters.md[/dim]")


@app.command()
def expand_chapters(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: int = typer.Option(None, "--chapter", "-c", help="可选：指定细化某一章，不指定则细化所有章节")
):
    """细化章节规划（补全地点、时间等信息）"""
    import asyncio
    from novel_ai_agent.agents.outline_agent import OutlineAgent
    from novel_ai_agent.utils.file_manager import file_manager

    console.print(Panel(f"[bold cyan]细化章节规划[/bold cyan]"))
    console.print(f"小说ID: [yellow]{novel_id}[/yellow]")

    # 加载小说
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    if not novel.outline or not novel.outline.chapters_plan:
        console.print(f"[red]错误:[/red] 小说没有大纲")
        return

    # 确定要细化的章节
    if chapter:
        chapters_to_expand = [cp for cp in novel.outline.chapters_plan if cp.chapter_number == chapter]
        if not chapters_to_expand:
            console.print(f"[red]错误:[/red] 未找到第{chapter}章")
            return
    else:
        chapters_to_expand = novel.outline.chapters_plan

    console.print(f"待细化章节: {[cp.chapter_number for cp in chapters_to_expand]}\n")

    # 创建OutlineAgent
    outline_agent = OutlineAgent()

    # 构建故事上下文
    story_context = {
        "world_state": {},
        "recent_history": []
    }

    # 执行细化
    async def expand_all():
        for cp in chapters_to_expand:
            with console.status(f"[bold green]正在细化第{cp.chapter_number}章..."):
                result = await outline_agent.expand_chapter_plan(
                    outline=novel.outline,
                    chapter_number=cp.chapter_number,
                    story_context=story_context
                )
                if result["status"] == "success":
                    cp.detailed_plan = result["detailed_plan"]
                    console.print(f"  [green]✓[/green] 第{cp.chapter_number}章细化完成")
                    # 打印新增的地点和时间信息
                    if cp.detailed_plan:
                        loc = getattr(cp.detailed_plan, 'location', '')
                        tp = getattr(cp.detailed_plan, 'time_point', '')
                        td = getattr(cp.detailed_plan, 'time_duration', '')
                        if loc or tp or td:
                            console.print(f"      地点: {loc}, 时间: {tp}, 跨度: {td}")
                else:
                    console.print(f"  [red]✗[/red] 第{cp.chapter_number}章细化失败: {result.get('message')}")

    asyncio.run(expand_all())

    # 保存
    file_manager.save_novel_json(novel)
    file_manager.save_outline_markdown(novel.outline, novel_id)

    console.print(f"\n[green]✓[/green] 细化完成，已保存")


@app.command()
def version():
    """显示版本信息"""
    console.print(Panel("[bold cyan]小说AI Agent[/bold cyan]"))
    console.print("版本: [yellow]0.4.0[/yellow] (Phase 4 - 大纲角色修改)")
    console.print("作者: Keith Xi")
    console.print("\n[bold]已实现功能:[/bold]")
    console.print("- ✅ 多Agent协作创作")
    console.print("- ✅ 大纲规划和角色设定（先生成角色再生成大纲）")
    console.print("- ✅ 智能章节创作")
    console.print("- ✅ 章节编辑和润色")
    console.print("- ✅ 大纲和角色修改（支持单章修改）")
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
