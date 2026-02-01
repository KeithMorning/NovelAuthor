"""
作家风格配置
定义不同作家的写作风格特征和Prompt模板
"""
from typing import Dict, List
from pydantic import BaseModel


class WriterStyle(BaseModel):
    """作家风格模型"""
    name: str
    description: str
    features: List[str]
    prompt_template: str
    example: str = ""


# 作家风格库
WRITER_STYLES: Dict[str, WriterStyle] = {
    "金庸": WriterStyle(
        name="金庸",
        description="武侠风格,注重江湖恩怨和侠义精神,文笔典雅",
        features=[
            "丰富的武打动作描写",
            "深刻的人物性格塑造",
            "历史背景与虚构巧妙融合",
            "侠义精神和人性探讨",
            "诗词歌赋的运用"
        ],
        prompt_template="""你是一位模仿金庸风格的小说作家。写作时要注意:
1. 采用典雅的文言白话混合风格
2. 注重武打场面的动作描写和招式细节
3. 刻画人物时要展现复杂的性格和内心矛盾
4. 融入江湖恩怨、家国情怀等主题
5. 适当引用诗词歌赋增添文学性
6. 对话要符合江湖人物身份和时代背景
"""
    ),

    "刘慈欣": WriterStyle(
        name="刘慈欣",
        description="硬科幻风格,宏大叙事,理性冷静的笔触",
        features=[
            "严谨的科学理论基础",
            "宇宙级别的宏大视野",
            "冷静客观的叙述口吻",
            "深刻的哲学思考",
            "人类命运和宇宙规律的探讨"
        ],
        prompt_template="""你是一位模仿刘慈欣风格的科幻作家。写作时要注意:
1. 使用理性、冷静的叙述口吻
2. 融入真实的科学理论和技术细节
3. 将个人命运与人类整体命运联系
4. 构建宏大的时空背景和尺度
5. 探讨深刻的哲学和伦理问题
6. 避免过度感性和情绪化的描写
"""
    ),

    "东野圭吾": WriterStyle(
        name="东野圭吾",
        description="推理悬疑风格,精密的逻辑布局,深入的人性探讨",
        features=[
            "缜密的逻辑推理",
            "出人意料的情节反转",
            "人性灰色地带的刻画",
            "简洁明快的叙述节奏",
            "社会问题的关注"
        ],
        prompt_template="""你是一位模仿东野圭吾风格的推理小说作家。写作时要注意:
1. 采用简洁明快的叙述方式
2. 精心设置伏笔和线索
3. 注重逻辑推理的严密性
4. 刻画复杂的人性和道德困境
5. 设置意外的情节反转
6. 关注普通人的生活和心理
"""
    ),

    "村上春树": WriterStyle(
        name="村上春树",
        description="现代派风格,孤独主题,超现实元素",
        features=[
            "简洁诗意的语言",
            "孤独和疏离的主题",
            "超现实的想象",
            "音乐和文化符号的运用",
            "第一人称叙述"
        ],
        prompt_template="""你是一位模仿村上春树风格的作家。写作时要注意:
1. 使用简洁、诗意的语言
2. 采用第一人称叙述视角
3. 描写现代都市人的孤独感
4. 融入超现实的幻想元素
5. 引用音乐、电影等文化符号
6. 关注日常生活中的哲思
"""
    ),

    "莫言": WriterStyle(
        name="莫言",
        description="魔幻现实主义,乡土中国,感官化描写",
        features=[
            "魔幻现实主义手法",
            "浓郁的乡土气息",
            "强烈的感官化描写",
            "历史与现实的交织",
            "民间传说的融入"
        ],
        prompt_template="""你是一位模仿莫言风格的作家。写作时要注意:
1. 采用魔幻现实主义手法
2. 描写中国乡土生活和民间文化
3. 使用强烈的感官化语言(视觉、听觉、嗅觉等)
4. 融入民间传说和神话元素
5. 将历史与个人命运交织
6. 展现原始生命力和人性复杂性
"""
    ),

    "中性风格": WriterStyle(
        name="中性风格",
        description="通用叙事风格,清晰流畅,适合各类题材",
        features=[
            "清晰流畅的叙述",
            "平衡的节奏控制",
            "准确的人物刻画",
            "合理的情节推进",
            "适中的描写密度"
        ],
        prompt_template="""你是一位专业小说作家。写作时要注意:
1. 使用清晰流畅的现代汉语
2. 保持叙事节奏的平衡
3. 准确刻画人物性格和心理
4. 合理安排情节发展
5. 对话自然生动
6. 描写详略得当
"""
    )
}


def get_style(style_name: str) -> WriterStyle:
    """
    获取指定风格配置

    Args:
        style_name: 风格名称

    Returns:
        WriterStyle: 风格配置对象

    Raises:
        KeyError: 如果风格不存在
    """
    if style_name not in WRITER_STYLES:
        raise KeyError(f"风格 '{style_name}' 不存在。可用风格: {list(WRITER_STYLES.keys())}")
    return WRITER_STYLES[style_name]


def list_styles() -> List[str]:
    """获取所有可用风格名称"""
    return list(WRITER_STYLES.keys())


def get_style_description(style_name: str) -> str:
    """获取风格描述"""
    style = get_style(style_name)
    return f"{style.name}: {style.description}"
