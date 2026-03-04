"""
命令接收器模块 - 接收消息并控制发送频率

使用 buffer 控制同群消息间隔，避免风控。
处理逻辑仍在 NoneBot 上下文中执行。

通过 CommandReceiver 和 MessageReceiver 分别处理命令和消息，
实现权限检查、功能开关控制和频率限制。

使用方式：
    from plugins.common.handler import PluginHandler
    from plugins.common.receiver import CommandReceiver
    
    class MyHandler(PluginHandler):
        name = "测试"
        command = "test"
        
        async def handle(self, event, args):
            await self.reply(f"收到: {args}")
    
    # 创建接收器自动注册命令
    handler = MyHandler()
    receiver = CommandReceiver(handler)

Example:
    >>> handler = MyHandler()
    >>> receiver = CommandReceiver(handler)  # 自动注册 /test 命令
"""

import asyncio
from contextvars import ContextVar
from typing import Optional, Callable

from .compat import (
    NONEBOT_AVAILABLE,
    MessageEvent,
    GroupMessageEvent,
    Matcher,
    CommandArg,
)

if NONEBOT_AVAILABLE:
    from nonebot import on_command, on_message
    from nonebot.exception import FinishedException
else:
    class FinishedException(Exception):
        pass
    def on_command(*args, **kwargs):
        class FakeMatcher:
            def handle(self, **kwargs): return lambda f: f
        return FakeMatcher()
    def on_message(*args, **kwargs):
        class FakeMatcher:
            def handle(self, **kwargs): return lambda f: f
        return FakeMatcher()

from .protocols import ServiceLocator, BanServiceProtocol
from .config import config
from .handler import PluginHandler, MessageHandler, _current_event_var

# ContextVar 存储当前请求的 matcher（解决并发冲突）
_current_matcher_var: ContextVar[Optional[Matcher]] = ContextVar('_current_matcher', default=None)


class CommandReceiver:
    """
    命令接收器 - 带频率控制
    
    封装 NoneBot 命令注册，提供统一的权限检查、功能开关控制和频率限制。
    自动将 Handler 注册到插件注册表。
    
    Attributes:
        _handler: 关联的 PluginHandler 实例
        _matcher: NoneBot Matcher 对象
        
    Example:
        >>> handler = MyHandler()
        >>> receiver = CommandReceiver(handler)  # 自动注册命令
    """
    
    def __init__(self, handler: PluginHandler) -> None:
        """
        初始化命令接收器
        
        Args:
            handler: 插件处理器实例
            
        Returns:
            None
            
        Example:
            >>> handler = MyHandler()
            >>> receiver = CommandReceiver(handler)
        """
        self._handler = handler
        self._matcher: Optional[Matcher] = None
        self._register_to_registry()
        if NONEBOT_AVAILABLE:
            self._register_command()
    
    def _register_to_registry(self) -> None:
        """
        注册到插件注册表
        
        将插件信息注册到 PluginRegistry，供帮助系统使用。
        
        Returns:
            None
        """
        try:
            from .services.registry import PluginRegistry, PluginInfo
            registry = PluginRegistry.get_instance()
            info = PluginInfo(
                name=self._handler.name,
                description=self._handler.description,
                command=self._handler.command,
                aliases=self._handler.aliases,
                feature_name=self._handler.feature_name,
                usage=self._get_usage(),
                is_message_plugin=False,
                hidden=self._handler.hidden_in_help
            )
            registry.register(info)
        except Exception:
            pass
    
    def _get_usage(self) -> str:
        """
        获取命令用法说明
        
        Returns:
            命令用法字符串
            
        Example:
            >>> usage = receiver._get_usage()
            >>> print(usage)  # "/command [参数]"
        """
        if self._handler.command:
            return f"/{self._handler.command} [参数]"
        return "自动触发"
    
    def _register_command(self) -> None:
        """
        注册 NoneBot 命令
        
        使用 on_command 注册命令，设置优先级、阻断等参数。
        
        Returns:
            None
            
        Raises:
            ValueError: 如果 handler 没有设置 command
        """
        if not self._handler.command:
            raise ValueError(f"Handler {self._handler.name} 没有设置 command")
        try:
            self._matcher = on_command(
                self._handler.command,
                aliases=self._handler.aliases,
                priority=self._handler.priority,
                block=self._handler.block
            )
            self._matcher.handle()(self._create_handler())
        except ValueError as e:
            if "NoneBot has not been initialized" not in str(e):
                raise
    
    def _create_handler(self) -> Callable:
        """
        创建处理器 - 带频率控制
        
        创建实际的命令处理函数，包含权限检查、功能开关检查和错误处理。
        
        Returns:
            处理函数（接受 matcher, event, args 参数）
            
        Example:
            >>> handler_func = receiver._create_handler()
            >>> # 此函数会被 NoneBot 调用
        """
        receiver = self
        
        async def handler(matcher: Matcher, event: MessageEvent, args=CommandArg()):
            # 权限检查
            if not receiver._check_permission(event):
                await matcher.finish("笨蛋,你的账号被拉黑了!")
                return
            
            # 功能开关检查
            if not receiver._check_feature():
                await matcher.finish("笨蛋,这个功能被关掉了!")
                return
            
            # 执行处理（在 NoneBot 上下文中）
            event_token = _current_event_var.set(event)
            matcher_token = _current_matcher_var.set(matcher)
            try:
                content = args.extract_plain_text().strip() if args else ""
                
                try:
                    await receiver._handler.handle(event, content)
                except FinishedException:
                    raise
                except Exception as e:
                    await receiver._handler.handle_error(e)
            finally:
                _current_event_var.reset(event_token)
                _current_matcher_var.reset(matcher_token)
        
        return handler
    
    def _check_permission(self, event: MessageEvent) -> bool:
        """
        检查用户权限
        
        Args:
            event: 消息事件对象
            
        Returns:
            True 如果用户未被拉黑，False 如果被拉黑
            
        Example:
            >>> if receiver._check_permission(event):
            ...     await self.handle(event, args)
        """
        ban_service = ServiceLocator.get(BanServiceProtocol)
        if ban_service is None:
            return True
        return not ban_service.is_banned(event.user_id)
    
    def _check_feature(self) -> bool:
        """
        检查功能是否启用
        
        Returns:
            True 如果功能已启用或没有功能开关，False 如果被禁用
            
        Example:
            >>> if receiver._check_feature():
            ...     await self.handle(event, args)
        """
        if not self._handler.feature_name:
            return True
        return config.is_enabled(self._handler.feature_name)


class MessageReceiver:
    """
    消息接收器 - 带频率控制
    
    封装 NoneBot 消息处理器注册，监听所有群聊/私聊消息。
    提供统一的权限检查和功能开关控制。
    
    Attributes:
        _handler: 关联的 MessageHandler 实例
        _matcher: NoneBot Matcher 对象
        
    Example:
        >>> handler = MyMessageHandler()
        >>> receiver = MessageReceiver(handler)  # 自动注册消息监听
    """
    
    def __init__(self, handler: MessageHandler) -> None:
        """
        初始化消息接收器
        
        Args:
            handler: 消息处理器实例
            
        Returns:
            None
            
        Example:
            >>> handler = MyMessageHandler()
            >>> receiver = MessageReceiver(handler)
        """
        self._handler = handler
        self._matcher: Optional[Matcher] = None
        self._register_to_registry()
        if NONEBOT_AVAILABLE:
            self._register_message_handler()
    
    def _register_to_registry(self) -> None:
        """
        注册到插件注册表
        
        将消息插件信息注册到 PluginRegistry。
        
        Returns:
            None
        """
        try:
            from .services.registry import PluginRegistry, PluginInfo
            registry = PluginRegistry.get_instance()
            info = PluginInfo(
                name=self._handler.name,
                description=self._handler.description,
                command=None,
                aliases=None,
                feature_name=self._handler.feature_name,
                usage="自动触发",
                is_message_plugin=True,
                hidden=self._handler.hidden_in_help
            )
            registry.register(info)
        except Exception:
            pass
    
    def _register_message_handler(self) -> None:
        """
        注册消息处理器
        
        使用 on_message 注册消息监听。
        
        Returns:
            None
        """
        try:
            self._matcher = on_message(
                priority=self._handler.message_priority,
                block=self._handler.message_block
            )
            self._matcher.handle()(self._create_handler())
        except ValueError as e:
            if "NoneBot has not been initialized" not in str(e):
                raise
    
    def _create_handler(self) -> Callable:
        """
        创建消息处理函数
        
        创建实际的消息处理函数，包含权限检查和功能开关检查。
        
        Returns:
            处理函数（接受 matcher, event 参数）
            
        Example:
            >>> handler_func = receiver._create_handler()
            >>> # 此函数会被 NoneBot 调用
        """
        receiver = self
        
        async def handler(matcher: Matcher, event: MessageEvent):
            if not receiver._check_permission(event):
                return
            if not receiver._check_feature():
                return
            
            # 执行处理（在 NoneBot 上下文中）
            event_token = _current_event_var.set(event)
            matcher_token = _current_matcher_var.set(matcher)
            try:
                try:
                    await receiver._handler.handle_message(event)
                except FinishedException:
                    raise
                except Exception as e:
                    print(f"Message handler error: {e}")
            finally:
                _current_event_var.reset(event_token)
                _current_matcher_var.reset(matcher_token)
        
        return handler
    
    def _check_permission(self, event: MessageEvent) -> bool:
        """
        检查用户权限
        
        Args:
            event: 消息事件对象
            
        Returns:
            True 如果用户未被拉黑，False 如果被拉黑
            
        Example:
            >>> if receiver._check_permission(event):
            ...     await self.handle_message(event)
        """
        ban_service = ServiceLocator.get(BanServiceProtocol)
        if ban_service is None:
            return True
        return not ban_service.is_banned(event.user_id)
    
    def _check_feature(self) -> bool:
        """
        检查功能是否启用
        
        Returns:
            True 如果功能已启用或没有功能开关，False 如果被禁用
            
        Example:
            >>> if receiver._check_feature():
            ...     await self.handle_message(event)
        """
        if not self._handler.feature_name:
            return True
        return config.is_enabled(self._handler.feature_name)
