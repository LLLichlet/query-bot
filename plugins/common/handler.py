"""
处理器基类模块 - 插件业务逻辑接口

Handler 只负责业务处理，不处理命令接收。
通过 ContextVar 实现请求上下文隔离，支持多用户并发。

使用方式：
    from plugins.common.handler import PluginHandler
    from plugins.common.base import Result
    
    class MyHandler(PluginHandler):
        name = "我的插件"
        command = "mycommand"
        ERROR_MESSAGES = {
            "empty_input": "Please enter something",
        }
        
        async def handle(self, event, args):
            if not args:
                await self.reply(self.get_error_message("empty_input"))
                return
            await self.reply(f"收到: {args}")

Example:
    >>> handler = MyHandler()
    >>> await handler.handle(event, "test")
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, ClassVar
from contextvars import ContextVar

from .compat import (
    NONEBOT_AVAILABLE,
    MessageEvent,
    GroupMessageEvent,
    Matcher,
)
from .base import Result

# 上下文变量：存储当前处理的事件和 matcher
_current_event_var: ContextVar[Optional[MessageEvent]] = ContextVar('current_event', default=None)


class PluginHandler(ABC):
    """
    插件业务逻辑处理器基类
    
    子类通过实现 handle 方法处理命令，使用 send/reply 方法发送消息。
    通过 ContextVar 实现请求上下文隔离，支持多用户并发访问。
    
    Attributes:
        name: 插件名称
        description: 插件描述
        command: 命令名（不带/）
        aliases: 命令别名集合
        priority: 命令优先级
        block: 是否阻断后续处理器
        feature_name: 功能开关名
        hidden_in_help: 是否在帮助中隐藏
        ERROR_MESSAGES: 错误类型到用户消息的映射字典
        
    Example:
        >>> class MyHandler(PluginHandler):
        ...     name = "测试插件"
        ...     command = "test"
        ...     ERROR_MESSAGES = {"empty": "Please enter something"}
        ...     
        ...     async def handle(self, event, args):
        ...         if not args:
        ...             await self.reply(self.get_error_message("empty"))
        ...             return
        ...         await self.reply(f"Hello, {args}!")
    """
    
    # 元数据（子类配置）
    name: str = ""
    description: str = ""
    command: Optional[str] = None
    aliases: Optional[set] = None
    priority: int = 10
    block: bool = True
    feature_name: Optional[str] = None
    hidden_in_help: bool = False
    
    # 错误消息映射（子类可覆盖）
    ERROR_MESSAGES: ClassVar[dict[str, str]] = {}
    
    @abstractmethod
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理命令（子类必须实现）
        
        Args:
            event: 消息事件对象
            args: 命令参数（已去除命令名）
            
        Returns:
            None
            
        Example:
            >>> async def handle(self, event, args):
            ...     await self.reply(f"收到参数: {args}")
        """
        pass
    
    def get_error_message(self, error: str, context: dict = None) -> str:
        """
        根据错误类型获取用户友好的错误消息
        
        从 ERROR_MESSAGES 字典中查找对应的错误消息。
        如果找不到，返回默认错误消息。
        
        Args:
            error: 错误类型或错误信息
            context: 上下文信息（用于格式化错误消息）
            
        Returns:
            用户友好的错误消息
            
        Example:
            >>> class MyHandler(PluginHandler):
            ...     ERROR_MESSAGES = {"not_found": "Item not found: {name}"}
            ...     
            ...     async def handle(self, event, args):
            ...         msg = self.get_error_message("not_found", {"name": args})
            ...         # msg = "Item not found: test"
        """
        message = self.ERROR_MESSAGES.get(error)
        if message is None:
            return f"Operation failed: {error}"
        
        # 支持格式化字符串
        if context:
            try:
                return message.format(**context)
            except (KeyError, ValueError):
                pass
        
        return message
    
    def ok(self, value: Any = None) -> Result:
        """
        创建成功的 Result
        
        Args:
            value: 返回值
            
        Returns:
            Result.ok(value)
            
        Example:
            >>> def find_item(self, id: str) -> Result[Item]:
            ...     item = self._find(id)
            ...     if item:
            ...         return self.ok(item)
            ...     return self.err("not_found")
        """
        return Result.ok(value)
    
    def err(self, error: str) -> Result:
        """
        创建失败的 Result
        
        Args:
            error: 错误类型
            
        Returns:
            Result.err(error)
            
        Example:
            >>> def find_item(self, id: str) -> Result[Item]:
            ...     if not id:
            ...         return self.err("empty_id")
            ...     return self.ok(item)
        """
        return Result.err(error)
    
    def check(self, condition: bool, error: str, value: Any = None) -> Result:
        """
        条件检查，快速创建 Result
        
        条件为真返回 ok，否则返回 err。
        
        Args:
            condition: 检查条件
            error: 条件为假时的错误类型
            value: 条件为真时的返回值
            
        Returns:
            根据条件返回 Result.ok 或 Result.err
            
        Example:
            >>> def validate(self, args: str) -> Result[str]:
            ...     return self.check(len(args) > 0, "empty_input", args)
        """
        if condition:
            return Result.ok(value)
        return Result.err(error)
    
    async def handle_error(self, error: Exception) -> None:
        """
        处理错误（可重写）
        
        当 handle 方法抛出异常时调用，默认发送错误信息。
        
        Args:
            error: 异常对象
            
        Returns:
            None
            
        Example:
            >>> async def handle_error(self, error):
            ...     await self.send(f"出错了: {error}", finish=True)
        """
        await self.send(f"处理出错: {error}", finish=True)
    
    def _get_current_matcher(self) -> Optional[Matcher]:
        """
        获取当前请求的 matcher（从 ContextVar，支持并发）
        
        Returns:
            当前请求的 Matcher 对象，如果不存在返回 None
            
        Example:
            >>> matcher = self._get_current_matcher()
            >>> if matcher:
            ...     await matcher.send("Hello")
        """
        # 避免循环导入，延迟导入
        from .receiver import _current_matcher_var
        return _current_matcher_var.get()
    
    async def send(self, message: Any, *, at: bool = False, finish: bool = False) -> None:
        """
        发送消息（默认使用缓冲，防风控）
        
        通过发送缓冲区控制发送频率，避免触发风控。
        在调用者上下文中执行，避免 ContextVar 丢失。
        
        Args:
            message: 消息内容
            at: 是否@发送者
            finish: 是否结束会话（调用 matcher.finish）
            
        Returns:
            None
            
        Example:
            >>> await self.send("Hello")  # 普通发送
            >>> await self.send("Hello", at=True)  # @用户
            >>> await self.send("Bye", finish=True)  # 结束会话
        """
        matcher = self._get_current_matcher()
        if not matcher:
            return
        
        from .buffer import get_buffer
        from .config import config
        
        # 构建消息
        if at and NONEBOT_AVAILABLE:
            event = _current_event_var.get()
            if event:
                from ..utils import build_at_message
                msg = build_at_message(event.user_id, str(message))
            else:
                msg = message
        else:
            msg = message
        
        # 并发调试模式：附加buffer队列数量
        if config.debug_concurrent:
            buffer = get_buffer()
            queue_size = buffer.qsize()
            msg = f"[{queue_size}]{msg}"
        
        # 获取群号
        event = _current_event_var.get()
        group_id = event.group_id if event and hasattr(event, 'group_id') else 0
        
        # 使用缓冲发送
        if finish:
            # finish 需要立即执行并结束
            # 捕获 FinishedException，防止异常传播到插件代码
            try:
                await matcher.finish(msg)
            except Exception as e:
                # 检查是否为 NoneBot 的 FinishedException
                if e.__class__.__name__ == 'FinishedException':
                    # 静默处理，这是预期的控制流异常
                    pass
                else:
                    raise
        else:
            await get_buffer().send(group_id, msg, matcher.send)
    
    async def reply(self, message: Any, *, finish: bool = False) -> None:
        """
        回复用户（自动@）
        
        调用 send 方法并设置 at=True，自动@消息发送者。
        
        Args:
            message: 消息内容
            finish: 是否结束会话
            
        Returns:
            None
            
        Example:
            >>> await self.reply("收到你的消息")
            >>> await self.reply("再见", finish=True)
        """
        await self.send(message, at=True, finish=finish)
    
    @property
    def _event(self) -> Optional[MessageEvent]:
        """
        获取当前事件
        
        Returns:
            当前消息事件对象，如果不存在返回 None
            
        Example:
            >>> event = self._event
            >>> if event:
            ...     print(f"用户ID: {event.user_id}")
        """
        return _current_event_var.get()
    
    @property
    def is_group(self) -> bool:
        """
        是否为群聊
        
        Returns:
            True 如果是群聊消息，False 如果是私聊消息
            
        Example:
            >>> if self.is_group:
            ...     await self.reply("群聊消息")
            ... else:
            ...     await self.reply("私聊消息")
        """
        return isinstance(self._event, GroupMessageEvent)


class MessageHandler(PluginHandler):
    """
    消息处理器基类 - 处理所有消息
    
    用于监听所有群聊/私聊消息，不需要特定命令触发。
    子类重写 handle_message 方法实现消息处理逻辑。
    
    Attributes:
        message_priority: 消息处理优先级
        message_block: 是否阻断后续处理器
        
    Example:
        >>> class MyMessageHandler(MessageHandler):
        ...     name = "消息监听"
        ...     
        ...     async def handle_message(self, event):
        ...         if "关键词" in event.get_plaintext():
        ...             await self.reply("收到关键词")
    """
    
    message_priority: int = 1
    message_block: bool = False
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        默认调用 handle_message
        
        Args:
            event: 消息事件对象
            args: 命令参数（消息处理器中通常为空）
            
        Returns:
            None
        """
        await self.handle_message(event)
    
    async def handle_message(self, event: MessageEvent) -> None:
        """
        处理消息（子类重写）
        
        Args:
            event: 消息事件对象
            
        Returns:
            None
            
        Example:
            >>> async def handle_message(self, event):
            ...     text = event.get_plaintext()
            ...     if "hello" in text.lower():
            ...         await self.reply("Hi there!")
        """
        pass
