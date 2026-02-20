"""
游戏服务基类 - 统一的群聊游戏状态管理

提供标准化的群聊游戏状态管理，支持多群同时游戏，
每群独立状态，自动处理游戏生命周期。

使用示例:
    >>> from plugins.common.services.game import GameServiceBase, GameState
    
    >>> class MyGameState(GameState):
    ...     score: int = 0
    ...     level: int = 1
    
    >>> class MyGameService(GameServiceBase[MyGameState]):
    ...     def create_game(self, group_id: int, **kwargs) -> MyGameState:
    ...         return MyGameState(group_id=group_id, score=0, level=1)
    
    >>> service = MyGameService.get_instance()
    >>> result = service.start_game(123456)  # 开始游戏
    >>> game = service.get_game(123456)      # 获取游戏状态
    >>> service.end_game(123456)             # 结束游戏

设计特点:
    1. 泛型支持：支持自定义 GameState 类型
    2. 单例模式：每种类型的服务全局唯一
    3. 类型安全：完整的类型注解
    4. 自动清理：结束游戏时自动清理状态
"""

from abc import abstractmethod
from typing import Dict, Generic, Optional, TypeVar
from dataclasses import dataclass, field

from ..base import Result, ServiceBase


@dataclass
class GameState:
    """
    游戏状态基类
    
    所有游戏状态的父类，包含通用字段。
    子类应继承此类并添加游戏特定字段。
    
    Attributes:
        group_id: 群号
        is_active: 游戏是否进行中
        metadata: 额外元数据（可选）
    
    Example:
        >>> @dataclass
        ... class PokerState(GameState):
        ...     players: List[int] = field(default_factory=list)
        ...     deck: List[str] = field(default_factory=list)
    """
    group_id: int
    is_active: bool = True
    metadata: Dict[str, any] = field(default_factory=dict)


T = TypeVar('T', bound=GameState)


class GameServiceBase(ServiceBase, Generic[T]):
    """
    游戏服务基类
    
    提供标准化的群聊游戏管理功能。
    使用泛型支持自定义状态类型。
    
    特性:
        - 单例模式：每种服务类型全局唯一实例
        - 多群隔离：每群独立游戏状态
        - 类型安全：泛型确保状态类型正确
    
    子类必须实现:
        - create_game(): 创建初始游戏状态
    
    Attributes:
        _games: 群号到游戏状态的映射
        _initialized: 是否已初始化
    
    Example:
        >>> class DiceService(GameServiceBase[DiceState]):
        ...     def create_game(self, group_id: int, **kwargs) -> DiceState:
        ...         return DiceState(group_id=group_id, dice_count=kwargs.get('dice_count', 2))
    """
    
    _instances: Dict[type, 'GameServiceBase'] = {}
    
    def __new__(cls: type) -> 'GameServiceBase':
        """确保每种子类只有一个实例"""
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
            cls._instances[cls]._initialized = False
        return cls._instances[cls]
    
    @classmethod
    def get_instance(cls: type) -> 'GameServiceBase':
        """
        获取服务单例
        
        Returns:
            该服务类型的全局唯一实例
        """
        return cls()
    
    def __init__(self) -> None:
        """初始化服务（只执行一次）"""
        if self._initialized:
            return
        super().__init__()  # 调用 ServiceBase.__init__()，设置 logger
        self._games: Dict[int, T] = {}
        self._initialized = True
    
    @abstractmethod
    def create_game(self, group_id: int, **kwargs) -> T:
        """
        创建游戏状态（子类必须实现）
        
        根据游戏类型创建初始状态对象。
        
        Args:
            group_id: 群号
            **kwargs: 额外参数（如难度、玩家列表等）
            
        Returns:
            初始化的游戏状态对象
            
        Example:
            >>> def create_game(self, group_id: int, **kwargs) -> MyState:
            ...     return MyState(
            ...         group_id=group_id,
            ...         difficulty=kwargs.get('difficulty', 'normal')
            ...     )
        """
        pass
    
    def has_active_game(self, group_id: int) -> bool:
        """
        检查指定群是否有进行中的游戏
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果有进行中的游戏，False 如果没有或已结束
        """
        game = self._games.get(group_id)
        return game is not None and game.is_active
    
    def get_game(self, group_id: int) -> Optional[T]:
        """
        获取指定群的游戏状态
        
        Args:
            group_id: 群号
            
        Returns:
            游戏状态对象，如果不存在返回 None
        """
        return self._games.get(group_id)
    
    def start_game(self, group_id: int, **kwargs) -> Result[T]:
        """
        开始新游戏
        
        如果该群已有进行中的游戏，会结束旧游戏并开始新游戏。
        如需阻止重复开始，请先调用 has_active_game() 检查。
        
        Args:
            group_id: 群号
            **kwargs: 传递给 create_game() 的参数
            
        Returns:
            Result[T]: 成功返回游戏状态，失败返回错误
            
        Example:
            >>> # 先检查
            >>> if service.has_active_game(group_id):
            ...     await reply("已有进行中的游戏")
            ...     return
            >>> 
            >>> # 开始新游戏
            >>> result = service.start_game(group_id, difficulty='hard')
            >>> if result.is_success:
            ...     game = result.value
        """
        try:
            # 如果已有游戏，先结束它
            if group_id in self._games:
                self.end_game(group_id)
            
            # 创建新游戏状态
            game = self.create_game(group_id, **kwargs)
            self._games[group_id] = game
            
            return Result.success(game)
        except Exception as e:
            return Result.fail(f"开始游戏失败: {e}")
    
    def end_game(self, group_id: int) -> bool:
        """
        结束游戏
        
        将游戏标记为结束并从状态中移除。
        
        Args:
            group_id: 群号
            
        Returns:
            True 如果成功结束游戏，False 如果没有进行中的游戏
        """
        game = self._games.get(group_id)
        if game is None:
            return False
        
        game.is_active = False
        del self._games[group_id]
        return True
    
    def get_active_games_count(self) -> int:
        """
        获取进行中的游戏数量
        
        Returns:
            当前进行中的游戏总数
        """
        return sum(1 for game in self._games.values() if game.is_active)
    
    def list_active_games(self) -> Dict[int, T]:
        """
        获取所有进行中的游戏
        
        Returns:
            群号到游戏状态的映射字典（只包含活跃游戏）
        """
        return {
            gid: game for gid, game in self._games.items() 
            if game.is_active
        }
