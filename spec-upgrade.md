# 小说生成系统升级规格说明书

## 问题分析

### 当前问题
1. **上下文传递方式**: 使用文本摘要而非完整内容，导致细节丢失
2. **章节过渡问题**: 仅靠最近2章结尾800字 + 伏笔追踪不足以保证连贯性
3. **细节不一致**: 角色状态、世界设定在长篇中容易出现矛盾
4. **向量检索未启用**: 已有 MemoryManager 但未接入写作流程

### 核心目标
利用128k-1M上下文窗口，实现类似"编程续写"的严谨写作能力

---

## 升级方案设计

### 1. 上下文增强架构

#### 1.1 多层上下文策略
```
┌─────────────────────────────────────────────────────────────┐
│                    完整小说上下文                             │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: 当前章节规划 (DetailedChapterPlan)                  │
│ Layer 2: 前文完整内容 (可选，取决于章节数)                    │
│ Layer 3: 全局设定文档 (World Bible)                          │
│ Layer 4: 角色状态快照 (Character Bible)                       │
│ Layer 5: 伏笔/线索追踪表 (Plot Thread Tracker)               │
│ Layer 6: 最近章节完整结尾 (最后3章 × 2000字)                  │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 上下文模式
- **模式B (目标)**: 完整模式 - 所有之前章节完整内容，适用于中短篇（<20章）
  - 直接将所有前文纳入上下文，类似"编程续写"
  - 无摘要丢失，细节100%保留
  - 目标：章节间绝对连贯

---

### 2. 核心模块设计

#### 2.1 World Bible (世界设定圣经)
```python
class WorldBible:
    """世界设定的权威来源"""

    locations: Dict[str, Location]           # 地点设定
    timeline: List[TimelineEvent]             # 时间线
    rules: List[WorldRule]                   # 世界规则 (物理法则、社会规则)
    items: Dict[str, Item]                   # 关键物品/科技
    history: Dict[str, str]                  # 历史背景

    # 一致性检查
    def check_consistency(self, new_content: str) -> ConsistencyReport:
        """检查新内容是否与世界观冲突"""
```

#### 2.2 Character Bible (角色圣经)
```python
class CharacterBible:
    """角色状态的权威来源"""

    # 角色基础信息 (不变)
    base_info: Dict[str, CharacterBase]

    # 角色状态快照 (动态更新)
    current_states: Dict[str, CharacterState]  # 位置、状态、外观
    relationships: Dict[str, List[Relationship]]  # 关系网
    knowledge: Dict[str, List[str]]            # 角色知道的信息

    # 状态变更日志
    state_history: List[StateChange]          # 所有状态变更记录

    def apply_state_change(self, chapter_num: int, changes: List[StateChange]):
        """章节完成后应用状态变更"""

    def get_state_at_chapter(self, chapter_num: int) -> Dict[str, CharacterState]:
        """获取指定章节时的角色状态"""
```

#### 2.3 Plot Thread Tracker (伏笔追踪器)
```python
class PlotThreadTracker:
    """伏笔/线索的权威管理"""

    threads: Dict[str, PlotThread]           # 所有伏笔

    # 伏笔状态
    PLANTED = "planted"       # 已埋下
    MATURED = "matured"        # 条件成熟
    RESOLVED = "resolved"     # 已回收
    ABANDONED = "abandoned"   # 已放弃

    def add_thread(self, chapter_num: int, thread: PlotThread):
        """埋下新伏笔"""

    def resolve_thread(self, thread_id: str, resolution: str):
        """回收伏笔"""

    def get_unresolved_threads(self) -> List[PlotThread]:
        """获取所有未回收伏笔"""

    def check_thread_availability(self, thread: PlotThread) -> bool:
        """检查伏笔是否可使用（角色是否存活/在场）"""
```

---

### 3. 写作流程升级

#### 3.1 章节写作新流程
```
┌─────────────────────────────────────────────────────────────┐
│                    Chapter Writing Flow                     │
├─────────────────────────────────────────────────────────────┤
│ 1. 加载 World Bible + Character Bible + Plot Tracker        │
│ 2. 构建上下文:                                                │
│    - 当前章节规划                                            │
│    - 完整前文内容 (模式B) 或 前文摘要 (模式A)                  │
│    - 最近章节结尾                                            │
│    - 未回收伏笔列表                                          │
│    - 角色状态清单                                            │
│ 3. 一致性预检查:                                              │
│    - 检查角色状态是否与前文冲突                               │
│    - 检查世界规则是否被遵守                                   │
│ 4. 生成章节 (带一致性约束)                                     │
│ 5. 提取本章:                                                  │
│    - 实际摘要                                                │
│    - 伏笔埋下/回收                                           │
│    - 角色状态变更                                            │
│    - 关键物品变化                                            │
│ 6. 更新 Bible 和 Tracker                                     │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2 上下文构建优化
```python
class ContextBuilder:
    """构建写作上下文"""

    def __init__(self, novel: Novel, mode: str = "mixed"):
        self.novel = novel
        self.mode = mode  # "summary", "full", "mixed"

    def build_writing_context(
        self,
        chapter_num: int,
        include_full_history: bool = False
    ) -> WritingContext:
        """构建完整的写作上下文"""

        # 1. 章节规划
        chapter_plan = self._get_chapter_plan(chapter_num)

        # 2. 前文内容
        if include_full_history and self.mode == "full":
            # 完整模式：所有之前章节的完整内容
            previous_content = self._get_all_previous_content(chapter_num)
        else:
            # 摘要模式
            previous_content = self._get_summarized_content(chapter_num)

        # 3. 最近章节结尾 (用于自然过渡)
        recent_endings = self._get_recent_endings(chapter_num, count=3)

        # 4. 角色状态
        character_states = self._get_character_states(chapter_num)

        # 5. 伏笔列表
        plot_threads = self._get_active_plot_threads()

        # 6. 一致性约束 (核心！)
        constraints = self._build_consistency_constraints(chapter_num)

        return WritingContext(
            chapter_plan=chapter_plan,
            previous_content=previous_content,
            recent_endings=recent_endings,
            character_states=character_states,
            plot_threads=plot_threads,
            constraints=constraints
        )
```

---

### 4. 一致性保障机制

#### 4.1 写作时的一致性约束
```python
CONSISTENCY_SYSTEM_PROMPT = """你正在续写小说《{title}》。

【重要】你必须严格遵守以下一致性规则：

1. 角色状态
   - {character_states}
   - 已死亡/消失的角色绝对不能出现或被提及
   - 受伤状态必须保持一致

2. 世界规则
   - {world_rules}
   - 不能违反已设定的物理法则

3. 时间线
   - 当前时间: {current_time}
   - 不能出现时间倒流或跳过未描写的时间

4. 伏笔线索
   - 必须回收以下伏笔: {unresolved_threads}
   - 不能遗忘之前埋下的重要线索

5. 上一章结尾
   - 必须承接以下结尾:
   {recent_ending}

确保你的续写与上述所有内容保持绝对一致！"""
```

#### 4.2 章节完成后的验证
```python
class ConsistencyValidator:
    """章节完成后的一致性验证"""

    def validate_chapter(self, chapter: Chapter, bible: NovelBible) -> ValidationReport:
        """验证章节与全局设定的一致性"""

        issues = []

        # 1. 检查角色状态
        issues.extend(self._check_character_states(chapter, bible))

        # 2. 检查世界规则
        issues.extend(self._check_world_rules(chapter, bible))

        # 3. 检查伏笔一致性
        issues.extend(self._check_plot_threads(chapter, bible))

        # 4. 检查时间线
        issues.extend(self._check_timeline(chapter, bible))

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues
        )
```

---

### 5. 数据模型扩展

#### 5.1 新增模型
```python
# novel_ai_agent/models/bible.py

class WorldBible(BaseModel):
    """世界设定圣经"""
    locations: Dict[str, Location] = {}
    timeline: List[TimelineEvent] = []
    rules: List[WorldRule] = []
    items: Dict[str, Item] = {}
    history: Dict[str, str] = {}
    technology_level: str = ""  # 科技水平描述


class CharacterBible(BaseModel):
    """角色圣经"""
    characters: Dict[str, CharacterBase] = {}
    current_states: Dict[str, CharacterState] = {}
    relationships: Dict[str, List[Relationship]] = {}
    state_history: List[StateChange] = []


class NovelBible(BaseModel):
    """小说全设定圣经"""
    world: WorldBible
    characters: CharacterBible
    plot_threads: Dict[str, PlotThread] = {}
    metadata: BibleMetadata
```

#### 5.2 扩展Chapter模型
```python
class Chapter(BaseModel):
    # ... 现有字段 ...

    # 新增字段
    state_changes: List[StateChange] = []      # 本章导致的状态变更
    item_changes: Dict[str, ItemChange] = {}    # 物品变化
    timeline_markers: List[str] = []            # 本章涉及的时间点
    location_changes: Dict[str, str] = {}       # 角色位置变化
```

---

### 6. 实施计划

#### Phase 1: 基础设施 (已完成)
- [x] 创建 `models/bible.py` 定义 Bible 模型
- [x] 实现 `WorldBible`, `CharacterBible`, `PlotThreadTracker`
- [x] 添加数据迁移脚本（无需，数据模型兼容）

#### Phase 2: 上下文升级 (已完成)
- [x] 实现 `ContextBuilder` 类 (模式B: 完整模式)
- [x] 升级 WriterAgent 的上下文构建逻辑
- [x] 实现完整上下文模式（所有前文直接纳入）

#### Phase 3: 一致性保障 (已完成)
- [x] 扩展系统提示词，添加一致性约束
- [x] 实现 `ConsistencyValidator`
- [ ] 添加自动修复建议功能（可选）

#### Phase 4: 集成测试 (待做)
- [ ] 端到端测试
- [ ] 验证模式B上下文大小

---

### 7. 关键技术决策

#### 7.1 向量嵌入 - 已移除
**决策：不使用向量嵌入**

原因：
- 模式B（完整上下文）下，所有前文直接纳入上下文窗口，无需语义检索
- 向量检索的价值是从大量文本中定位相关内容，但128k窗口已是完整内容
- 减少依赖：删除 `local_embeddings.py`、`vector_store.py`、`embedding_patch.py`
- 简化后的 `MemoryManager` 只保留短期记忆功能

**保留的 Memory 功能**：
- 短期记忆：最近章节列表、对话历史
- 上下文由LLM直接处理（模式B）

#### 7.1 上下文策略 (模式B)
- 模式B下：直接加载所有之前章节完整内容
- 无需截断策略，依赖128k+上下文窗口
- 超出窗口时给出明确错误提示

#### 7.2 性能考虑
- 首次写作加载全部上下文到内存
- 使用增量更新而非每次全量加载
- 向量检索作为补充（快速定位特定场景）

---

### 8. 预期效果

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 角色状态一致性 | ~70% | ~95% |
| 伏笔回收率 | ~60% | ~90% |
| 章节过渡自然度 | 一般 | 优秀 |
| 上下文细节保留 | 摘要丢失 | 完整保留 |
| 长篇连贯性 | 差 | 好 |

---

## 附录: 迁移路径

现有代码保持兼容，新功能通过参数启用：
```python
# 旧方式 (默认)
await coordinator.write_chapter(novel_id, chapter_num)

# 新方式 (显式启用)
await coordinator.write_chapter(
    novel_id,
    chapter_num,
    context_mode="full",  # 或 "mixed"
    enable_consistency_check=True
)
```
