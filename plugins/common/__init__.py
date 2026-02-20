"""
公共模块 - 插件开发基础设施

提供所有插件共享的核心功能，采用分层架构设计：
    - 配置层: 统一配置管理（config）
    - 服务层: 业务逻辑封装（AIService, BanService, ChatService）
    - 接口层: 便捷的权限检查和依赖注入（CommandGuard, deps, PluginBase）
    - 工具层: 通用工具函数（build_at_message, download_image）
    - 基础层: 服务基类和通用工具（ServiceBase, Result）

快速开始:
    >>> from plugins.common import (
    ...     config,
    ...     CommandGuard,
    ...     AIService,
    ...     build_at_message,
    ... )

使用新的插件基类:
    >>> from plugins.common import CommandPlugin
    >>> 
    >>> class MyPlugin(CommandPlugin):
    ...     name = "我的插件"
    ...     command = "命令"
    ...     feature_name = "myfeature"
    ...     
    ...     async def handle(self, event, args):
    ...         await self.reply(f"收到: {args}")
"""

import logging
from nonebot.plugin import PluginMetadata

# 版本信息
__version__ = "2.2.1"

__plugin_meta__ = PluginMetadata(
    name="公共模块",
    usage="提供配置、服务、权限检查等基础设施",
    description="为所有插件提供统一的基础设施支持",
    extra={"author": "Lichlet"}
)

# ==================== 基础层 ====================
from .base import (
    ServiceBase,
    Result,
    safe_call,
)

# ==================== 游戏服务基类层 ====================
from .services.game import (
    GameServiceBase,
    GameState,
)

# ==================== 插件注册表层 ====================
from .services.registry import (
    PluginRegistry,
    PluginInfo,
    get_plugin_registry,
)

# ==================== 配置层 ====================
from .config import config, PluginConfig

# ==================== 服务层 ====================
from .services import (
    AIService,
    BanService,
    ChatService,
    BotService,
    ChatMessage,
    get_ai_service,
    get_ban_service,
    get_chat_service,
    get_bot_service,
    TokenService,
    get_token_service,
    SystemMonitorService,
    get_system_monitor_service,
)

# ==================== 插件基类层 ====================
from .plugin_base import (
    PluginBase,
    CommandPlugin,
    MessagePlugin,
)

# ==================== 装饰器层 ====================
from .decorators import (
    PermissionChecker,
    FeatureChecker,
    CommandGuard,
    require_permission,
    require_feature,
)

# ==================== 依赖注入层 ====================
from .deps import (
    dep_ai_service,
    dep_ban_service,
    dep_chat_service,
    dep_check_permission,
    dep_check_feature,
    dep_is_group_admin,
    dep_is_bot_admin,
    dep_chat_context,
    dep_recent_users,
)

# ==================== 工具函数层 ====================

def _import_utils():
    """延迟导入 utils 模块"""
    try:
        from ..utils import (
            build_at_message,
            build_reply_message,
            fetch_html,
            fetch_html_async,
            download_image,
            image_to_message,
            merge_images,
        )
        return {
            'build_at_message': build_at_message,
            'build_reply_message': build_reply_message,
            'fetch_html': fetch_html,
            'fetch_html_async': fetch_html_async,
            'download_image': download_image,
            'image_to_message': image_to_message,
            'merge_images': merge_images,
        }
    except ImportError as e:
        import warnings
        warnings.warn(f"Utils import failed: {e}")
        return {}

_utils = _import_utils()
build_at_message = _utils.get('build_at_message')
build_reply_message = _utils.get('build_reply_message')
fetch_html = _utils.get('fetch_html')
fetch_html_async = _utils.get('fetch_html_async')
download_image = _utils.get('download_image')
image_to_message = _utils.get('image_to_message')
merge_images = _utils.get('merge_images')


# ==================== 便捷函数 ====================

def read_prompt(prompt_name: str) -> str:
    """读取提示词文件"""
    import os
    
    paths_to_try = [
        os.path.join("prompts", prompt_name),
        os.path.join("prompts", f"{prompt_name}.txt"),
    ]
    
    for path in paths_to_try:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                pass
    
    return ""


# ==================== 初始化 ====================
logger = logging.getLogger("plugins.common")


def initialize_common() -> bool:
    """初始化公共模块"""
    if not config.deepseek_api_key:
        logger.warning("DeepSeek API密钥未设置，AI功能可能不可用")
    
    # 初始化服务
    ban_service = BanService.get_instance()
    ban_service.initialize()
    
    chat_service = ChatService.get_instance()
    chat_service.initialize()
    
    ai_service = AIService.get_instance()
    ai_service.initialize()
    
    bot_service = BotService.get_instance()
    bot_service.initialize()
    
    print("=" * 50)
    print(f"[Common] v{__version__} initialized")
    print(f"  Banned users: {ban_service.get_banned_count()}")
    print(f"  Math: {config.math_enabled}")
    print(f"  Random reply: {config.random_enabled}")
    print("=" * 50)
    
    logger.info(f"Common module initialized")
    return True


# 模块导入时自动初始化
try:
    initialize_common()
except Exception as e:
    logger.error(f"Initialization failed: {e}")


# ==================== 导出列表 ====================
__all__ = [
    # 版本
    "__version__",
    
    # 基础
    "ServiceBase",
    "Result",
    "safe_call",
    
    # 游戏服务基类
    "GameServiceBase",
    "GameState",
    
    # 插件注册表
    "PluginRegistry",
    "PluginInfo",
    "get_plugin_registry",
    
    # 配置
    "config",
    "PluginConfig",
    
    # 服务
    "AIService",
    "BanService",
    "ChatService",
    "BotService",
    "ChatMessage",
    "get_ai_service",
    "get_ban_service",
    "get_chat_service",
    "get_bot_service",
    
    # 插件基类
    "PluginBase",
    "CommandPlugin",
    "MessagePlugin",
    
    # 装饰器
    "PermissionChecker",
    "FeatureChecker",
    "CommandGuard",
    "require_permission",
    "require_feature",
    
    # 依赖注入
    "dep_ai_service",
    "dep_ban_service",
    "dep_chat_service",
    "dep_check_permission",
    "dep_check_feature",
    "dep_is_group_admin",
    "dep_is_bot_admin",
    "dep_chat_context",
    "dep_recent_users",
    
    # 工具函数
    "read_prompt",
    "build_at_message",
    "build_reply_message",
    "fetch_html",
    "fetch_html_async",
    "download_image",
    "image_to_message",
    "merge_images",
]
