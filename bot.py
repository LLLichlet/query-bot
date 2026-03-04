"""
Anemone Bot - QQ 群聊机器人主程序

基于 NoneBot2 框架开发的多功能 QQ 群聊机器人。
提供数学知识查询、游戏娱乐和智能对话功能。

快速开始:
    # 安装依赖
    pip install -r requirements.txt
    
    # 配置环境变量 (复制 .env.example 到 .env 并填写)
    cp .env.example .env
    
    # 启动机器人
    python bot.py
    # 或使用 nb-cli
    nb run

功能模块:
    - 数学定义查询: /define [数学名词]
    - 数学谜题: /mathpuzzle (20 Questions 模式)
    - 午时已到: /highnoon (俄罗斯轮盘赌禁言游戏)
    - 随机回复: 自动触发 AI 回复
    - PJSK 谱面: /chart (随机谱面图片)

架构说明:
    采用 7 层严格分层架构:
    1. 插件层 (Plugins) - 功能实现
    2. 处理器层 (Handler) - 业务逻辑
    3. 接收层 (Receiver) - 命令注册
    4. 协议层 (Protocol) - 接口定义
    5. 服务层 (Services) - 协议实现
    6. 基础层 (Base) - 通用基类
    7. 配置层 (Config) - 配置管理

Example:
    >>> # 启动机器人
    >>> import bot
    >>> bot.main()
    
    >>> # 使用 nb-cli 启动
    >>> # nb run
"""

import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from nonebot.log import logger, default_format

__version__ = "2.4.0"

# 初始化NoneBot
nonebot.init()

# 获取驱动器
driver = nonebot.get_driver()
driver.register_adapter(Adapter)


# 启动时初始化服务
@driver.on_startup
async def init_services():
    """初始化所有核心服务"""
    from plugins.common.services import (
        AIService, BanService, ChatService, BotService,
        TokenService, SystemMonitorService
    )
    from plugins.common.buffer import init_buffer
    
    # 初始化并注册所有服务到 ServiceLocator
    AIService.get_instance().initialize()
    BanService.get_instance().initialize()
    ChatService.get_instance().initialize()
    BotService.get_instance().initialize()
    TokenService.get_instance().initialize()
    SystemMonitorService.get_instance().initialize()
    
    # 初始化消息缓冲区（防止高并发丢消息）
    init_buffer()
    
    logger.success("核心服务初始化完成")


# 启动信息
@driver.on_startup
async def startup():
    """机器人启动信息"""
    logger.success(f"机器人启动成功!当前版本{__version__}")


# 加载所有插件（从plugins目录及其子目录）
nonebot.load_plugins("plugins")


# nb-cli 入口点
def main():
    """
    nb-cli 入口函数
    
    用于 nb-cli 启动机器人时的入口点。
    
    Example:
        >>> main()  # 启动机器人
    """
    nonebot.run()


if __name__ == "__main__":
    main()
