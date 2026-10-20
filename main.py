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
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

_pasted_texts: dict = {}
_paste_counter = 0

_kb = KeyBindings()

@_kb.add(Keys.BracketedPaste)
def _(event):
    global _paste_counter
    data = event.data
    # 统一换行符
    data = data.replace('\r\n', '\n').replace('\r', '\n')

    if len(data) > 200:
        _paste_counter += 1
        # 取前 60 字显示预览，换行符替换为可见符号
        preview = data[:60].replace('\n', '↵')
        marker = f"[粘贴文本 {_paste_counter} · {len(data)}字 · \"{preview}...\"]"
        _pasted_texts[marker] = data
        event.current_buffer.insert_text(marker)
    else:
        event.current_buffer.insert_text(data)

_pt_session = _PTSession(key_bindings=_kb)

async def async_prompt(prompt_text: str) -> str:
    """
    带粘贴折叠功能的 prompt：
    - 大段粘贴 (>200字) 显示为紧凑 marker，包含预览
    - resolved 后 marker 自动从字典中移除，防止内存累积
    """
    user_input = await _pt_session.prompt_async(prompt_text)
    user_input = user_input.strip()
    resolved_markers = []
    for marker, real_data in _pasted_texts.items():
        if marker in user_input:
            user_input = user_input.replace(marker, real_data)
            resolved_markers.append(marker)
    # 清理已展开的 marker
    for m in resolved_markers:
        del _pasted_texts[m]
    return user_input

# 配置日志（确保日志目录存在，避免首次运行时 FileHandler 初始化失败）
Path('logs').mkdir(parents=True, exist_ok=True)
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
    "write_chapter":     "创作章节内容",
    "expand_chapter":    "细化章节规划",
    "polish_chapter":    "润色章节内容",
    "revise_chapter":    "修改章节内容",
    "edit_chapter":      "局部编辑章节",
    "modify_outline":    "修改小说大纲",
    "modify_character":  "修改角色设定",
    "redesign_characters": "重新设计角色",
    "local_replace_text": "本地文本替换（不耗算力）",
}

# 支持流式展示的工具列表
_STREAMING_TOOLS = {"write_chapter", "revise_chapter", "polish_chapter", "edit_chapter"}

# 每个工具对应的 Todo 步骤
_TOOL_STEPS = {
    "write_chapter":     ["分析创作要求", "生成章节内容", "保存文件"],
    "revise_chapter":    ["读取章节内容", "生成修改内容", "保存文件"],
    "edit_chapter":      ["读取章节内容", "生成局部编辑指令", "应用编辑", "保存文件"],
    "polish_chapter":    ["读取章节内容", "生成润色内容", "保存文件"],
    "expand_chapter":    ["读取章节规划", "细化规划内容", "保存规划"],
    "modify_outline":    ["读取当前大纲", "生成修改后大纲", "保存大纲"],
    "modify_character":  ["读取角色设定", "生成修改后设定", "保存角色"],
    "redesign_characters": ["读取当前角色", "重新设计角色", "保存角色"],
    "local_replace_text": ["定位修改章节", "执行文本替换", "保存文件"],
}


class TodoDisplay:
    """Claude Code 风格的 Todo 列表，用 rich.Live 实时渲染进度"""

    ICONS = {
        "pending": ("○", "dim"),
        "active":  ("⟳", "bold cyan"),
        "done":    ("✓", "bold green"),
        "failed":  ("✗", "bold red"),
    }

    def __init__(self, label: str, steps: list[str]):
        from rich.text import Text
        self.label = label
        self.steps = steps
        self.statuses = ["pending"] * len(steps)
        self.details = [""] * len(steps)

    def _current(self) -> int:
        """返回当前 active 步骤的 index，-1 表示没有"""
        try:
            return self.statuses.index("active")
        except ValueError:
            return -1

    def set_active(self, idx: int) -> None:
        self.statuses[idx] = "active"

    def set_done(self, idx: int, detail: str = "") -> None:
        self.statuses[idx] = "done"
        self.details[idx] = detail

    def set_failed(self, idx: int, detail: str = "") -> None:
        self.statuses[idx] = "failed"
        self.details[idx] = detail

    def update_detail(self, idx: int, detail: str) -> None:
        self.details[idx] = detail

    def render(self):
        from rich.text import Text
        from rich.panel import Panel

        lines = Text()
        lines.append(f"  {self.label}\n", style="bold")
        for i, step in enumerate(self.steps):
            status = self.statuses[i]
            icon, icon_style = self.ICONS[status]
            lines.append(f"  {icon} ", style=icon_style)
            step_style = "bold" if status == "active" else ("dim" if status == "pending" else "")
            lines.append(step, style=step_style)
            if self.details[i]:
                lines.append(f"  {self.details[i]}", style="dim cyan")
            lines.append("\n")
        return Panel(lines, border_style="dim", padding=(0, 1))

    def print_final(self) -> None:
        """执行完成后打印最终状态（非 transient）"""
        console.print(self.render())


async def _exec_with_stream(dialogue_agent, action: dict, exec_context: dict) -> dict:
    """
    执行 execute_action，以 Claude Code 风格的 Todo List 展示实时进度。
    流式工具（revise/polish/edit）逐字显示生成字数；
    其他工具显示 spinner + Todo 状态。
    """
    from rich.live import Live

    tool = action.get("tool", "")
    label = _TOOL_LABELS.get(tool, tool)
    steps = _TOOL_STEPS.get(tool, [label, "保存文件"])
    todo = TodoDisplay(label, steps)

    # 第0步：读取（即刻完成，因为是在函数内完成的）
    todo.set_done(0)

    if tool in _STREAMING_TOOLS:
        # 生成步骤是第1步（index 1）
        gen_idx = 1
        save_idx = len(steps) - 1
        chars = [0]
        live_ref = [None]

        todo.set_active(gen_idx)

        def on_token(token: str):
            chars[0] += len(token)
            todo.update_detail(gen_idx, f"已生成 {chars[0]} 字")
            if live_ref[0]:
                live_ref[0].update(todo.render())

        with Live(
            todo.render(),
            console=console,
            refresh_per_second=4,
            transient=True
        ) as live:
            live_ref[0] = live
            result = await dialogue_agent.execute_action(action, exec_context, on_token=on_token)

        if result.get("status") == "success":
            mode_label = "局部编辑" if result.get("mode") == "edit_instruction" else ""
            detail = f"{chars[0]} 字"
            if tool == "edit_chapter":
                ec = result.get("edit_count", 0)
                detail = f"{ec} 处编辑" if result.get("mode") == "edit_instruction" else f"全文重写，{chars[0]} 字"
            todo.set_done(gen_idx, detail)
            # apply 步骤（edit_chapter 专有，index 2）
            if tool == "edit_chapter" and len(steps) == 4:
                todo.set_done(2)
            todo.set_done(save_idx)
        else:
            todo.set_failed(gen_idx, result.get("message", ""))

        todo.print_final()
        return result

    else:
        # 非流式工具：spinner + todo
        gen_idx = 1
        save_idx = len(steps) - 1
        todo.set_active(gen_idx)

        with Live(
            todo.render(),
            console=console,
            refresh_per_second=4,
            transient=True
        ) as live:
            result = await dialogue_agent.execute_action(action, exec_context)
            if result.get("status") == "success":
                todo.set_done(gen_idx)
                todo.set_done(save_idx)
            else:
                todo.set_failed(gen_idx, result.get("message", ""))
            live.update(todo.render())

        todo.print_final()
        return result


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

    # 确保输出目录存在（以 settings 为准，兼容 .env 中自定义的 OUTPUT_DIR）
    from novel_ai_agent.config.settings import get_settings

    settings = get_settings()
    output_dir = Path(settings.output_dir)
    output_dirs = [
        output_dir,
        output_dir / "novels",
        output_dir / "outlines",
        output_dir / "characters",
        Path(settings.chroma_persist_directory),
        Path("logs"),
    ]

    for dir_path in output_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]✓[/green] 已创建输出目录: [cyan]{output_dir}[/cyan]")
    console.print("\n[bold green]初始化完成![/bold green]")
    console.print("\n使用 [cyan]python main.py --help[/cyan] 查看可用命令")


@app.command()
def create(
    title: str = typer.Option(..., "--title", "-t", help="小说标题"),
    genre: str = typer.Option(..., "--genre", "-g", help="小说类型 (如:武侠/科幻/推理)"),
    theme: str = typer.Option("", "--theme", help="故事主题"),
    style: str = typer.Option("中性风格", "--style", "-s", help="作家风格"),
    core_concepts: str = typer.Option("", "--core-concepts", "-c", help="核心科幻概念与世界观设定（高级参数），可传文件路径"),
    chapters: int = typer.Option(20, "--chapters", "-n", help="章节数量"),
    requirements: str = typer.Option("", "--requirements", "-r", help="额外需求"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="创建后进入交互式对话模式进行修改"),
    auto: bool = typer.Option(False, "--auto", "-a", help="创建后自动按顺序写完所有章节")
):
    """创建新小说项目 (包含大纲和角色)"""
    import asyncio
    from novel_ai_agent.agents.coordinator import CoordinatorAgent
    from novel_ai_agent.utils.file_manager import file_manager

    if not theme and not core_concepts:
        console.print("[red]错误: 必须提供 --theme 或 --core-concepts (-c) 中的至少一个。[/red]")
        raise typer.Exit(code=1)

    # 支持从本地文件读取主题内容
    if theme:
        theme_path = Path(theme)
        if theme_path.exists() and theme_path.is_file():
            theme = theme_path.read_text(encoding="utf-8").strip()
            console.print(f"[dim]从文件读取主题: {theme_path}[/dim]")

    # 支持从本地文件读取核心设定
    if core_concepts:
        cc_path = Path(core_concepts)
        if cc_path.exists() and cc_path.is_file():
            core_concepts = cc_path.read_text(encoding="utf-8").strip()
            console.print(f"[dim]从文件读取核心设定: {cc_path}[/dim]")

    if not theme and core_concepts:
        theme = "（详见核心设定）"

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
    STEPS = ["初级大纲生成", "角色生成", "详细大纲生成", "保存文件"]

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

        from typing import Any
        async def interactive_callback(step_name: str, data: Any) -> str:
            if not interactive:
                return "y"
            
            progress.stop()
            console.print("\n")
            if step_name == "preliminary_outline":
                console.print(Panel("[bold cyan]初级大纲生成结果[/bold cyan]"))
                console.print(f"[bold]故事简介:[/bold] {data.summary}")
                console.print(f"[bold]主题思想:[/bold] {data.theme}")
                console.print(f"[bold]背景设定:[/bold] {data.setting}")
                if data.plot_points:
                    console.print("[bold]主要情节点:[/bold]")
                    for pp in data.plot_points:
                        console.print(f"  - [cyan]{pp.name}[/cyan] ({pp.chapter_range}): {pp.description}")
            elif step_name == "characters":
                console.print(Panel("[bold cyan]角色生成结果[/bold cyan]"))
                for char in data:
                    console.print(f"[bold]{char.name}[/bold] ({char.role})")
                    console.print(f"   [dim]核心矛盾:[/dim] {char.core_contradiction}")
            elif step_name == "detailed_outline":
                console.print(Panel("[bold cyan]详细大纲生成结果[/bold cyan]"))
                for cp in data.chapters_plan[:5]:
                    console.print(f"[bold]第{cp.chapter_number}章 {cp.title}[/bold]")
                    console.print(f"   [dim]梗概:[/dim] {cp.summary}")
                if len(data.chapters_plan) > 5:
                    console.print(f"   [dim]...以及其他 {len(data.chapters_plan) - 5} 章[/dim]")
                    
            from rich.prompt import Prompt
            feedback = Prompt.ask("\n[bold yellow]是否满意？(输入 'y' 继续，或输入修改意见进行优化)[/bold yellow]")
            progress.start()
            return feedback

        result = asyncio.run(coordinator.create_novel_workflow(
            title=title,
            genre=genre,
            theme=theme,
            style=style,
            core_concepts=core_concepts,
            chapter_count=chapters,
            user_requirements=requirements,
            progress_callback=progress_callback,
            interactive_callback=interactive_callback
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

            # 按顺序写作每一章（所有章节共用一个事件循环，复用 HTTP 连接）
            from rich.live import Live
            from rich.text import Text

            async def _auto_write_all() -> bool:
                for ch in range(1, total_chapters + 1):
                    chars = [0]   # 用列表绕开闭包 nonlocal 限制
                    live_ref = [None]

                    def _make_on_token(chapter_num, chars_ref, live_ref):
                        def _on_token(token: str):
                            chars_ref[0] += len(token)
                            if live_ref[0]:
                                live_ref[0].update(Text(
                                    f"✍  正在写作第{chapter_num}章...  已生成 {chars_ref[0]} 字",
                                    style="cyan"
                                ))
                        return _on_token

                    on_token = _make_on_token(ch, chars, live_ref)

                    with Live(Text(f"✍  正在写作第{ch}章...  已生成 0 字", style="cyan"),
                              console=console, refresh_per_second=4) as live2:
                        live_ref[0] = live2
                        write_result = await coordinator.write_chapter_workflow(
                            novel_id=novel_id,
                            chapter_number=ch,
                            enable_expansion=True,
                            force=False,
                            on_token=on_token
                        )

                    if write_result["status"] == "success":
                        ch_obj = write_result["chapter"]
                        console.print(f"[green]✓[/green] 第{ch}章完成: {ch_obj.title} ({ch_obj.word_count}字)")
                    else:
                        console.print(f"[red]✗[/red] 第{ch}章写作失败: {write_result.get('message', '未知错误')}")
                        return False
                return True

            if asyncio.run(_auto_write_all()):
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
                        user_input = await async_prompt("你> ")

                        if user_input.lower() in ["quit", "exit", "退出"]:
                            console.print("\n[yellow]退出对话模式[/yellow]")
                            break

                        if not user_input:
                            continue

                        # 规则路由（fast_route 可能返回多个 action）
                        fast_actions = dialogue_agent.fast_route(user_input)
                        if fast_actions:
                            for fa in fast_actions:
                                console.print(f"[dim]→ {fa['reason']}，执行中...[/dim]")
                                exec_context["novel"] = novel
                                exec_result = await _exec_with_stream(dialogue_agent, fa, exec_context)
                                if exec_result.get("status") == "success":
                                    console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                    novel = file_manager.load_novel_json(novel_id)
                                    context["novel"] = novel
                                else:
                                    console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                                    break
                        else:
                            with console.status("[bold green]正在思考..."):
                                chat_result = await dialogue_agent.chat(user_input, context)
                            if chat_result["status"] == "success":
                                console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")
                                for act in chat_result.get("actions") or []:
                                    console.print(f"[dim]→ {_TOOL_LABELS.get(act['tool'], act.get('reason', act['tool']))}...[/dim]")
                                    exec_context["novel"] = novel
                                    exec_result = await _exec_with_stream(dialogue_agent, act, exec_context)
                                    if exec_result.get("status") == "success":
                                        console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                        novel = file_manager.load_novel_json(novel_id)
                                        context["novel"] = novel
                                    else:
                                        console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                                        break
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
                        user_input = await async_prompt("你> ")

                        if user_input.lower() in ["quit", "exit", "退出"]:
                            console.print("\n[yellow]退出对话模式[/yellow]")
                            break

                        if not user_input:
                            continue

                        # 规则路由（fast_route 可能返回多个 action）
                        fast_actions = dialogue_agent.fast_route(user_input)
                        if fast_actions:
                            for fa in fast_actions:
                                console.print(f"[dim]→ {fa['reason']}，执行中...[/dim]")
                                exec_context["novel"] = novel
                                exec_result = await _exec_with_stream(dialogue_agent, fa, exec_context)
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
                                    break
                        else:
                            with console.status("[bold green]正在思考..."):
                                chat_result = await dialogue_agent.chat(user_input, context)
                            if chat_result["status"] == "success":
                                console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")
                                for act in chat_result.get("actions") or []:
                                    console.print(f"[dim]→ {_TOOL_LABELS.get(act['tool'], act.get('reason', act['tool']))}...[/dim]")
                                    exec_context["novel"] = novel
                                    exec_result = await _exec_with_stream(dialogue_agent, act, exec_context)
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
                                        break
                            else:
                                console.print(f"[red]错误: {chat_result.get('message', '未知错误')}[/red]")

                    except Exception as e:
                        console.print(f"[red]错误: {e}[/red]")


            asyncio.run(chat_loop())
    else:
        console.print(f"\n[red]✗[/red] {result['message']}")
        if "error" in result:
            console.print(f"[red]错误详情: {result['error']}[/red]")


from typing import Optional

@app.command("sync")
def sync_command(
    id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="指定章节号（默认同步所有章节）")
):
    """
    将用户在 output/.../novels/ 下手动修改的 Markdown 章节文件，同步回 novel.json
    以便后续 AI 创作时能读取到最新文本。
    """
    from novel_ai_agent.utils.file_manager import file_manager

    novel = file_manager.load_novel_json(id)
    if not novel:
        console.print(f"[bold red]✗ 找不到小说 {id}[/bold red]")
        raise typer.Exit(1)
        
    chapters_to_sync = []
    if chapter is not None:
        chapters_to_sync.append(chapter)
    else:
        chapters_to_sync = [ch.number for ch in (novel.chapters or [])]
        
    success_count = 0
    with console.status("[cyan]正在同步章节更新...[/cyan]"):
        for ch_num in chapters_to_sync:
            if file_manager.sync_chapter_markdown_to_json(id, ch_num):
                console.print(f"[green]✓ 成功从 markdown 同步第 {ch_num} 章的最新修改[/green]")
                success_count += 1
            
    if success_count > 0:
        console.print(f"\n[bold green]同步完成！共更新 {success_count} 章。[/bold green]")
    else:
        console.print("\n[dim]未检测到任何 Markdown 修改或同步失败。[/dim]")

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

        async def _write_all_chapters():
            chapters_completed = []
            total_words = 0

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

                result = await coordinator.write_chapter_workflow(
                    novel_id=novel_id,
                    chapter_number=ch_num,
                    enable_expansion=expand,
                    force=force,
                    on_token=make_on_token(ch_num, chars)
                )

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
                    return chapters_completed, total_words, True

            return chapters_completed, total_words, False

        chapters_completed, total_words, failed = asyncio.run(_write_all_chapters())

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
                        user_input = await async_prompt("你> ")

                        if user_input.lower() in ["quit", "exit", "退出"]:
                            console.print("\n[yellow]退出对话模式[/yellow]")
                            break

                        if not user_input:
                            continue

                        # 规则路由（fast_route 可能返回多个 action）
                        fast_actions = dialogue_agent.fast_route(user_input)
                        if fast_actions:
                            for fa in fast_actions:
                                console.print(f"[dim]→ {fa['reason']}，执行中...[/dim]")
                                exec_context["novel"] = novel
                                exec_result = await _exec_with_stream(dialogue_agent, fa, exec_context)
                                if exec_result.get("status") == "success":
                                    console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                    novel = file_manager.load_novel_json(novel_id)
                                    context["novel"] = novel
                                else:
                                    console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                                    break
                        else:
                            with console.status("[bold green]正在思考..."):
                                chat_result = await dialogue_agent.chat(user_input, context)
                            if chat_result["status"] == "success":
                                console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")
                                for act in chat_result.get("actions") or []:
                                    console.print(f"[dim]→ {_TOOL_LABELS.get(act['tool'], act.get('reason', act['tool']))}...[/dim]")
                                    exec_context["novel"] = novel
                                    exec_result = await _exec_with_stream(dialogue_agent, act, exec_context)
                                    if exec_result.get("status") == "success":
                                        console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                        novel = file_manager.load_novel_json(novel_id)
                                        context["novel"] = novel
                                    else:
                                        console.print(f"[red]✗ {exec_result.get('message', '执行失败')}[/red]\n")
                                        break
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
    chapter: int = typer.Option(None, "--chapter", "-c", help="章节号（可选）"),
    plan: bool = typer.Option(False, "--plan/--no-plan", "-p", help="计划模式：AI先制定计划并与你讨论，确认后再执行")
):
    """启动交互式创作对话模式（别名: chat）"""
    import asyncio
    from novel_ai_agent.agents.dialogue_agent import DialogueAgent, is_planning_request
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

    planning_mode = plan

    console.print("\n[bold]开始对话...[/bold]")
    if planning_mode:
        console.print("[bold cyan]📋 计划模式已开启[/bold cyan] — AI 将先制定修改计划，确认后再执行")
    console.print("[dim]\\[/plan 切换计划模式 | /clear 清除历史 | /resume 恢复上次会话 | /help 帮助][/dim]\n")

    # 对话循环
    async def chat_loop():
        nonlocal novel, dialogue_agent, planning_mode
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
                user_input = await async_prompt("你> ")

                if user_input.lower() in ["quit", "exit", "退出"]:
                    saved = dialogue_agent.save_session()
                    if saved:
                        console.print(f"[dim]💾 对话历史已保存，下次可用 /resume 恢复[/dim]")
                    console.print("\n[yellow]退出对话模式[/yellow]")
                    break

                if not user_input:
                    continue

                # 内建命令
                if user_input == "/plan":
                    planning_mode = not planning_mode
                    state = "[开启]✅" if planning_mode else "[关闭]🔘"
                    mode_desc = "先制定计划并与你讨论，确认后再执行" if planning_mode else "直接执行操作"
                    console.print(f"[cyan]📋 计划模式 {state} — AI将{mode_desc}[/cyan]\n")
                    continue

                if user_input == "/clear":
                    dialogue_agent.clear_history()
                    console.print("[yellow]✓ 对话历史已清除[/yellow]\n")
                    continue

                if user_input == "/resume":
                    turns = dialogue_agent.load_session()
                    if turns == 0:
                        console.print("[yellow]没有可恢复的历史对话[/yellow]\n")
                    else:
                        console.print(f"[green]✓ 已恢复上次对话（{turns // 2} 轮）[/green]")
                        # 显示最近 3 轮的摘要
                        history = dialogue_agent.get_history()
                        recent = history[-6:]
                        for msg in recent:
                            role_label = "[cyan]你[/cyan]" if msg["role"] == "user" else "[green]助手[/green]"
                            preview = msg["content"][:80] + ("…" if len(msg["content"]) > 80 else "")
                            console.print(f"  {role_label}: {preview}")
                        console.print()
                    continue

                if user_input == "/help":
                    console.print("""
[bold cyan]内建指令[/bold cyan]
  /plan   — 切换计划模式（执行前先制定并确认计划）
  /clear  — 清除当前对话历史
  /resume — 恢复上次对话（退出时自动保存）
  /help   — 显示此帮助
""")
                    continue

                # ── 第零步：关键词自动触发计划模式 ──────────────
                is_plan_kw = is_planning_request(user_input)
                if is_plan_kw or planning_mode:
                    # ── Todo：展示整个计划+执行流程 ──────────────
                    from rich.live import Live
                    plan_steps = ["分析现有剧情", "制定修改计划", "等待用户确认", "执行修改"]
                    plan_todo = TodoDisplay("📋 修改计划", plan_steps)

                    # Step 0: 分析现有剧情
                    plan_todo.set_active(0)
                    with Live(plan_todo.render(), console=console, refresh_per_second=4, transient=True) as live:
                        plan_result = await dialogue_agent.make_plan(user_input, context)
                        plan_todo.set_done(0)
                        # Step 1: 制定修改计划
                        plan_todo.set_done(1)
                        live.update(plan_todo.render())

                    if plan_result["status"] != "success":
                        console.print(f"[red]计划生成失败：{plan_result.get('message')}[/red]\n")
                        continue

                    plan_text = plan_result["plan_text"]
                    proposed_actions = plan_result.get("proposed_actions", [])

                    # 展示计划
                    console.print(f"\n[bold cyan]─── 修改计划 ───[/bold cyan]\n")
                    console.print(plan_text)
                    console.print(f"\n[bold cyan]────────────────[/bold cyan]\n")

                    if not proposed_actions:
                        plan_todo.set_done(2, "无需操作")
                        plan_todo.set_done(3, "无需操作")
                        plan_todo.print_final()
                        console.print("[dim]（此请求不需要执行操作）[/dim]\n")
                        continue

                    plan_labels = [_TOOL_LABELS.get(a['tool'], a.get('reason', a['tool'])) for a in proposed_actions]
                    console.print(f"[dim]计划执行：{' -> '.join(plan_labels)}[/dim]")
                    console.print("[dim]输入 y/确认 开始连续执行，n/取消 放弃，或补充更多修改要求[/dim]\n")

                    # Step 2: 等待用户确认
                    plan_todo.set_active(2)
                    plan_todo.print_final()
                    confirm_input = await async_prompt("确认> ")

                    if confirm_input.lower() in ("n", "no", "取消", "算了", "不用了"):
                        plan_todo.set_failed(2, "已取消")
                        plan_todo.print_final()
                        console.print("[yellow]已取消执行[/yellow]\n")
                        continue

                    if confirm_input and confirm_input.lower() not in ("y", "yes", "确认", "好", "是", "ok", "开始", "go", ""):
                        # 对于多个操作，可以把附加要求默认塞给每一个允许接收要求的工具
                        for pa in proposed_actions:
                            pa["params"]["requirements"] = (
                                pa["params"].get("requirements", "") + "\n" + confirm_input
                            ).strip()

                    plan_todo.set_done(2)

                    # Step 3: 执行修改（交给 _exec_with_stream，遍历 actions）
                    plan_todo.set_done(3, f"→ 开始执行 {len(proposed_actions)} 步操作")
                    plan_todo.print_final()

                    for idx, pa in enumerate(proposed_actions, 1):
                        pa_label = _TOOL_LABELS.get(pa['tool'], pa.get('reason', pa['tool']))
                        console.print(f"\n[dim]--- 步骤 {idx}/{len(proposed_actions)}: {pa_label} ---[/dim]")
                        exec_context["novel"] = novel
                        exec_result = await _exec_with_stream(dialogue_agent, pa, exec_context)
                        if exec_result.get("status") == "success":
                            console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                            novel = file_manager.load_novel_json(novel_id)
                            context["novel"] = novel
                            exec_context["novel"] = novel
                        else:
                            console.print(f"[red]✗ 第 {idx} 步({pa_label})执行失败，终止后续操作：{exec_result.get('message', '未知错误')}[/red]\n")
                            break
                    continue  # 跳过下面的 fast_route / LLM 路径

                # ── 第一步：规则路由（零延迟）────────────────
                fast_actions = dialogue_agent.fast_route(user_input)

                if fast_actions:
                    if planning_mode:
                        plan_labels = [_TOOL_LABELS.get(a['tool'], a.get('reason', a['tool'])) for a in fast_actions]
                        plan_lines = [f"📋  **修改计划**：{' -> '.join(plan_labels)}"]
                        
                        # 挑选第一个有效的章节作为显示
                        req = fast_actions[0].get("params", {}).get("requirements") or fast_actions[0].get("params", {}).get("feedback")
                        ch_num = fast_actions[0].get("params", {}).get("chapter_number")
                        if ch_num:
                            plan_lines.append(f"   目标章节：第{ch_num}章")
                        if req and req != user_input:
                            plan_lines.append(f"   具体要求：{req}")
                        plan_lines.append("")
                        plan_lines.append("[dim]输入 y/确认开始执行，其他任意内容为补充要求[/dim]")
                        console.print("\n" + "\n".join(plan_lines) + "\n")

                        confirm_input = await async_prompt("确认> ")
                        if confirm_input.lower() in ("y", "yes", "确认", "好", "是", "ok", "开始", "go", ""):
                            pass  # 继续执行
                        elif not confirm_input:
                            console.print("[yellow]已取消[/yellow]\n")
                            continue
                        else:
                            # 用户补充了要求，覆盖到所有相关的 action 的 params
                            for fa in fast_actions:
                                if fa["tool"] in ("revise_chapter", "polish_chapter", "modify_outline", "modify_character"):
                                    fa["params"]["requirements"] = confirm_input
                                    fa["params"]["feedback"] = confirm_input
                            # 继续执行

                    for idx, fa in enumerate(fast_actions, 1):
                        fa_label = _TOOL_LABELS.get(fa['tool'], fa.get('reason', fa['tool']))
                        console.print(f"\n[dim]--- 步骤 {idx}/{len(fast_actions)}: {fa_label} ---[/dim]")
                        exec_context["novel"] = novel
                        exec_result = await _exec_with_stream(dialogue_agent, fa, exec_context)

                        if exec_result.get("status") == "success":
                            console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                            novel = file_manager.load_novel_json(novel_id)
                            context["novel"] = novel
                            exec_context["novel"] = novel
                        else:
                            console.print(f"[red]✗ {exec_result.get('message', '执行失败')}，终止操作[/red]\n")
                            break

                else:
                    # ── 第二步：LLM 调用理解意图，自动执行结果 ──
                    with console.status("[bold green]正在思考..."):
                        chat_result = await dialogue_agent.chat(user_input, context)

                    if chat_result["status"] == "success":
                        console.print(f"\n[bold green]助手[/bold green]: {chat_result['response']}\n")

                        # 有 actions 则处理执行
                        if chat_result.get("actions"):
                            actions = chat_result["actions"]
                            plan_labels = [_TOOL_LABELS.get(a['tool'], a.get('reason', a['tool'])) for a in actions]
                            combined_label = " -> ".join(plan_labels)

                            if planning_mode:
                                # AI 的回复已经就是计划，直接等待确认
                                console.print(f"[dim]📋 计划：{combined_label}[/dim]")
                                console.print("[dim]输入 y/确认开始执行，n/取消，或补充更多要求[/dim]\n")
                                confirm_input = await async_prompt("确认> ")
                                if confirm_input.lower() in ("n", "no", "取消", "算了", "不用了"):
                                    console.print("[yellow]已取消执行[/yellow]\n")
                                    continue
                                elif confirm_input and confirm_input.lower() not in ("y", "yes", "确认", "好", "是", "ok", "开始", "go"):
                                    # 用户补充了要求
                                    for act in actions:
                                        act["params"]["requirements"] = confirm_input
                                        act["params"]["feedback"] = confirm_input

                            for idx, act in enumerate(actions, 1):
                                act_label = _TOOL_LABELS.get(act['tool'], act.get('reason', act['tool']))
                                console.print(f"\n[dim]--- 步骤 {idx}/{len(actions)}: {act_label} ---[/dim]")
                                exec_context["novel"] = novel
                                exec_result = await _exec_with_stream(dialogue_agent, act, exec_context)

                                if exec_result.get("status") == "success":
                                    console.print(f"[green]✓ {exec_result.get('message', '操作完成')}[/green]\n")
                                    novel = file_manager.load_novel_json(novel_id)
                                    context["novel"] = novel
                                    exec_context["novel"] = novel
                                else:
                                    console.print(f"[red]✗ 第 {idx} 步失败，终止后续操作：{exec_result.get('message', '执行失败')}[/red]\n")
                                    break
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
def sync_outline(
    novel_id: str = typer.Option(..., "--id", "-i", help="小说ID"),
    md_file: str = typer.Option(None, "--file", "-f", help="指定大纲MD文件路径（默认自动查找最新版本）")
):
    """将手动编辑的大纲Markdown文件同步回JSON存档"""
    import asyncio
    import json
    from pathlib import Path
    from novel_ai_agent.utils.file_manager import file_manager
    from novel_ai_agent.agents.base_agent import BaseAgent
    from novel_ai_agent.models.outline import Outline, ChapterPlan, PlotPoint
    from datetime import datetime

    console.print(Panel(f"[bold cyan]同步大纲 MD → JSON[/bold cyan]"))

    # 加载小说
    novel = file_manager.load_novel_json(novel_id)
    if not novel:
        console.print(f"[red]错误:[/red] 未找到小说 {novel_id}")
        return

    # 确定 MD 文件路径
    if md_file:
        md_path = Path(md_file)
    else:
        # 自动寻找最新版本的大纲 MD
        outlines_dir = Path(file_manager.settings.output_dir) / novel_id / "outlines"
        if not outlines_dir.exists():
            # 兼容旧路径
            outlines_dir = Path("novel_ai_agent/output/outlines")
        md_files = sorted(outlines_dir.glob(f"{novel_id}_outline_v*.md"))
        if not md_files:
            console.print(f"[red]错误:[/red] 未找到大纲MD文件，请用 --file 参数指定路径")
            return
        md_path = md_files[-1]  # 最新版本

    console.print(f"读取大纲文件: [yellow]{md_path}[/yellow]")

    if not md_path.exists():
        console.print(f"[red]错误:[/red] 文件不存在: {md_path}")
        return

    md_content = md_path.read_text(encoding="utf-8")
    console.print(f"文件大小: {len(md_content)} 字符")

    # 用 LLM 解析 MD → 结构化 JSON
    parse_prompt = f"""你是一个专业的结构化数据解析工具。请将以下小说大纲Markdown文件解析为JSON格式，严格按照指定的schema输出。

## 输入的大纲Markdown

{md_content}

## 要求

请输出一个合法的JSON对象，包含以下字段：
- `summary`: string，故事简介
- `theme`: string，主题思想
- `setting`: string 或 null，故事背景设定
- `plot_points`: 情节点数组，每项包含: name(string), description(string), chapter_range(string), importance("高"/"中"/"低")
- `chapters_plan`: 章节数组，每项包含:
  - `chapter_number`: int
  - `title`: string
  - `summary`: string，章节梗概
  - `key_events`: string数组
  - `characters_involved`: string数组
  - `estimated_words`: int（如MD中没有则用5000）

注意：
- 只输出JSON，不要有其他内容
- 不要包含 created_at、updated_at、version 等时间字段
- 如果某字段在MD中找不到，用空字符串或空数组表示"""

    async def _parse():
        agent = BaseAgent(name="Parser", description="Parse outline MD")
        from langchain_core.messages import HumanMessage
        json_llm = agent._get_json_llm()
        from langchain_core.messages import SystemMessage
        messages = [
            SystemMessage(content="你是一个结构化数据解析工具，只输出合法JSON。"),
            HumanMessage(content=parse_prompt)
        ]
        return await agent._stream_invoke(json_llm, messages)

    with console.status("[bold green]AI 正在解析大纲结构..."):
        raw = asyncio.run(_parse())

    # 解析 JSON
    try:
        # 去掉可能的 markdown 代码块
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
    except Exception as e:
        console.print(f"[red]JSON解析失败:[/red] {e}")
        console.print("[dim]原始输出:[/dim]")
        console.print(raw[:500])
        return

    # 更新 Outline 对象（保留 detailed_plan 等MD中没有的字段）
    current_outline = novel.outline
    if not current_outline:
        console.print("[red]错误:[/red] 小说没有大纲，无法同步")
        return

    # 更新顶层字段
    current_outline.summary = parsed.get("summary", current_outline.summary)
    current_outline.theme = parsed.get("theme", current_outline.theme)
    current_outline.setting = parsed.get("setting", current_outline.setting)
    current_outline.updated_at = datetime.now()
    current_outline.version += 1

    # 更新情节点
    if parsed.get("plot_points"):
        try:
            current_outline.plot_points = [PlotPoint(**pp) for pp in parsed["plot_points"]]
        except Exception as e:
            console.print(f"[yellow]⚠ 情节点解析失败，跳过: {e}[/yellow]")

    # 更新章节规划（保留 detailed_plan）
    if parsed.get("chapters_plan"):
        # 建立旧章节的 detailed_plan 索引
        old_detailed = {cp.chapter_number: cp.detailed_plan for cp in current_outline.chapters_plan}
        new_chapters = []
        for cp_data in parsed["chapters_plan"]:
            ch_num = cp_data.get("chapter_number", 0)
            new_cp = ChapterPlan(
                chapter_number=ch_num,
                title=cp_data.get("title", ""),
                summary=cp_data.get("summary", ""),
                key_events=cp_data.get("key_events", []),
                characters_involved=cp_data.get("characters_involved", []),
                estimated_words=cp_data.get("estimated_words", 5000),
                detailed_plan=old_detailed.get(ch_num)  # 保留细化规划
            )
            new_chapters.append(new_cp)
        current_outline.chapters_plan = new_chapters

    # 保存
    novel.outline = current_outline
    file_manager.save_novel_json(novel)
    file_manager.save_outline_markdown(current_outline, novel_id)

    console.print(f"\n[green]✓[/green] 同步完成！")
    console.print(f"  大纲版本: v{current_outline.version}")
    console.print(f"  章节数: {len(current_outline.chapters_plan)}")
    console.print(f"  情节点数: {len(current_outline.plot_points)}")
    console.print(f"\n[dim]已保存: {file_manager.settings.output_dir}/{novel_id}/novels/{novel_id}.json[/dim]")


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
