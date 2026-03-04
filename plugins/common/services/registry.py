"""
插件注册表服务模块 - 插件元数据管理

服务层 - 收集和管理所有插件的元数据

自动收集所有插件的元数据，用于动态生成帮助信息。
提供统一的插件信息查询接口，支持按命令、功能名等查询。

使用方式:
    >>> from plugins.common.services import PluginRegistry, PluginInfo
    >>> registry = PluginRegistry.get_instance()
    >>> 
    >>> # 获取所有插件
    >>> plugins = registry.get_all_plugins()
    >>> 
    >>> # 按命令查找
    >>> plugin = registry.get_plugin_by_command("define")

Example:
    >>> registry = PluginRegistry.get_instance()
    >>> info = registry.get_plugin("math")
    >>> if info:
    ...     print(f"{info.name}: {info.description}")
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from ..base import ServiceBase


@dataclass
class PluginInfo:
    """
    插件信息数据类
    
    存储单个插件的完整元数据信息。
    
    Attributes:
        name: 插件显示名称
        description: 功能描述
        command: 主命令（不含/），消息插件为 None
        aliases: 命令别名集合
        feature_name: 功能开关名（用于配置控制）
        usage: 使用说明字符串
        is_message_plugin: 是否为消息插件（自动触发）
        hidden: 是否在帮助中隐藏
        
    Example:
        >>> info = PluginInfo(
        ...     name="数学定义",
        ...     description="查询数学名词定义",
        ...     command="define",
        ...     aliases={"定义"},
        ...     feature_name="math"
        ... )
    """
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
    插件注册表服务类
    
    自动收集所有插件的元数据，提供统一的插件信息查询接口。
    单例模式，所有插件实例化时自动注册。
    
    Attributes:
        _plugins: feature_name/name 到 PluginInfo 的映射字典
        _commands: 命令名到 feature_name/name 的映射字典
        
    Example:
        >>> registry = PluginRegistry.get_instance()
        >>> 
        >>> # 注册插件（通常自动完成）
        >>> info = PluginInfo(name="测试", description="测试插件", command="test")
        >>> registry.register(info)
        >>> 
        >>> # 查询插件
        >>> plugin = registry.get_plugin("test")
        >>> print(plugin.name)
    """
    
    def __init__(self) -> None:
        """
        初始化插件注册表
        
        创建空的存储结构。
        
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> len(registry._plugins)
            0
        """
        super().__init__()
        self._plugins: Dict[str, PluginInfo] = {}  # feature_name -> PluginInfo
        self._commands: Dict[str, str] = {}         # command -> feature_name
    
    def register(self, info: PluginInfo) -> None:
        """
        注册插件信息
        
        由 CommandReceiver/MessageReceiver 在插件实例化时自动调用。
        如果已存在相同 key 的插件，会跳过注册。
        
        Args:
            info: 插件信息对象
            
        Returns:
            None
            
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> info = PluginInfo(name="测试", description="测试插件", command="test")
            >>> registry.register(info)
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
            
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> plugin = registry.get_plugin("math")
            >>> if plugin:
            ...     print(plugin.description)
        """
        return self._plugins.get(key)
    
    def get_plugin_by_command(self, command: str) -> Optional[PluginInfo]:
        """
        根据命令名获取插件信息
        
        Args:
            command: 命令名（不带/）
            
        Returns:
            插件信息对象，未找到返回 None
            
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> plugin = registry.get_plugin_by_command("define")
            >>> if plugin:
            ...     print(plugin.name)
        """
        key = self._commands.get(command)
        if key:
            return self._plugins.get(key)
        return None
    
    def get_all_plugins(self, include_hidden: bool = False) -> List[PluginInfo]:
        """
        获取所有已注册插件
        
        Args:
            include_hidden: 是否包含隐藏的插件，默认 False
            
        Returns:
            插件信息列表
            
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> plugins = registry.get_all_plugins()
            >>> print(f"共有 {len(plugins)} 个插件")
        """
        plugins = list(self._plugins.values())
        if not include_hidden:
            plugins = [p for p in plugins if not p.hidden]
        return plugins
    
    def get_command_plugins(self, include_hidden: bool = False) -> List[PluginInfo]:
        """
        获取所有命令插件（非消息插件）
        
        Args:
            include_hidden: 是否包含隐藏的插件，默认 False
            
        Returns:
            命令插件信息列表
            
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> commands = registry.get_command_plugins()
            >>> for p in commands:
            ...     print(f"/{p.command}: {p.description}")
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
            include_hidden: 是否包含隐藏的插件，默认 False
            
        Returns:
            消息插件信息列表
            
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> msg_plugins = registry.get_message_plugins()
            >>> for p in msg_plugins:
            ...     print(f"{p.name}: 自动触发")
        """
        plugins = [
            p for p in self._plugins.values()
            if p.is_message_plugin
        ]
        if not include_hidden:
            plugins = [p for p in plugins if not p.hidden]
        return plugins
    
    def get_plugin_count(self) -> int:
        """
        获取已注册插件数量
        
        Returns:
            插件总数
            
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> count = registry.get_plugin_count()
            >>> print(f"已注册 {count} 个插件")
        """
        return len(self._plugins)
    
    def clear(self) -> None:
        """
        清空注册表（主要用于测试）
        
        删除所有已注册的插件信息。
        
        Example:
            >>> registry = PluginRegistry.get_instance()
            >>> registry.clear()
            >>> registry.get_plugin_count()
            0
        """
        self._plugins.clear()
        self._commands.clear()


# 全局注册表实例（用于兼容直接导入）
_plugin_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    """
    获取插件注册表实例（向后兼容）
    
    Returns:
        PluginRegistry 单例实例
        
    Example:
        >>> registry = get_plugin_registry()
        >>> plugins = registry.get_all_plugins()
    """
    global _plugin_registry
    if _plugin_registry is None:
        _plugin_registry = PluginRegistry.get_instance()
    return _plugin_registry
