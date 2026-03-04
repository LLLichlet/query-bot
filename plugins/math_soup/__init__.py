"""
数学谜题插件 - 20 Questions 模式

AI 在心中选定一个数学概念（定理、公式、人物或对象），
玩家通过最多 20 个是非问题来推理出答案。
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
    config,
)
from plugins.common.base import Result

from .service import MathPuzzleService


class MathPuzzleBaseHandler(PluginHandler):
    """数学谜题处理器基类"""
    
    ERROR_MESSAGES = {
        "game_in_progress": "A game is already in progress! Use /reveal to end it before starting a new one.",
        "no_active_game": "No active game. Start one with /mathpuzzle first.",
        "empty_question": "Please enter a question, e.g., /ask Is this about geometry?",
        "empty_guess": "Please enter your guess, e.g., /guess Euler's formula",
        "ask_failed": "Failed to process your question. Please try again later.",
        "guess_failed": "Failed to process your guess. Please try again later.",
        "start_game_failed": "Failed to start game. Please try again later.",
        "game_state_error": "Game state error.",
    }
    
    def _validate_input(self, args: str, error_type: str) -> Result[str]:
        """验证输入不为空"""
        trimmed = args.strip() if args else ""
        if not trimmed:
            return self.err(error_type)
        return self.ok(trimmed)
    
    def _check_game_not_exists(self, group_id: int) -> Result[None]:
        """检查没有进行中的游戏"""
        service = MathPuzzleService.get_instance()
        if service.has_active_game(group_id):
            return self.err("game_in_progress")
        return self.ok(None)
    
    def _check_game_exists(self, group_id: int) -> Result[None]:
        """检查有进行中的游戏"""
        service = MathPuzzleService.get_instance()
        if not service.has_active_game(group_id):
            return self.err("no_active_game")
        return self.ok(None)


class MathPuzzleStartHandler(MathPuzzleBaseHandler):
    """数学谜题 - 开始游戏"""
    
    name = "数学谜题"
    description = "通过是非问题猜测数学概念的猜谜游戏"
    command = "mathpuzzle"
    aliases = {"数学谜"}
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> Result[None]:
        """处理开始游戏命令"""
        # 检查没有现有游戏
        check_result = self._check_game_not_exists(event.group_id)
        if check_result.is_failure:
            await self.reply(self.get_error_message(check_result.error))
            return check_result
        
        # 开始新游戏
        service = MathPuzzleService.get_instance()
        result = await service.start_game(event.group_id)
        
        if result.is_failure:
            await self.reply(self.get_error_message("start_game_failed"))
            return self.err("start_game_failed")
        
        game = result.value
        msg = "Math puzzle started!"
        
        # 调试模式：显示答案
        if config.debug_mode or config.debug_math_soup:
            msg += f" [Debug: {game.concept.answer}]"
        
        await self.reply(msg)
        return self.ok(None)


class MathPuzzleAskHandler(MathPuzzleBaseHandler):
    """数学谜题 - 提问"""
    
    name = "数学谜题提问"
    description = "提出是非问题来推理答案"
    command = "ask"
    aliases = {"问"}
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> Result[None]:
        """处理提问命令"""
        # 验证输入
        validation = self._validate_input(args, "empty_question")
        if validation.is_failure:
            await self.reply(self.get_error_message(validation.error))
            return validation
        
        question = validation.value
        
        # 检查游戏存在
        check_result = self._check_game_exists(event.group_id)
        if check_result.is_failure:
            await self.reply(self.get_error_message(check_result.error))
            return check_result
        
        # 处理问题
        service = MathPuzzleService.get_instance()
        result = await service.ask_question(event.group_id, question)
        
        if result.is_failure:
            await self.reply(self.get_error_message("ask_failed"))
            return self.err("ask_failed")
        
        await self.reply(f"{result.value}")
        return self.ok(None)


class MathPuzzleGuessHandler(MathPuzzleBaseHandler):
    """数学谜题 - 猜测"""
    
    name = "数学谜题猜测"
    description = "直接猜测答案"
    command = "guess"
    aliases = {"猜"}
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> Result[None]:
        """处理猜测命令"""
        # 验证输入
        validation = self._validate_input(args, "empty_guess")
        if validation.is_failure:
            await self.reply(self.get_error_message(validation.error))
            return validation
        
        guess = validation.value
        
        # 检查游戏存在
        check_result = self._check_game_exists(event.group_id)
        if check_result.is_failure:
            await self.reply(self.get_error_message(check_result.error))
            return check_result
        
        # 处理猜测
        service = MathPuzzleService.get_instance()
        result = await service.make_guess(event.group_id, guess)
        
        if result.is_failure:
            await self.reply(self.get_error_message("guess_failed"))
            return self.err("guess_failed")
        
        data = result.value
        if data["correct"]:
            await self.reply(
                f"Correct! The answer is {data['answer']}.\n"
                f"{data['description']}"
            )
        else:
            sim = data.get("similarity", 0)
            if sim > 50:
                await self.reply(f"Close! Similarity: {sim:.0f}%")
            else:
                await self.reply("Wrong.")
        
        return self.ok(None)


class MathPuzzleRevealHandler(MathPuzzleBaseHandler):
    """数学谜题 - 揭示答案"""
    
    name = "数学谜题答案"
    description = "揭示答案并结束游戏"
    command = "reveal"
    aliases = {"答案", "不猜了", "揭晓"}
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> Result[None]:
        """处理揭示答案命令"""
        service = MathPuzzleService.get_instance()
        
        # 获取游戏并验证状态
        game = service.get_game(event.group_id)
        if game is None or not game.is_active:
            await self.reply(self.get_error_message("no_active_game"))
            return self.err("no_active_game")
        
        if game.concept is None:
            await self.reply(self.get_error_message("game_state_error"))
            return self.err("game_state_error")
        
        concept = game.concept
        await service.end_game(event.group_id)
        
        await self.reply(
            f"Answer: {concept.answer}\n"
            f"{concept.description}\n"
            f"Questions: {game.question_count}, Guesses: {game.guess_count}"
        )
        
        return self.ok(None)


# 创建处理器和接收器
start_handler = MathPuzzleStartHandler()
ask_handler = MathPuzzleAskHandler()
guess_handler = MathPuzzleGuessHandler()
reveal_handler = MathPuzzleRevealHandler()

start_receiver = CommandReceiver(start_handler)
ask_receiver = CommandReceiver(ask_handler)
guess_receiver = CommandReceiver(guess_handler)
reveal_receiver = CommandReceiver(reveal_handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name="数学谜题",
        description="通过是非问题猜测数学概念的猜谜游戏",
        usage="/mathpuzzle (数学谜) - 开始游戏，/ask (问) [问题] - 提问，/guess (猜) [答案] - 猜测",
        extra={"author": "Lichlet", "version": "2.4.0"}
    )
