"""
帮助插件

自动从 PluginRegistry 读取插件元数据，动态生成帮助信息。
支持查看功能列表和指定指令的详细用法。

触发方式:
    - /help - 显示所有可用功能列表
    - /help [指令名] - 查看指定指令的详细用法

配置:
    无特殊配置项

使用方式:
    /help [指令名]
"""

try:
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    PluginHandler,
    CommandReceiver,
    config,
    PluginRegistry,
)
from plugins.common.base import Result


class HelpHandler(PluginHandler):
    """
    帮助信息处理器
    
    Attributes:
        name: 插件名称
        description: 功能描述
        command: 命令名称
        aliases: 命令别名集合
        priority: 命令处理优先级
        feature_name: 功能开关名（None表示不受开关控制）
        ERROR_MESSAGES: 错误消息映射
    """
    
    name = "帮助"
    description = "查看插件使用帮助"
    command = "help"
    aliases = {"帮助"}
    priority = 10
    feature_name = None
    
    ERROR_MESSAGES = {
        "command_not_found": "Command not found",
        "feature_disabled": "Feature is currently disabled",
        "no_features_available": "All features are currently disabled. Please contact the administrator.",
    }
    
    async def handle(self, event, args: str) -> Result[None]:
        """
        处理帮助命令
        
        Args:
            event: 消息事件对象
            args: 用户输入的参数，为空显示列表，否则显示详情
            
        Returns:
            Result[None]: 操作结果
        """
        registry = PluginRegistry.get_instance()
        
        # 如果有参数，显示特定指令的详细信息
        if args:
            result = await self._show_plugin_detail(registry, args.strip())
            if result.is_failure:
                await self.reply(f"{self.get_error_message(result.error)}: /{args.strip()}")
            return result
        
        # 否则显示功能列表
        result = await self._show_plugin_list(registry)
        if result.is_failure:
            await self.send(self.get_error_message(result.error), finish=True)
        return result
    
    async def _show_plugin_detail(self, registry: PluginRegistry, query: str) -> Result[None]:
        """
        显示特定插件的详细信息
        
        Args:
            registry: 插件注册表实例
            query: 用户查询的指令名
            
        Returns:
            Result[None]: 操作结果
        """
        # 去掉可能的前导 /
        query = query.lstrip("/")
        
        # 特殊处理 help 自身
        if query in ("help", "帮助"):
            lines = ["/help 帮助"]
            lines.append("Aliases: /帮助")
            lines.append("Description: 查看插件使用帮助")
            lines.append("Usage: /help [command] - Show feature list or specific command details")
            await self.send("\n".join(lines), finish=True)
            return Result.ok(None)
        
        # 通过命令名查找插件
        plugin = registry.get_plugin_by_command(query)
        
        if plugin is None or plugin.hidden:
            return Result.err("command_not_found")
        
        # 检查功能开关
        if plugin.feature_name and not config.is_enabled(plugin.feature_name):
            return Result.err("feature_disabled")
        
        lines = [f"/{plugin.command} {plugin.name}"]
        
        if plugin.aliases:
            aliases_text = ", ".join(f"/{a}" for a in sorted(plugin.aliases))
            lines.append(f"Aliases: {aliases_text}")
        
        lines.append(f"Description: {plugin.description}")
        
        if plugin.usage:
            lines.append(f"Usage: {plugin.usage}")
        
        await self.send("\n".join(lines), finish=True)
        return Result.ok(None)
    
    async def _show_plugin_list(self, registry: PluginRegistry) -> Result[None]:
        """
        显示所有可用功能列表
        
        Args:
            registry: 插件注册表实例
            
        Returns:
            Result[None]: 操作结果
        """
        plugins = registry.get_command_plugins(include_hidden=False)
        
        if not plugins:
            await self.send("Welcome to Anemone bot!\n\nNo features available", finish=True)
            return Result.err("no_features_available")
        
        enabled_plugins = []
        for plugin in plugins:
            if plugin.command == "help":
                continue
            
            # 检查功能开关
            if plugin.feature_name and not config.is_enabled(plugin.feature_name):
                continue
            
            enabled_plugins.append(plugin)
        
        lines = ["Welcome to Anemone bot!"]
        
        for plugin in enabled_plugins:
            lines.append(f"/{plugin.command} {plugin.name}")
        
        message_plugins = registry.get_message_plugins(include_hidden=False)
        for plugin in message_plugins:
            if plugin.feature_name and not config.is_enabled(plugin.feature_name):
                continue
            
            lines.append(f"(Auto) {plugin.name}")
        
        if len(enabled_plugins) == 0:
            lines.append("All features are currently disabled, please contact the administrator")
        
        lines.append("\nUse /help [command] to view detailed usage")
        
        await self.send("\n".join(lines), finish=True)
        return Result.ok(None)


# 创建处理器和接收器
handler = HelpHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage=f"/{handler.command}",
        extra={"author": "Lichlet", "version": "2.4.0"}
    )
