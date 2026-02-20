"""
通用装饰器模块 - 权限和功能检查

提供便捷的权限检查和功能开关检查装饰器，简化插件开发。

使用示例:
    >>> from plugins.common import CommandGuard
    >>> 
    >>> # 在处理器中使用
    >>> @handler.handle()
    >>> async def handle(event: MessageEvent):
    ...     # 检查权限 + 功能开关
    ...     guard = CommandGuard(handler, feature_name='math')
    ...     if not await guard.check(event):
    ...         return  # 检查失败会自动 finish
    
    >>> # 仅权限检查
    >>> checker = PermissionChecker(handler)
    >>> if not await checker.check(event):
    ...     return
    
    >>> # 仅功能检查
    >>> checker = FeatureChecker(handler)
    >>> if not await checker.check('math', event):
    ...     return

设计原则:
    - 可组合: 权限、功能检查可单独使用或组合
    - 自动响应: 检查失败自动调用 handler.finish()
    - 灵活控制: 支持 finish=False 手动处理失败

扩展指南:
    如需更多检查器:
    - 群管理检查: AdminChecker
    - 频率限制: RateLimitChecker
    - 参数验证: ParamValidator
    
    如需装饰器语法:
    - @require_admin(handler)
    - @require_cooldown(seconds=60)
"""

from functools import wraps
from typing import Callable, Optional

from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent

from .services import get_ban_service
from .config import config


class PermissionChecker:
    """
    权限检查类 - 检查用户是否被拉黑
    
    适用于需要单独进行权限检查的场景。
    
    Attributes:
        handler: 命令处理器，用于调用 finish
        ban_service: 黑名单服务实例
        banned_message: 被拉黑时的提示消息
    
    Example:
        >>> checker = PermissionChecker(handler, banned_message="访问被拒绝")
        >>> if not await checker.check(event):
        ...     return
    """
    
    def __init__(
        self,
        handler,
        banned_message: str = "笨蛋,你的账号被拉黑了!"
    ):
        """
        初始化检查器
        
        Args:
            handler: 命令处理器（如 math_handler）
            banned_message: 用户被拉黑时的提示消息
        """
        self.handler = handler
        self.ban_service = get_ban_service()
        self.banned_message = banned_message
    
    async def check(self, event: MessageEvent, finish: bool = True) -> bool:
        """
        检查用户权限
        
        Args:
            event: 消息事件
            finish: 检查失败时是否自动调用 handler.finish
            
        Returns:
            True 如果用户未被拉黑，False 如果被拉黑
            
        Example:
            >>> checker = PermissionChecker(handler)
            >>> 
            >>> # 自动 finish（推荐）
            >>> if not await checker.check(event):
            ...     return
            >>> 
            >>> # 手动处理
            >>> if not await checker.check(event, finish=False):
            ...     await handler.send("你被拉黑了")
            ...     # 做其他处理
        """
        if self.ban_service.is_banned(event.user_id):
            if finish:
                await self.handler.finish(self.banned_message)
            return False
        return True


class FeatureChecker:
    """
    功能开关检查类 - 检查功能是否启用
    
    通过读取 config 中的 feature_name_enabled 配置项判断。
    
    Example:
        >>> checker = FeatureChecker(handler, disabled_message="功能已关闭")
        >>> if not await checker.check('math', event):
        ...     return
    """
    
    def __init__(
        self,
        handler,
        disabled_message: str = "笨蛋,这个功能被关掉了!"
    ):
        """
        初始化检查器
        
        Args:
            handler: 命令处理器
            disabled_message: 功能关闭时的提示消息
        """
        self.handler = handler
        self.disabled_message = disabled_message
    
    async def check(
        self,
        feature_name: str,
        event: Optional[MessageEvent] = None,
        finish: bool = True
    ) -> bool:
        """
        检查功能是否开启
        
        读取 config.{feature_name}_enabled 配置。
        
        Args:
            feature_name: 功能配置名，如 'math', 'random', 'highnoon'
            event: 消息事件（可选，当前未使用但保留扩展性）
            finish: 检查失败时是否自动 finish
            
        Returns:
            True 如果功能开启，False 如果关闭
            
        Example:
            >>> checker = FeatureChecker(handler)
            >>> 
            >>> # 检查数学功能
            >>> if not await checker.check('math', event):
            ...     return
            >>> 
            >>> # 检查随机回复
            >>> if not await checker.check('random', event):
            ...     return
        """
        enabled = getattr(config, f"{feature_name}_enabled", True)
        if not enabled:
            if finish:
                await self.handler.finish(self.disabled_message)
            return False
        return True


class CommandGuard:
    """
    命令守卫 - 组合权限和功能检查
    
    最常用的检查器，一行代码完成权限+功能检查。
    
    检查顺序:
    1. 黑名单检查（PermissionChecker）
    2. 功能开关检查（FeatureChecker，如果指定了 feature_name）
    
    Example:
        >>> # 完整检查
        >>> guard = CommandGuard(handler, feature_name='math')
        >>> if not await guard.check(event):
        ...     return
        >>> 
        >>> # 仅权限检查（不检查功能开关）
        >>> guard = CommandGuard(handler)
        >>> if not await guard.check(event):
        ...     return
    """
    
    def __init__(
        self,
        handler,
        feature_name: Optional[str] = None,
        banned_message: str = "笨蛋,你的账号被拉黑了!",
        disabled_message: str = "笨蛋,这个功能被关掉了!"
    ):
        """
        初始化守卫
        
        Args:
            handler: 命令处理器
            feature_name: 功能配置名，None 则只检查权限
            banned_message: 被拉黑提示
            disabled_message: 功能关闭提示
        """
        self.handler = handler
        self.feature_name = feature_name
        self.permission = PermissionChecker(handler, banned_message)
        self.feature = FeatureChecker(handler, disabled_message)
    
    async def check(self, event: MessageEvent, finish: bool = True) -> bool:
        """
        执行所有检查
        
        按顺序检查：权限 → 功能开关（如果指定）
        
        Args:
            event: 消息事件
            finish: 失败时是否自动 finish
            
        Returns:
            True 通过所有检查，False 任一检查失败
            
        Example:
            >>> guard = CommandGuard(handler, feature_name='math')
            >>> 
            >>> # 标准用法
            >>> @handler.handle()
            ... async def handle(event: MessageEvent):
            ...     if not await guard.check(event):
            ...         return
            ...     # 执行业务逻辑
            >>> 
            >>> # 手动处理失败
            >>> if not await guard.check(event, finish=False):
            ...     await handler.send("检查失败")
            ...     return
        """
        # 1. 检查权限
        if not await self.permission.check(event, finish=finish):
            return False
        
        # 2. 检查功能开关（如果指定）
        if self.feature_name:
            if not await self.feature.check(self.feature_name, event, finish=finish):
                return False
        
        return True


def require_permission(
    handler,
    banned_message: str = "笨蛋,你的账号被拉黑了!",
    finish_on_fail: bool = True
):
    """
    权限检查装饰器（函数装饰器版本）
    
    适用于需要装饰函数的场景。
    
    Args:
        handler: 命令处理器
        banned_message: 被拉黑提示
        finish_on_fail: 失败时是否 finish
        
    Returns:
        装饰器函数
        
    Example:
        >>> @handler.handle()
        >>> @require_permission(handler)
        >>> async def handle(event: MessageEvent):
        ...     # 自动通过权限检查
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(event: MessageEvent, **kwargs):
            checker = PermissionChecker(handler, banned_message)
            if not await checker.check(event, finish=finish_on_fail):
                return None
            return await func(event, **kwargs)
        return wrapper
    return decorator


def require_feature(
    feature_name: str,
    handler,
    disabled_message: str = "笨蛋,这个功能被关掉了!",
    finish_on_fail: bool = True
):
    """
    功能开关检查装饰器（函数装饰器版本）
    
    Args:
        feature_name: 功能配置名
        handler: 命令处理器
        disabled_message: 功能关闭提示
        finish_on_fail: 失败时是否 finish
        
    Returns:
        装饰器函数
        
    Example:
        >>> @handler.handle()
        >>> @require_feature('math', handler)
        >>> async def handle(event: MessageEvent):
        ...     # 自动通过功能检查
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(event: MessageEvent, **kwargs):
            checker = FeatureChecker(handler, disabled_message)
            if not await checker.check(feature_name, event, finish=finish_on_fail):
                return None
            return await func(event, **kwargs)
        return wrapper
    return decorator
