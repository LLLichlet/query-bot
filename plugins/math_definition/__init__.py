"""
数学定义查询插件

使用新架构（PluginHandler + CommandReceiver）开发。

功能:
    查询数学名词的定义和解释，使用香蕉空间风格。
    支持中英法德俄日多语言回复。

使用:
    /define [数学名词]
    
    例如:
    /define 群论
    /define 黎曼猜想
    /define 拓扑空间

配置:
    QUERY_MATH_ENABLED=True/False      # 功能开关
    QUERY_MATH_TEMPERATURE=0.1         # AI 温度
    QUERY_MATH_MAX_TOKENS=8192         # 最大 token
    QUERY_MATH_TOP_P=0.1               # Top-p 参数
"""

try:
    from nonebot.adapters.onebot.v11 import MessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import (
    PluginHandler,
    CommandReceiver,
    ServiceLocator,
    AIServiceProtocol,
    config,
    read_prompt,
)
from plugins.common.base import Result


class MathDefinitionHandler(PluginHandler):
    """
    数学定义查询处理器
    
    Attributes:
        name: 插件名称
        description: 功能描述
        command: 命令名称
        aliases: 命令别名集合
        feature_name: 功能开关名
        priority: 命令处理优先级
        ERROR_MESSAGES: 错误消息映射
    """
    
    name = "数学定义查询"
    description = "查询数学名词的定义和解释"
    command = "define"
    aliases = {"定义"}
    feature_name = "math"
    priority = 10
    
    ERROR_MESSAGES = {
        "empty_input": "Please enter a mathematical term to query",
        "prompt_not_found": "System prompt file not found, please contact admin",
        "ai_not_initialized": "AI service not initialized",
        "ai_not_configured": "AI service not configured, unable to query",
    }
    
    def _load_prompt(self) -> Result[str]:
        """加载系统提示词"""
        prompt = read_prompt("math_def")
        return self.check(prompt is not None, "prompt_not_found", prompt)
    
    def _get_ai_service(self) -> Result[AIServiceProtocol]:
        """获取 AI 服务"""
        ai = ServiceLocator.get(AIServiceProtocol)
        if ai is None:
            return self.err("ai_not_initialized")
        if not ai.is_available:
            return self.err("ai_not_configured")
        return self.ok(ai)
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理数学定义查询
        
        Args:
            event: 消息事件对象
            args: 命令参数（已去除首尾空格）
        """
        # 验证输入
        if not args:
            await self.reply(self.get_error_message("empty_input"))
            return
        
        # 加载提示词
        prompt_result = self._load_prompt()
        if prompt_result.is_failure:
            await self.reply(self.get_error_message(prompt_result.error))
            return
        
        # 获取 AI 服务
        ai_result = self._get_ai_service()
        if ai_result.is_failure:
            await self.reply(self.get_error_message(ai_result.error))
            return
        
        # 调用 AI
        result = await ai_result.value.chat(
            system_prompt=prompt_result.value,
            user_input=args,
            temperature=config.math_temperature,
            max_tokens=config.math_max_tokens,
            top_p=config.math_top_p
        )
        
        # 处理结果
        if result.is_success:
            await self.reply(result.value)
        else:
            await self.reply(f"Query failed: {result.error}")


# 创建处理器和接收器
handler = MathDefinitionHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage=f"/{handler.command} ({'/'.join(handler.aliases)}) [数学名词]",
        extra={"author": "Lichlet", "version": "2.4.0"}
    )
