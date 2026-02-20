"""
聊天服务模块 - 聊天记录和冷却管理

提供群聊历史记录、上下文获取、冷却时间控制等功能。
使用内存存储，重启后数据丢失（符合设计预期）。

快速开始:
    >>> from plugins.common import ChatService
    
    >>> chat = ChatService.get_instance()
    
    >>> # 记录消息
    >>> chat.record_message(
    ...     group_id=123456,
    ...     user_id=789,
    ...     username="张三",
    ...     message="你好"
    ... )
    
    >>> # 获取上下文（用于 AI 提示）
    >>> context = chat.get_context(group_id=123456, limit=50)
    
    >>> # 检查冷却
    >>> if chat.check_cooldown(group_id=123456):
    ...     chat.set_cooldown(group_id=123456)
    ...     # 执行需要冷却的操作
    
    >>> # 获取最近活跃用户
    >>> users = chat.get_recent_users(group_id=123456, limit=10)

数据存储:
    - 内存存储（deque），重启后丢失
    - 每群独立存储
    - 限制最大记录数（默认 50 条）
"""

import re
import time
from collections import deque
from typing import Dict, Deque, List, Tuple, Optional
from dataclasses import dataclass
import logging

from ..base import ServiceBase
from ..config import config


@dataclass
class ChatMessage:
    """
    聊天消息数据类
    
    存储单条消息的完整信息。
    
    Attributes:
        timestamp: 消息时间戳（Unix 时间）
        user_id: 用户 QQ 号
        username: 用户昵称
        message: 消息内容（已清理 CQ 码）
        is_bot: 是否为机器人发送的消息
        
    Properties:
        time_str: 格式化的时间字符串（HH:MM:SS）
    """
    timestamp: float
    user_id: int
    username: str
    message: str
    is_bot: bool = False
    
    @property
    def time_str(self) -> str:
        """格式化时间字符串"""
        from datetime import datetime
        return datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")


class ChatService(ServiceBase):
    """
    聊天服务类 - 管理群聊历史和冷却
    
    功能:
    - 消息记录（自动清理 CQ 码）
    - 聊天上下文获取（用于 AI 提示词）
    - 冷却时间管理（防止频繁触发）
    - 最近活跃用户获取
    
    存储:
    - 使用内存存储（Dict[int, Deque]）
    - 按群组分别管理
    - 重启后数据丢失（符合设计预期）
    
    线程安全:
    - 适用于 asyncio 单线程环境
    - dict 和 deque 操作是原子的
    
    Example:
        >>> chat = ChatService.get_instance()
        >>> 
        >>> # 记录用户消息
        >>> chat.record_message(
        ...     group_id=123456,
        ...     user_id=789,
        ...     username="张三",
        ...     message="你好"
        ... )
        >>> 
        >>> # 获取上下文用于 AI
        >>> context = chat.get_context(123456, limit=20)
        >>> # 返回: "最近的聊天：\n张三: 你好\n李四: 大家好\n\n"
    """
    
    def __init__(self) -> None:
        """初始化服务"""
        super().__init__()
        # 群号 -> 聊天记录队列
        self._history: Dict[int, Deque[ChatMessage]] = {}
        # 群号 -> 最后冷却时间
        self._cooldown: Dict[int, float] = {}
        self.logger = logging.getLogger("plugins.common.services.chat")
    
    def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return
        self._initialized = True
        self.logger.info("Chat Service initialized")
    
    def _get_or_create_history(self, group_id: int) -> Deque[ChatMessage]:
        """
        获取或创建群聊历史
        
        Args:
            group_id: QQ 群号
            
        Returns:
            该群的消息队列
        """
        if group_id not in self._history:
            self._history[group_id] = deque(maxlen=config.max_history_per_group)
        return self._history[group_id]
    
    @staticmethod
    def _clean_cq_codes(message: str) -> str:
        """
        清理消息中的 CQ 码
        
        CQ 码是 QQ 消息的特殊格式，如 [CQ:at,qq=123456]
        
        Args:
            message: 原始消息
            
        Returns:
            清理后的纯文本消息
        """
        cleaned = re.sub(r'\[CQ:[^\]]+\]', '', message)
        return cleaned.strip()
    
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
        
        自动清理 CQ 码，限制单群历史数量。
        
        Args:
            group_id: QQ 群号
            user_id: 用户 QQ 号
            username: 用户昵称
            message: 消息内容（会自动清理 CQ 码）
            is_bot: 是否为机器人发送的消息
            
        Example:
            >>> chat.record_message(
            ...     group_id=123456,
            ...     user_id=789,
            ...     username="张三",
            ...     message="[CQ:at,qq=123] 你好",
            ...     is_bot=False
            ... )
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
    
    def get_context(
        self,
        group_id: int,
        limit: int = 50,
        include_bot: bool = False
    ) -> str:
        """
        获取格式化的聊天上下文
        
        返回格式化的最近聊天记录，可用于 AI 提示词。
        
        Args:
            group_id: QQ 群号
            limit: 最多获取多少条记录
            include_bot: 是否包含机器人自己的消息
            
        Returns:
            格式化的上下文字符串，如果没有记录返回空字符串
            
        Example:
            >>> context = chat.get_context(123456, limit=20)
            >>> print(context)
            最近的聊天：
            张三: 你好
            李四: 大家好
            
        """
        self.ensure_initialized()
        
        if group_id not in self._history or not self._history[group_id]:
            return ""
        
        messages = list(self._history[group_id])
        if not include_bot:
            messages = [m for m in messages if not m.is_bot]
        
        recent = messages[-limit:] if len(messages) > limit else messages
        
        lines = []
        for msg in recent:
            content = msg.message[:80]  # 截断长消息
            if content:
                lines.append(f"{msg.username}: {content}")
        
        if lines:
            return "最近的聊天：\n" + "\n".join(lines) + "\n\n"
        return ""
    
    def get_messages(
        self,
        group_id: int,
        limit: int = 50,
        include_bot: bool = False
    ) -> List[ChatMessage]:
        """
        获取消息列表
        
        Args:
            group_id: QQ 群号
            limit: 最多返回多少条
            include_bot: 是否包含机器人消息
            
        Returns:
            ChatMessage 对象列表
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
        
        按时间倒序返回最近发言的用户，用于禁言游戏等功能。
        
        Args:
            group_id: QQ 群号
            limit: 最多返回多少用户
            
        Returns:
            [(user_id, username), ...] 列表
            
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
        
        # 倒序遍历获取最近用户
        for msg in reversed(self._history[group_id]):
            if msg.user_id and msg.user_id not in seen:
                seen.add(msg.user_id)
                users.append((msg.user_id, msg.username))
                if len(users) >= limit:
                    break
        
        return users
    
    def check_cooldown(self, group_id: int) -> bool:
        """
        检查群组冷却时间是否已过
        
        判断是否已过配置的冷却时间（config.random_reply_cooldown）。
        
        Args:
            group_id: QQ 群号
            
        Returns:
            True 如果已过冷却时间或首次操作，False 如果还在冷却中
            
        Example:
            >>> if chat.check_cooldown(123456):
            ...     # 执行操作
            ...     chat.set_cooldown(123456)
        """
        self.ensure_initialized()
        
        if group_id not in self._cooldown:
            return True
        
        elapsed = time.time() - self._cooldown[group_id]
        return elapsed >= config.random_reply_cooldown
    
    def set_cooldown(self, group_id: int) -> None:
        """
        设置群组冷却时间
        
        将当前时间设为该群的最后操作时间。
        
        Args:
            group_id: QQ 群号
        """
        self.ensure_initialized()
        self._cooldown[group_id] = time.time()
    
    def get_cooldown_remaining(self, group_id: int) -> float:
        """
        获取剩余冷却秒数
        
        Args:
            group_id: QQ 群号
            
        Returns:
            剩余冷却秒数，0 表示已过冷却
        """
        self.ensure_initialized()
        
        if group_id not in self._cooldown:
            return 0
        
        remaining = config.random_reply_cooldown - (time.time() - self._cooldown[group_id])
        return max(0, remaining)
    
    def clear_history(self, group_id: Optional[int] = None) -> None:
        """
        清除聊天记录
        
        Args:
            group_id: 指定群号，为 None 则清除所有群记录
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
        
        Args:
            group_id: 指定群号，为 None 则清除所有群
        """
        self.ensure_initialized()
        
        if group_id is None:
            self._cooldown.clear()
        else:
            self._cooldown.pop(group_id, None)


# 向后兼容
def get_chat_service() -> ChatService:
    """
    获取聊天服务单例（向后兼容）
    
    推荐使用 ChatService.get_instance()
    
    Returns:
        ChatService 单例实例
    """
    return ChatService.get_instance()
