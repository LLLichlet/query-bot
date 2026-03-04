"""
兼容性模块 - 统一处理可选依赖的导入

集中处理 NoneBot 等可选依赖的导入，避免每个文件重复 try/except。
提供统一的导入接口，当 NoneBot 不可用时提供桩实现。

使用方式：
    from plugins.common.compat import MessageEvent, Matcher, NONEBOT_AVAILABLE
    
    if NONEBOT_AVAILABLE:
        # 使用 NoneBot 功能
        pass

Example:
    >>> from plugins.common.compat import MessageEvent, NONEBOT_AVAILABLE
    >>> if NONEBOT_AVAILABLE:
    ...     print("NoneBot 可用")
    ... else:
    ...     print("NoneBot 不可用，使用桩实现")
"""

try:
    from nonebot import get_bot
    from nonebot.adapters.onebot.v11 import (
        MessageEvent,
        GroupMessageEvent,
        PrivateMessageEvent,
        Bot,
        Message,
        MessageSegment,
    )
    from nonebot.matcher import Matcher
    from nonebot.plugin import PluginMetadata
    from nonebot.params import CommandArg

    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False

    def get_bot():
        return None

    class MessageEvent:
        pass

    class GroupMessageEvent:
        pass

    class PrivateMessageEvent:
        pass

    class Bot:
        pass

    class Message:
        pass

    class MessageSegment:
        @staticmethod
        def at(user_id):
            return ""

        @staticmethod
        def image(file):
            return ""

    class Matcher:
        async def send(self, msg):
            pass

        async def finish(self, msg):
            pass

    class PluginMetadata:
        def __init__(self, **kwargs):
            pass

    def CommandArg():
        return None


__all__ = [
    "NONEBOT_AVAILABLE",
    "get_bot",
    "MessageEvent",
    "GroupMessageEvent",
    "PrivateMessageEvent",
    "Bot",
    "Message",
    "MessageSegment",
    "Matcher",
    "PluginMetadata",
    "CommandArg",
]
