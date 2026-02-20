"""
插件注册表服务

自动收集所有插件的元数据，用于动态生成帮助信息。
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from ..base import ServiceBase


@dataclass
class PluginInfo:
    """插件信息数据类"""
    name: str                           # 插件显示名称
    description: str                    # 功能描述
    command: Optional[str] = None       # 主命令
    aliases: Optional[Set[str]] = None  # 命令别名
    feature_name: Optional[str] = None  # 功能开关名
    usage: str = ""                     # 使用说明
    is_message_plugin: bool = False     # 是否为消息插件（自动触发）
    hidden: bool = False                # 是否在帮助中隐藏


class PluginRegistry(ServiceBase):
    """
    插件注册表服务
    
    自动收集所有插件的元数据，提供统一的插件信息查询接口。
    单例模式，所有插件实例化时自动注册。
    
    Example:
        >>> registry = PluginRegistry.get_instance()
        >>> plugins = registry.get_all_plugins()
        >>> for plugin in plugins:
        ...     print(f"{plugin.name}: {plugin.description}")
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._plugins: Dict[str, PluginInfo] = {}  # feature_name -> PluginInfo
        self._commands: Dict[str, str] = {}         # command -> feature_name
    
    def register(self, info: PluginInfo) -> None:
        """
        注册插件信息
        
        由 PluginBase 在插件实例化时自动调用。
        
        Args:
            info: 插件信息对象
        """
        key = info.feature_name or info.name
        
        # 避免重复注册
        if key in self._plugins:
            self.logger.debug(f"插件已注册，跳过: {key}")
            return
        
        self._plugins[key] = info
        
        # 记录命令映射
        if info.command:
            self._commands[info.command] = key
            if info.aliases:
                for alias in info.aliases:
                    self._commands[alias] = key
        
        self.logger.debug(f"注册插件: {info.name} (key={key})")
    
    def get_plugin(self, key: str) -> Optional[PluginInfo]:
        """
        根据 feature_name 或 name 获取插件信息
        
        Args:
            key: feature_name 或插件名称
            
        Returns:
            插件信息对象，未找到返回 None
        """
        return self._plugins.get(key)
    
    def get_plugin_by_command(self, command: str) -> Optional[PluginInfo]:
        """
        根据命令名获取插件信息
        
        Args:
            command: 命令名（不带/）
            
        Returns:
            插件信息对象，未找到返回 None
        """
        key = self._commands.get(command)
        if key:
            return self._plugins.get(key)
        return None
    
    def get_all_plugins(self, include_hidden: bool = False) -> List[PluginInfo]:
        """
        获取所有已注册插件
        
        Args:
            include_hidden: 是否包含隐藏的插件
            
        Returns:
            插件信息列表
        """
        plugins = list(self._plugins.values())
        if not include_hidden:
            plugins = [p for p in plugins if not p.hidden]
        return plugins
    
    def get_command_plugins(self, include_hidden: bool = False) -> List[PluginInfo]:
        """
        获取所有命令插件（非消息插件）
        
        Args:
            include_hidden: 是否包含隐藏的插件
            
        Returns:
            命令插件信息列表
        """
        plugins = [
            p for p in self._plugins.values()
            if p.command and not p.is_message_plugin
        ]
        if not include_hidden:
            plugins = [p for p in plugins if not p.hidden]
        return plugins
    
    def get_message_plugins(self, include_hidden: bool = False) -> List[PluginInfo]:
        """
        获取所有消息插件（自动触发）
        
        Args:
            include_hidden: 是否包含隐藏的插件
            
        Returns:
            消息插件信息列表
        """
        plugins = [
            p for p in self._plugins.values()
            if p.is_message_plugin
        ]
        if not include_hidden:
            plugins = [p for p in plugins if not p.hidden]
        return plugins
    
    def get_plugin_count(self) -> int:
        """获取已注册插件数量"""
        return len(self._plugins)
    
    def clear(self) -> None:
        """清空注册表（主要用于测试）"""
        self._plugins.clear()
        self._commands.clear()


# 全局注册表实例（用于兼容直接导入）
_plugin_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """获取插件注册表实例"""
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry.get_instance()
    return _plugin_registry
