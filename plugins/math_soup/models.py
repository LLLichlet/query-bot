"""
数学谜题插件 - 数据模型

定义游戏所需的数据结构，包括数学概念和游戏状态。

使用方式:
    >>> from plugins.math_soup.models import MathConcept, MathPuzzleState
    >>> concept = MathConcept(id="test", answer="测试答案")
    >>> state = MathPuzzleState(group_id=123456, concept=concept)
"""

from typing import Optional, List
from dataclasses import dataclass, field

from plugins.common import GameState


@dataclass
class MathConcept:
    """
    数学概念数据类
    
    存储一个数学概念的信息，包括标准答案、别名、分类等。
    
    Attributes:
        id: 概念唯一标识符
        answer: 标准答案（主要名称）
        aliases: 别名列表（可选）
        category: 分类（如"数论"、"代数"）
        tags: 标签列表
        description: 描述信息
        
    Example:
        >>> concept = MathConcept(
        ...     id="fermat_last_theorem",
        ...     answer="费马大定理",
        ...     aliases=["费马最后定理"],
        ...     category="数论"
        ... )
    """
    id: str
    answer: str
    aliases: List[str] = field(default_factory=list)
    category: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "MathConcept":
        """
        从字典创建 MathConcept 对象
        
        Args:
            data: 包含概念数据的字典，应包含 id, answer 等字段
            
        Returns:
            MathConcept 实例
            
        Example:
            >>> data = {"id": "test", "answer": "答案", "aliases": ["别名"]}
            >>> concept = MathConcept.from_dict(data)
        """
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
    """
    数学谜题游戏状态
    
    存储单个群聊中数学谜题游戏的当前状态。
    
    Attributes:
        concept: 当前游戏的概念对象，None 表示游戏未开始
        question_count: 玩家提问次数计数
        guess_count: 玩家猜测次数计数
        
    Example:
        >>> from plugins.math_soup.models import MathConcept
        >>> concept = MathConcept(id="test", answer="答案")
        >>> state = MathPuzzleState(group_id=123456, concept=concept)
        >>> state.question_count += 1
    """
    concept: Optional[MathConcept] = None
    question_count: int = 0
    guess_count: int = 0
