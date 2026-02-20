"""
Bot API 服务 - 封装 NoneBot 群管理接口

提供统一的群禁言、群成员管理等 Bot API 封装。
所有直接调用 Bot API 的操作都应通过此服务。

快速开始:
    >>> from plugins.common import BotService
    
    >>> bot = BotService.get_instance()
    
    >>> # 禁言用户
    >>> result = await bot.ban_user(group_id=123456, user_id=789, duration=300)
    
    >>> # 获取群成员列表
    >>> members = await bot.get_group_members(group_id=123456)
    
    >>> # 批量禁言
    >>> result = await bot.ban_multiple(
    ...     group_id=123456,
    ...     user_ids=[111, 222, 333],
    ...     duration=600
    ... )
"""

from typing import List, Dict, Any, Optional
import random
import logging

try:
    from nonebot import get_bot
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class Bot: pass
    class Message: pass
    class MessageSegment: pass
    def get_bot(): pass

from ..base import ServiceBase, Result


class BotService(ServiceBase):
    """
    Bot API 服务类 - 封装群管理操作
    
    提供类型安全、错误处理友好的 Bot API 封装。
    所有操作返回 Result 类型，失败时包含错误信息。
    
    Example:
        >>> bot = BotService.get_instance()
        >>> 
        >>> # 禁言单个用户
        >>> result = await bot.ban_user(
        ...     group_id=123456,
        ...     user_id=789,
        ...     duration=300  # 5分钟
        ... )
        >>> if result.is_success:
        ...     print("禁言成功")
        >>> else:
        ...     print(f"禁言失败: {result.error}")
    """
    
    def __init__(self) -> None:
        """初始化服务"""
        super().__init__()
        self.logger = logging.getLogger("plugins.common.services.bot")
    
    def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return
        self._initialized = True
        self.logger.info("Bot Service initialized")
    
    def _get_bot(self) -> Optional[Bot]:
        """
        获取 Bot 实例
        
        Returns:
            Bot 实例，如果不可用返回 None
        """
        if not NONEBOT_AVAILABLE:
            return None
        try:
            return get_bot()
        except Exception as e:
            self.logger.error(f"Failed to get bot: {e}")
            return None
    
    async def send_message(
        self,
        event,
        message: Any,
        at_user: bool = False,
        user_id: Optional[int] = None
    ) -> Result[bool]:
        """
        发送消息
        
        Args:
            event: 消息事件对象
            message: 消息内容（字符串、Message 对象等）
            at_user: 是否 @ 用户
            user_id: 要 @ 的用户 ID（默认从 event 获取）
            
        Returns:
            Result 对象
        """
        bot = self._get_bot()
        if not bot:
            return Result.fail("Bot 不可用")
        
        try:
            if at_user:
                if user_id is None and hasattr(event, 'user_id'):
                    user_id = event.user_id
                
                if user_id:
                    msg = Message()
                    msg.append(MessageSegment.at(user_id))
                    msg.append(" ")
                    msg.append(message)
                    message = msg
            
            await bot.send(event, message)
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Send message failed: {e}")
            return Result.fail(f"发送消息失败: {e}")
    
    async def ban_user(
        self,
        group_id: int,
        user_id: int,
        duration: int = 60
    ) -> Result[bool]:
        """
        禁言群成员
        
        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            duration: 禁言时长（秒），默认 60 秒
            
        Returns:
            Result 对象
            - success(True): 禁言成功
            - fail: 禁言失败，error 包含原因
            
        Example:
            >>> result = await bot.ban_user(123456, 789, 300)
            >>> if result.is_success:
            ...     print(f"已禁言 {duration} 秒")
        """
        bot = self._get_bot()
        if not bot:
            return Result.fail("Bot 不可用")
        
        try:
            await bot.set_group_ban(
                group_id=group_id,
                user_id=user_id,
                duration=duration
            )
            self.logger.info(f"Banned user {user_id} in group {group_id} for {duration}s")
            return Result.success(True)
        except Exception as e:
            self.logger.error(f"Ban user failed: {e}")
            return Result.fail(f"禁言失败: {e}")
    
    async def ban_random_duration(
        self,
        group_id: int,
        user_id: int,
        min_minutes: int = 1,
        max_minutes: int = 10
    ) -> Result[int]:
        """
        随机时长禁言
        
        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            min_minutes: 最小时长（分钟）
            max_minutes: 最大时长（分钟）
            
        Returns:
            Result 对象，value 为实际禁言秒数
            
        Example:
            >>> result = await bot.ban_random_duration(123456, 789, 1, 10)
            >>> if result.is_success:
            ...     print(f"随机禁言 {result.value // 60} 分钟")
        """
        duration_seconds = random.randint(min_minutes, max_minutes) * 60
        result = await self.ban_user(group_id, user_id, duration_seconds)
        
        if result.is_success:
            return Result.success(duration_seconds)
        return Result.fail(result.error or "随机禁言失败")
    
    async def ban_multiple(
        self,
        group_id: int,
        user_ids: List[int],
        duration: int = 60
    ) -> Result[Dict[int, bool]]:
        """
        批量禁言用户
        
        Args:
            group_id: 群号
            user_ids: 用户 ID 列表
            duration: 禁言时长（秒）
            
        Returns:
            Result 对象，value 为 {user_id: success} 字典
            
        Example:
            >>> result = await bot.ban_multiple(123456, [111, 222, 333], 300)
            >>> for uid, success in result.value.items():
            ...     print(f"{uid}: {'成功' if success else '失败'}")
        """
        results = {}
        
        for user_id in user_ids:
            result = await self.ban_user(group_id, user_id, duration)
            results[user_id] = result.is_success
        
        success_count = sum(results.values())
        self.logger.info(f"Batch ban: {success_count}/{len(user_ids)} succeeded")
        
        return Result.success(results)
    
    async def get_group_members(
        self,
        group_id: int
    ) -> Result[List[Dict[str, Any]]]:
        """
        获取群成员列表
        
        Args:
            group_id: 群号
            
        Returns:
            Result 对象，value 为成员信息列表
            
        Example:
            >>> result = await bot.get_group_members(123456)
            >>> if result.is_success:
            ...     for member in result.value:
            ...         print(f"{member['nickname']}: {member['user_id']}")
        """
        bot = self._get_bot()
        if not bot:
            return Result.fail("Bot 不可用")
        
        try:
            members = await bot.get_group_member_list(group_id=group_id)
            return Result.success(members)
        except Exception as e:
            self.logger.error(f"Get group members failed: {e}")
            return Result.fail(f"获取群成员列表失败: {e}")
    
    async def get_group_member_info(
        self,
        group_id: int,
        user_id: int
    ) -> Result[Dict[str, Any]]:
        """
        获取群成员信息
        
        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            
        Returns:
            Result 对象，value 为成员信息字典
        """
        bot = self._get_bot()
        if not bot:
            return Result.fail("Bot 不可用")
        
        try:
            info = await bot.get_group_member_info(
                group_id=group_id,
                user_id=user_id
            )
            return Result.success(info)
        except Exception as e:
            self.logger.error(f"Get member info failed: {e}")
            return Result.fail(f"获取成员信息失败: {e}")
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            True 如果 Bot 可用
        """
        return self._get_bot() is not None


# 向后兼容
def get_bot_service() -> BotService:
    """
    获取 Bot 服务单例（向后兼容）
    
    推荐使用 BotService.get_instance()
    
    Returns:
        BotService 单例实例
    """
    return BotService.get_instance()
