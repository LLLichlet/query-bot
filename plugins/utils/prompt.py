"""
提示词文件工具模块

读取 prompts/ 目录下的提示词文件，支持默认回退机制。

使用方式:
    >>> from plugins.utils import read_prompt, read_prompt_with_fallback
    >>> 
    >>> # 读取提示词，不存在返回 None
    >>> content = read_prompt("math_def")
    >>> 
    >>> # 读取提示词，不存在返回默认值
    >>> content = read_prompt_with_fallback("math_def", default="你是一个助手")

注意：提示词文件应放在项目根目录的 prompts/ 文件夹中。
"""

from pathlib import Path
from typing import Optional


# prompts 目录路径
_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def read_prompt(name: str, suffix: str = ".txt") -> Optional[str]:
    """
    读取提示词文件内容
    
    从 prompts/ 目录读取指定名称的提示词文件。
    
    Args:
        name: 文件名（不含后缀）
        suffix: 文件后缀，默认 .txt
        
    Returns:
        文件内容，如果文件不存在返回 None
        
    Example:
        >>> content = read_prompt("math_def")
        >>> if content:
        ...     print(f"Prompt length: {len(content)}")
    """
    file_path = _PROMPTS_DIR / f"{name}{suffix}"
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def read_prompt_with_fallback(name: str, default: str = "", suffix: str = ".txt") -> str:
    """
    读取提示词文件，失败时返回默认值
    
    安全地读取提示词文件，文件不存在时返回指定的默认值。
    
    Args:
        name: 文件名（不含后缀）
        default: 读取失败时的默认值
        suffix: 文件后缀
        
    Returns:
        文件内容或默认值
        
    Example:
        >>> content = read_prompt_with_fallback(
        ...     "math_def",
        ...     default="你是一个数学专家"
        ... )
    """
    content = read_prompt(name, suffix)
    return content if content is not None else default
