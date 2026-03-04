"""
消息发送缓冲 - 用于防风控

使用方式：
    from plugins.common.buffer import get_buffer
    
    # 排队发送（间隔默认 800ms，可通过配置调整，防风控）
    await get_buffer().send(group_id, message, send_func)
    
    # 立即发送（可能触发风控）
    await matcher.send(message)

Example:
    >>> from plugins.common.buffer import get_buffer
    >>> buffer = get_buffer()
    >>> await buffer.send(123456, "Hello", matcher.send)
"""

import asyncio
import time
from typing import Optional, Any, Callable, Dict


class SendBuffer:
    """
    发送缓冲器 - 控制发送频率，在调用者上下文中执行发送
    
    通过限制同群消息的发送间隔，避免触发 QQ 风控。
    每群独立控制，不同群之间并发发送。
    
    Attributes:
        _interval: 发送间隔（秒）
        _last_time: 每群上次发送时间记录
        _locks: 每群的异步锁
        
    Example:
        >>> buffer = SendBuffer(interval_ms=500)
        >>> await buffer.send(123456, "Hello", matcher.send)
    """
    
    def __init__(self, interval_ms: float = 800.0):
        """
        初始化发送缓冲器
        
        Args:
            interval_ms: 发送间隔（毫秒），默认 800ms
            
        Example:
            >>> buffer = SendBuffer(interval_ms=1000)  # 1秒间隔
        """
        self._interval = interval_ms / 1000.0
        self._last_time: Dict[int, float] = {}
        self._locks: Dict[int, asyncio.Lock] = {}
    
    def _get_lock(self, group_id: int) -> asyncio.Lock:
        """
        获取群的锁（每群独立，不同群并发）
        
        Args:
            group_id: 群号
            
        Returns:
            该群的异步锁
            
        Example:
            >>> lock = buffer._get_lock(123456)
        """
        if group_id not in self._locks:
            self._locks[group_id] = asyncio.Lock()
        return self._locks[group_id]
    
    async def send(self, group_id: int, message: Any, send_func: Callable):
        """
        发送消息（带频率控制）
        
        在调用者上下文中执行，避免 ContextVar 丢失问题。
        同群消息按顺序执行，间隔至少配置的毫秒数。
        
        Args:
            group_id: 群号
            message: 消息内容
            send_func: 发送函数（如 matcher.send）
            
        Returns:
            None
            
        Example:
            >>> await buffer.send(123456, "Hello", matcher.send)
        """
        lock = self._get_lock(group_id)
        
        async with lock:
            # 等待间隔
            now = time.time()
            last = self._last_time.get(group_id, 0)
            wait = self._interval - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            
            # 发送（在调用者上下文中）
            try:
                await send_func(message)
            except Exception as e:
                print(f"[SendBuffer] 发送失败: {e}")
            
            self._last_time[group_id] = time.time()
    
    def qsize(self) -> int:
        """
        获取当前等待中的消息数量（估算值）
        
        Returns:
            正在发送的消息数量（被锁定的群数量）
            
        Example:
            >>> size = buffer.qsize()
            >>> print(f"当前有 {size} 条消息在发送中")
        """
        return sum(1 for lock in self._locks.values() if lock.locked())


_buffer: Optional[SendBuffer] = None


def get_buffer() -> SendBuffer:
    """
    获取全局发送缓冲区
    
    懒加载模式，首次调用时根据配置初始化。
    
    Returns:
        全局 SendBuffer 实例
        
    Example:
        >>> buffer = get_buffer()
        >>> await buffer.send(123456, "Hello", matcher.send)
    """
    global _buffer
    if _buffer is None:
        from plugins.common import config
        _buffer = SendBuffer(interval_ms=config.buffer_interval_ms)
    return _buffer


def init_buffer():
    """
    初始化（在 bot.py 启动时调用）- 新版本无需启动 task
    
    当前版本采用在调用者上下文中执行的方式，
    不再需要启动后台任务，此函数保留用于兼容性。
    
    Returns:
        None
        
    Example:
        >>> init_buffer()  # 兼容性调用，实际无需操作
    """
    pass
