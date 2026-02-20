import nonebot
from nonebot.adapters.onebot.v11 import Adapter
from nonebot.log import logger, default_format

__version__ = "2.2.1"

# 初始化NoneBot
nonebot.init()

# 获取驱动器
driver = nonebot.get_driver()
driver.register_adapter(Adapter)

# 加载所有插件（从plugins目录及其子目录）
nonebot.load_plugins("plugins")

# 启动信息
@driver.on_startup
async def startup():
    logger.success(f"机器人启动成功!当前版本{__version__}")

# nb-cli 入口点
def main():
    """nb-cli 入口"""
    nonebot.run()

if __name__ == "__main__":
    main()