"""
午时已到（俄罗斯轮盘赌）插件

使用 GameServiceBase 重构版本 - 统一的游戏状态管理
"""
import random
from typing import Optional
from dataclasses import dataclass, field

try:
    from nonebot.adapters.onebot.v11 import GroupMessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class GroupMessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import CommandPlugin, config, BotService, GameServiceBase, GameState


# ========== 数据模型 ==========

@dataclass
class HighNoonState(GameState):
    """
    午时已到游戏状态
    
    Attributes:
        bullet_pos: 子弹位置 (1-6)
        shot_count: 已开枪次数
        players: 参与玩家列表
    """
    bullet_pos: int = 0
    shot_count: int = 0
    players: list = field(default_factory=list)


# ========== 游戏服务 ==========

class HighNoonService(GameServiceBase[HighNoonState]):
    """
    午时已到游戏服务
    
    使用 GameServiceBase 统一管理游戏状态。
    """
    
    # 游戏阶段提示语
    STATEMENTS = [
        "无需退路。( 1 / 6 )",
        "英雄们啊，为这最强大的信念，请站在我们这边。( 2 / 6 )",
        "颤抖吧，在真正的勇敢面前。( 3 / 6 )",
        "哭嚎吧，为你们不堪一击的信念。( 4 / 6 )",
        "现在可没有后悔的余地了。( 5 / 6 )"
    ]
    
    def _log(self, message: str) -> None:
        """调试日志输出"""
        if config.debug_mode or config.debug_highnoon:
            self.logger.info(f"[HighNoon] {message}")
    
    def create_game(self, group_id: int, **kwargs) -> HighNoonState:
        """
        创建新游戏状态
        
        随机生成子弹位置（1-6）。
        """
        bullet_pos = random.randint(1, 6)
        self._log(f"创建新游戏 - 群{group_id}: 子弹位置={bullet_pos}")
        
        return HighNoonState(
            group_id=group_id,
            bullet_pos=bullet_pos,
            shot_count=0,
            players=[]
        )
    
    async def fire(self, group_id: int, user_id: int, username: str) -> Optional[dict]:
        """
        处理开枪
        
        Returns:
            结果字典或 None（如果没有游戏）
        """
        game = self.get_game(group_id)
        if game is None or not game.is_active:
            return None
        
        # 添加玩家到列表
        if user_id not in game.players:
            game.players.append(user_id)
        
        game.shot_count += 1
        
        self._log(
            f"群{group_id} 开枪: shot_count={game.shot_count}, "
            f"bullet_pos={game.bullet_pos}, user={username}"
        )
        
        # 判断是否中弹
        if game.shot_count == game.bullet_pos:
            self._log(f"群{group_id}: 中弹！")
            self.end_game(group_id)
            return {
                "hit": True,
                "message": f"来吧,{username},鲜血会染红这神圣的场所",
                "game_over": True
            }
        else:
            self._log(f"群{group_id}: 安全")
            return {
                "hit": False,
                "message": self.STATEMENTS[game.shot_count - 1],
                "game_over": False
            }


# ========== 插件类 ==========

class HighNoonStartPlugin(CommandPlugin):
    """午时已到 - 开始游戏"""
    
    name = "决斗"
    description = "俄罗斯轮盘赌禁言游戏"
    command = "午时已到"
    feature_name = "highnoon"
    priority = 10
    
    async def handle(self, event: GroupMessageEvent, args: str) -> None:
        """开始午时已到游戏"""
        if not NONEBOT_AVAILABLE:
            return
        
        group_id = event.group_id  # type: ignore
        service = HighNoonService.get_instance()
        
        # 直接开始新游戏（覆盖旧游戏）
        result = service.start_game(group_id)
        
        if result.is_failure:
            await self.reply("开始游戏失败")
            return
        
        # 获取游戏状态用于调试
        game = result.value
        if config.debug_mode or config.debug_highnoon:
            await self.send(
                f"午时已到\n"
                f"（调试：子弹位置={game.bullet_pos}）"
            )
        else:
            await self.send("午时已到")


class FirePlugin(CommandPlugin):
    """午时已到 - 开枪"""
    
    name = "开枪"
    description = "午时已到游戏开枪命令"
    command = "开枪"
    feature_name = "highnoon"
    priority = 5
    block = False
    
    async def handle(self, event: GroupMessageEvent, args: str) -> None:
        """处理开枪命令"""
        if not NONEBOT_AVAILABLE:
            return
        
        group_id = event.group_id  # type: ignore
        user_id = event.user_id  # type: ignore
        username = event.sender.card or event.sender.nickname or f"用户{user_id}"  # type: ignore
        
        service = HighNoonService.get_instance()
        
        # 检查游戏是否进行中
        if not service.has_active_game(group_id):
            return
        
        # 处理开枪
        result = await service.fire(group_id, user_id, username)
        
        if result is None:
            return
        
        bot = BotService.get_instance()
        
        if result["hit"]:
            # 中弹！禁言
            ban_result = await bot.ban_random_duration(
                group_id=group_id,
                user_id=user_id,
                min_minutes=1,
                max_minutes=10
            )
            
            if ban_result.is_success:
                await bot.send_message(event, result["message"])
            else:
                await bot.send_message(
                    event,
                    f"{username},哀悼的钟声为你停下……"
                )
            
            await bot.send_message(event, "钟摆落地,一切归于宁静")
        else:
            # 安全
            await bot.send_message(event, result["message"])


# ========== 实例化 ==========
high_noon_plugin = HighNoonStartPlugin()
fire_plugin = FirePlugin()


# ========== 导出元数据 ==========
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name="午时已到",
        description="俄罗斯轮盘赌禁言游戏",
        usage="/午时已到 开始游戏，/开枪 参与",
        extra={
            "author": high_noon_plugin.author,
            "version": high_noon_plugin.version,
        }
    )
