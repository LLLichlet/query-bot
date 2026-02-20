"""
系统监控服务

提供 bot 进程资源使用情况查询，包括 CPU、内存、运行时间等。
"""
import os
import time
import platform
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from ..base import ServiceBase


@dataclass
class ProcessStatus:
    """进程状态信息"""
    cpu_percent: float      # 进程 CPU 使用率
    memory_mb: float        # 进程内存使用 (MB)
    memory_percent: float   # 进程内存占用率（占系统总内存）
    threads: int            # 线程数
    uptime_seconds: float   # 运行时间
    platform: str           # 系统平台
    python_version: str     # Python 版本


class SystemMonitorService(ServiceBase):
    """
    系统监控服务
    
    获取当前 bot 进程的资源使用情况。
    
    Example:
        >>> service = SystemMonitorService.get_instance()
        >>> status = service.get_status()
        >>> print(f"CPU: {status.cpu_percent}%")
        >>> print(f"Memory: {status.memory_mb}MB")
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._start_time = time.time()
        self._psutil_available = False
        self._process = None
        
        # 尝试导入 psutil
        try:
            import psutil
            self._psutil = psutil
            self._psutil_available = True
            # 获取当前进程
            self._process = psutil.Process()
        except ImportError:
            self.logger.warning("psutil not installed, system monitoring limited")
    
    def is_available(self) -> bool:
        """检查是否可用（psutil 是否安装）"""
        return self._psutil_available
    
    def get_status(self) -> ProcessStatus:
        """
        获取进程状态
        
        Returns:
            ProcessStatus 包含 CPU、内存、线程数等信息
        """
        if self._psutil_available and self._process:
            return self._get_status_with_psutil()
        else:
            return self._get_status_basic()
    
    def _get_status_with_psutil(self) -> ProcessStatus:
        """使用 psutil 获取进程状态"""
        # 进程 CPU 使用率（需要间隔采样）
        cpu_percent = self._process.cpu_percent(interval=0.1)
        
        # 进程内存信息
        memory_info = self._process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # RSS 实际使用内存
        
        # 进程内存占用率（占系统总内存的百分比）
        memory_percent = self._process.memory_percent()
        
        # 线程数
        threads = self._process.num_threads()
        
        # 运行时间
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
        """基础状态（无 psutil 时）"""
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
        格式化运行时间
        
        Args:
            seconds: 秒数
            
        Returns:
            人类可读的时间字符串，如 "2天3小时15分钟"
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
    
    def get_status_text(self) -> str:
        """
        获取格式化的状态文本
        
        Returns:
            格式化的进程状态字符串
        """
        status = self.get_status()
        
        lines = []
        lines.append(f"进程: query_bot")
        
        # CPU
        if status.cpu_percent >= 0:
            lines.append(f"CPU: {status.cpu_percent}%")
        else:
            lines.append("CPU: N/A (psutil not installed)")
        
        # Memory
        if status.memory_percent >= 0:
            lines.append(f"Memory: {status.memory_mb}MB ({status.memory_percent}%)")
        else:
            lines.append("Memory: N/A")
        
        # Threads
        if status.threads > 0:
            lines.append(f"Threads: {status.threads}")
        
        # Runtime
        uptime_str = self.format_uptime(status.uptime_seconds)
        lines.append(f"Runtime: {uptime_str}")
        
        return "\n".join(lines)


# 便捷获取函数
def get_system_monitor_service() -> SystemMonitorService:
    """获取系统监控服务实例"""
    return SystemMonitorService.get_instance()
