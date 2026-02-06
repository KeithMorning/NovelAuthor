"""
JSON解析工具
处理从LLM响应中提取和解析JSON的各种边缘情况
"""
import json
import re
import os
from typing import Any, Union, Dict, List


def extract_json_from_response(
    response: str,
    debug_file_prefix: str = "debug_response"
) -> Union[Dict, List]:
    """
    从LLM响应中提取并解析JSON

    这个函数处理多种常见的响应格式:
    - 使用```json代码块包裹的JSON
    - 使用```代码块包裹的JSON
    - 纯JSON文本
    - 包含额外文本的混合响应

    Args:
        response: LLM的原始响应文本
        debug_file_prefix: 调试文件的前缀名（当解析失败时保存调试信息）

    Returns:
        Dict或List: 解析后的JSON对象

    Raises:
        ValueError: 无法从响应中提取有效的JSON时抛出

    Examples:
        >>> response = '```json\\n{"name": "test"}\\n```'
        >>> extract_json_from_response(response)
        {'name': 'test'}
    """
    # 步骤1: 提取代码块中的JSON字符串
    json_str = _extract_json_string(response)

    # 步骤2: 清理JSON字符串
    json_str = _clean_json_string(json_str)

    # 步骤3: 尝试解析JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # 步骤4: 如果失败，尝试更激进的提取方法
        return _fallback_json_extraction(
            response, json_str, e, debug_file_prefix
        )


def _extract_json_string(response: str) -> str:
    """
    从响应中提取JSON字符串

    优先级:
    1. ```json 代码块
    2. ``` 代码块
    3. 整个响应文本
    """
    # 尝试找到JSON代码块
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end == -1:
            # 如果没有结束标记，取到最后
            json_str = response[start:].strip()
        else:
            json_str = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end == -1:
            json_str = response[start:].strip()
        else:
            json_str = response[start:end].strip()
    else:
        # 假设整个响应就是JSON
        json_str = response.strip()

    return json_str


def _clean_json_string(json_str: str) -> str:
    """
    清理JSON字符串中的常见问题
    """
    # 清理BOM和特殊字符
    json_str = json_str.replace('\ufeff', '').replace('\r\n', '\n')

    # 移除多余的空行
    json_str = json_str.replace('\n\n', '\n').strip()

    # 修复中文标点符号（不在字符串值内部的）
    # 注意：这里不能简单替换，因为可能破坏字符串内容
    # 暂时注释掉，使用更安全的方法
    # json_str = json_str.replace('"', '"').replace('"', '"')

    # 修复字符串值中未转义的引号
    # 这是LLM生成JSON时的常见问题
    json_str = _escape_unescaped_quotes(json_str)

    # 移除JSON标准不允许的尾部逗号
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    # 找到JSON的真正开始位置
    json_start = _find_json_start(json_str)
    if json_start > 0:
        json_str = json_str[json_start:]

    return json_str


def _escape_unescaped_quotes(json_str: str) -> str:
    """
    转义JSON字符串值中未转义的引号

    这是处理LLM生成的JSON时的常见问题。
    例如: "text": "这是"引号"内容" -> "text": "这是\\"引号\\"内容"

    策略：使用正则表达式找到所有 "key": "value" 模式，
    然后只在value部分转义未转义的引号
    """
    # 使用正则表达式匹配 "key": "value" 模式
    # 这个正则表达式匹配从一个引号开始，到冒号，再到下一个引号开始的值
    pattern = r'("[\w\u4e00-\u9fa5/\(\)（）]+"\s*:\s*")(.*?)("(?=\s*[,}\]\n]|$))'

    def replace_quotes_in_value(match):
        key_part = match.group(1)  # "key": "
        value_part = match.group(2)  # value content
        end_quote = match.group(3)  # "

        # 在value部分，转义所有未转义的引号
        # 先处理已经转义的引号（保持不变）
        # 然后转义其他的引号
        value_fixed = value_part.replace('\\"', '\x00')  # 临时标记已转义的
        value_fixed = value_fixed.replace('"', '\\"')     # 转义未转义的
        value_fixed = value_fixed.replace('\x00', '\\"')  # 恢复已转义的

        return key_part + value_fixed + end_quote

    result = re.sub(pattern, replace_quotes_in_value, json_str, flags=re.DOTALL)
    return result


def _find_json_start(json_str: str) -> int:
    """
    找到JSON的开始位置

    返回第一个 { 或 [ 的位置
    """
    if json_str.startswith('{') or json_str.startswith('['):
        return 0

    bracket_pos = json_str.find('[')
    brace_pos = json_str.find('{')

    if bracket_pos != -1 and brace_pos != -1:
        return min(bracket_pos, brace_pos)
    elif bracket_pos != -1:
        return bracket_pos
    elif brace_pos != -1:
        return brace_pos
    else:
        return -1


def _fallback_json_extraction(
    original_response: str,
    json_str: str,
    error: json.JSONDecodeError,
    debug_file_prefix: str
) -> Union[Dict, List]:
    """
    当标准解析失败时，使用后备提取方法
    """
    # 尝试找到最外层的JSON边界
    if '[' in json_str:
        start_idx = json_str.find('[')
        end_idx = json_str.rfind(']')
    else:
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str_extracted = json_str[start_idx:end_idx+1]
        # 再次清理尾部逗号
        json_str_extracted = re.sub(r',(\s*[}\]])', r'\1', json_str_extracted)

        try:
            return json.loads(json_str_extracted)
        except json.JSONDecodeError as e2:
            # 最后的尝试失败，保存调试信息
            _save_debug_info(
                original_response, json_str, json_str_extracted,
                e2, debug_file_prefix
            )
            raise ValueError(
                f"无法从响应中提取有效的JSON: {e2}\n"
                f"响应预览: {original_response[:300]}...\n"
                f"调试信息已保存"
            )
    else:
        # 无法找到有效的JSON边界
        print(f"⚠️  无法找到有效的JSON边界")
        print(f"响应内容预览: {original_response[:500]}")
        raise ValueError(
            f"无法从响应中提取有效的JSON: {error}\n"
            f"响应预览: {original_response[:300]}..."
        )


def _save_debug_info(
    original_response: str,
    json_str: str,
    json_str_extracted: str,
    error: Exception,
    debug_file_prefix: str
) -> None:
    """
    保存调试信息到文件
    """
    debug_file = os.path.join(os.getcwd(), f"{debug_file_prefix}.txt")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("JSON解析错误调试信息\n")
        f.write("=" * 80 + "\n\n")

        f.write("错误信息:\n")
        f.write(f"{error}\n\n")

        f.write("=" * 80 + "\n")
        f.write("原始响应:\n")
        f.write("=" * 80 + "\n")
        f.write(original_response)
        f.write("\n\n")

        f.write("=" * 80 + "\n")
        f.write("清理后的JSON字符串:\n")
        f.write("=" * 80 + "\n")
        f.write(json_str)
        f.write("\n\n")

        f.write("=" * 80 + "\n")
        f.write("提取的JSON字符串:\n")
        f.write("=" * 80 + "\n")
        f.write(json_str_extracted)
        f.write("\n")

    print(f"📝 JSON解析错误，调试信息已保存到: {debug_file}")
