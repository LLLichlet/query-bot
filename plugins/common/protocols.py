"""
协议层 - 定义层间通信接口

此模块定义所有层间通信的抽象接口，实现依赖倒置原则。
上层（插件层）只依赖此协议的抽象接口，不依赖下层具体实现。

分层依赖关系:
    插件层 ──依赖──> 协议层 <──实现── 服务层
    接收层 ──依赖──> 协议层 <──实现── 服务层
    服务层 ──依赖──> 协议层（基础部分）
    
设计原则:
    1. 协议层不包含任何实现，只有抽象接口
    2. 上层通过协议接口调用下层能力
    3. 下层实现协议接口并注册到服务定位器
    4. 禁止跨层直接导入具体类

使用方式：
    from plugins.common.protocols import ServiceLocator, AIServiceProtocol
    
    # 获取服务
    ai = ServiceLocator.get(AIServiceProtocol)
    if ai:
        result = await ai.chat("系统提示", "用户输入")

Example:
    >>> from plugins.common.protocols import ServiceLocator, BanServiceProtocol
    >>> ban = ServiceLocator.get(BanServiceProtocol)
    >>> if ban and ban.is_banned(123456):
    ...     print("用户被拉黑")
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic, Callable, Type

# 导入基础层的结果类型
from .base import Result


# ========== 服务协议接口 ==========

class AIServiceProtocol(ABC):
    """
    AI 服务协议 - 插件层通过此接口使用 AI 能力
    
    封装 AI API 调用，提供统一的对话接口。
    
    Example:
        >>> ai = ServiceLocator.get(AIServiceProtocol)
        >>> if ai and ai.is_available:
        ...     result = await ai.chat("你是助手", "你好", temperature=0.7)
        ...     if result.is_success:
        ...         print(result.value)
    """
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        AI 服务是否可用
        
        Returns:
            True 如果 API 密钥已配置且服务可用
            
        Example:
            >>> if ai.is_available:
            ...     result = await ai.chat(...)
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9
    ) -> Result[str]:
        """
        调用 AI 对话
        
        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            temperature: 温度参数（创造性）
            max_tokens: 最大生成 token 数
            top_p: 核采样参数
            
        Returns:
            Result[str] 包含 AI 回复内容或错误信息
            
        Example:
            >>> result = await ai.chat("你是数学专家", "解释群论", temperature=0.3)
            >>> if result.is_success:
            ...     reply = result.value
        """
        pass


class BanServiceProtocol(ABC):
    """
    黑名单服务协议
    
    管理用户黑名单，支持拉黑、解封和检查操作。
    
    Example:
        >>> ban = ServiceLocator.get(BanServiceProtocol)
        >>> if ban.is_banned(123456):
        ...     print("用户已被拉黑")
    """
    
    @abstractmethod
    def is_banned(self, user_id: int) -> bool:
        """
        检查用户是否被拉黑
        
        Args:
            user_id: 用户 QQ 号
            
        Returns:
            True 如果用户已被拉黑
            
        Example:
            >>> if ban.is_banned(123456):
            ...     return "你已被拉黑"
        """
        pass
    
    @abstractmethod
    def ban(self, user_id: int) -> Result[bool]:
        """
        拉黑用户
        
        Args:
            user_id: 用户 QQ 号
            
        Returns:
            Result[bool] 操作结果
            
        Example:
            >>> result = ban.ban(123456)
            >>> if result.is_success:
            ...     print("拉黑成功")
        """
        pass
    
    @abstractmethod
    def unban(self, user_id: int) -> Result[bool]:
        """
        解封用户
        
        Args:
            user_id: 用户 QQ 号
            
        Returns:
            Result[bool] 操作结果
            
        Example:
            >>> result = ban.unban(123456)
            >>> if result.is_success:
            ...     print("解封成功")
        """
        pass


class ChatServiceProtocol(ABC):
    """
    聊天服务协议
    
    管理群聊历史记录和冷却时间控制。
    
    Example:
        >>> chat = ServiceLocator.get(ChatServiceProtocol)
        >>> chat.record_message(123456, 789, "用户", "Hello")
        >>> context = chat.get_context(123456, limit=10)
    """
    
    @abstractmethod
    def record_message(
        self,
        group_id: int,
        user_id: int,
        username: str,
        message: str,
        is_bot: bool = False
    ) -> None:
        """
        记录消息到历史
        
        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            username: 用户名
            message: 消息内容
            is_bot: 是否为机器人消息
            
        Returns:
            None
            
        Example:
            >>> chat.record_message(123456, 789, "张三", "Hello", is_bot=False)
        """
        pass
    
    @abstractmethod
    def get_context(self, group_id: int, limit: int = 50) -> str:
        """
        获取群聊上下文
        
        Args:
            group_id: 群号
            limit: 最大返回消息数
            
        Returns:
            格式化的聊天记录字符串
            
        Example:
            >>> context = chat.get_context(123456, limit=20)
            >>> print(context)
        """
        pass
    
    @abstractmethod
    def check_cooldown(self, group_id: int, cooldown_seconds: int = 30) -> bool:
        """
        检查冷却时间
        
        Args:
            group_id: 群号
            cooldown_seconds: 冷却时间（秒）
            
        Returns:
            True 如果在冷却中，False 如果可以使用
            
        Example:
            >>> if not chat.check_cooldown(123456, 60):
            ...     await self.reply("可以使用")
        """
        pass
    
    @abstractmethod
    def set_cooldown(self, group_id: int) -> None:
        """
        设置冷却时间
        
        Args:
            group_id: 群号
            
        Returns:
            None
            
        Example:
            >>> chat.set_cooldown(123456)
        """
        pass


class BotServiceProtocol(ABC):
    """
    Bot API 服务协议
    
    封装 NoneBot 的群管理 API 调用。
    
    Example:
        >>> bot = ServiceLocator.get(BotServiceProtocol)
        >>> await bot.send_message(event, "Hello", at_user=True)
        >>> await bot.ban_user(123456, 789, 300)  # 禁言5分钟
    """
    
    @abstractmethod
    async def send_message(self, event: Any, message: Any, at_user: bool = False) -> Result[bool]:
        """
        发送消息
        
        Args:
            event: 消息事件对象
            message: 消息内容
            at_user: 是否@发送者
            
        Returns:
            Result[bool] 发送结果
            
        Example:
            >>> result = await bot.send_message(event, "Hello", at_user=True)
        """
        pass
    
    @abstractmethod
    async def ban_user(self, group_id: int, user_id: int, duration: int) -> Result[bool]:
        """
        禁言用户
        
        Args:
            group_id: 群号
            user_id: 用户 QQ 号
            duration: 禁言时长（秒）
            
        Returns:
            Result[bool] 操作结果
            
        Example:
            >>> result = await bot.ban_user(123456, 789, 300)  # 5分钟
        """
        pass


class TokenServiceProtocol(ABC):
    """
    令牌服务协议
    
    提供基于时间的短期令牌生成和验证。
    
    Example:
        >>> token_service = ServiceLocator.get(TokenServiceProtocol)
        >>> token = token_service.generate_token(123456)
        >>> if token_service.verify_token(123456, token):
        ...     print("验证通过")
    """
    
    @abstractmethod
    def generate_token(self, user_id: int) -> str:
        """
        生成一次性令牌
        
        Args:
            user_id: 用户 QQ 号
            
        Returns:
            生成的令牌字符串（10位字母数字）
            
        Example:
            >>> token = token_service.generate_token(123456)
            >>> print(f"您的令牌: {token}")
        """
        pass
    
    @abstractmethod
    def verify_token(self, user_id: int, token: str) -> bool:
        """
        验证令牌
        
        Args:
            user_id: 用户 QQ 号
            token: 待验证的令牌
            
        Returns:
            True 如果令牌有效且未过期
            
        Example:
            >>> if token_service.verify_token(123456, user_input):
            ...     print("验证成功")
        """
        pass


class SystemMonitorProtocol(ABC):
    """
    系统监控服务协议
    
    获取当前 bot 进程的资源使用情况。
    
    Example:
        >>> monitor = ServiceLocator.get(SystemMonitorProtocol)
        >>> status = monitor.get_status_text()
        >>> print(status)
    """
    
    @abstractmethod
    def get_status_text(self) -> str:
        """
        获取格式化的状态文本
        
        Returns:
            包含 CPU、内存、运行时间等信息的格式化字符串
            
        Example:
            >>> text = monitor.get_status_text()
            >>> await self.reply(text)
        """
        pass




# ========== 服务定位器 ==========

T = TypeVar('T')


class ServiceLocator:
    """
    服务定位器 - 解耦服务的获取与实现
    
    上层通过 locator 获取服务接口，不关心具体实现。
    下层在初始化完成后注册到 locator。
    
    采用类级别存储，全局统一管理所有服务注册。
    
    Example:
        # 服务层初始化完成后注册
        >>> service.initialize()
        >>> ServiceLocator.register(AIServiceProtocol, service)
        
        # 插件层通过 locator 获取
        >>> ai = ServiceLocator.get(AIServiceProtocol)
        >>> if ai:
        ...     result = await ai.chat(...)
    """
    
    _services: dict[Type[Any], Any] = {}
    
    @classmethod
    def register(cls, protocol: Type[T], implementation: T) -> None:
        """
        注册服务实现
        
        Args:
            protocol: 协议接口类
            implementation: 协议实现实例（必须已完成初始化）
            
        Returns:
            None
            
        Example:
            >>> ai_service = AIService()
            >>> ai_service.initialize()
            >>> ServiceLocator.register(AIServiceProtocol, ai_service)
        """
        cls._services[protocol] = implementation
    
    @classmethod
    def get(cls, protocol: Type[T]) -> Optional[T]:
        """
        获取服务实现
        
        Args:
            protocol: 协议接口类
            
        Returns:
            协议实现实例，如果未注册返回 None
            
        Example:
            >>> ai = ServiceLocator.get(AIServiceProtocol)
            >>> if ai is None:
            ...     print("AI 服务未注册")
        """
        return cls._services.get(protocol)
    
    @classmethod
    def has(cls, protocol: Type[Any]) -> bool:
        """
        检查是否已注册某协议
        
        Args:
            protocol: 协议接口类
            
        Returns:
            True 如果该协议已有实现注册
            
        Example:
            >>> if ServiceLocator.has(AIServiceProtocol):
            ...     ai = ServiceLocator.get(AIServiceProtocol)
        """
        return protocol in cls._services


