"""
数学定义查询插件

使用基类开发的示例插件，演示如何快速开发命令插件。

功能:
    查询数学名词的定义和解释，使用香蕉空间风格。
    支持中英法德俄日多语言回复。

使用:
    /定义 [数学名词]
    
    例如:
    /定义 群论
    /定义 黎曼猜想
    /定义 拓扑空间

配置:
    QUERY_MATH_ENABLED=True/False      # 功能开关
    QUERY_MATH_TEMPERATURE=0.1         # AI 温度
    QUERY_MATH_MAX_TOKENS=8192         # 最大 token
    QUERY_MATH_TOP_P=0.1               # Top-p 参数

开发说明:
    这是使用 CommandPlugin 基类的标准示例。
    只需设置元数据和实现 handle 方法即可。
"""

# ========== 导入 ==========
# 尝试导入 NoneBot 组件，失败时使用占位符（便于类型检查）
try:
    from nonebot.adapters.onebot.v11 import MessageEvent  # type: ignore
    from nonebot.plugin import PluginMetadata # type: ignore
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    # 占位符，避免导入错误
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

# 从公共模块导入基类和工具
from plugins.common import CommandPlugin, config, read_prompt, AIService


# ========== 插件类 ==========
class MathDefinitionPlugin(CommandPlugin):
    """
    数学定义查询插件
    
    继承 CommandPlugin，自动获得：
    - 命令注册（/定义）
    - 权限检查（黑名单）
    - 功能开关检查（config.math_enabled）
    - 参数提取和处理
    - 错误处理
    
    需要配置的类属性:
        name: 插件显示名称
        description: 功能描述
        command: 命令名（不带/）
        feature_name: 功能开关名（对应 config.math_enabled）
        priority: 优先级（越小越优先）
    
    需要实现的方法:
        handle(self, event, args): 处理命令的核心逻辑
    """
    
    # 插件元数据（必须）
    name = "数学定义查询"                    # 显示名称
    description = "查询数学名词的定义和解释"  # 功能描述
    command = "定义"                        # 命令名（用户输入 /定义）
    feature_name = "math"                   # 功能开关（对应 config.math_enabled）
    priority = 10                           # 优先级（10 是默认值）
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理数学定义查询
        
        这是核心处理方法，基类会在以下情况调用：
        1. 用户权限检查通过（未被拉黑）
        2. 功能开关已开启（config.math_enabled=True）
        3. 命令匹配成功
        
        Args:
            event: 消息事件对象，包含 user_id, group_id 等信息
            args: 命令参数（已去除首尾空格，不包含命令本身）
                  例如用户输入 "/定义 群论"，args = "群论"
        
        可用的便捷方法:
            - self.reply(text, at_user=True): 回复用户（自动@）
            - self.send(message): 发送消息（不结束）
            - self.finish(message): 发送并结束会话
            - self.is_group_chat: 是否为群聊
        
        可用的服务:
            - self._ai_service: AI 服务
            - self._ban_service: 黑名单服务
            - self._chat_service: 聊天服务
        """
        
        # ========== 参数检查 ==========
        # 检查用户是否输入了参数
        if not args:
            # 使用 self.reply 自动@用户
            await self.reply("请输入要查询的数学名词")
            return
        
        # ========== 读取提示词 ==========
        # 从 prompts/math_def.txt 读取系统提示
        system_prompt = read_prompt("math_def")
        if not system_prompt:
            # 提示词文件不存在时的降级处理
            await self.reply("数学定义系统提示文件不存在，请联系管理员")
            return
        
        # ========== 调用 AI ==========
        # 获取 AI 服务实例
        ai = AIService.get_instance()
        
        # 检查 AI 服务是否可用（API 密钥已配置）
        if not ai.is_available:
            await self.reply("AI 服务未配置，无法查询")
            return
        
        # 调用 AI，使用配置中的参数
        result = await ai.chat(
            system_prompt=system_prompt,           # 系统提示（定义风格）
            user_input=args,                       # 用户输入（数学名词）
            temperature=config.math_temperature,   # 温度（配置中读取）
            max_tokens=config.math_max_tokens,     # 最大 token
            top_p=config.math_top_p                # Top-p
        )
        
        # ========== 处理结果 ==========
        # AI 服务返回 Result 类型，需要检查是否成功
        if result.is_success:
            # 成功：result.value 包含 AI 回复
            await self.reply(result.value)  # type: ignore
        else:
            # 失败：result.error 包含错误信息
            await self.reply(f"查询失败: {result.error}")
        
        # 注意：不需要手动调用 finish，方法结束后基类会自动处理


# ========== 实例化 ==========
# 这行代码必须存在！实例化即注册插件
# 基类的 __init__ 会自动完成：
# - 创建命令处理器
# - 注册到 NoneBot
# - 设置元数据
plugin = MathDefinitionPlugin()


# ========== 导出元数据 ==========
# 供 NoneBot 读取的元数据（显示在帮助、插件列表等）
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=plugin.name,           # 插件名称
        description=plugin.description,  # 描述
        usage="/定义 [数学名词]",   # 使用说明
        extra={
            "author": plugin.author,    # 作者
            "version": plugin.version,  # 版本
        }
    )
