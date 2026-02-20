"""
帮助插件

自动从 PluginRegistry 读取插件元数据，动态生成帮助信息。
"""
try:
    from nonebot.plugin import PluginMetadata  # type: ignore
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import CommandPlugin, config, PluginRegistry


class HelpPlugin(CommandPlugin):
    """帮助插件"""
    
    name = "帮助"
    description = "查看插件使用帮助"
    command = "帮助"
    priority = 10
    feature_name = None  # 帮助功能始终可用
    
    async def handle(self, event, args: str) -> None:
        """处理帮助命令"""
        # 获取插件注册表
        registry = PluginRegistry.get_instance()
        
        # 获取所有命令插件（排除隐藏的）
        plugins = registry.get_command_plugins(include_hidden=False)
        
        if not plugins:
            await self.finish("当前没有可用的功能")
            return
        
        # 过滤出启用的插件
        enabled_plugins = []
        for plugin in plugins:
            # 跳过帮助插件本身
            if plugin.command == "帮助":
                continue
            
            # 检查功能开关
            if plugin.feature_name:
                is_enabled = getattr(config, f"{plugin.feature_name}_enabled", True)
                if not is_enabled:
                    continue
            
            enabled_plugins.append(plugin)
        
        # 生成帮助文本
        lines = ["功能列表:"]
        
        for i, plugin in enumerate(enabled_plugins, 1):
            # 构建命令文本
            cmd_text = f"/{plugin.command}"
            if plugin.aliases:
                aliases_text = ", ".join(f"/{a}" for a in sorted(plugin.aliases))
                cmd_text = f"{cmd_text} ({aliases_text})"
            
            # 添加到帮助列表
            lines.append(f"{i}. {plugin.name}: {cmd_text}")
            lines.append(f"   {plugin.description}")
        
        # 添加消息插件
        message_plugins = registry.get_message_plugins(include_hidden=False)
        for plugin in message_plugins:
            if plugin.feature_name:
                is_enabled = getattr(config, f"{plugin.feature_name}_enabled", True)
                if not is_enabled:
                    continue
            
            lines.append(f"{len(enabled_plugins) + 1}. {plugin.name}: 自动触发")
            lines.append(f"   {plugin.description}")
            break  # 目前只有一个消息插件
        
        if len(lines) == 1:
            lines.append("当前所有功能已关闭，请联系管理员")
        
        await self.finish("\n".join(lines))


# 实例化插件
plugin = HelpPlugin()

# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=plugin.name,
        description=plugin.description,
        usage="/帮助",
        extra={
            "author": plugin.author,
            "version": plugin.version,
        }
    )
