"""
数学谜题插件 - 游戏服务

实现游戏逻辑和 AI 交互，支持玩家提问和猜测答案。

使用方式:
    >>> from plugins.math_soup.service import MathPuzzleService
    >>> service = MathPuzzleService.get_instance()
    >>> result = await service.start_game(123456)
"""

from typing import Optional

from plugins.common import (
    GameServiceBase,
    ServiceLocator,
    AIServiceProtocol,
    read_prompt,
)
from plugins.common.base import Result
from plugins.utils import calculate_similarity, normalize_text

from .models import MathConcept, MathPuzzleState
from .repository import ConceptRepository


class MathPuzzleService(GameServiceBase[MathPuzzleState]):
    """
    数学谜题游戏服务
    
    实现 20 Questions 风格的数学概念猜测游戏逻辑，
    包括开始游戏、提问、猜测、结束游戏等功能。
    
    Attributes:
        _repository: 概念题库仓库，用于获取随机概念
        
    Example:
        >>> service = MathPuzzleService.get_instance()
        >>> result = service.create_game(123456)
        >>> if result:
        ...     print(f"游戏开始，概念: {result.concept.answer}")
    """
    
    def __init__(self) -> None:
        """
        初始化游戏服务
        
        创建题库仓库实例，实际游戏状态管理由基类处理。
        
        Example:
            >>> service = MathPuzzleService.get_instance()
            >>> service._repository is not None
            True
        """
        super().__init__()
        self._repository = ConceptRepository()
    
    def _get_ai_service(self) -> Optional[AIServiceProtocol]:
        """
        获取 AI 服务
        
        通过 ServiceLocator 获取已注册的 AI 服务实例。
        
        Returns:
            AIServiceProtocol 实例，如果未注册则返回 None
            
        Example:
            >>> service = MathPuzzleService.get_instance()
            >>> ai = service._get_ai_service()
            >>> if ai and ai.is_available:
            ...     print("AI 服务可用")
        """
        return ServiceLocator.get(AIServiceProtocol)
    
    def create_game(self, group_id: int, **kwargs) -> MathPuzzleState:
        """
        创建新游戏状态
        
        从题库随机选择一个概念，创建该群聊的游戏状态。
        
        Args:
            group_id: 群聊 ID
            **kwargs: 额外参数（保留给基类使用）
            
        Returns:
            新创建的 MathPuzzleState 实例
            
        Raises:
            RuntimeError: 题库为空时抛出
            
        Example:
            >>> service = MathPuzzleService.get_instance()
            >>> state = service.create_game(123456)
            >>> state.group_id
            123456
        """
        concept = self._repository.get_random_concept()
        if concept is None:
            raise RuntimeError("题库为空，无法开始游戏")
        
        return MathPuzzleState(
            group_id=group_id,
            concept=concept,
            question_count=0,
            guess_count=0
        )
    
    async def ask_question(self, group_id: int, question_text: str) -> Result[str]:
        """
        处理玩家提问并返回答复
        
        使用 AI 判断玩家问题与答案概念的关系，返回"是"、"否"或"不确定"。
        
        Args:
            group_id: 群聊 ID
            question_text: 玩家的问题文本
            
        Returns:
            Result[str]: 成功时返回"是"/"否"/"不确定"，失败时返回错误信息
            
        Example:
            >>> result = await service.ask_question(123456, "这是一个数论概念吗？")
            >>> if result.is_success:
            ...     print(result.value)  # "是" 或 "否" 或 "不确定"
        """
        game = self.get_game(group_id)
        if game is None or not game.is_active:
            return Result.fail("没有进行中的游戏")
        
        if game.concept is None:
            return Result.fail("游戏状态异常")
        
        # 读取并填充提示词模板
        system_prompt = read_prompt("math_soup_judge")
        if not system_prompt:
            system_prompt = self._get_default_judge_prompt()
        
        aliases_text = ", ".join(game.concept.aliases) if game.concept.aliases else "无"
        system_prompt = system_prompt.format(
            answer=game.concept.answer,
            category=game.concept.category,
            aliases=aliases_text,
            question=question_text
        )
        
        # 通过协议层获取 AI 服务
        ai = self._get_ai_service()
        if ai is None:
            return Result.fail("AI 服务不可用")
        
        # 调用 AI 判定
        ai_result = await ai.chat(
            system_prompt=system_prompt,
            user_input=question_text,
            temperature=0.1,
            max_tokens=10
        )
        
        if ai_result.is_failure:
            return Result.fail("AI 服务暂时不可用，请稍后再试")
        
        # 解析 AI 回答
        answer = ai_result.value.strip().lower()
        
        if "是" in answer or "yes" in answer:
            final_answer = "是"
        elif "否" in answer or "no" in answer:
            final_answer = "否"
        else:
            final_answer = "不确定"
        
        # 更新游戏状态（"不确定"不消耗次数）
        if final_answer != "不确定":
            game.question_count += 1
        
        return Result.success(final_answer)
    
    def _get_default_judge_prompt(self) -> str:
        """
        获取默认判定提示词
        
        当外部提示词文件不可用时，返回内置的 AI 判定提示词模板。
        
        Returns:
            默认的提示词模板字符串，包含 {answer}, {category}, {aliases}, {question} 占位符
            
        Example:
            >>> service = MathPuzzleService.get_instance()
            >>> prompt = service._get_default_judge_prompt()
            >>> "{answer}" in prompt
            True
        """
        return """你是一个数学谜题游戏的裁判。玩家正在猜测一个数学概念。

## 当前概念
- 答案：{answer}
- 别名：{aliases}
- 分类：{category}

## 当前问题
{question}

## 规则
- 回答"是"：问题描述与概念一致
- 回答"否"：问题描述与概念不符
- 回答"不确定"：无法明确判断

只回答"是"、"否"或"不确定"，不要解释。"""
    
    async def make_guess(self, group_id: int, guess_text: str) -> Result[dict]:
        """
        处理玩家猜测答案
        
        检查玩家猜测是否与正确答案匹配，支持别名匹配和相似度计算。
        
        Args:
            group_id: 群聊 ID
            guess_text: 玩家的猜测文本
            
        Returns:
            Result[dict]: 包含猜测结果的字典
                - correct: 是否猜对 (bool)
                - answer: 正确答案（猜对时）
                - description: 概念描述（猜对时）
                - category: 概念分类（猜对时）
                - similarity: 相似度分数 (float)
                
        Example:
            >>> result = await service.make_guess(123456, "费马大定理")
            >>> if result.is_success and result.value["correct"]:
            ...     print("猜对了！")
        """
        game = self.get_game(group_id)
        if game is None or not game.is_active:
            return Result.fail("没有进行中的游戏")
        
        if game.concept is None:
            return Result.fail("游戏状态异常")
        
        game.guess_count += 1
        
        # 标准化猜测文本和答案
        guess_normalized = normalize_text(guess_text)
        answer_normalized = normalize_text(game.concept.answer)
        is_correct = (guess_normalized == answer_normalized)
        
        # 检查别名匹配
        if not is_correct:
            for alias in game.concept.aliases:
                alias_normalized = normalize_text(alias)
                if guess_normalized == alias_normalized:
                    is_correct = True
                    break
        
        # 计算最大相似度（用于提示）
        max_similarity = calculate_similarity(guess_text, game.concept.answer)
        
        for alias in game.concept.aliases:
            sim = calculate_similarity(guess_text, alias)
            max_similarity = max(max_similarity, sim)
        
        if is_correct:
            await self.end_game(group_id)
            return Result.success({
                "correct": True,
                "answer": game.concept.answer,
                "description": game.concept.description,
                "category": game.concept.category,
                "similarity": max_similarity
            })
        else:
            return Result.success({
                "correct": False,
                "answer": None,
                "description": None,
                "similarity": max_similarity
            })
    
    def get_game_info(self, group_id: int) -> Optional[dict]:
        """
        获取游戏信息
        
        返回指定群聊当前游戏的状态信息。
        
        Args:
            group_id: 群聊 ID
            
        Returns:
            游戏信息字典，无游戏时返回 None
            - question_count: 提问次数
            - guess_count: 猜测次数
            - concept_answer: 正确答案（调试用）
            
        Example:
            >>> info = service.get_game_info(123456)
            >>> if info:
            ...     print(f"已提问 {info['question_count']} 次")
        """
        game = self.get_game(group_id)
        if game is None:
            return None
        
        return {
            "question_count": game.question_count,
            "guess_count": game.guess_count,
            "concept_answer": game.concept.answer if game.concept else None
        }
