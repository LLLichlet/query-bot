"""
服务层模块 - 业务逻辑封装

提供核心业务服务，所有服务继承 ServiceBase，支持单例模式。

使用示例:
    >>> from plugins.common.services import AIService, BanService, ChatService
    >>> 
    >>> # 获取服务实例
    >>> ai = AIService.get_instance()
    >>> ban = BanService.get_instance()
    >>> chat = ChatService.get_instance()
    >>> 
    >>> # 使用服务
    >>> if ai.is_available:
    ...     result = await ai.chat("系统提示", "用户输入")
    ...     if result.is_success:
    ...         print(result.value)
"""

from .ai import AIService, get_ai_service
from .ban import BanService, get_ban_service
from .chat import ChatService, ChatMessage, get_chat_service
from .bot import BotService, get_bot_service
from .game import GameServiceBase, GameState
from .registry import PluginRegistry, PluginInfo, get_plugin_registry
from .token import TokenService, get_token_service
from .system import SystemMonitorService, get_system_monitor_service

__all__ = [
    # 服务类（推荐使用 .get_instance()）
    "AIService",
    "BanService",
    "ChatService",
    "BotService",
    "GameServiceBase",
    "PluginRegistry",
    
    # 数据类
    "ChatMessage",
    "GameState",
    "PluginInfo",
    
    # 向后兼容的获取函数
    "get_ai_service",
    "get_ban_service",
    "get_chat_service",
    "get_bot_service",
    "get_plugin_registry",
]
