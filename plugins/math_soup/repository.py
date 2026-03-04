"""
数学谜题插件 - 概念题库

管理数学概念的加载和查询，支持从 JSON 文件加载或加载内置默认概念。

使用方式:
    >>> from plugins.math_soup.repository import ConceptRepository
    >>> repo = ConceptRepository()
    >>> repo.initialize()
    >>> concept = repo.get_random_concept()
"""

import json
import os
import random
from typing import Dict, Optional

from .models import MathConcept


class ConceptRepository:
    """
    数学概念题库
    
    负责从文件系统加载数学概念数据，并提供查询接口。
    支持延迟初始化和自动回退到内置默认概念。
    
    Attributes:
        DEFAULT_CONCEPTS: 内置默认概念列表，当外部文件不可用时使用
        
    Example:
        >>> repo = ConceptRepository()
        >>> repo.initialize()
        >>> count = repo.get_concept_count()
        >>> concept = repo.get_random_concept()
    """
    
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
        """
        初始化题库仓库
        
        创建空的存储结构，实际数据加载在 initialize() 中延迟执行。
        
        Example:
            >>> repo = ConceptRepository()
            >>> repo._initialized
            False
        """
        self._concepts: Dict[str, MathConcept] = {}
        self._initialized = False
    
    def initialize(self) -> None:
        """
        延迟初始化，加载概念数据
        
        尝试从 prompts/math_concepts.json 加载概念数据，
        如果文件不存在或加载失败，则使用内置默认概念。
        
        Example:
            >>> repo = ConceptRepository()
            >>> repo.initialize()
            >>> repo._initialized
            True
        """
        if self._initialized:
            return
        
        data_file = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "math_concepts.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get("concepts", []):
                        concept = MathConcept.from_dict(item)
                        self._concepts[concept.id] = concept
            except Exception:
                self._load_defaults()
        else:
            self._load_defaults()
        
        self._initialized = True
    
    def _load_defaults(self) -> None:
        """
        加载内置默认概念
        
        将 DEFAULT_CONCEPTS 列表中的概念加载到内存中。
        
        Example:
            >>> repo = ConceptRepository()
            >>> repo._load_defaults()
            >>> len(repo._concepts) > 0
            True
        """
        for item in self.DEFAULT_CONCEPTS:
            concept = MathConcept.from_dict(item)
            self._concepts[concept.id] = concept
    
    def get_random_concept(self) -> Optional[MathConcept]:
        """
        随机获取一个数学概念
        
        从题库中随机选择一个概念用于游戏。
        
        Returns:
            MathConcept 对象，题库为空时返回 None
            
        Example:
            >>> repo = ConceptRepository()
            >>> repo.initialize()
            >>> concept = repo.get_random_concept()
            >>> if concept:
            ...     print(concept.answer)
        """
        self.initialize()
        concepts = list(self._concepts.values())
        if not concepts:
            return None
        return random.choice(concepts)
    
    def get_concept_count(self) -> int:
        """
        获取概念总数
        
        返回当前题库中概念的总数量。
        
        Returns:
            概念总数
            
        Example:
            >>> repo = ConceptRepository()
            >>> repo.initialize()
            >>> count = repo.get_concept_count()
            >>> count >= 0
            True
        """
        self.initialize()
        return len(self._concepts)
