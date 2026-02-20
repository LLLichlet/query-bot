"""
数学谜题插件 - 20 Questions 模式

AI 在心中选定一个数学概念（定理、公式、人物或对象），
玩家通过最多 20 个是非问题来推理出答案。
"""

# ========== 导入 ==========
import json
import os
import random
from typing import Dict, Optional, List
from dataclasses import dataclass, field

try:
    from nonebot.adapters.onebot.v11 import MessageEvent # type: ignore
    from nonebot.plugin import PluginMetadata # type: ignore
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import CommandPlugin, config, AIService, GameServiceBase, GameState, read_prompt
from plugins.common.base import Result


# ========== 数据模型 ==========

@dataclass
class MathConcept:
    """数学概念数据类"""
    id: str
    answer: str
    aliases: List[str] = field(default_factory=list)
    category: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "MathConcept":
        """从字典创建对象"""
        return cls(
            id=data["id"],
            answer=data["answer"],
            aliases=data.get("aliases", []),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            description=data.get("description", "")
        )


@dataclass
class MathPuzzleState(GameState):
    """数学谜题游戏状态"""
    concept: Optional[MathConcept] = None
    question_count: int = 0
    guess_count: int = 0
    history: List[tuple] = field(default_factory=list)


# ========== 概念库 ==========

class ConceptRepository:
    """数学概念题库"""
    
    # 内置默认概念（作为 fallback）
    DEFAULT_CONCEPTS = [
        {
            "id": "fermat_last_theorem",
            "answer": "费马大定理",
            "aliases": ["费马最后定理"],
            "category": "数论",
            "tags": ["数论", "证明", "358年"],
            "description": "当整数n>2时，方程a^n+b^n=c^n没有正整数解"
        }
    ]
    
    def __init__(self) -> None:
        self._concepts: Dict[str, MathConcept] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """延迟初始化，加载概念数据"""
        if self._initialized:
            return
        
        # 尝试从文件加载
        data_file = os.path.join("prompts", "math_concepts.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get("concepts", []):
                        concept = MathConcept.from_dict(item)
                        self._concepts[concept.id] = concept
                self._log(f"从文件加载了 {len(self._concepts)} 个概念")
            except Exception as e:
                self._log(f"加载文件失败: {e}，使用内置数据")
                self._load_defaults()
        else:
            self._log("概念文件不存在，使用内置数据")
            self._load_defaults()
        
        self._initialized = True
    
    def _load_defaults(self) -> None:
        """加载内置默认概念"""
        for item in self.DEFAULT_CONCEPTS:
            concept = MathConcept.from_dict(item)
            self._concepts[concept.id] = concept
        self._log(f"加载了 {len(self._concepts)} 个内置概念")
    
    def _log(self, message: str) -> None:
        """调试日志"""
        if config.debug_mode or config.debug_math_soup:
            import logging
            logging.getLogger("plugins.math_soup").info(f"[Repository] {message}")
    
    def get_random_concept(self) -> Optional[MathConcept]:
        """随机获取一个数学概念"""
        self.initialize()
        concepts = list(self._concepts.values())
        if not concepts:
            return None
        return random.choice(concepts)
    
    def get_concept_count(self) -> int:
        """获取概念总数"""
        self.initialize()
        return len(self._concepts)


# ========== 游戏服务 ==========

class MathPuzzleService(GameServiceBase[MathPuzzleState]):
    """数学谜题游戏服务"""
    
    def __init__(self) -> None:
        super().__init__()
        self._repository = ConceptRepository()
        self._ai_service = AIService.get_instance()
    
    def _log(self, message: str) -> None:
        """调试日志输出"""
        if config.debug_mode or config.debug_math_soup:
            self.logger.info(f"[MathPuzzle] {message}")
    
    def create_game(self, group_id: int, **kwargs) -> MathPuzzleState:
        """创建新游戏状态"""
        concept = self._repository.get_random_concept()
        if concept is None:
            raise RuntimeError("题库为空，无法开始游戏")
        
        self._log(f"创建新游戏 - 群{group_id}: 答案={concept.answer}")
        
        return MathPuzzleState(
            group_id=group_id,
            concept=concept,
            question_count=0,
            guess_count=0,
            history=[]
        )
    
    async def ask_question(self, group_id: int, question_text: str) -> Result[str]: # type: ignore
        """
        处理玩家提问并返回答复
        
        使用 AI 判定问题，返回"是"/"否"/"不确定"。
        """
        game = self.get_game(group_id)
        if game is None or not game.is_active:
            return Result.fail("没有进行中的游戏")
        

        
        if game.concept is None:
            return Result.fail("游戏状态异常")
        
        # 构建历史记录文本
        history_text = ""
        if game.history:
            history_lines = []
            for q, a in game.history[-5:]:  # 只显示最近5条
                history_lines.append(f"- Q: {q} -> A: {a}")
            history_text = "\n".join(history_lines)
        else:
            history_text = "（无）"
        
        # 读取并填充提示词模板
        system_prompt = read_prompt("math_soup_judge")
        if not system_prompt:
            # 使用默认提示词
            system_prompt = self._get_default_judge_prompt()
        
        # 填充模板（只使用answer、aliases、category，不使用description）
        aliases_text = ", ".join(game.concept.aliases) if game.concept.aliases else "无"
        system_prompt = system_prompt.format(
            answer=game.concept.answer,
            category=game.concept.category,
            aliases=aliases_text,
            history=history_text,
            question=question_text
        )
        
        # 调用 AI 判定
        ai_result = await self._ai_service.chat(
            system_prompt=system_prompt,
            user_input=question_text,
            temperature=0.1,  # 低温度确保确定性回答
            max_tokens=10     # 只需要短回答
        )
        
        if ai_result.is_failure:
            self._log(f"AI 判定失败: {ai_result.error}")
            return Result.fail("AI 服务暂时不可用，请稍后再试")
        
        # 解析 AI 回答
        answer = ai_result.value.strip().lower() # type: ignore
        
        # 标准化回答
        if "是" in answer or "yes" in answer:
            final_answer = "是"
        elif "否" in answer or "no" in answer:
            final_answer = "否"
        else:
            final_answer = "不确定"
        
        self._log(f"提问: {question_text} -> 回答: {final_answer}")
        
        # 更新游戏状态
        if final_answer != "不确定(不消耗次数)":
            game.question_count += 1
        game.history.append((question_text, final_answer))
        
        return Result.success(final_answer)
    
    def _get_default_judge_prompt(self) -> str:
        """获取默认判定提示词（当文件不存在时使用）"""
        return """你是一个数学谜题游戏的裁判。玩家正在猜测一个数学概念。

## 当前概念
- 答案：{answer}
- 别名：{aliases}
- 分类：{category}

## 历史问答
{history}

## 当前问题
{question}

## 规则
- 回答"是"：问题描述与概念一致
- 回答"否"：问题描述与概念不符
- 回答"不确定"：无法明确判断

只回答"是"、"否"或"不确定"，不要解释。"""
    
    def _similarity(self, s1: str, s2: str) -> float:
        """
        计算两个字符串的相似度（0-100%）
        考虑字符匹配率和包含关系
        """
        # 标准化：小写并去除空格和特殊字符
        s1_clean = s1.lower().replace(" ", "").replace("·", "").replace("•", "").replace("-", "").replace("ˈ", "")
        s2_clean = s2.lower().replace(" ", "").replace("·", "").replace("•", "").replace("-", "").replace("ˈ", "")
        
        if not s1_clean or not s2_clean:
            return 0.0
        
        # 完全匹配
        if s1_clean == s2_clean:
            return 100.0
        
        # 包含关系检查：如果一个完全包含另一个
        if s1_clean in s2_clean or s2_clean in s1_clean:
            # 计算包含比例
            shorter = min(len(s1_clean), len(s2_clean))
            longer = max(len(s1_clean), len(s2_clean))
            # 包含关系的基础相似度为70%，加上长度比例调整
            return 70.0 + 25.0 * (shorter / longer)
        
        # 使用编辑距离计算相似度
        import difflib
        matcher = difflib.SequenceMatcher(None, s1_clean, s2_clean)
        ratio = matcher.ratio()
        
        # 对于短字符串（<=4字符），提高相似度阈值，避免误判
        if len(s1_clean) <= 4 or len(s2_clean) <= 4:
            # 如果编辑距离大于1，降低相似度
            if ratio < 0.8:
                return ratio * 80
        
        return ratio * 100
    
    async def make_guess(self, group_id: int, guess_text: str) -> Result[dict]: # type: ignore
        """处理玩家猜测答案"""
        game = self.get_game(group_id)
        if game is None or not game.is_active:
            return Result.fail("没有进行中的游戏")
        
        if game.concept is None:
            return Result.fail("游戏状态异常")
        
        game.guess_count += 1
        
        # 标准化猜测文本
        guess_normalized = guess_text.lower().replace(" ", "").replace("·", "").replace("•", "")
        
        # 检查是否匹配答案
        answer_normalized = game.concept.answer.lower().replace(" ", "")
        is_correct = (guess_normalized == answer_normalized)
        
        # 检查别名
        if not is_correct:
            for alias in game.concept.aliases:
                alias_normalized = alias.lower().replace(" ", "").replace("·", "").replace("•", "")
                if guess_normalized == alias_normalized:
                    is_correct = True
                    break
        
        # 计算与答案及各别名的相似度
        max_similarity = 0.0
        
        # 与答案比较
        sim = self._similarity(guess_text, game.concept.answer)
        max_similarity = max(max_similarity, sim)
        
        # 与别名比较
        for alias in game.concept.aliases:
            sim = self._similarity(guess_text, alias)
            max_similarity = max(max_similarity, sim)
        
        if is_correct:
            self._log(f"群{group_id}: 猜对了！答案是 {game.concept.answer}")
            self.end_game(group_id)
            return Result.success({
                "correct": True,
                "answer": game.concept.answer,
                "description": game.concept.description,
                "category": game.concept.category,
                "similarity": max_similarity
            })
        else:
            self._log(f"群{group_id}: 猜错了，猜测='{guess_text}'，相似度={max_similarity:.1f}%")
            return Result.success({
                "correct": False,
                "answer": None,
                "description": None,
                "similarity": max_similarity
            })
    

    
    def get_game_info(self, group_id: int) -> Optional[dict]:
        """获取游戏信息（用于调试）"""
        game = self.get_game(group_id)
        if game is None:
            return None
        
        return {
            "question_count": game.question_count,
            "guess_count": game.guess_count,

            "concept_answer": game.concept.answer if game.concept else None,
            "history": game.history
        }


# ========== 插件类 ==========

class MathPuzzleStartPlugin(CommandPlugin):
    """数学谜题 - 开始游戏"""
    
    name = "数学谜题"
    description = "通过是非问题猜测数学概念的猜谜游戏"
    command = "数学谜"
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理开始游戏命令"""
        service = MathPuzzleService.get_instance()
        
        # 检查是否已有进行中的游戏
        if service.has_active_game(event.group_id):  # type: ignore
            await self.reply(
                "当前已有进行中的数学谜题！\n"
                "请使用 /答案 结束当前游戏后再开始新游戏。"
            )
            return
        
        # 开始新游戏
        result = service.start_game(event.group_id)  # type: ignore
        
        if result.is_failure:
            await self.reply(f"开始游戏失败: {result.error}")
            return
        
        game = result.value
        msg = f"数学谜题开始"
        
        if config.debug_mode or config.debug_math_soup:
            msg += f" [调试: {game.concept.answer}]" # type: ignore
        
        await self.reply(msg)


class MathPuzzleAskPlugin(CommandPlugin):
    """数学谜题 - 提问"""
    
    name = "数学谜题提问"
    description = "提出是非问题来推理答案"
    command = "问"
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理提问命令"""
        if not args:
            await self.reply("请输入问题内容，例如：/问 这是关于几何的吗")
            return
        
        service = MathPuzzleService.get_instance()
        
        if not service.has_active_game(event.group_id):  # type: ignore
            await self.reply("请先使用 /数学谜 开始游戏")
            return
        
        result = await service.ask_question(event.group_id, args)  # type: ignore
        
        if result.is_failure:
            await self.reply(result.error)  # type: ignore
            return
        
        game = service.get_game(event.group_id)  # type: ignore
        await self.reply(f"{result.value}") # type: ignore


class MathPuzzleGuessPlugin(CommandPlugin):
    """数学谜题 - 猜测答案"""
    
    name = "数学谜题猜测"
    description = "直接猜测答案"
    command = "猜"
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理猜测命令"""
        if not args:
            await self.reply("请输入猜测的答案，例如：/猜 欧拉公式")
            return
        
        service = MathPuzzleService.get_instance()
        
        if not service.has_active_game(event.group_id):  # type: ignore
            await self.reply("请先使用 /数学谜 开始游戏")
            return
        
        result = await service.make_guess(event.group_id, args)  # type: ignore
        
        if result.is_failure:
            await self.reply(result.error)  # type: ignore
            return
        
        data = result.value
        if data["correct"]:
            await self.reply(
                f"正确。答案是 {data['answer']}。\n"
                f"{data['description']}"
            )
        else:
            sim = data.get("similarity", 0)
            if sim > 50:
                await self.reply(f"很接近了--相似度{sim:.0f}%")
            else:
                await self.reply("错误。")


class MathPuzzleRevealPlugin(CommandPlugin):
    """数学谜题 - 揭示答案"""
    
    name = "数学谜题答案"
    description = "揭示答案并结束游戏"
    command = "答案"
    aliases = {"不猜了", "揭晓"}
    feature_name = "math_soup"
    priority = 10
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """处理揭示答案命令"""
        service = MathPuzzleService.get_instance()
        
        game = service.get_game(event.group_id)  # type: ignore
        if game is None or not game.is_active:
            await self.reply("当前没有进行中的游戏")
            return
        
        if game.concept is None:
            await self.reply("游戏状态异常")
            return
        
        concept = game.concept
        service.end_game(event.group_id)  # type: ignore
        
        await self.reply(
            f"答案: {concept.answer}\n"
            f"{concept.description}\n"
            f"提问: {game.question_count}次, 猜测: {game.guess_count}次"
        )


# ========== 实例化 ==========
start_plugin = MathPuzzleStartPlugin()
ask_plugin = MathPuzzleAskPlugin()
guess_plugin = MathPuzzleGuessPlugin()
reveal_plugin = MathPuzzleRevealPlugin()


# ========== 导出元数据 ==========
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name="数学谜题",
        description="通过是非问题猜测数学概念的猜谜游戏",
        usage="/数学谜 - 开始游戏，/问 [问题] - 提问，/猜 [答案] - 猜测",
        extra={
            "author": "Lichlet",
            "version": "2.1.1",
        }
    )
