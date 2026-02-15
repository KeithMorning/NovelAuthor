"""
小说圣经模型
用于管理世界设定、角色状态、伏笔追踪等全局一致性信息
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from collections import defaultdict


class CharacterState(BaseModel):
    """角色当前状态快照"""
    name: str = Field(..., description="角色名称")
    location: Optional[str] = Field(None, description="当前位置")
    status: str = Field(..., description="状态描述，如：健康、受伤、死亡、消失")
    physical_state: Optional[str] = Field(None, description="生理状态，如：疲惫、兴奋")
    emotional_state: Optional[str] = Field(None, description="情感状态，如：悲伤、愤怒")
    appearance_notes: Optional[str] = Field(None, description="外貌变化")
    last_seen_chapter: Optional[int] = Field(None, description="最后出现的章节")
    is_alive: bool = Field(True, description="是否存活")
    is_present: bool = Field(True, description="是否在场（可能存活但不在当前场景）")

    def can_appear(self) -> bool:
        """检查角色是否可以出现在场景中"""
        return self.is_alive and self.is_present and "死亡" not in self.status


class CharacterBible:
    """
    角色圣经 - 管理所有角色的状态快照
    不使用Pydantic BaseModel，用普通类以便灵活更新
    """

    def __init__(self):
        # 角色基础信息（不变）
        self.base_info: Dict[str, Dict] = {}
        # 角色当前状态（动态）
        self.current_states: Dict[str, CharacterState] = {}
        # 角色关系
        self.relationships: Dict[str, List[Dict]] = defaultdict(list)
        # 状态变更历史
        self.state_history: List[Dict] = []

    def add_character(self, name: str, base_info: Dict, initial_state: CharacterState):
        """添加角色及其初始状态"""
        self.base_info[name] = base_info
        self.current_states[name] = initial_state

    def update_state(self, name: str, new_state: CharacterState, chapter_num: int):
        """更新角色状态并记录变更"""
        old_state = self.current_states.get(name)
        self.current_states[name] = new_state

        # 记录变更历史
        self.state_history.append({
            "chapter": chapter_num,
            "character": name,
            "old_state": old_state.model_dump() if old_state else None,
            "new_state": new_state.model_dump(),
            "timestamp": datetime.now().isoformat()
        })

    def get_state(self, name: str) -> Optional[CharacterState]:
        """获取角色当前状态"""
        return self.current_states.get(name)

    def get_all_states(self) -> Dict[str, CharacterState]:
        """获取所有角色状态"""
        return self.current_states.copy()

    def get_available_characters(self) -> List[str]:
        """获取当前可出场的角色列表"""
        return [
            name for name, state in self.current_states.items()
            if state.can_appear()
        ]

    def get_dead_or_gone_characters(self) -> List[str]:
        """获取已死亡或消失的角色列表"""
        return [
            name for name, state in self.current_states.items()
            if not state.can_appear()
        ]

    def add_relationship(self, char1: str, char2: str, relationship: str):
        """添加/更新角色关系"""
        # 避免重复
        existing = [r for r in self.relationships[char1] if r.get("with") != char2]
        existing.append({"with": char2, "description": relationship})
        self.relationships[char1] = existing

    def get_relationships(self, name: str) -> List[Dict]:
        """获取角色的关系"""
        return self.relationships.get(name, [])

    def to_context_str(self) -> str:
        """生成用于上下文的字符串"""
        lines = ["【角色状态一览】"]

        # 先列出不可出场的角色
        unavailable = self.get_dead_or_gone_characters()
        if unavailable:
            lines.append("\n⚠️ 已死亡/消失角色（绝对不能出场）:")
            for name in unavailable:
                state = self.current_states[name]
                lines.append(f"  - {name}: {state.status}")

        # 列出可出场角色
        available = self.get_available_characters()
        lines.append(f"\n可出场角色 ({len(available)}人):")
        for name in available:
            state = self.current_states[name]
            location = f"位于{state.location}" if state.location else "位置未知"
            lines.append(f"  - {name}: {state.status} | {location}")

        return "\n".join(lines)


class WorldLocation(BaseModel):
    """世界地点"""
    name: str = Field(..., description="地点名称")
    description: str = Field(..., description="地点描述")
    atmosphere: Optional[str] = Field(None, description="氛围特点")
    connected_locations: List[str] = Field(default_factory=list, description="相连地点")
    importance: str = Field("中等", description="重要程度")


class WorldRule(BaseModel):
    """世界规则/法则"""
    name: str = Field(..., description="规则名称")
    description: str = Field(..., description="规则描述")
    category: str = Field("物理", description="类别：物理/魔法/社会/科技")


class WorldItem(BaseModel):
    """关键物品/科技"""
    name: str = Field(..., description="物品名称")
    description: str = Field(..., description="物品描述")
    owner: Optional[str] = Field(None, description="当前拥有者")
    significance: str = Field("重要", description="重要程度")


class TimelineEvent(BaseModel):
    """时间线事件"""
    chapter: int = Field(..., description="发生章节")
    time_point: str = Field(..., description="时间点描述")
    description: str = Field(..., description="事件描述")


class WorldBible:
    """
    世界设定圣经
    """

    def __init__(self):
        self.locations: Dict[str, WorldLocation] = {}
        self.rules: List[WorldRule] = []
        self.items: Dict[str, WorldItem] = {}
        self.timeline: List[TimelineEvent] = []
        self.history: Dict[str, str] = {}  # 历史背景
        self.tech_level: str = ""  # 科技水平

    def add_location(self, location: WorldLocation):
        self.locations[location.name] = location

    def add_rule(self, rule: WorldRule):
        self.rules.append(rule)

    def add_item(self, item: WorldItem):
        self.items[item.name] = item

    def add_timeline_event(self, event: TimelineEvent):
        self.timeline.append(event)
        self.timeline.sort(key=lambda x: x.chapter)

    def get_location(self, name: str) -> Optional[WorldLocation]:
        return self.locations.get(name)

    def get_active_items(self) -> List[WorldItem]:
        """获取当前存在的关键物品"""
        return [item for item in self.items.values() if item.owner is not None]

    def to_context_str(self) -> str:
        """生成用于上下文的字符串"""
        lines = ["【世界设定】"]

        # 科技水平
        if self.tech_level:
            lines.append(f"\n科技水平: {self.tech_level}")

        # 地点
        if self.locations:
            lines.append("\n地点:")
            for loc in self.locations.values():
                lines.append(f"  - {loc.name}: {loc.description}")

        # 规则
        if self.rules:
            lines.append("\n世界规则:")
            for rule in self.rules:
                lines.append(f"  - {rule.name}: {rule.description}")

        # 关键物品
        active_items = self.get_active_items()
        if active_items:
            lines.append("\n关键物品:")
            for item in active_items:
                owner = f"（{item.owner}持有）" if item.owner else ""
                lines.append(f"  - {item.name}: {item.description} {owner}")

        return "\n".join(lines)


class PlotThreadStatus(str, Enum):
    """伏笔状态"""
    PLANTED = "planted"      # 已埋下
    MATURED = "matured"       # 条件成熟
    RESOLVED = "resolved"     # 已回收
    ABANDONED = "abandoned"   # 已放弃


class PlotThread(BaseModel):
    """伏笔/线索"""
    id: str = Field(..., description="伏笔ID")
    name: str = Field(..., description="伏笔名称")
    description: str = Field(..., description="伏笔描述")
    planted_chapter: int = Field(..., description="埋下伏笔的章节")
    expected_resolution: Optional[int] = Field(None, description="预期回收章节")
    status: PlotThreadStatus = Field(PlotThreadStatus.PLANTED, description="当前状态")
    resolution: Optional[str] = Field(None, description="回收方式描述")
    related_characters: List[str] = Field(default_factory=list, description="相关角色")
    related_items: List[str] = Field(default_factory=list, description="相关物品")


class PlotThreadTracker:
    """
    伏笔追踪器
    """

    def __init__(self):
        self.threads: Dict[str, PlotThread] = {}

    def plant(self, thread: PlotThread):
        """埋下新伏笔"""
        self.threads[thread.id] = thread

    def mature(self, thread_id: str):
        """标记伏笔成熟"""
        if thread_id in self.threads:
            self.threads[thread_id].status = PlotThreadStatus.MATURED

    def resolve(self, thread_id: str, resolution: str):
        """回收伏笔"""
        if thread_id in self.threads:
            self.threads[thread_id].status = PlotThreadStatus.RESOLVED
            self.threads[thread_id].resolution = resolution

    def abandon(self, thread_id: str, reason: str = ""):
        """放弃伏笔"""
        if thread_id in self.threads:
            self.threads[thread_id].status = PlotThreadStatus.ABANDONED
            self.threads[thread_id].resolution = reason

    def get_unresolved(self) -> List[PlotThread]:
        """获取所有未回收伏笔"""
        return [
            t for t in self.threads.values()
            if t.status in [PlotThreadStatus.PLANTED, PlotThreadStatus.MATURED]
        ]

    def get_active_by_chapter(self, chapter_num: int) -> List[PlotThread]:
        """获取在指定章节时可用的伏笔"""
        return [
            t for t in self.get_unresolved()
            if t.planted_chapter < chapter_num
        ]

    def to_context_str(self) -> str:
        """生成用于上下文的字符串"""
        lines = ["【伏笔追踪】"]

        unresolved = self.get_unresolved()
        if not unresolved:
            lines.append("\n无未回收伏笔")
            return "\n".join(lines)

        # 按状态分组
        planted = [t for t in unresolved if t.status == PlotThreadStatus.PLANTED]
        matured = [t for t in unresolved if t.status == PlotThreadStatus.MATURED]

        if planted:
            lines.append("\n已埋下伏笔:")
            for t in planted:
                lines.append(f"  - 第{t.planted_chapter}章: {t.name} ({t.description})")

        if matured:
            lines.append("\n条件成熟待回收:")
            for t in matured:
                lines.append(f"  - {t.name}: {t.description}")

        return "\n".join(lines)


class NovelBible:
    """
    小说全设定圣经
    整合 WorldBible, CharacterBible, PlotThreadTracker
    """

    def __init__(self, novel_title: str = ""):
        self.novel_title = novel_title
        self.world = WorldBible()
        self.characters = CharacterBible()
        self.plot_threads = PlotThreadTracker()
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

    def update_timestamp(self):
        self.metadata["last_updated"] = datetime.now().isoformat()

    def to_full_context(self) -> str:
        """生成完整的上下文字符串（用于模式B）"""
        parts = []

        # 1. 角色状态（最重要，优先显示）
        parts.append(self.characters.to_context_str())

        # 2. 伏笔追踪
        parts.append(self.plot_threads.to_context_str())

        # 3. 世界设定
        parts.append(self.world.to_context_str())

        return "\n\n".join(parts)
