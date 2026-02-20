"""
黑名单服务模块 - 用户封禁管理

提供用户拉黑/解封功能，数据持久化为 JSON 格式，自动兼容旧版 pickle。
所有修改操作返回 Result[bool]，便于确认操作结果。

快速开始:
    >>> from plugins.common import BanService
    
    >>> ban = BanService.get_instance()
    
    >>> # 检查用户
    >>> if ban.is_banned(123456789):
    ...     print("用户已被拉黑")
    
    >>> # 拉黑用户
    >>> result = ban.ban(123456789)
    >>> if result.is_success and result.value:
    ...     print("拉黑成功")
    
    >>> # 解封用户
    >>> result = ban.unban(123456789)
    >>> if result.is_success:
    ...     print("解封成功" if result.value else "用户不在黑名单")

数据存储:
    - 新版: data/banned.json (JSON 格式，可人工编辑)
    - 旧版: data/banned.pkl (自动迁移到 JSON 后删除)
"""

import json
import os
from pathlib import Path
from typing import List, Set
import logging

from ..base import ServiceBase, Result
from ..config import config


class BanService(ServiceBase):
    """
    黑名单服务类 - 管理被禁用户
    
    特性:
    - 内存缓存 + JSON 持久化
    - 自动从旧版 pickle 迁移数据
    - 所有修改操作自动保存到文件
    - 返回 Result 类型，操作结果明确
    
    Attributes:
        _banned_users: 内存中的黑名单用户 ID 集合
        _initialized: 是否已完成初始化
        
    线程安全:
        当前实现适用于单线程 asyncio 环境。
        所有操作都是原子性的，无需额外锁。
        
    Example:
        >>> ban = BanService.get_instance()
        >>> 
        >>> # 检查权限
        >>> if not ban.is_banned(user_id):
        ...     # 执行操作
        ...     pass
        >>> 
        >>> # 拉黑
        >>> result = ban.ban(user_id)
        >>> if not result.is_success:
        ...     print(f"拉黑失败: {result.error}")
    """
    
    def __init__(self) -> None:
        """初始化服务，数据延迟加载"""
        super().__init__()
        self._banned_users: Set[int] = set()
        self.logger = logging.getLogger("plugins.common.services.ban")
    
    def initialize(self) -> None:
        """
        初始化黑名单数据
        
        从文件加载黑名单，自动处理旧版 pickle 迁移。
        多次调用无副作用，只会加载一次。
        
        注意: 此方法由基类自动调用，无需手动调用
        """
        if self._initialized:
            return
        
        self._banned_users = set(self._load_banned_list())
        self._initialized = True
        self.logger.info(f"Initialized with {len(self._banned_users)} banned users")
    
    def _get_banned_file_path(self) -> Path:
        """
        获取黑名单文件路径
        
        优先使用 JSON 格式，兼容旧版 pickle。
        
        Returns:
            Path 对象，指向数据文件
        """
        data_dir = Path(config.data_dir)
        
        json_path = data_dir / "banned.json"
        pkl_path = data_dir / "banned.pkl"
        
        # 优先使用新的 json 格式
        if json_path.exists():
            return json_path
        
        # 兼容旧的 pickle 格式
        if pkl_path.exists():
            return pkl_path
        
        # 默认返回 json 路径（新建）
        return json_path
    
    def _load_banned_list(self) -> List[int]:
        """
        加载黑名单数据
        
        自动检测格式（JSON 或旧版 pickle），pickle 会自动迁移到 JSON。
        
        Returns:
            用户 ID 列表
        """
        banned_file = self._get_banned_file_path()
        
        if not banned_file.exists():
            return []
        
        # 处理 pickle 格式（兼容旧数据）
        if banned_file.suffix == '.pkl':
            return self._migrate_from_pickle(banned_file)
        
        # 处理 json 格式
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
        
        读取 pickle 文件，保存为 JSON，然后删除旧文件。
        
        Args:
            pkl_path: pickle 文件路径
            
        Returns:
            用户 ID 列表
        """
        try:
            import pickle
            with open(pkl_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, list):
                    self._save_banned_list(data)
                    pkl_path.unlink()  # 删除旧文件
                    self.logger.info(f"Migrated {len(data)} users from pickle to json")
                    return data
        except Exception as e:
            self.logger.error(f"Failed to migrate pickle: {e}")
        return []
    
    def _save_banned_list(self, users: List[int]) -> Result[None]: # type: ignore
        """
        保存黑名单到文件
        
        Args:
            users: 用户 ID 列表
            
        Returns:
            Result 对象，表示保存是否成功
        """
        banned_file = Path(config.data_dir) / "banned.json"
        try:
            with open(banned_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            return Result.success(None)
        except Exception as e:
            self.logger.error(f"Failed to save: {e}")
            return Result.fail(f"保存失败: {e}")
    
    def is_banned(self, user_id: int) -> bool:
        """
        检查用户是否被拉黑
        
        Args:
            user_id: 用户 QQ 号
            
        Returns:
            True 如果用户在黑名单中
            
        Example:
            >>> ban = BanService.get_instance()
            >>> if ban.is_banned(123456):
            ...     print("Access denied")
        """
        self.ensure_initialized()
        return user_id in self._banned_users
    
    def ban(self, user_id: int) -> Result[bool]: # type: ignore
        """
        拉黑用户
        
        将用户添加到黑名单并保存到文件。
        
        Args:
            user_id: 要拉黑的用户 QQ 号
            
        Returns:
            Result 对象:
            - success(True): 新拉黑成功
            - success(False): 用户已在黑名单中
            - fail: 保存失败，error 包含原因
            
        Example:
            >>> result = ban.ban(123456)
            >>> if result.is_success:
            ...     if result.value:
            ...         print("拉黑成功")
            ...     else:
            ...         print("用户已在黑名单")
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
    
    def unban(self, user_id: int) -> Result[bool]: # type: ignore
        """
        解封用户
        
        将用户从黑名单移除并保存到文件。
        
        Args:
            user_id: 要解封的用户 QQ 号
            
        Returns:
            Result 对象:
            - success(True): 解封成功
            - success(False): 用户不在黑名单中
            - fail: 保存失败
            
        Example:
            >>> result = ban.unban(123456)
            >>> if result.is_success and result.value:
            ...     print("解封成功")
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
    
    def get_banned_count(self) -> int:
        """
        获取黑名单用户数量
        
        Returns:
            当前黑名单中的用户数量
        """
        self.ensure_initialized()
        return len(self._banned_users)
    
    def get_banned_list(self) -> List[int]:
        """
        获取黑名单列表
        
        Returns:
            黑名单用户 ID 列表（副本，修改不影响原数据）
        """
        self.ensure_initialized()
        return list(self._banned_users)


# 向后兼容
def get_ban_service() -> BanService:
    """
    获取黑名单服务单例（向后兼容）
    
    推荐使用 BanService.get_instance()
    
    Returns:
        BanService 单例实例
    """
    return BanService.get_instance()
