"""
黑名单服务模块 - 用户封禁管理

服务层 - 实现 BanServiceProtocol 协议

提供用户黑名单的增删查功能，数据持久化到 JSON 文件。
自动兼容旧版 pickle 格式数据并迁移。
在 initialize() 完成后自动注册到 ServiceLocator。

使用方式:
    >>> from plugins.common.services import BanService
    >>> ban = BanService.get_instance()
    >>> ban.initialize()
    >>> 
    >>> # 检查用户
    >>> if ban.is_banned(123456):
    ...     print("用户已被拉黑")
    >>> 
    >>> # 拉黑用户
    >>> result = ban.ban(123456)
    >>> if result.is_success:
    ...     print("拉黑成功")
"""

import json
from pathlib import Path
from typing import List, Set
import logging

from ..base import ServiceBase, Result
from ..config import config
from ..protocols import (
    BanServiceProtocol,
    ServiceLocator,
)


class BanService(ServiceBase, BanServiceProtocol):
    """
    黑名单服务类 - 用户封禁管理
    
    实现 BanServiceProtocol 协议，管理用户黑名单。
    数据持久化存储到 JSON 文件，支持 pickle 格式迁移。
    在 initialize() 完成后自动注册到 ServiceLocator。
    
    Attributes:
        _banned_users: 被禁用户ID集合
        logger: 日志记录器实例
        
    Example:
        >>> ban = BanService.get_instance()
        >>> ban.initialize()
        >>> result = ban.ban(123456)
        >>> if result.is_success and result.value:
        ...     print("新拉黑用户")
    """
    
    def __init__(self) -> None:
        """
        初始化服务
        
        数据延迟加载，实际加载在 initialize() 中完成。
        
        Example:
            >>> ban = BanService.get_instance()
            >>> # _banned_users 此时为空集合
        """
        super().__init__()
        self._banned_users: Set[int] = set()
        self.logger = logging.getLogger("plugins.common.services.ban")
    
    def initialize(self) -> None:
        """
        初始化黑名单数据
        
        从文件加载黑名单，并在完成后注册到 ServiceLocator。
        支持从旧版 pickle 格式自动迁移。
        
        Example:
            >>> ban = BanService.get_instance()
            >>> ban.initialize()
            >>> # 服务已注册到 ServiceLocator
        """
        if self._initialized:
            return
        
        self._banned_users = set(self._load_banned_list())
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(BanServiceProtocol, self)
        self.logger.info(f"Initialized with {len(self._banned_users)} banned users")
    
    def _get_banned_file_path(self) -> Path:
        """
        获取黑名单文件路径
        
        优先返回已存在的文件路径（支持 JSON 和 pickle 格式）。
        如果都不存在，返回 JSON 路径。
        
        Returns:
            Path: 黑名单文件路径
            
        Example:
            >>> path = ban._get_banned_file_path()
            >>> print(path.suffix)  # .json 或 .pkl
        """
        data_dir = Path(config.data_dir)
        
        json_path = data_dir / "banned.json"
        pkl_path = data_dir / "banned.pkl"
        
        if json_path.exists():
            return json_path
        
        if pkl_path.exists():
            return pkl_path
        
        return json_path
    
    def _load_banned_list(self) -> List[int]:
        """
        加载黑名单数据
        
        从文件加载黑名单用户ID列表，支持 JSON 和 pickle 格式。
        如果是 pickle 格式，会自动迁移到 JSON。
        
        Returns:
            List[int]: 用户ID列表
            
        Example:
            >>> users = ban._load_banned_list()
            >>> print(f"已加载 {len(users)} 个用户")
        """
        banned_file = self._get_banned_file_path()
        
        if not banned_file.exists():
            return []
        
        if banned_file.suffix == '.pkl':
            return self._migrate_from_pickle(banned_file)
        
        try:
            with open(banned_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [int(uid) for uid in data] if isinstance(data, list) else []
        except Exception as e:
            self.logger.error(f"Failed to load json: {e}")
            return []
    
    def _migrate_from_pickle(self, pkl_path: Path) -> List[int]:
        """
        从旧版 pickle 迁移数据
        
        读取 pickle 格式数据，保存为 JSON 格式，然后删除原文件。
        
        Args:
            pkl_path: pickle 文件路径
            
        Returns:
            List[int]: 迁移的用户ID列表
            
        Example:
            >>> users = ban._migrate_from_pickle(Path("data/banned.pkl"))
            >>> print(f"迁移了 {len(users)} 个用户")
        """
        try:
            import pickle
            with open(pkl_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, list):
                    self._save_banned_list(data)
                    pkl_path.unlink()
                    self.logger.info(f"Migrated {len(data)} users from pickle to json")
                    return data
        except Exception as e:
            self.logger.error(f"Failed to migrate pickle: {e}")
        return []
    
    def _save_banned_list(self, users: List[int]) -> Result[None]:
        """
        保存黑名单到文件
        
        将用户ID列表保存为 JSON 格式。
        
        Args:
            users: 用户ID列表
            
        Returns:
            Result[None]: 成功时 value 为 None，失败时包含错误信息
            
        Example:
            >>> result = ban._save_banned_list([123, 456])
            >>> if result.is_success:
            ...     print("保存成功")
        """
        banned_file = Path(config.data_dir) / "banned.json"
        try:
            with open(banned_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            return Result.success(None)
        except Exception as e:
            self.logger.error(f"Failed to save: {e}")
            return Result.fail(f"保存失败: {e}")
    
    # ========== BanServiceProtocol 实现 ==========
    
    def is_banned(self, user_id: int) -> bool:
        """
        检查用户是否被拉黑
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            True 如果用户已被拉黑，False 否则
            
        Example:
            >>> if ban.is_banned(123456):
            ...     print("用户已被拉黑")
        """
        self.ensure_initialized()
        return user_id in self._banned_users
    
    def ban(self, user_id: int) -> Result[bool]:
        """
        拉黑用户
        
        将用户添加到黑名单并持久化到文件。
        如果用户已在黑名单中，返回成功但 value 为 False。
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            Result[bool]: 成功时 value 表示是否新拉黑用户
            
        Example:
            >>> result = ban.ban(123456)
            >>> if result.is_success and result.value:
            ...     print("新拉黑用户")
        """
        self.ensure_initialized()
        
        if user_id in self._banned_users:
            return Result.success(False)
        
        self._banned_users.add(user_id)
        save_result = self._save_banned_list(list(self._banned_users))
        
        if save_result.is_success:
            self.logger.info(f"User {user_id} banned")
            return Result.success(True)
        return Result.fail(save_result.error or "保存失败")
    
    def unban(self, user_id: int) -> Result[bool]:
        """
        解封用户
        
        将用户从黑名单移除并持久化到文件。
        如果用户不在黑名单中，返回成功但 value 为 False。
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            Result[bool]: 成功时 value 表示是否成功解封
            
        Example:
            >>> result = ban.unban(123456)
            >>> if result.is_success and result.value:
            ...     print("成功解封")
        """
        self.ensure_initialized()
        
        if user_id not in self._banned_users:
            return Result.success(False)
        
        self._banned_users.discard(user_id)
        save_result = self._save_banned_list(list(self._banned_users))
        
        if save_result.is_success:
            self.logger.info(f"User {user_id} unbanned")
            return Result.success(True)
        return Result.fail(save_result.error or "保存失败")
    
    # ========== 额外方法（不在协议中）==========
    
    def get_banned_count(self) -> int:
        """
        获取黑名单用户数量
        
        Returns:
            黑名单中的用户数量
            
        Example:
            >>> count = ban.get_banned_count()
            >>> print(f"共有 {count} 个被禁用户")
        """
        self.ensure_initialized()
        return len(self._banned_users)
    
    def get_banned_list(self) -> List[int]:
        """
        获取黑名单列表
        
        Returns:
            被禁用户ID列表（副本）
            
        Example:
            >>> users = ban.get_banned_list()
            >>> for uid in users:
            ...     print(f"被禁用户: {uid}")
        """
        self.ensure_initialized()
        return list(self._banned_users)


def get_ban_service() -> BanService:
    """
    获取黑名单服务单例（向后兼容）
    
    Returns:
        BanService 单例实例
        
    Example:
        >>> ban = get_ban_service()
        >>> ban.initialize()
    """
    return BanService.get_instance()
