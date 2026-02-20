"""
消息构建工具 - QQ 消息格式化

提供便捷的 QQ 消息构建函数，避免重复的 Message/MessageSegment 操作。

使用示例:
    >>> from plugins.utils import build_at_message, build_reply_message
    >>> from nonebot.adapters.onebot.v11 import Message
    >>> 
    >>> # 简单 @ 回复
    >>> msg = build_at_message(123456789, "这是回复内容")
    >>> 
    >>> # 带前缀的回复
    >>> msg = build_reply_message(
    ...     user_id=123456789,
    ...     text="这是回复",
    ...     prefix="提示"
    ... )

设计原则:
    - 纯函数：不修改输入，返回新对象
    - 类型安全：完整的类型提示
    - 链式友好：返回值可直接用于后续操作

扩展指南:
    如需更多消息类型:
    - 图文混合: build_image_text_message(image, text)
    - 引用回复: build_quote_message(message_id, text)
    - 转发消息: build_forward_message(messages)
"""

from typing import Optional, Union
from nonebot.adapters.onebot.v11 import Message, MessageSegment


def build_at_message(user_id: int, text: str) -> Message:
    """
    构建 @ 某人的消息
    
    生成的消息格式: "@user text"
    
    Args:
        user_id: 用户 QQ 号
        text: 回复文本内容
        
    Returns:
        Message 对象，可直接用于 finish/send
        
    Example:
        >>> msg = build_at_message(123456789, "你好")
        >>> await handler.finish(msg)
        
        # 输出效果: @用户 你好
    """
    msg = Message()
    msg.append(MessageSegment.at(user_id))
    msg.append(" ")
    msg.append(text)
    return msg


def build_reply_message(
    user_id: int,
    text: str,
    prefix: Optional[str] = None
) -> Message:
    """
    构建回复消息（带 @ 和可选前缀）
    
    支持添加前缀文本，适用于需要强调或分类的场景。
    
    Args:
        user_id: 用户 QQ 号
        text: 回复文本内容
        prefix: 可选前缀，会显示在 @ 之后，如 "提示:" "错误:"
        
    Returns:
        Message 对象
        
    Example:
        >>> # 简单回复
        >>> msg = build_reply_message(123456, "操作成功")
        
        >>> # 带前缀
        >>> msg = build_reply_message(
        ...     123456,
        ...     "请输入正确的格式",
        ...     prefix="错误"
        ... )
        
        # 输出效果: @用户 错误 请输入正确的格式
    """
    msg = Message()
    msg.append(MessageSegment.at(user_id))
    
    if prefix:
        msg.append(f" {prefix} ")
    else:
        msg.append(" ")
    
    msg.append(text)
    return msg


def ensure_message(text: Union[str, Message]) -> Message:
    """
    确保返回 Message 对象
    
    输入为字符串时包装为 Message，为 Message 时直接返回。
    用于处理可能为两种类型的输入。
    
    Args:
        text: 字符串或 Message 对象
        
    Returns:
        Message 对象
        
    Example:
        >>> msg1 = ensure_message("纯文本")  # → Message("纯文本")
        >>> msg2 = ensure_message(msg1)     # → msg1（不包装）
    """
    if isinstance(text, Message):
        return text
    return Message(text)
