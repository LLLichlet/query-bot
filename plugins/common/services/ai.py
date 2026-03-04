"""
AI 服务模块 - DeepSeek API 封装

服务层 - 实现 AIServiceProtocol 协议

提供 DeepSeek API 的异步调用封装，支持对话生成、参数调优等功能。
在 initialize() 完成后自动注册到 ServiceLocator。

使用方式:
    >>> from plugins.common.services import AIService
    >>> ai = AIService.get_instance()
    >>> ai.initialize()
    >>> result = await ai.chat("你是数学家", "解释群论")
    >>> if result.is_success:
    ...     print(result.value)
    ... else:
    ...     print(f"错误: {result.error}")
"""

from typing import Optional, Any
import logging

from openai import AsyncOpenAI

from ..base import ServiceBase, Result
from ..config import config
from ..protocols import (
    AIServiceProtocol,
    ServiceLocator,
)


class AIService(ServiceBase, AIServiceProtocol):
    """
    AI 服务类 - 封装 DeepSeek API 调用
    
    实现 AIServiceProtocol 协议，提供异步对话能力。
    在 initialize() 完成后自动注册到 ServiceLocator。
    
    Attributes:
        _client: AsyncOpenAI 客户端实例，延迟初始化
        logger: 日志记录器实例
        
    Example:
        >>> ai = AIService.get_instance()
        >>> ai.initialize()
        >>> if ai.is_available:
        ...     result = await ai.chat("prompt", "input", 0.3, 512)
        ...     if result.is_success:
        ...         reply = result.value
    """
    
    def __init__(self) -> None:
        """
        初始化服务
        
        客户端延迟加载，实际初始化在 initialize() 中完成。
        
        Example:
            >>> ai = AIService.get_instance()
            >>> # _client 此时为 None
        """
        super().__init__()
        self._client: Optional[AsyncOpenAI] = None
        self.logger = logging.getLogger("plugins.common.services.ai")
    
    def initialize(self) -> None:
        """
        初始化 OpenAI 客户端
        
        根据配置创建 AsyncOpenAI 客户端实例，并在完成后注册到 ServiceLocator。
        如果 API 密钥未配置，服务将不可用但仍会注册。
        
        Example:
            >>> ai = AIService.get_instance()
            >>> ai.initialize()
            >>> # 服务已注册到 ServiceLocator
        """
        if self._initialized:
            return
        
        if config.deepseek_api_key:
            self._client = AsyncOpenAI(
                api_key=config.deepseek_api_key,
                base_url=config.deepseek_base_url
            )
            self.logger.info("AI Service initialized")
        else:
            self.logger.warning("AI Service not initialized: API key not set")
        
        self._initialized = True
        
        # 初始化完成后注册到服务定位器
        ServiceLocator.register(AIServiceProtocol, self)
    
    @property
    def client(self) -> Optional[AsyncOpenAI]:
        """
        获取 OpenAI 客户端
        
        Returns:
            AsyncOpenAI 客户端实例，如果未初始化则返回 None
            
        Example:
            >>> ai = AIService.get_instance()
            >>> ai.initialize()
            >>> client = ai.client
        """
        self.ensure_initialized()
        return self._client
    
    # ========== AIServiceProtocol 实现 ==========
    
    @property
    def is_available(self) -> bool:
        """
        检查 AI 服务是否可用
        
        Returns:
            True 如果客户端已初始化，False 否则
            
        Example:
            >>> ai = AIService.get_instance()
            >>> ai.initialize()
            >>> if ai.is_available:
            ...     # 可以调用 API
        """
        return self.client is not None
    
    async def chat(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.5,
        max_tokens: int = 512,
        top_p: float = 0.9
    ) -> Result[str]:
        """
        调用 AI 聊天接口
        
        发送系统提示和用户输入到 DeepSeek API，返回生成的回复。
        
        Args:
            system_prompt: 系统提示词，设定 AI 角色和行为
            user_input: 用户输入内容
            temperature: 温度参数（0-2），控制创造性，默认 0.5
            max_tokens: 最大生成 token 数，默认 512
            top_p: 核采样参数（0-1），默认 0.9
            
        Returns:
            Result[str]: 成功时包含 AI 回复文本，失败时包含错误信息
            
        Example:
            >>> result = await ai.chat("你是数学家", "解释群论", 0.3, 1024)
            >>> if result.is_success:
            ...     print(result.value)
            ... else:
            ...     print(f"失败: {result.error}")
        """
        if not self.is_available:
            return Result.fail("AI服务未初始化")
        
        try:
            response = await self.client.chat.completions.create(  # type: ignore
                model=config.deepseek_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
            content = response.choices[0].message.content.strip()
            return Result.success(content)
        except Exception as e:
            self.logger.error(f"AI API调用失败: {e}")
            return Result.fail(f"AI服务暂时不可用: {e}")
    

def get_ai_service() -> AIService:
    """
    获取 AI 服务单例实例（向后兼容）
    
    Returns:
        AIService 单例实例
        
    Example:
        >>> ai = get_ai_service()
        >>> ai.initialize()
    """
    return AIService.get_instance()
