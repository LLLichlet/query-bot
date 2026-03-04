"""
聊天服务模块 - 聊天记录和冷却管理

服务层 - 实现 ChatServiceProtocol 协议

提供群聊历史记录管理、冷却时间控制等功能。
数据存储在内存中，重启后丢失（符合设计预期）。
在 initialize() 完成后自动注册到 ServiceLocator。

使用方式:
    >>> from plugins.common.services import ChatService
    >>> chat = ChatService.get_instance()
    >>> chat.initialize()
    >>> 
    >>> # 记录消息
    >>> chat.record_message(123456, 789012, "张三", "你好")
    >>> 
    >>> # 获取上下文
    >>> context = chat.get_context(123456, limit=10)
"""

import re
import time
from collections import deque
from typing import Dict, Deque, List, Tuple, Optional
from dataclasses import dataclass
import logging

from ..base import ServiceBase
from ..config import config
from ..protocols import (
    ChatServiceProtocol,
    ServiceLocator,
)


@dataclass
class ChatMessage:
    """
    聊天消息数据类
    
    存储单条聊天消息的完整信息。
    
    Attributes:
        timestamp: 消息时间戳（Unix 时间）
        user_id: 发送者QQ号
        username: 发送者昵称
        message: 消息内容（已清理 CQ 码）
        is_bot: 是否机器人发送的消息
        
    Example:
        >>> msg = ChatMessage(
        ...     timestamp=time.time(),
        ...     user_id=123456,
        ...     username="张三",
        ...     message="你好",
        ...     is_bot=False
        ... )
        >>> print(msg.time_str)
    """
    timestamp: float
    user_id: int
    username: str
    message: str
    is_bot: bool = False
    
    @property
    def time_str(self) -> str:
        """
        格式化时间字符串
        
        Returns:
            HH:MM:SS 格式的时间字符串
            
        Example:
            >>> msg = ChatMessage(timestamp=time.time(), user_id=1, username="a", message="hi")
            >>> print(msg.time_str)  # "14:30:00"
        """
        from datetime import datetime
        return datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")


class ChatService(ServiceBase, ChatServiceProtocol):
    """
    聊天服务类 - 管理群聊历史和冷却
    
    实现 ChatServiceProtocol 协议，提供消息记录、上下文获取、冷却控制。
    每群独立存储，最大记录数由配置决定（默认 50 条）。
    在 initialize() 完成后自动注册到 ServiceLocator。
    
    Attributes:
        _history: 群号到消息队列的映射
        _cooldown: 群号到最后触发时间的映射
        logger: 日志记录器实例
        
    Example:
        >>> chat = ChatService.get_instance()
        >>> chat.initialize()
        >>> chat.record_message(123456, 789012, "张三", "你好")
        >>> context = chat.get_context(123456)
    """
    
    def __init__(self) -> None:
        """
        初始化服务
        
        创建空的存储结构，实际使用在 initialize() 后开始。
        
        Example:
            >>> chat = ChatService.get_instance()
        """
        super().__init__()
        self._history: Dict[int, Deque[ChatMessage]] = {}
        self._cooldown: Dict[int, float] = {}
        self.logger = logging.getLogger("plugins.common.services.chat")
    
    def initialize(self) -> None:
        """
        初始化服务
        
        注册服务到 ServiceLocator，标记为已初始化。
        
        Example:
            >>> chat = ChatService.get_instance()
            >>> chat.initialize()
            >>> # 服务已注册到 ServiceLocator
        """
        if self._initialized:
            return
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(ChatServiceProtocol, self)
        self.logger.info("Chat Service initialized")
    
    def _get_or_create_history(self, group_id: int) -> Deque[ChatMessage]:
        """
        获取或创建群聊历史
        
        Args:
            group_id: QQ群号
            
        Returns:
            该群的消息队列（自动创建如果不存在）
            
        Example:
            >>> history = chat._get_or_create_history(123456)
            >>> print(len(history))
        """
        if group_id not in self._history:
            self._history[group_id] = deque(maxlen=config.max_history_per_group)
        return self._history[group_id]
    
    @staticmethod
    def _clean_cq_codes(message: str) -> str:
        """
        清理消息中的 CQ 码
        
        移除所有 [CQ:...] 格式的特殊消息码。
        
        Args:
            message: 原始消息内容
            
        Returns:
            清理后的纯文本消息
            
        Example:
            >>> cleaned = ChatService._clean_cq_codes("[CQ:at,qq=123]你好")
            >>> print(cleaned)  # "你好"
        """
        cleaned = re.sub(r'\[CQ:[^\]]+\]', '', message)
        return cleaned.strip()
    
    # ========== ChatServiceProtocol 实现 ==========
    
    def record_message(
        self,
        group_id: int,
        user_id: int,
        username: str,
        message: str,
        is_bot: bool = False
    ) -> None:
        """
        记录聊天消息
        
        将消息添加到对应群的历史记录中。
        
        Args:
            group_id: QQ群号
            user_id: 发送者QQ号
            username: 发送者昵称
            message: 消息内容
            is_bot: 是否机器人发送，默认 False
            
        Example:
            >>> chat.record_message(123456, 789012, "张三", "你好")
            >>> chat.record_message(123456, 0, "Bot", "回复", is_bot=True)
        """
        self.ensure_initialized()
        
        history = self._get_or_create_history(group_id)
        clean_message = self._clean_cq_codes(message)
        
        entry = ChatMessage(
            timestamp=time.time(),
            user_id=user_id,
            username=username,
            message=clean_message,
            is_bot=is_bot
        )
        
        history.append(entry)
    
    def get_context(self, group_id: int, limit: int = 50) -> str:
        """
        获取格式化的聊天上下文
        
        返回指定群最近的聊天记录，用于 AI 提示词。
        自动过滤机器人消息。
        
        Args:
            group_id: QQ群号
            limit: 返回的最大消息数，默认 50
            
        Returns:
            格式化的聊天记录字符串，如果没有记录返回空字符串
            
        Example:
            >>> context = chat.get_context(123456, limit=10)
            >>> if context:
            ...     print(context)
        """
        self.ensure_initialized()
        
        if group_id not in self._history or not self._history[group_id]:
            return ""
        
        messages = list(self._history[group_id])
        messages = [m for m in messages if not m.is_bot]
        
        recent = messages[-limit:] if len(messages) > limit else messages
        
        lines = []
        for msg in recent:
            content = msg.message[:80]
            if content:
                lines.append(f"{msg.username}: {content}")
        
        if lines:
            return "最近的聊天：\n" + "\n".join(lines) + "\n\n"
        return ""
    
    def check_cooldown(self, group_id: int, cooldown_seconds: int = 30) -> bool:
        """
        检查群组冷却时间是否已过
        
        Args:
            group_id: QQ群号
            cooldown_seconds: 冷却时长（秒），默认 30
            
        Returns:
            True 如果冷却时间已过或从未设置，False 否则
            
        Example:
            >>> if chat.check_cooldown(123456, 60):
            ...     # 执行操作
            ...     chat.set_cooldown(123456)
        """
        self.ensure_initialized()
        
        if group_id not in self._cooldown:
            return True
        
        elapsed = time.time() - self._cooldown[group_id]
        return elapsed >= cooldown_seconds
    
    def set_cooldown(self, group_id: int) -> None:
        """
        设置群组冷却时间
        
        将当前时间记录为该群的最后触发时间。
        
        Args:
            group_id: QQ群号
            
        Example:
            >>> chat.set_cooldown(123456)
            >>> # 30秒内 check_cooldown 将返回 False
        """
        self.ensure_initialized()
        self._cooldown[group_id] = time.time()
    
    # ========== 额外方法（不在协议中）==========
    
    def get_messages(
        self,
        group_id: int,
        limit: int = 50,
        include_bot: bool = False
    ) -> List[ChatMessage]:
        """
        获取消息列表
        
        Args:
            group_id: QQ群号
            limit: 返回的最大消息数，默认 50
            include_bot: 是否包含机器人消息，默认 False
            
        Returns:
            ChatMessage 对象列表
            
        Example:
            >>> messages = chat.get_messages(123456, limit=10)
            >>> for msg in messages:
            ...     print(f"{msg.username}: {msg.message}")
        """
        self.ensure_initialized()
        
        if group_id not in self._history:
            return []
        
        messages = list(self._history[group_id])
        if not include_bot:
            messages = [m for m in messages if not m.is_bot]
        
        return messages[-limit:] if len(messages) > limit else messages
    
    def get_recent_users(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[Tuple[int, str]]:
        """
        获取最近活跃用户
        
        返回最近发言的用户列表（去重）。
        
        Args:
            group_id: QQ群号
            limit: 返回的最大用户数，默认 10
            
        Returns:
            (user_id, username) 元组列表
            
        Example:
            >>> users = chat.get_recent_users(123456, limit=5)
            >>> for uid, name in users:
            ...     print(f"{name} ({uid})")
        """
        self.ensure_initialized()
        
        if group_id not in self._history or not self._history[group_id]:
            return []
        
        seen = set()
        users = []
        
        for msg in reversed(self._history[group_id]):
            if msg.user_id and msg.user_id not in seen:
                seen.add(msg.user_id)
                users.append((msg.user_id, msg.username))
                if len(users) >= limit:
                    break
        
        return users
    
    def get_cooldown_remaining(self, group_id: int, cooldown_seconds: int = 30) -> float:
        """
        获取剩余冷却秒数
        
        Args:
            group_id: QQ群号
            cooldown_seconds: 冷却时长（秒），默认 30
            
        Returns:
            剩余冷却秒数，如果冷却已过返回 0
            
        Example:
            >>> remaining = chat.get_cooldown_remaining(123456, 60)
            >>> if remaining > 0:
            ...     print(f"还需等待 {remaining:.1f} 秒")
        """
        self.ensure_initialized()
        
        if group_id not in self._cooldown:
            return 0
        
        remaining = cooldown_seconds - (time.time() - self._cooldown[group_id])
        return max(0, remaining)
    
    def clear_history(self, group_id: Optional[int] = None) -> None:
        """
        清除聊天记录
        
        清除指定群或所有群的聊天记录。
        
        Args:
            group_id: QQ群号，如果为 None 则清除所有群
            
        Example:
            >>> chat.clear_history(123456)  # 清除指定群
            >>> chat.clear_history()  # 清除所有群
        """
        self.ensure_initialized()
        
        if group_id is None:
            self._history.clear()
            self.logger.info("Cleared all chat history")
        else:
            self._history.pop(group_id, None)
            self.logger.info(f"Cleared history for group {group_id}")
    
    def clear_cooldown(self, group_id: Optional[int] = None) -> None:
        """
        清除冷却时间
        
        清除指定群或所有群的冷却时间。
        
        Args:
            group_id: QQ群号，如果为 None 则清除所有群
            
        Example:
            >>> chat.clear_cooldown(123456)  # 清除指定群
            >>> chat.clear_cooldown()  # 清除所有群
        """
        self.ensure_initialized()
        
        if group_id is None:
            self._cooldown.clear()
        else:
            self._cooldown.pop(group_id, None)


def get_chat_service() -> ChatService:
    """
    获取聊天服务单例（向后兼容）
    
    Returns:
        ChatService 单例实例
        
    Example:
        >>> chat = get_chat_service()
        >>> chat.initialize()
    """
    return ChatService.get_instance()
