"""
角色数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class Character(BaseModel):
    """角色模型"""

    name: str = Field(..., description="角色名称")
    role: str = Field(..., description="角色定位: 主角/配角/反派等")
    personality: str = Field(..., description="性格特征")
    background: str = Field(..., description="背景故事")
    motivation: str = Field(..., description="行动动机")
    appearance: Optional[str] = Field(None, description="外貌描述")
    relationships: Dict[str, str] = Field(
        default_factory=dict,
        description="与其他角色的关系, key为角色名, value为关系描述"
    )
    arc: Optional[str] = Field(None, description="角色发展弧线")
    skills: Optional[str] = Field(None, description="特殊技能或能力")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = f"### {self.name}\n\n"
        md += f"**角色定位**: {self.role}\n\n"
        md += f"**性格**: {self.personality}\n\n"
        md += f"**背景**: {self.background}\n\n"
        md += f"**动机**: {self.motivation}\n\n"

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

        return md

    class Config:
        json_schema_extra = {
            "example": {
                "name": "张无忌",
                "role": "主角",
                "personality": "善良正直,优柔寡断,重情重义",
                "background": "明教教主之子,自幼历经磨难",
                "motivation": "为父母报仇,匡扶正义",
                "appearance": "剑眉星目,面如冠玉",
                "relationships": {
                    "赵敏": "爱人,相互吸引但立场复杂",
                    "周芷若": "青梅竹马,最终反目"
                },
                "arc": "从懦弱少年成长为明教教主",
                "skills": "九阳神功,乾坤大挪移"
            }
        }
