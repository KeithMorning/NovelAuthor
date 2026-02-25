"""
角色数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class Character(BaseModel):
    """角色模型 (动态锚点强化版)"""

    name: str = Field(..., description="角色名称")
    role: str = Field(..., description="角色定位: 主角/配角/反派等")

    # 替换原本扁平的 personality / background / motivation，使用动态锚点设计
    core_contradiction: str = Field(default="", description="核心特质与隐藏矛盾 (代替单调的性格)")
    deep_desire: str = Field(default="", description="表层目标与深层渴望 (代替直接的动机)")
    life_filter: str = Field(default="", description="人生滤镜 (代替干瘪的履历背景，描述过去如何影响现在看待世界)")

    from pydantic import model_validator
    
    @model_validator(mode='before')
    @classmethod
    def migrate_old_fields(cls, data: dict) -> dict:
        """向后兼容处理：如果加载了旧版带有 personality/motivation/background/behavioral_anchor/speech_style 的数据，将其迁移到新字段或抛弃"""
        if "core_contradiction" not in data and "personality" in data:
            data["core_contradiction"] = data.pop("personality")
        if "deep_desire" not in data and "motivation" in data:
            data["deep_desire"] = data.pop("motivation")
        if "life_filter" not in data and "background" in data:
            data["life_filter"] = data.pop("background")
        
        # 移除废弃字段
        data.pop("behavioral_anchor", None)
        data.pop("speech_style", None)
        return data

    appearance: Optional[str] = Field(None, description="外貌描述")
    relationships: Dict[str, str] = Field(
        default_factory=dict,
        description="与其他角色的关系, key为角色名, value为关系描述"
    )
    arc: Optional[str] = Field(None, description="角色在故事中的成长变化或执念深化")
    skills: Optional[str] = Field(None, description="特殊技能或能力")
    quirk: Optional[str] = Field(None, description="个人怪癖/小特点")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = f"### {self.name}\n\n"
        md += f"**角色定位**: {self.role}\n\n"
        md += f"**核心特质与矛盾**: {self.core_contradiction}\n\n"
        md += f"**表层目标与深层渴望**: {self.deep_desire}\n\n"
        md += f"**人生滤镜 (背景)**: {self.life_filter}\n\n"

        if self.appearance:
            md += f"**外貌**: {self.appearance}\n\n"

        if self.skills:
            md += f"**技能**: {self.skills}\n\n"

        if self.relationships:
            md += "**人物关系**:\n"
            for char_name, relation in self.relationships.items():
                md += f"- {char_name}: {relation}\n"
            md += "\n"

        if self.arc:
            md += f"**角色发展**: {self.arc}\n\n"

        if self.quirk:
            md += f"**个人特点**: {self.quirk}\n\n"

        return md

    class Config:
        json_schema_extra = {
            "example": {
                "name": "张无忌",
                "role": "主角",
                "core_contradiction": "身怀绝世武功却极度畏惧伤人；表面上优柔寡断，但在大是大非面前退无可退时会爆发出惊人的决断力。",
                "deep_desire": "表层目标是化解武林恩怨、不再有人流血；深层渴望是逃离所有责任，回到冰火岛过平凡生活。",
                "life_filter": "童年目睹父母被迫违心自尽，导致他对任何形式的'逼迫'和'名门正派的集体意志'有着生理性的厌恶与不信任。",
                "appearance": "剑眉星目，面容清隽，常穿宽大且不显眼的粗布衣衫。",
                "relationships": {
                    "赵敏": "爱人，相互吸引但立场复杂",
                    "周芷若": "青梅竹马，最终反目"
                },
                "arc": "从试图讨好所有人以求和平的少年，被迫成长为承担无情抉择的明教教主，最终领悟到唯有放下权力才能获得真正的自由。",
                "skills": "九阳神功，乾坤大挪移"
            }
        }
