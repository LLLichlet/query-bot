"""
AI 服务模块 - DeepSeek API 封装

提供统一的 AI 调用接口，支持异步聊天 completions。
所有 AI 调用都返回 Result[str] 类型，便于错误处理。

快速开始:
    >>> from plugins.common import AIService
    
    >>> # 获取服务实例
    >>> ai = AIService.get_instance()
    
    >>> # 检查服务是否可用
    >>> if ai.is_available:
    ...     result = await ai.chat(
    ...         system_prompt="你是一个 helpful 助手",
    ...         user_input="你好",
    ...         temperature=0.7
    ...     )
    ...     if result.is_success:
    ...         print(result.value)
    ...     else:
    ...         print(f"错误: {result.error}")

配置:
    需要在 .env 文件中设置:
    QUERY_DEEPSEEK_API_KEY=your_api_key
    QUERY_DEEPSEEK_BASE_URL=https://api.deepseek.com  # 可选
    QUERY_DEEPSEEK_MODEL=deepseek-chat  # 可选
"""

from typing import Optional, Any
import logging

from openai import AsyncOpenAI

from ..base import ServiceBase, Result
from ..config import config


class AIService(ServiceBase):
    """
    AI 服务类 - 封装 DeepSeek API 调用
    
    特性:
    - 单例模式，全局唯一实例
    - 异步调用，不阻塞事件循环
    - 延迟初始化，首次使用时连接
    - 返回 Result 类型，错误处理友好
    
    Attributes:
        _client: AsyncOpenAI 客户端实例
        is_available: 服务是否可用（API 密钥已配置）
        
    Example:
        >>> ai = AIService.get_instance()
        >>> 
        >>> # 方式1: 使用 Result（推荐）
        >>> result = await ai.chat(
        ...     system_prompt="你是数学专家",
        ...     user_input="解释群论",
        ...     temperature=0.3,
        ...     max_tokens=1024
        ... )
        >>> if result.is_success:
        ...     reply = result.value
        ... else:
        ...     reply = f"AI错误: {result.error}"
        >>>
        >>> # 方式2: 使用简化版（直接返回字符串）
        >>> reply = await ai.chat_simple(
        ...     system_prompt="你是助手",
        ...     user_input="你好"
        ... )  # 失败时返回 "AI服务暂时不可用"
    """
    
    def __init__(self) -> None:
        """初始化服务，客户端延迟加载"""
        super().__init__()
        self._client: Optional[AsyncOpenAI] = None
        self.logger = logging.getLogger("plugins.common.services.ai")
    
    def initialize(self) -> None:
        """
        初始化 OpenAI 客户端
        
        根据配置创建 AsyncOpenAI 客户端。
        如果未配置 API 密钥，服务将不可用。
        
        注意: 此方法由基类自动调用，无需手动调用
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
    
    @property
    def client(self) -> Optional[AsyncOpenAI]:
        """
        获取 OpenAI 客户端
        
        自动初始化（如未初始化）。
        
        Returns:
            AsyncOpenAI 客户端，如果未配置 API 密钥则返回 None
        """
        self.ensure_initialized()
        return self._client
    
    @property
    def is_available(self) -> bool:
        """
        检查 AI 服务是否可用
        
        Returns:
            True 如果已配置 API 密钥，False 如果未配置
            
        Example:
            >>> ai = AIService.get_instance()
            >>> if not ai.is_available:
            ...     print("AI 服务未配置")
        """
        return self.client is not None
    
    async def chat(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.5,
        max_tokens: int = 512,
        top_p: float = 0.9,
        **kwargs: Any
    ) -> Result[str]: # type: ignore
        """
        调用 AI 聊天接口
        
        发送系统提示和用户输入，返回 AI 生成的回复。
        这是一个通用接口，可用于任何对话场景。
        
        Args:
            system_prompt: 系统提示词，定义 AI 的角色和行为
            user_input: 用户输入内容
            temperature: 温度参数 (0-2)，控制随机性，越高越随机
            max_tokens: 最大生成 token 数
            top_p: nucleus sampling 参数 (0-1)
            **kwargs: 其他 OpenAI API 参数
            
        Returns:
            Result 对象
            - success: value 包含 AI 回复文本
            - fail: error 包含错误信息
            
        Example:
            >>> result = await ai.chat(
            ...     system_prompt="你是一个数学专家，用中文回答",
            ...     user_input="什么是群论？",
            ...     temperature=0.3,
            ...     max_tokens=1024
            ... )
            >>> if result.is_success:
            ...     print(result.value)
        """
        if not self.is_available:
            return Result.fail("AI服务未初始化")
        
        try:
            response = await self.client.chat.completions.create( # type: ignore
                model=config.deepseek_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **kwargs
            )
            content = response.choices[0].message.content.strip()
            return Result.success(content)
        except Exception as e:
            self.logger.error(f"AI API调用失败: {e}")
            return Result.fail(f"AI服务暂时不可用: {e}")
    
    async def chat_simple(
        self,
        system_prompt: str,
        user_input: str,
        **kwargs: Any
    ) -> str:
        """
        简化版聊天接口，直接返回字符串
        
        与 chat() 相同，但直接返回字符串而非 Result。
        失败时返回错误提示字符串，不会抛出异常。
        
        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            **kwargs: 其他参数（temperature, max_tokens 等）
            
        Returns:
            AI 回复文本，失败时返回 "AI服务暂时不可用"
            
        Example:
            >>> reply = await ai.chat_simple(
            ...     "你是助手",
            ...     "你好"
            ... )
            >>> print(reply)  # 直接输出，无需判断 Result
        """
        result = await self.chat(system_prompt, user_input, **kwargs)
        return result.unwrap_or("AI服务暂时不可用")


# 向后兼容的获取函数
def get_ai_service() -> AIService:
    """
    获取 AI 服务单例实例（向后兼容）
    
    推荐使用 AIService.get_instance() 替代。
    
    Returns:
        AIService 单例实例
    """
    return AIService.get_instance()
