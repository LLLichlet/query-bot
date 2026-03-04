"""
复读插件

自动复读群聊消息，支持随机概率触发和倒序复读。

触发方式:
    - 概率触发：消息有 1% 概率被复读
    - 倒序复读：复读时有 20% 概率倒序显示消息

配置:
    QUERY_ECHO_ENABLED=True/False         # 功能开关
    QUERY_ECHO_PROBABILITY=0.01           # 复读概率 (0-1)
    QUERY_ECHO_REVERSE_PROBABILITY=0.2    # 倒序复读概率 (0-1)

使用方式:
    无需手动触发，自动监听群聊消息
"""
import random

try:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class GroupMessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    MessageHandler,
    MessageReceiver,
    config,
)


class EchoHandler(MessageHandler):
    """
    复读消息处理器
    
    监听所有群聊消息，按配置概率自动复读。
    
    Attributes:
        name: 插件名称
        description: 功能描述
        feature_name: 功能开关名
        message_priority: 消息处理优先级
        message_block: 是否阻止后续处理
        
    Example:
        >>> handler = EchoHandler()
        >>> await handler.handle_message(event)  # 可能触发复读
    """
    
    name = "复读"
    description = "随机复读群聊消息，有概率倒着复读"
    feature_name = "echo"
    message_priority = 2  # 优先级比随机回复低
    message_block = False
    
    def _should_echo(self, event: GroupMessageEvent) -> tuple[bool, bool]:
        """
        判断是否满足复读条件
        
        根据配置的概率决定是否复读，以及在复读时是否倒序。
        
        Args:
            event: 群聊消息事件对象，包含消息内容、发送者等信息
            
        Returns:
            tuple[bool, bool]: (是否复读, 是否倒序)
            
        Example:
            >>> should_echo, is_reverse = handler._should_echo(event)
            >>> if should_echo:
            ...     print(f"复读消息，倒序={is_reverse}")
        """
        if not NONEBOT_AVAILABLE:
            return False, False
            
        if event.user_id == event.self_id:
            return False, False
        
        message = event.get_plaintext().strip()
        
        # 过滤命令消息
        if message.startswith('/'):
            return False, False
        
        # 过滤太短的消息
        if len(message) < 2:
            return False, False
        
        # 获取配置
        echo_prob = config.echo_probability
        reverse_prob = config.echo_reverse_probability
        
        # 判断是否复读
        if random.random() >= echo_prob:
            return False, False
        
        # 判断是否倒序（在复读的基础上）
        is_reverse = random.random() < reverse_prob
        
        return True, is_reverse
    
    async def handle_message(self, event: GroupMessageEvent) -> None:
        """
        处理群聊消息
        
        检查消息是否触发复读条件，如触发则发送复读消息。
        
        Args:
            event: 消息事件对象，包含消息内容、发送者等信息
            
        Returns:
            None
            
        Example:
            >>> await handler.handle_message(event)
            # 有概率输出: 原消息内容 或 容内息消原
        """
        if not NONEBOT_AVAILABLE:
            return
        
        should_echo, is_reverse = self._should_echo(event)
        
        if not should_echo:
            return
        
        # 获取消息内容
        message = event.get_plaintext().strip()
        
        # 处理消息
        if is_reverse:
            # 倒序复读
            reply = message[::-1]
        else:
            # 正序复读
            reply = message
        
        # 发送回复
        await self.send(reply)


# 创建处理器和接收器
handler = EchoHandler()
receiver = MessageReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage="无命令，自动触发",
        extra={"author": "Lichlet", "version": "2.4.0"}
    )
