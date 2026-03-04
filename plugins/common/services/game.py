"""
游戏服务基类 - 统一的群聊游戏状态管理

服务层 - 为各游戏插件提供基础支持

提供标准化的群聊游戏状态管理，支持多群同时游戏，
每群独立状态，自动处理游戏生命周期。

使用方式:
    >>> from plugins.common.services.game import GameServiceBase, GameState
    >>> from dataclasses import dataclass
    >>> 
    >>> @dataclass
    ... class MyGameState(GameState):
    ...     score: int = 0
    ...     level: int = 1
    >>> 
    >>> class MyGameService(GameServiceBase[MyGameState]):
    ...     def create_game(self, group_id: int, **kwargs) -> MyGameState:
    ...         return MyGameState(
    ...             group_id=group_id,
    ...             score=kwargs.get('score', 0),
    ...             level=kwargs.get('level', 1)
    ...         )
    >>> 
    >>> service = MyGameService.get_instance()
    >>> result = await service.start_game(123456, score=100)
    >>> if result.is_success:
    ...     game = result.value
"""

import asyncio
from abc import abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar
from dataclasses import dataclass, field

from ..base import Result, ServiceBase


@dataclass
class GameState:
    """
    游戏状态基类
    
    所有游戏状态的父类，包含通用字段。
    子类应该继承此类并添加自定义字段。
    
    Attributes:
        group_id: 群号
        is_active: 游戏是否进行中
        metadata: 额外元数据字典（可选）
        
    Example:
        >>> @dataclass
        ... class MyState(GameState):
        ...     score: int = 0
        >>> state = MyState(group_id=123456, score=100)
        >>> print(state.is_active)  # True
    """
    group_id: int
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T', bound=GameState)


class GameServiceBase(ServiceBase, Generic[T]):
    """
    游戏服务基类 - 标准化群聊游戏管理
    
    提供标准化的群聊游戏管理功能，支持多群并发游戏。
    使用 asyncio.Lock 确保并发安全。
    子类必须实现 create_game() 方法。
    
    设计特点:
        1. 泛型支持：支持自定义 GameState 类型
        2. 单例模式：每种服务类型全局唯一
        3. 类型安全：完整的类型注解
        4. 并发安全：使用 asyncio.Lock 保护状态
        5. 自动清理：结束游戏时自动清理状态
    
    Attributes:
        _instances: 子类实例字典（用于单例模式）
        _games: 群号到游戏状态的映射
        _lock: 并发锁
        
    Example:
        >>> class MyService(GameServiceBase[MyState]):
        ...     def create_game(self, group_id, **kwargs):
        ...         return MyState(group_id=group_id)
        >>> service = MyService.get_instance()
        >>> result = await service.start_game(123456)
    """
    
    _instances: Dict[type, 'GameServiceBase'] = {}
    
    def __new__(cls: type) -> 'GameServiceBase':
        """
        确保每种子类只有一个实例
        
        Returns:
            单例实例
            
        Example:
            >>> s1 = MyService()
            >>> s2 = MyService()
            >>> s1 is s2  # True
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
            cls._instances[cls]._initialized = False
        return cls._instances[cls]
    
    @classmethod
    def get_instance(cls: type) -> 'GameServiceBase':
        """
        获取服务单例
        
        Returns:
            该服务类的单例实例
            
        Example:
            >>> service = MyService.get_instance()
        """
        return cls()
    
    def __init__(self) -> None:
        """
        初始化服务（只执行一次）
        
        创建存储结构和并发锁，单例模式下仅首次有效。
        
        Example:
            >>> service = MyService.get_instance()
            >>> # _games 和 _lock 已初始化
        """
        if self._initialized:
            return
        super().__init__()
        self._games: Dict[int, T] = {}
        self._lock = asyncio.Lock()  # 并发锁
        self._initialized = True
    
    @abstractmethod
    def create_game(self, group_id: int, **kwargs) -> T:
        """
        创建游戏状态（子类必须实现）
        
        根据群号和额外参数创建初始游戏状态对象。
        
        Args:
            group_id: 群号
            **kwargs: 额外参数，可用于传递游戏配置
            
        Returns:
            初始化的游戏状态对象
            
        Example:
            >>> class MyService(GameServiceBase[MyState]):
            ...     def create_game(self, group_id, **kwargs):
            ...         return MyState(
            ...             group_id=group_id,
            ...             score=kwargs.get('score', 0)
            ...         )
        """
        pass
    
    def has_active_game(self, group_id: int) -> bool:
        """
        检查指定群是否有进行中的游戏
        
        注意：此方法不加锁，仅用于快速查询。
        如需精确判断，请使用 get_game()。
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果有进行中的游戏
            
        Example:
            >>> if service.has_active_game(123456):
            ...     print("该群有进行中的游戏")
        """
        game = self._games.get(group_id)
        return game is not None and game.is_active
    
    def get_game(self, group_id: int) -> Optional[T]:
        """
        获取指定群的游戏状态
        
        注意：此方法不加锁，返回当前状态的快照。
        如需修改状态，请使用 start_game() / end_game()。
        
        Args:
            group_id: 群号
            
        Returns:
            游戏状态对象，如果不存在返回 None
            
        Example:
            >>> game = service.get_game(123456)
            >>> if game:
            ...     print(f"游戏进行中: {game.is_active}")
        """
        return self._games.get(group_id)
    
    async def start_game(self, group_id: int, **kwargs) -> Result[T]:
        """
        开始新游戏（线程安全）
        
        如果该群已有进行中的游戏，会结束旧游戏并开始新游戏。
        
        Args:
            group_id: 群号
            **kwargs: 传递给 create_game() 的参数
            
        Returns:
            Result[T]: 成功返回游戏状态，失败返回错误
            
        Example:
            >>> result = await service.start_game(123456, level=2)
            >>> if result.is_success:
            ...     game = result.value
            ...     print(f"游戏开始: {game}")
        """
        async with self._lock:
            try:
                # 如果已有游戏，先结束它
                if group_id in self._games:
                    await self._end_game_locked(group_id)
                
                # 创建新游戏状态
                game = self.create_game(group_id, **kwargs)
                self._games[group_id] = game
                
                return Result.success(game)
            except Exception as e:
                return Result.fail(f"开始游戏失败: {e}")
    
    async def end_game(self, group_id: int) -> bool:
        """
        结束游戏（线程安全）
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果成功结束游戏，False 如果没有进行中的游戏
            
        Example:
            >>> if await service.end_game(123456):
            ...     print("游戏已结束")
            ... else:
            ...     print("没有进行中的游戏")
        """
        async with self._lock:
            return await self._end_game_locked(group_id)
    
    async def _end_game_locked(self, group_id: int) -> bool:
        """
        结束游戏（内部方法，需在持有锁时调用）
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果成功结束游戏
            
        Example:
            >>> # 通常在 start_game 内部调用
            >>> await self._end_game_locked(123456)
        """
        game = self._games.get(group_id)
        if game is None:
            return False
        
        game.is_active = False
        del self._games[group_id]
        return True
    
    def get_active_games_count(self) -> int:
        """
        获取当前活跃游戏数量
        
        Returns:
            活跃游戏数量
            
        Example:
            >>> count = service.get_active_games_count()
            >>> print(f"当前有 {count} 个游戏进行中")
        """
        return len(self._games)
    
    def list_active_games(self) -> Dict[int, T]:
        """
        获取所有活跃游戏的快照
        
        Returns:
            群号到游戏状态的映射字典（副本）
            
        Example:
            >>> games = service.list_active_games()
            >>> for gid, game in games.items():
            ...     print(f"群 {gid}: {game}")
        """
        return self._games.copy()
