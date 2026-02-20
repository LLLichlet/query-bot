"""
依赖注入模块 - NoneBot 原生依赖支持

提供符合 NoneBot 依赖注入规范的函数，支持 Depends() 语法。

使用示例:
    >>> from nonebot import Depends
    >>> from plugins.common.deps import dep_ai_service, dep_chat_service
    >>> 
    >>> @handler.handle()
    ... async def handle(
    ...     event: MessageEvent,
    ...     ai: AIService = Depends(dep_ai_service),
    ...     chat: ChatService = Depends(dep_chat_service)
    ... ):
    ...     # 使用注入的服务
    ...     context = chat.get_context(event.group_id)
    ...     response = await ai.chat(...)

设计原则:
    - 符合 NoneBot 规范：函数签名适配 Depends()
    - 延迟加载：服务首次使用时初始化
    - 可测试：便于 Mock 替换

扩展指南:
    如需更多依赖:
    - 数据库连接: dep_db_session()
    - 缓存服务: dep_cache_service()
    - 配置对象: dep_config()
"""

from typing import Optional

from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Bot

from .services import (
    AIService,
    BanService,
    ChatService,
    get_ai_service,
    get_ban_service,
    get_chat_service,
)
from .config import config


# ==================== 服务依赖 ====================

def dep_ai_service() -> AIService:
    """
    AI 服务依赖
    
    注入 AIService 实例，用于调用 AI API。
    
    Example:
        >>> @handler.handle()
        ... async def handle(ai: AIService = Depends(dep_ai_service)):
        ...     response = await ai.chat("系统提示", "用户输入")
    """
    return get_ai_service()


def dep_ban_service() -> BanService:
    """
    黑名单服务依赖
    
    注入 BanService 实例，用于用户封禁管理。
    
    Example:
        >>> @handler.handle()
        ... async def handle(ban: BanService = Depends(dep_ban_service)):
        ...     if ban.is_banned(user_id):
        ...         return
    """
    return get_ban_service()


def dep_chat_service() -> ChatService:
    """
    聊天服务依赖
    
    注入 ChatService 实例，用于聊天记录和冷却管理。
    
    Example:
        >>> @handler.handle()
        ... async def handle(chat: ChatService = Depends(dep_chat_service)):
        ...     chat.record_message(group_id, user_id, username, message)
    """
    return get_chat_service()


# ==================== 权限检查依赖 ====================

async def dep_check_permission(event: MessageEvent) -> bool:
    """
    权限检查依赖
    
    检查用户是否被拉黑，被拉黑时抛出异常（由 NoneBot 处理）。
    
    Args:
        event: 消息事件
        
    Returns:
        True 如果通过检查
        
    Raises:
        不会直接抛出，但依赖系统会处理返回 False 的情况
        
    Example:
        >>> @handler.handle()
        ... async def handle(_: bool = Depends(dep_check_permission)):
        ...     # 已通过权限检查
        ...     pass
    """
    ban_service = get_ban_service()
    if ban_service.is_banned(event.user_id):
        raise PermissionError("用户被拉黑")
    return True


def dep_check_feature(feature_name: str):
    """
    功能开关检查依赖（工厂函数）
    
    返回一个检查函数，用于验证功能是否开启。
    
    Args:
        feature_name: 功能配置名，如 'math', 'random'
        
    Returns:
        检查函数，用于 Depends()
        
    Example:
        >>> # 创建特定功能的检查
        >>> from functools import partial
        >>> check_math = partial(dep_check_feature, 'math')
        >>> 
        >>> @handler.handle()
        ... async def handle(_: bool = Depends(check_math)):
        ...     # 数学功能已开启
        ...     pass
    """
    async def checker(event: MessageEvent) -> bool:
        enabled = getattr(config, f"{feature_name}_enabled", True)
        if not enabled:
            raise RuntimeError(f"功能 {feature_name} 已关闭")
        return True
    return checker


# ==================== 群组相关依赖 ====================

async def dep_is_group_admin(bot: Bot, event: GroupMessageEvent) -> bool:
    """
    群管理员检查依赖
    
    检查事件用户是否为群管理员或群主。
    
    Args:
        bot: Bot 实例（自动注入）
        event: 群消息事件（自动注入）
        
    Returns:
        True 如果是管理员或群主
        
    Example:
        >>> @handler.handle()
        ... async def handle(
        ...     event: GroupMessageEvent,
        ...     is_admin: bool = Depends(dep_is_group_admin)
        ... ):
        ...     if not is_admin:
        ...         await handler.finish("需要管理员权限")
    """
    try:
        member_info = await bot.get_group_member_info(
            group_id=event.group_id,
            user_id=event.user_id
        )
        role = member_info.get("role", "member")
        return role in ("owner", "admin")
    except Exception:
        return False


async def dep_is_bot_admin(bot: Bot, event: GroupMessageEvent) -> bool:
    """
    机器人管理员检查依赖
    
    检查机器人本身是否为群管理员。
    
    Args:
        bot: Bot 实例
        event: 群消息事件
        
    Returns:
        True 如果机器人是管理员或群主
        
    Example:
        >>> @handler.handle()
        ... async def handle(
        ...     bot_admin: bool = Depends(dep_is_bot_admin)
        ... ):
        ...     if not bot_admin:
        ...         await handler.finish("机器人需要管理员权限")
    """
    try:
        bot_info = await bot.get_group_member_info(
            group_id=event.group_id,
            user_id=int(bot.self_id)
        )
        role = bot_info.get("role", "member")
        return role in ("owner", "admin")
    except Exception:
        return False


# ==================== 数据获取依赖 ====================

def dep_chat_context(event: GroupMessageEvent, limit: int = 50) -> str:
    """
    聊天上下文依赖
    
    获取群聊历史上下文。
    
    Args:
        event: 群消息事件
        limit: 最大消息数，默认 50
        
    Returns:
        格式化的上下文字符串
        
    Example:
        >>> @handler.handle()
        ... async def handle(
        ...     context: str = Depends(dep_chat_context)
        ... ):
        ...     # context 包含最近 50 条消息
        ...     pass
    """
    chat_service = get_chat_service()
    return chat_service.get_context(event.group_id, limit=limit)


def dep_recent_users(event: GroupMessageEvent, limit: int = 10):
    """
    最近用户依赖
    
    获取最近活跃用户列表。
    
    Args:
        event: 群消息事件
        limit: 最大用户数，默认 10
        
    Returns:
        [(user_id, username), ...]
        
    Example:
        >>> @handler.handle()
        ... async def handle(
        ...     users = Depends(dep_recent_users)
        ... ):
        ...     for uid, name in users:
        ...         print(f"{name}: {uid}")
    """
    chat_service = get_chat_service()
    return chat_service.get_recent_users(event.group_id, limit=limit)
