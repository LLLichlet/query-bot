"""
一次性令牌服务

提供基于时间的短期令牌生成和验证，用于管理员身份验证。
"""
import secrets
import time
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from ..base import ServiceBase


@dataclass
class TokenInfo:
    """令牌信息"""
    token: str
    expire_time: float
    used: bool = False


class TokenService(ServiceBase):
    """
    一次性令牌服务
    
    为管理员操作提供短期、一次性的身份验证令牌。
    令牌通过私聊获取，在群内使用，有效期5分钟，使用一次即失效。
    
    Example:
        >>> service = TokenService.get_instance()
        >>> 
        >>> # 生成令牌（私聊时调用）
        >>> token = service.generate_token(user_id=123456)
        >>> print(f"您的令牌: {token}（5分钟内有效）")
        >>> 
        >>> # 验证令牌（群内命令时调用）
        >>> if service.verify_token(user_id=123456, token="xxx"):
        ...     print("验证通过")
        ... else:
        ...     print("令牌无效或已过期")
    """
    
    # 令牌有效期（秒）
    TOKEN_EXPIRE_SECONDS = 300  # 5分钟
    
    # 令牌长度（字节）
    TOKEN_BYTES = 8  # 约11位base64字符
    
    def __init__(self) -> None:
        super().__init__()
        # user_id -> TokenInfo
        self._tokens: Dict[int, TokenInfo] = {}
    
    def generate_token(self, user_id: int) -> str:
        """
        生成一次性令牌
        
        为指定用户生成新的随机令牌，有效期5分钟。
        如果用户已有未过期令牌，会先删除旧令牌。
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            生成的令牌字符串（base64url编码，约11位）
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
        
        self.logger.info(f"为用户 {user_id} 生成令牌，过期时间: {expire_time}")
        return token
    
    def verify_token(self, user_id: int, token: str) -> bool:
        """
        验证并消耗令牌
        
        验证指定用户的令牌是否有效，有效则标记为已使用（一次性）。
        
        Args:
            user_id: 用户QQ号
            token: 待验证的令牌
            
        Returns:
            True 如果令牌有效且未过期，False 否则
        """
        # 检查用户是否有令牌
        if user_id not in self._tokens:
            self.logger.debug(f"用户 {user_id} 没有令牌记录")
            return False
        
        token_info = self._tokens[user_id]
        
        # 检查是否已使用
        if token_info.used:
            self.logger.info(f"用户 {user_id} 的令牌已被使用")
            del self._tokens[user_id]
            return False
        
        # 检查是否过期
        current_time = time.time()
        if current_time > token_info.expire_time:
            self.logger.info(f"用户 {user_id} 的令牌已过期")
            del self._tokens[user_id]
            return False
        
        # 验证令牌内容（防止时序攻击）
        if not secrets.compare_digest(token_info.token, token):
            self.logger.info(f"用户 {user_id} 的令牌不匹配")
            return False
        
        # 标记为已使用（一次性）
        token_info.used = True
        del self._tokens[user_id]  # 使用后立即删除
        
        self.logger.info(f"用户 {user_id} 的令牌验证通过")
        return True
    
    def has_valid_token(self, user_id: int) -> bool:
        """
        检查用户是否有有效未使用的令牌
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            True 如果用户有有效且未使用的令牌
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
            剩余秒数，如果没有有效令牌返回 None
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
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            True 如果成功吊销，False 如果用户没有令牌
        """
        if user_id in self._tokens:
            del self._tokens[user_id]
            self.logger.info(f"已吊销用户 {user_id} 的令牌")
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """
        清理所有过期令牌
        
        Returns:
            清理的令牌数量
        """
        current_time = time.time()
        expired_users = [
            user_id for user_id, info in self._tokens.items()
            if current_time > info.expire_time
        ]
        
        for user_id in expired_users:
            del self._tokens[user_id]
        
        if expired_users:
            self.logger.debug(f"清理了 {len(expired_users)} 个过期令牌")
        
        return len(expired_users)


# 便捷获取函数
def get_token_service() -> TokenService:
    """获取令牌服务实例"""
    return TokenService.get_instance()
