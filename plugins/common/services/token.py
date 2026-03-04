"""
一次性令牌服务模块 - 管理员身份验证

服务层 - 实现 TokenServiceProtocol 协议

提供基于时间的短期令牌生成和验证，用于管理员身份验证。
令牌具有以下特性：
- 有效期 5 分钟
- 一次性使用（验证后即失效）
- 防时序攻击（使用 secrets.compare_digest）

在 initialize() 完成后自动注册到 ServiceLocator。

使用方式:
    >>> from plugins.common.services import TokenService
    >>> service = TokenService.get_instance()
    >>> service.initialize()
    >>> 
    >>> # 生成令牌
    >>> token = service.generate_token(123456)
    >>> print(f"您的令牌: {token}")
    >>> 
    >>> # 验证令牌
    >>> if service.verify_token(123456, user_input):
    ...     print("验证通过")

Example:
    >>> service = TokenService.get_instance()
    >>> token = service.generate_token(123456)
    >>> service.verify_token(123456, token)  # True
    >>> service.verify_token(123456, token)  # False (已使用)
"""

import secrets
import time
from typing import Dict, Optional
from dataclasses import dataclass
import logging

from ..base import ServiceBase
from ..protocols import (
    TokenServiceProtocol,
    ServiceLocator,
)


@dataclass
class TokenInfo:
    """
    令牌信息数据类
    
    存储令牌的值、过期时间和使用状态。
    
    Attributes:
        token: 令牌字符串
        expire_time: 过期时间戳（Unix 时间）
        used: 是否已使用
        
    Example:
        >>> info = TokenInfo(token="abc123", expire_time=1234567890.0, used=False)
        >>> print(info.token)
    """
    token: str
    expire_time: float
    used: bool = False


class TokenService(ServiceBase, TokenServiceProtocol):
    """
    一次性令牌服务类
    
    实现 TokenServiceProtocol 协议，提供安全的短期令牌管理。
    令牌有效期 5 分钟，一次性使用，防止重放攻击。
    在 initialize() 完成后自动注册到 ServiceLocator。
    
    Attributes:
        TOKEN_EXPIRE_SECONDS: 令牌有效期（秒），默认 300（5分钟）
        TOKEN_BYTES: 令牌字节数，默认 8（约11位base64字符）
        _tokens: 用户ID到令牌信息的映射
        
    Example:
        >>> service = TokenService.get_instance()
        >>> service.initialize()
        >>> token = service.generate_token(123456)
        >>> if service.verify_token(123456, token):
        ...     print("管理员验证通过")
    """
    
    # 令牌有效期（秒）
    TOKEN_EXPIRE_SECONDS = 300  # 5分钟
    
    # 令牌长度（字节）
    TOKEN_BYTES = 8  # 约11位base64字符
    
    def __init__(self) -> None:
        """
        初始化令牌服务
        
        创建空的令牌存储字典。
        
        Example:
            >>> service = TokenService.get_instance()
            >>> service._tokens
            {}
        """
        super().__init__()
        self._tokens: Dict[int, TokenInfo] = {}
        self.logger = logging.getLogger("plugins.common.services.token")
    
    def initialize(self) -> None:
        """
        初始化服务
        
        注册服务到 ServiceLocator，标记为已初始化。
        
        Example:
            >>> service = TokenService.get_instance()
            >>> service.initialize()
            >>> # 服务已注册到 ServiceLocator
        """
        if self._initialized:
            return
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(TokenServiceProtocol, self)
        self.logger.info("Token Service initialized")
    
    # ========== TokenServiceProtocol 实现 ==========
    
    def generate_token(self, user_id: int) -> str:
        """
        生成一次性令牌
        
        为指定用户生成一个新的令牌，替换该用户的旧令牌（如果存在）。
        令牌有效期为 TOKEN_EXPIRE_SECONDS（默认5分钟）。
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            生成的令牌字符串（URL安全的base64格式）
            
        Example:
            >>> service = TokenService.get_instance()
            >>> token = service.generate_token(123456)
            >>> print(f"令牌: {token}")  # 如: aB3xK9mNpQ
        """
        # 清除该用户的旧令牌
        if user_id in self._tokens:
            del self._tokens[user_id]
        
        # 生成新令牌
        token = secrets.token_urlsafe(self.TOKEN_BYTES)
        expire_time = time.time() + self.TOKEN_EXPIRE_SECONDS
        
        self._tokens[user_id] = TokenInfo(
            token=token,
            expire_time=expire_time,
            used=False
        )
        
        self.logger.info(f"为用户 {user_id} 生成令牌")
        return token
    
    def verify_token(self, user_id: int, token: str) -> bool:
        """
        验证并消耗令牌
        
        验证令牌是否有效，验证成功后令牌被标记为已使用（一次性）。
        使用 secrets.compare_digest 防止时序攻击。
        
        Args:
            user_id: 用户QQ号
            token: 待验证的令牌字符串
            
        Returns:
            True 如果令牌有效且未过期，False 否则
            
        Example:
            >>> service = TokenService.get_instance()
            >>> token = service.generate_token(123456)
            >>> service.verify_token(123456, token)  # True
            >>> service.verify_token(123456, token)  # False (已使用)
            >>> service.verify_token(123456, "wrong")  # False
        """
        if user_id not in self._tokens:
            return False
        
        token_info = self._tokens[user_id]
        
        # 检查是否已使用
        if token_info.used:
            del self._tokens[user_id]
            return False
        
        # 检查是否过期
        current_time = time.time()
        if current_time > token_info.expire_time:
            del self._tokens[user_id]
            return False
        
        # 验证令牌内容（防止时序攻击）
        if not secrets.compare_digest(token_info.token, token):
            return False
        
        # 标记为已使用（一次性）
        del self._tokens[user_id]
        
        self.logger.info(f"用户 {user_id} 的令牌验证通过")
        return True
    
    # ========== 额外方法（不在协议中）==========
    
    def has_valid_token(self, user_id: int) -> bool:
        """
        检查用户是否有有效未使用的令牌
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            True 如果用户有有效且未使用的令牌
            
        Example:
            >>> service = TokenService.get_instance()
            >>> service.generate_token(123456)
            >>> service.has_valid_token(123456)  # True
        """
        if user_id not in self._tokens:
            return False
        
        token_info = self._tokens[user_id]
        
        if token_info.used:
            return False
        
        if time.time() > token_info.expire_time:
            return False
        
        return True
    
    def get_token_remaining_time(self, user_id: int) -> Optional[int]:
        """
        获取令牌剩余有效时间（秒）
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            剩余秒数，如果令牌不存在或已过期返回 None
            
        Example:
            >>> service = TokenService.get_instance()
            >>> service.generate_token(123456)
            >>> remaining = service.get_token_remaining_time(123456)
            >>> print(f"剩余 {remaining} 秒")  # 如: 剩余 299 秒
        """
        if user_id not in self._tokens:
            return None
        
        token_info = self._tokens[user_id]
        
        if token_info.used:
            return None
        
        remaining = int(token_info.expire_time - time.time())
        if remaining <= 0:
            return None
        
        return remaining
    
    def revoke_token(self, user_id: int) -> bool:
        """
        吊销用户的令牌
        
        立即删除指定用户的令牌，使其失效。
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            True 如果成功吊销，False 如果用户没有令牌
            
        Example:
            >>> service = TokenService.get_instance()
            >>> service.generate_token(123456)
            >>> service.revoke_token(123456)  # True
            >>> service.revoke_token(123456)  # False
        """
        if user_id in self._tokens:
            del self._tokens[user_id]
            self.logger.info(f"已吊销用户 {user_id} 的令牌")
            return True
        return False


def get_token_service() -> TokenService:
    """
    获取令牌服务实例（向后兼容）
    
    Returns:
        TokenService 单例实例
        
    Example:
        >>> service = get_token_service()
        >>> service.initialize()
    """
    return TokenService.get_instance()
