"""
插件基类模块 - 统一的插件开发框架

提供标准化的插件开发框架，封装了命令注册、权限检查、功能开关、
错误处理等通用逻辑，让插件开发者只需关注业务逻辑。

快速开始:
    >>> from plugins.common import CommandPlugin, AIService, config
    
    >>> class EchoPlugin(CommandPlugin):
    ...     name = "回声"                    # 插件名称（显示用）
    ...     description = "重复用户的话"     # 功能描述
    ...     command = "echo"                # 命令名（不带/）
    ...     feature_name = "echo"           # 功能开关名（对应 config.echo_enabled）
    ...     priority = 10                   # 优先级（越小越先处理）
    ...     
    ...     async def handle(self, event, args: str) -> None:
    ...         # args 是去掉命令后的纯文本参数
    ...         if not args:
    ...             await self.reply("请输入内容")
    ...             return
    ...         await self.reply(f"回声: {args}")
    
    >>> # 实例化即注册，这行代码必须存在
    >>> plugin = EchoPlugin()

基类自动处理：
- 命令处理器注册（on_command）
- 黑名单检查（BanService）
- 功能开关检查（config.{feature_name}_enabled）
- 参数提取和清理
- 错误处理和日志记录

传统方式对比：
    # 传统方式需要写的代码：
    - on_command 注册
    - CommandGuard 权限检查
    - FeatureChecker 功能检查
    - 参数提取处理
    - 错误 try-except
    
    # 使用基类只需：
    - 继承 CommandPlugin
    - 填写元数据（name, command 等）
    - 实现 handle 方法
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Dict
from functools import wraps
from contextvars import ContextVar

try:
    from nonebot import on_command, on_message, Bot # type: ignore
    from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent, Message, MessageSegment # type: ignore
    from nonebot.matcher import Matcher # type: ignore
    from nonebot.params import CommandArg
    from nonebot.plugin import PluginMetadata # type: ignore
    from nonebot.exception import FinishedException # type: ignore
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    # 占位符，用于类型检查
    class Matcher: pass
    class MessageEvent: pass
    class GroupMessageEvent: pass
    class Message: pass
    class MessageSegment: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass
    class FinishedException(Exception): pass
    def on_command(*args, **kwargs): 
        class FakeMatcher:
            def handle(self, **kwargs):
                return lambda f: f
        return FakeMatcher()
    def on_message(*args, **kwargs): 
        class FakeMatcher:
            def handle(self, **kwargs):
                return lambda f: f
        return FakeMatcher()
    class Bot: pass
    def CommandArg():
        return None

from .config import config
from .services import BanService, AIService, ChatService, BotService
from .services.registry import PluginRegistry, PluginInfo

# 上下文变量：存储当前处理的事件（每个异步任务独立）
_current_event_var: ContextVar[Optional[MessageEvent]] = ContextVar('current_event', default=None)


class PluginBase(ABC):
    """
    插件基类 - 所有插件的父类
    
    提供标准化的插件开发框架，封装了通用逻辑：
    - 命令/消息处理器自动注册
    - 统一的权限检查（黑名单）
    - 功能开关管理
    - 错误处理和日志
    - 便捷的消息发送方法
    
    子类必须实现：
    - name: 插件名称
    - description: 功能描述
    - command 或 use_on_message: 触发方式
    - handle() 或 handle_message(): 处理逻辑
    
    可选配置：
    - feature_name: 功能开关名（如 "math" 对应 config.math_enabled）
    - priority: 处理器优先级（默认 10，越小越优先）
    - block: 是否阻止后续处理器（默认 True）
    - aliases: 命令别名集合
    
    Attributes:
        _matcher: NoneBot 的 Matcher 对象，用于发送消息
        _current_event: 当前处理的消息事件
        _ban_service: 黑名单服务实例
        _ai_service: AI 服务实例
        _chat_service: 聊天服务实例
    
    Example:
        >>> class MyPlugin(CommandPlugin):
        ...     name = "示例插件"
        ...     description = "演示基类功能"
        ...     command = "示例"
        ...     feature_name = "example"
        ...     
        ...     async def handle(self, event, args: str) -> None:
        ...         # 权限和功能已自动检查
        ...         await self.reply(f"收到: {args}")
        ...
        >>> plugin = MyPlugin()  # 实例化即注册
    """
    
    # ========== 必须配置的元数据 ==========
    name: str = ""           # 插件显示名称
    description: str = ""   # 功能描述
    version: str = "2.2.1"  # 版本号
    author: str = "Lichlet" # 作者
    
    # ========== 命令配置 ==========
    command: Optional[str] = None      # 命令名（如 "定义"，不带/）
    aliases: Optional[set] = None      # 命令别名集合
    priority: int = 10                 # 优先级（1-100，越小越优先）
    block: bool = True                 # 是否阻止后续处理器
    
    # ========== 功能开关 ==========
    feature_name: Optional[str] = None  # 对应 config.{feature_name}_enabled
    
    # ========== 消息处理器配置 ==========
    use_on_message: bool = False        # 是否使用消息处理器（而非命令）
    message_priority: int = 1           # 消息处理器优先级
    message_block: bool = False         # 消息处理器是否阻止后续
    
    # ========== 帮助配置 ==========
    hidden_in_help: bool = False        # 是否在帮助中隐藏（如隐藏功能）
    
    def __init__(self) -> None:
        """
        初始化插件
        
        自动创建服务实例，并在 NoneBot 可用时注册处理器。
        子类如果重写此方法，必须调用 super().__init__()
        """
        self._matcher: Optional[Matcher] = None
        self._ban_service = BanService.get_instance()
        self._ai_service = AIService.get_instance()
        self._chat_service = ChatService.get_instance()
        self._bot_service = BotService.get_instance()
        
        # 注册到插件注册表
        self._register_to_registry()
        
        if NONEBOT_AVAILABLE:
            self._register()
    
    def _register(self) -> None:
        """
        注册插件处理器（内部方法，自动调用）
        
        根据配置自动注册命令处理器或消息处理器：
        - 如果设置了 command，注册命令处理器
        - 如果设置了 use_on_message=True，注册消息处理器
        """
        if not NONEBOT_AVAILABLE:
            return
        
        # 创建插件元数据供 NoneBot 读取
        self.__plugin_meta__ = PluginMetadata(
            name=self.name,
            description=self.description,
            usage=self.get_usage(),
            extra={
                "author": self.author,
                "version": self.version,
            }
        )
        
        # 注册命令处理器
        if self.command:
            self._matcher = on_command(
                self.command,
                aliases=self.aliases,
                priority=self.priority,
                block=self.block
            ) # type: ignore
            self._matcher.handle()(self._create_handler()) # type: ignore
        
        # 注册消息处理器
        elif self.use_on_message:
            self._matcher = on_message(
                priority=self.message_priority,
                block=self.message_block
            ) # type: ignore
            self._matcher.handle()(self._create_message_handler()) # type: ignore
    
    def _register_to_registry(self) -> None:
        """
        注册到插件注册表（内部方法，自动调用）
        
        收集插件元数据并注册到 PluginRegistry，用于动态生成帮助信息。
        """
        try:
            registry = PluginRegistry.get_instance()
            info = PluginInfo(
                name=self.name,
                description=self.description,
                command=self.command,
                aliases=self.aliases,
                feature_name=self.feature_name,
                usage=self.get_usage(),
                is_message_plugin=self.use_on_message,
                hidden=self.hidden_in_help
            )
            registry.register(info)
        except Exception as e:
            # 注册失败不应影响插件功能
            pass
    
    def get_usage(self) -> str:
        """
        获取使用说明
        
        Returns:
            命令使用说明字符串
            
        可重写此方法自定义帮助信息
        """
        if self.command:
            return f"/{self.command} [参数]"
        return "自动触发"
    
    def _check_permission(self, event: MessageEvent) -> bool:
        """
        检查用户权限（内部方法）
        
        检查用户是否在黑名单中。
        
        Args:
            event: 消息事件
            
        Returns:
            True 如果用户有权限，False 如果被拉黑
        """
        if self._ban_service.is_banned(event.user_id): # type: ignore
            return False
        return True
    
    def _check_feature(self) -> bool:
        """
        检查功能是否开启（内部方法）
        
        检查 config.{feature_name}_enabled 是否为 True。
        如果没有设置 feature_name，默认返回 True。
        
        Returns:
            True 如果功能开启，False 如果关闭
        """
        if not self.feature_name:
            return True
        return getattr(config, f"{self.feature_name}_enabled", True)
    
    def _create_handler(self) -> Callable:
        """
        创建命令处理器（内部方法）
        
        包装用户的 handle 方法，添加：
        - 权限检查
        - 功能开关检查
        - 参数提取
        - 错误处理
        
        使用 ContextVar 存储当前事件，确保并发安全。
        
        Returns:
            包装后的处理器函数
        """
        plugin = self  # 捕获 self 引用供闭包使用
        
        async def handler(event: MessageEvent, args=CommandArg()):
            """实际的处理器函数"""
            # 设置上下文变量（每个异步任务独立）
            token = _current_event_var.set(event)
            
            try:
                # 1. 权限检查
                if not plugin._check_permission(event):
                    await plugin.finish("笨蛋,你的账号被拉黑了!")
                    return
                
                # 2. 功能开关检查
                if not plugin._check_feature():
                    await plugin.finish("笨蛋,这个功能被关掉了!")
                    return
                
                # 3. 提取命令参数
                content = args.extract_plain_text().strip() # type: ignore
                
                # 4. 执行用户定义的处理逻辑
                try:
                    await plugin.handle(event, content)
                except FinishedException:
                    # 正常的会话结束信号，不处理
                    raise
                except Exception as e:
                    # 其他异常，调用错误处理器
                    await plugin.handle_error(e)
            finally:
                # 清理上下文变量
                _current_event_var.reset(token)
        
        return handler
    
    def _create_message_handler(self) -> Callable:
        """
        创建消息处理器（内部方法）
        
        包装用户的 handle_message 方法，添加权限和功能检查。
        使用 ContextVar 确保并发安全。
        
        Returns:
            包装后的处理器函数
        """
        plugin = self
        
        async def handler(event: MessageEvent):
            """消息处理器"""
            # 设置上下文变量（每个异步任务独立）
            token = _current_event_var.set(event)
            
            try:
                if not plugin._check_feature():
                    return
                
                if not plugin._check_permission(event):
                    return
                
                try:
                    await plugin.handle_message(event)
                except Exception:
                    pass  # 消息处理器静默处理错误
            finally:
                # 清理上下文变量
                _current_event_var.reset(token)
        
        return handler
    
    @abstractmethod
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理命令（子类必须实现）
        
        这是处理命令的核心方法，基类会自动调用它。
        无需手动处理权限检查、功能开关等，基类已处理完毕。
        
        Args:
            event: 消息事件对象，包含用户信息、群信息等
            args: 命令参数（已去除首尾空格，不包含命令本身）
            
        Example:
            >>> async def handle(self, event, args: str) -> None:
            ...     if not args:  # 检查空参数
            ...         await self.reply("请输入内容")
            ...         return
            ...     # 处理业务逻辑...
            ...     await self.reply(f"结果: {result}")
        """
        pass
    
    async def handle_message(self, event: MessageEvent) -> None:
        """
        处理普通消息（用于 on_message 插件）
        
        如果设置了 use_on_message=True，需要实现此方法。
        默认空实现，子类可重写。
        
        Args:
            event: 消息事件对象
        """
        pass
    
    async def handle_error(self, error: Exception) -> None:
        """
        处理错误（可重写）
        
        当 handle 方法抛出异常时调用。
        默认发送错误信息给用户。
        
        Args:
            error: 捕获的异常对象
            
        可重写此方法自定义错误处理：
            >>> async def handle_error(self, error):
            ...     self.logger.error(f"Error: {error}")
            ...     await self.reply("处理出错了，请稍后重试")
        """
        await self.finish(f"处理出错: {str(error)}")
    
    # ========== 便捷方法 ==========
    
    async def send(self, message: Any) -> None:
        """
        发送消息
        
        发送消息但不结束会话，后续可以继续处理。
        
        Args:
            message: 消息内容（字符串、Message 对象、MessageSegment 等）
            
        Example:
            >>> await self.send("第一步完成")
            >>> await self.send("第二步完成")
            >>> await self.finish("全部完成")  # 最后结束
        """
        if self._matcher:
            await self._matcher.send(message) # type: ignore
    
    async def finish(self, message: Any) -> None:
        """
        发送消息并结束会话
        
        发送消息后结束当前会话，阻止后续处理器。
        这是最常用的回复方式。
        
        Args:
            message: 消息内容
            
        Example:
            >>> await self.finish("处理完成")
        """
        if self._matcher:
            await self._matcher.finish(message) # type: ignore
    
    @property
    def _current_event(self) -> Optional[MessageEvent]:
        """
        获取当前处理的事件（从上下文变量）
        
        使用 ContextVar 确保并发安全，每个异步任务有独立的事件。
        
        Returns:
            当前消息事件，如果没有则返回 None
        """
        return _current_event_var.get()
    
    async def reply(self, text: str, at_user: bool = True) -> None:
        """
        回复用户（最常用）
        
        发送消息并@用户，默认自动@发送者。
        使用 ContextVar 获取当前事件，确保并发安全。
        
        Args:
            text: 回复文本内容
            at_user: 是否@用户（默认True）
            
        Example:
            >>> # 默认@用户
            >>> await self.reply("你好")
            >>> 
            >>> # 不@用户
            >>> await self.reply("广播消息", at_user=False)
        """
        if not NONEBOT_AVAILABLE:
            return
        
        current_event = self._current_event
        
        if not current_event:
            await self.send(text)
            return
        
        if at_user:
            # 使用工具函数构造@消息
            from ..utils import build_at_message
            msg = build_at_message(current_event.user_id, text)  # type: ignore
            await self.send(msg)
        else:
            await self.send(text)
    
    @property
    def is_group_chat(self) -> bool:
        """
        是否为群聊
        
        Returns:
            True 如果是群聊消息，False 如果是私聊
        """
        return isinstance(self._current_event, GroupMessageEvent)


class CommandPlugin(PluginBase):
    """
    命令插件基类 - 响应命令（如 /定义）
    
    这是最常用的插件类型，通过命令触发。
    只需设置 command 属性，实现 handle 方法。
    
    Example:
        >>> class MathPlugin(CommandPlugin):
        ...     name = "数学定义"
        ...     command = "定义"
        ...     feature_name = "math"
        ...     
        ...     async def handle(self, event, args):
        ...         # 用户发送 /定义 群论
        ...         # args = "群论"
        ...         pass
    """
    pass


class MessagePlugin(PluginBase):
    """
    消息插件基类 - 响应所有消息
    
    用于监听所有群聊消息，而非特定命令。
    需要设置 use_on_message = True，实现 handle_message 方法。
    
    Example:
        >>> class AutoReplyPlugin(MessagePlugin):
        ...     name = "自动回复"
        ...     use_on_message = True
        ...     message_priority = 1
        ...     
        ...     async def handle_message(self, event):
        ...         # 处理每条消息
        ...         if "关键词" in event.get_plaintext():
        ...             await self.reply("收到关键词")
    """
    use_on_message = True
    message_block = False
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """消息插件不需要实现此方法"""
        pass
