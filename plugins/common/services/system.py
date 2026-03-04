"""
系统监控服务模块 - 进程资源监控

服务层 - 实现 SystemMonitorProtocol 协议

提供 bot 进程资源使用情况查询，包括 CPU、内存、运行时间等。
支持 psutil 库（可选），未安装时提供基础信息。

在 initialize() 完成后自动注册到 ServiceLocator。

使用方式:
    >>> from plugins.common.services import SystemMonitorService
    >>> service = SystemMonitorService.get_instance()
    >>> service.initialize()
    >>> 
    >>> # 获取状态文本
    >>> status = service.get_status_text()
    >>> print(status)

Example:
    >>> service = SystemMonitorService.get_instance()
    >>> if service.is_available():
    ...     status = service.get_status()
    ...     print(f"CPU: {status.cpu_percent}%")
"""

import os
import time
import platform
from typing import Optional
from dataclasses import dataclass
import logging

from ..base import ServiceBase
from ..protocols import (
    SystemMonitorProtocol,
    ServiceLocator,
)


@dataclass
class ProcessStatus:
    """
    进程状态信息数据类
    
    存储进程的各项资源使用指标。
    
    Attributes:
        cpu_percent: CPU 使用率（%），-1 表示不可用
        memory_mb: 内存使用（MB）
        memory_percent: 内存使用率（%），-1 表示不可用
        threads: 线程数，0 表示不可用
        uptime_seconds: 运行时间（秒）
        platform: 操作系统平台信息
        python_version: Python 版本
        
    Example:
        >>> status = ProcessStatus(
        ...     cpu_percent=5.2,
        ...     memory_mb=128.5,
        ...     memory_percent=2.1,
        ...     threads=8,
        ...     uptime_seconds=3600,
        ...     platform="Windows-10",
        ...     python_version="3.11.0"
        ... )
    """
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    threads: int
    uptime_seconds: float
    platform: str
    python_version: str


class SystemMonitorService(ServiceBase, SystemMonitorProtocol):
    """
    系统监控服务类
    
    实现 SystemMonitorProtocol 协议，提供进程资源监控功能。
    优先使用 psutil 库获取详细信息，未安装时提供基础信息。
    在 initialize() 完成后自动注册到 ServiceLocator。
    
    Attributes:
        _start_time: 服务启动时间戳
        _psutil_available: 是否可用 psutil
        _process: psutil Process 对象（如果可用）
        
    Example:
        >>> service = SystemMonitorService.get_instance()
        >>> service.initialize()
        >>> if service.is_available():
        ...     print(service.get_status_text())
    """
    
    def __init__(self) -> None:
        """
        初始化系统监控服务
        
        记录启动时间，尝试导入 psutil。
        
        Example:
            >>> service = SystemMonitorService.get_instance()
            >>> service._start_time > 0
            True
        """
        super().__init__()
        self._start_time = time.time()
        self._psutil_available = False
        self._process = None
        self.logger = logging.getLogger("plugins.common.services.system")
        
        # 尝试导入 psutil
        try:
            import psutil
            self._psutil = psutil
            self._psutil_available = True
            self._process = psutil.Process()
        except ImportError:
            self.logger.warning("psutil not installed, system monitoring limited")
    
    def initialize(self) -> None:
        """
        初始化服务
        
        注册服务到 ServiceLocator，标记为已初始化。
        
        Example:
            >>> service = SystemMonitorService.get_instance()
            >>> service.initialize()
            >>> # 服务已注册到 ServiceLocator
        """
        if self._initialized:
            return
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(SystemMonitorProtocol, self)
        self.logger.info("System Monitor Service initialized")
    
    def is_available(self) -> bool:
        """
        检查监控功能是否可用（psutil 是否安装）
        
        Returns:
            True 如果 psutil 已安装，False 否则
            
        Example:
            >>> service = SystemMonitorService.get_instance()
            >>> if service.is_available():
            ...     print("完整监控功能可用")
            ... else:
            ...     print("仅基础信息可用")
        """
        return self._psutil_available
    
    def get_status(self) -> ProcessStatus:
        """
        获取进程状态
        
        返回包含 CPU、内存、运行时间等信息的状态对象。
        如果 psutil 可用，返回详细信息；否则返回基础信息。
        
        Returns:
            ProcessStatus 对象
            
        Example:
            >>> service = SystemMonitorService.get_instance()
            >>> status = service.get_status()
            >>> print(f"运行时间: {status.uptime_seconds}秒")
        """
        if self._psutil_available and self._process:
            return self._get_status_with_psutil()
        else:
            return self._get_status_basic()
    
    def _get_status_with_psutil(self) -> ProcessStatus:
        """
        使用 psutil 获取详细进程状态
        
        Returns:
            包含详细信息的 ProcessStatus 对象
            
        Example:
            >>> status = service._get_status_with_psutil()
            >>> print(f"CPU: {status.cpu_percent}%")
        """
        cpu_percent = self._process.cpu_percent(interval=0.1)
        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        memory_percent = self._process.memory_percent()
        threads = self._process.num_threads()
        uptime_seconds = time.time() - self._start_time
        
        return ProcessStatus(
            cpu_percent=round(cpu_percent, 1),
            memory_mb=round(memory_mb, 1),
            memory_percent=round(memory_percent, 1),
            threads=threads,
            uptime_seconds=uptime_seconds,
            platform=platform.platform(),
            python_version=platform.python_version()
        )
    
    def _get_status_basic(self) -> ProcessStatus:
        """
        获取基础进程状态（无 psutil 时）
        
        仅包含运行时间、平台信息等基础数据。
        
        Returns:
            基础 ProcessStatus 对象（CPU、内存为 -1）
            
        Example:
            >>> status = service._get_status_basic()
            >>> print(f"Python版本: {status.python_version}")
        """
        uptime_seconds = time.time() - self._start_time
        
        return ProcessStatus(
            cpu_percent=-1,
            memory_mb=0,
            memory_percent=-1,
            threads=0,
            uptime_seconds=uptime_seconds,
            platform=platform.platform(),
            python_version=platform.python_version()
        )
    
    def format_uptime(self, seconds: float) -> str:
        """
        格式化运行时间为人类可读字符串
        
        将秒数转换为 "X天Y小时Z分钟" 格式。
        
        Args:
            seconds: 运行时间（秒）
            
        Returns:
            格式化后的时间字符串
            
        Example:
            >>> service = SystemMonitorService.get_instance()
            >>> service.format_uptime(3661)  # "1小时1分钟"
            >>> service.format_uptime(90061)  # "1天1小时1分钟"
        """
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0 or not parts:
            parts.append(f"{minutes}分钟")
        
        return "".join(parts)
    
    # ========== SystemMonitorProtocol 实现 ==========
    
    def get_status_text(self) -> str:
        """
        获取格式化的状态文本
        
        返回适合直接显示的格式化字符串，包含所有监控指标。
        
        Returns:
            格式化的状态文本
            
        Example:
            >>> service = SystemMonitorService.get_instance()
            >>> text = service.get_status_text()
            >>> print(text)
            进程: query_bot
            CPU: 5.2%
            Memory: 128.5MB (2.1%)
            Runtime: 1小时30分钟
        """
        status = self.get_status()
        
        lines = []
        lines.append(f"进程: query_bot")
        
        if status.cpu_percent >= 0:
            lines.append(f"CPU: {status.cpu_percent}%")
        else:
            lines.append("CPU: N/A (psutil not installed)")
        
        if status.memory_percent >= 0:
            lines.append(f"Memory: {status.memory_mb}MB ({status.memory_percent}%)")
        else:
            lines.append("Memory: N/A")
        
        if status.threads > 0:
            lines.append(f"Threads: {status.threads}")
        
        uptime_str = self.format_uptime(status.uptime_seconds)
        lines.append(f"Runtime: {uptime_str}")
        
        return "\n".join(lines)


def get_system_monitor_service() -> SystemMonitorService:
    """
    获取系统监控服务实例（向后兼容）
    
    Returns:
        SystemMonitorService 单例实例
        
    Example:
        >>> service = get_system_monitor_service()
        >>> service.initialize()
    """
    return SystemMonitorService.get_instance()
