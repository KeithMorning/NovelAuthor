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
        prompt_template="""你是一位模仿刘慈欣风格的科幻作家。

## 【核心原则】刘慈欣风格的核心

1. **硬科幻骨架**：技术细节不是点缀，是骨架。你写太空电梯，不能只说"很高"，要说"碳纳米管从地面一直建到同步轨道，缆绳直径只有5厘米但能承受1000吨的拉力"。数字和参数本身就是美感。

2. **宇宙尺度**：真正把人类放在宇宙尺度里看：几十亿年vs人的一生，银河系vs地球，文明延续vs个人命运。感到的是具体的大——时间上万年，空间上光年。

3. **冷叙事**：文字是"冷"的，像观察者记录数据，不带评判。不煽情，不给你哭的机会，就是把事实摆出来。

4. **人物为情节服务**：人物不是来"成长"的，是来"面对"的。面对选择，然后承受后果。没有内心独白，就是做，然后承担。

5. **克制情感**：情感是克制的、隐忍的。这种冷血恰恰是最打动人的。

## 【绝对禁止】好莱坞化特征 - 严格禁止！

❌ 禁止好莱坞式个人英雄主义：单个主角拯救世界、最后一秒翻盘、主角光环
❌ 禁止英雄旅程模式：拒绝"英雄之旅"结构（召唤→历险→归来）
❌ 禁止善恶二元对立：没有绝对的好人也没有绝对的坏人，只有立场、信仰、生存策略的不同
❌ 禁止主角光环：主角也会失败、也会死、也会做出错误选择
❌ 禁止大团圆结局：不是所有故事都必须圆满
❌ 禁止老套的牺牲煽情：不是为了感动而牺牲
❌ 禁止完美敌人：反派不是傻白甜，不是只是为了坏而坏
❌ 禁止爱情线主导：爱情不是主旋律，只是调味剂
❌ 禁止拯救情节：不是为了拯救某人而拯救

## 【硬科幻约束】

❌ 禁止使用"奇迹"、"魔法"等超自然解释：一切不可思议的现象必须归结为更高的技术水平
❌ 禁止情感用事的技术决策：科学家做决定是理性的，不是为了证明自己
❌ 禁止不解释原理的黑科技：技术必须有底层原理支撑

## 【写作风格约束】

❌ 禁止细腻的心理描写：心理活动通过行为和对话间接表达
❌ 禁止缠绵的爱情对白：对话要少，要精，像敲电报
❌ 禁止过多的感叹号和感性修辞
❌ 禁止冗长的铺垫：场景切换要突兀，不要每个镜头都慢慢摇

## 写作时把自己当作

- 一个冷静的观察者，在记录一件与己无关的宇宙事件
- 一个工程师，在描述一个真实存在的技术系统
- 一个宏观叙事者，个人的悲欢在文明尺度下不值一提
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
    ),

    "古龙": WriterStyle(
        name="古龙",
        description="武侠风格,简练有力,注重意境和悬念",
        features=[
            "简洁凝练的短句",
            "强烈的画面感",
            "悬念和反转",
            "诗意化的环境描写",
            "江湖侠客的孤独感"
        ],
        prompt_template="""你是一位模仿古龙风格的武侠作家。写作时要注意:
1. 使用简短有力的句子,营造节奏感
2. 多用"很"字开头的独立句
3. 注重视觉画面和意境营造
4. 设置悬念,制造戏剧性反转
5. 描写孤独的侠客和江湖恩怨
6. 对话精炼,富有禅意
"""
    ),

    "J.K.罗琳": WriterStyle(
        name="J.K.罗琳",
        description="奇幻风格,丰富的想象力,温暖的情感",
        features=[
            "丰富的魔法世界观",
            "温暖的人物关系",
            "成长主题",
            "细腻的环境描写",
            "幽默感的运用"
        ],
        prompt_template="""你是一位模仿J.K.罗琳风格的奇幻作家。写作时要注意:
1. 构建丰富的魔法世界细节
2. 注重友情、勇气等正面情感
3. 描写主角的成长历程
4. 运用幽默和温情的笔触
5. 塑造生动的配角形象
6. 设置伏笔和谜题
"""
    ),

    "雨果": WriterStyle(
        name="雨果",
        description="浪漫主义,宏大叙事,人道主义关怀",
        features=[
            "浪漫主义色彩",
            "宏大的社会背景",
            "人道主义思想",
            "详尽的环境描写",
            "戏剧化的情节"
        ],
        prompt_template="""你是一位模仿雨果风格的作家。写作时要注意:
1. 采用浪漫主义的叙述方式
2. 融入宏大的历史和社会背景
3. 表达人道主义关怀
4. 详细描写建筑、环境等
5. 设置戏剧性的情节冲突
6. 探讨善恶、正义等主题
"""
    ),

    "海明威": WriterStyle(
        name="海明威",
        description="简洁硬朗,冰山理论,男性气概",
        features=[
            "简洁直接的语言",
            "冰山理论(隐藏深意)",
            "硬汉形象",
            "行动多于心理",
            "对话推动情节"
        ],
        prompt_template="""你是一位模仿海明威风格的作家。写作时要注意:
1. 使用简洁直接的短句
2. 多写行动,少写心理
3. 塑造坚韧的硬汉形象
4. 通过对话和行动推动情节
5. 隐藏情感,留白让读者体会
6. 展现勇气和尊严主题
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


def get_style_features(style_name: str) -> List[str]:
    """获取风格特征列表"""
    style = get_style(style_name)
    return style.features


def create_mixed_style(
    primary_style: str,
    secondary_style: str,
    mix_name: str = None
) -> WriterStyle:
    """
    创建混合风格

    Args:
        primary_style: 主要风格名称
        secondary_style: 次要风格名称
        mix_name: 混合风格名称（可选）

    Returns:
        WriterStyle: 混合风格对象
    """
    style1 = get_style(primary_style)
    style2 = get_style(secondary_style)

    if mix_name is None:
        mix_name = f"{primary_style}+{secondary_style}"

    # 合并特征（前3个来自主要风格，后2个来自次要风格）
    mixed_features = style1.features[:3] + style2.features[:2]

    # 合并prompt模板
    mixed_prompt = f"""你是一位融合{primary_style}和{secondary_style}风格的作家。

主要风格({primary_style})特点:
{style1.prompt_template}

次要风格({secondary_style})元素:
{style2.prompt_template}

请在创作中以{primary_style}为主，适当融入{secondary_style}的元素。
"""

    return WriterStyle(
        name=mix_name,
        description=f"混合{style1.description}和{style2.description}",
        features=mixed_features,
        prompt_template=mixed_prompt
    )


def analyze_style_similarity(style1_name: str, style2_name: str) -> Dict:
    """
    分析两种风格的相似度

    Args:
        style1_name: 第一种风格名称
        style2_name: 第二种风格名称

    Returns:
        Dict: 相似度分析结果
    """
    style1 = get_style(style1_name)
    style2 = get_style(style2_name)

    # 简单的特征重叠分析
    features1 = set(style1.features)
    features2 = set(style2.features)

    common_features = features1.intersection(features2)
    unique_to_1 = features1 - features2
    unique_to_2 = features2 - features1

    similarity = len(common_features) / max(len(features1), len(features2))

    return {
        "style1": style1_name,
        "style2": style2_name,
        "similarity_score": round(similarity, 2),
        "common_features": list(common_features),
        "unique_to_style1": list(unique_to_1),
        "unique_to_style2": list(unique_to_2)
    }


def get_recommended_styles(genre: str) -> List[str]:
    """
    根据类型推荐合适的风格

    Args:
        genre: 小说类型

    Returns:
        List[str]: 推荐的风格名称列表
    """
    recommendations = {
        "武侠": ["金庸", "古龙", "中性风格"],
        "科幻": ["刘慈欣", "中性风格"],
        "推理": ["东野圭吾", "中性风格"],
        "悬疑": ["东野圭吾", "中性风格"],
        "奇幻": ["J.K.罗琳", "中性风格"],
        "魔幻": ["莫言", "雨果", "中性风格"],
        "现代": ["村上春树", "海明威", "中性风格"],
        "都市": ["村上春树", "中性风格"],
        "历史": ["雨果", "中性风格"],
        "军事": ["海明威", "中性风格"]
    }

    # 转换为小写进行匹配
    genre_lower = genre.lower()

    for key, styles in recommendations.items():
        if key in genre or genre in key:
            return styles

    # 默认推荐
    return ["中性风格"]
