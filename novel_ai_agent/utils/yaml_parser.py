"""
YAML解析工具
处理从LLM响应中提取和解析YAML的各种情况
"""
import yaml
import re
import os
from typing import Any, Union, Dict, List


def extract_yaml_from_response(
    response: str,
    debug_file_prefix: str = "debug_response"
) -> Union[Dict, List]:
    """
    从LLM响应中提取并解析YAML

    YAML格式对LLM更友好：
    - 不需要转义引号
    - 支持多行文本
    - 格式更宽松

    Args:
        response: LLM的原始响应文本
        debug_file_prefix: 调试文件的前缀名（当解析失败时保存调试信息）

    Returns:
        Dict或List: 解析后的YAML对象

    Raises:
        ValueError: 无法从响应中提取有效的YAML时抛出

    Examples:
        >>> response = '```yaml\\nname: test\\n```'
        >>> extract_yaml_from_response(response)
        {'name': 'test'}
    """
    # 步骤1: 提取YAML字符串
    yaml_str = _extract_yaml_string(response)

    # 步骤2: 尝试解析YAML
    try:
        return yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        # 步骤3: 如果失败，尝试清理后再解析
        return _fallback_yaml_parsing(
            response, yaml_str, e, debug_file_prefix
        )


def _extract_yaml_string(response: str) -> str:
    """
    从响应中提取YAML字符串

    优先级:
    1. ```yaml 代码块
    2. ```yml 代码块
    3. ``` 代码块
    4. 整个响应文本
    """
    # 尝试找到YAML代码块
    if "```yaml" in response:
        start = response.find("```yaml") + 7
        end = response.find("```", start)
        if end == -1:
            yaml_str = response[start:].strip()
        else:
            yaml_str = response[start:end].strip()
    elif "```yml" in response:
        start = response.find("```yml") + 6
        end = response.find("```", start)
        if end == -1:
            yaml_str = response[start:].strip()
        else:
            yaml_str = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end == -1:
            yaml_str = response[start:].strip()
        else:
            yaml_str = response[start:end].strip()
    else:
        # 假设整个响应就是YAML
        yaml_str = response.strip()

    return yaml_str


def _fallback_yaml_parsing(
    original_response: str,
    yaml_str: str,
    error: yaml.YAMLError,
    debug_file_prefix: str
) -> Union[Dict, List]:
    """
    当标准解析失败时，尝试清理和修复YAML
    """
    # 尝试一些常见的修复
    cleaned_yaml = _clean_yaml_string(yaml_str)

    try:
        return yaml.safe_load(cleaned_yaml)
    except yaml.YAMLError as e2:
        # 保存调试信息
        _save_debug_info(
            original_response, yaml_str, cleaned_yaml,
            e2, debug_file_prefix
        )
        raise ValueError(
            f"无法从响应中提取有效的YAML: {e2}\n"
            f"响应预览: {original_response[:300]}...\n"
            f"调试信息已保存"
        )


def _clean_yaml_string(yaml_str: str) -> str:
    """
    清理YAML字符串中的常见问题
    """
    # 移除BOM
    yaml_str = yaml_str.replace('\ufeff', '')

    # 统一换行符
    yaml_str = yaml_str.replace('\r\n', '\n')

    # 移除开头的空行
    yaml_str = yaml_str.lstrip('\n')

    return yaml_str


def _save_debug_info(
    original_response: str,
    yaml_str: str,
    cleaned_yaml: str,
    error: Exception,
    debug_file_prefix: str
) -> None:
    """
    保存调试信息到文件
    """
    debug_file = os.path.join(os.getcwd(), f"{debug_file_prefix}.txt")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YAML解析错误调试信息\n")
        f.write("=" * 80 + "\n\n")

        f.write("错误信息:\n")
        f.write(f"{error}\n\n")

        f.write("=" * 80 + "\n")
        f.write("原始响应:\n")
        f.write("=" * 80 + "\n")
        f.write(original_response)
        f.write("\n\n")

        f.write("=" * 80 + "\n")
        f.write("提取的YAML字符串:\n")
        f.write("=" * 80 + "\n")
        f.write(yaml_str)
        f.write("\n\n")

        f.write("=" * 80 + "\n")
        f.write("清理后的YAML字符串:\n")
        f.write("=" * 80 + "\n")
        f.write(cleaned_yaml)
        f.write("\n")

    print(f"📝 YAML解析错误，调试信息已保存到: {debug_file}")


# 辅助函数：将字典转换为YAML字符串（用于测试）
def dict_to_yaml(data: Union[Dict, List], **kwargs) -> str:
    """
    将字典或列表转换为YAML字符串

    Args:
        data: 要转换的数据
        **kwargs: 传递给yaml.dump的额外参数

    Returns:
        str: YAML格式的字符串
    """
    default_kwargs = {
        'allow_unicode': True,
        'default_flow_style': False,
        'sort_keys': False,
    }
    default_kwargs.update(kwargs)

    return yaml.dump(data, **default_kwargs)
