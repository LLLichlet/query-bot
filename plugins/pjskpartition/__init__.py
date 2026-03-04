"""
PJSK 谱面插件

Project Sekai（世界计划）游戏谱面图片查询。
支持随机谱面、指定编号或歌曲名搜索。

触发方式:
    - /chart - 随机谱面
    - /chart <编号> - 指定编号谱面（如 /chart 001）
    - /chart <歌曲名> - 搜索歌曲谱面（如 /chart Tell Your World）
    - /chart [编号/歌曲名] [难度] - 指定难度（exp/mst/apd）

配置:
    QUERY_PJSKPARTTION_ENABLED=True/False    # 功能开关

数据来源:
    谱面图片从 sdvx.in 获取

使用方式:
    /chart [编号/歌曲名] [难度(exp/mst/apd)]
"""
import random
import asyncio
import json
import os
import re

try:
    from nonebot.adapters.onebot.v11 import MessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import PluginHandler, CommandReceiver
from plugins.common.base import Result

try:
    from plugins.utils import download_image, image_to_message, merge_images, calculate_similarity
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


class PJSKHandler(PluginHandler):
    """
    PJSK 谱面处理器
    
    Attributes:
        name: 插件名称
        description: 功能描述
        command: 命令名称
        aliases: 命令别名集合
        feature_name: 功能开关名
        priority: 命令处理优先级
        ERROR_MESSAGES: 错误消息映射
    """
    
    name = "PJSK谱面"
    description = "pjsk谱面相关功能，支持随机、指定编号、搜索歌曲名"
    command = "chart"
    aliases = {"pjsk随机谱面", "pjsk谱面"}
    feature_name = "pjskpartiton"
    priority = 10
    
    ERROR_MESSAGES = {
        "utils_not_available": "Image processing module not available",
        "invalid_song_id": "Song ID must be between 1 and 639",
        "song_not_found": "Song not found",
        "download_failed": "Network error, please try again later",
        "merge_failed": "Failed to merge images",
    }
    
    def __init__(self):
        super().__init__()
        self._songs_data = None
    
    @property
    def songs_data(self) -> dict:
        """懒加载歌曲数据"""
        if self._songs_data is None:
            self._songs_data = self._load_songs_data()
        return self._songs_data
    
    def _load_songs_data(self) -> dict:
        """加载歌曲数据"""
        json_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "pjsk_songs.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            songs = data.get("songs", [])
            return {
                "songs": songs,
                "id_to_name": {s["id_str"]: s["name"] for s in songs},
            }
        except Exception:
            return {"songs": [], "id_to_name": {}}
    
    def _find_song(self, query: str) -> tuple[str, str] | None:
        """根据歌曲名搜索"""
        query = query.lower()
        best_match = None
        best_score = 0.0
        
        for song in self.songs_data.get("songs", []):
            name = song["name"]
            if query == name.lower():
                return song["id_str"], name
            
            if UTILS_AVAILABLE:
                score = calculate_similarity(query, name.lower())
                if score > best_score:
                    best_score = score
                    best_match = (song["id_str"], name)
        
        if best_match and best_score > 0.4:
            return best_match
        return None
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理谱面命令
        
        Args:
            event: 消息事件对象
            args: 用户输入的参数（编号/歌曲名/难度）
        """
        # 检查环境
        if not UTILS_AVAILABLE:
            await self.reply(self.get_error_message("utils_not_available"))
            return
        
        # 解析参数
        song_id, song_name, difficulty = await self._parse_args(args)
        if song_id is None:
            return
        
        # 发送歌曲名（非随机模式）
        if args and song_name:
            await self.reply(song_name)
        
        # 下载图片
        bg_url = f"https://sdvx.in/prsk/bg/{song_id}bg.png"
        bar_url = f"https://sdvx.in/prsk/bg/{song_id}bar.png"
        data_url = f"https://sdvx.in/prsk/obj/data{song_id}{difficulty}.png"
        
        try:
            bg, bar, data = await asyncio.gather(
                download_image(bg_url),
                download_image(bar_url),
                download_image(data_url),
            )
        except Exception:
            await self.reply(self.get_error_message("download_failed"))
            return
        
        if bg is None or bar is None or data is None:
            await self.reply(self.get_error_message("download_failed"))
            return
        
        # 合并图片
        merged = merge_images(bg, data, bar)
        if merged is None:
            await self.reply(self.get_error_message("merge_failed"))
            return
        
        # 发送图片
        try:
            msg = image_to_message(merged)
            await self.send(msg, finish=True)
        except Exception:
            await self.reply(self.get_error_message("merge_failed"))
    
    async def _parse_args(self, args: str) -> tuple[str | None, str | None, str]:
        """
        解析命令参数
        
        Returns:
            (song_id, song_name, difficulty) 或 (None, None, "")
        """
        if not args:
            # 随机模式
            song_id = f"{random.randint(1, 639):03d}"
            song_name = self.songs_data.get("id_to_name", {}).get(song_id, "Unknown")
            return song_id, song_name, random.choice(["exp", "mst"])
        
        args = args.strip()
        
        # 检查难度参数
        diff_match = re.search(r'\s+(exp|mst|apd)$', args, re.IGNORECASE)
        difficulty = diff_match.group(1).lower() if diff_match else random.choice(["exp", "mst"])
        if diff_match:
            args = args[:diff_match.start()].strip()
        
        # 判断是编号还是歌曲名
        if args.isdigit():
            num = int(args)
            if 1 <= num <= 639:
                song_id = f"{num:03d}"
                song_name = self.songs_data.get("id_to_name", {}).get(song_id)
                return song_id, song_name, difficulty
            else:
                await self.reply(self.get_error_message("invalid_song_id"))
                return None, None, ""
        else:
            # 歌曲名搜索
            result = self._find_song(args)
            if result:
                return result[0], result[1], difficulty
            else:
                await self.reply(self.get_error_message("song_not_found"))
                return None, None, ""


# 创建处理器和接收器
handler = PJSKHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage="/chart [编号/歌曲名] [难度(exp/mst/apd)]",
        extra={"author": "Lichlet", "version": "2.4.0"}
    )
