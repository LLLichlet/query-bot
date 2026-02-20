"""
网络请求工具 - HTTP 客户端封装

提供同步和异步 HTTP 请求工具，支持重试机制和错误处理。
"""

from typing import Optional, Callable, Any, Dict
from functools import wraps
import asyncio
import logging

import requests
import httpx

logger = logging.getLogger("plugins.utils.network")

# 默认请求头
DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                        asyncio.sleep(delay)
            logger.error(f"All {max_retries} attempts failed: {last_error}")
            raise last_error
        return wrapper
    return decorator


def fetch_html(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
    **kwargs
) -> Optional[str]:
    """
    同步获取网页 HTML
    
    注意：在异步代码中使用会阻塞事件循环，
    异步代码请使用 fetch_html_async。
    
    Returns:
        HTML 文本，失败返回 None
    """
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        response = requests.get(url, headers=request_headers, timeout=timeout, **kwargs)
        response.raise_for_status()
        
        if response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding
        
        return response.text
    except requests.RequestException as e:
        logger.error(f"Request failed [{url}]: {e}")
        return None


def fetch_binary(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10
) -> Optional[bytes]:
    """
    同步获取二进制数据
    
    Returns:
        二进制数据，失败返回 None
    """
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        response = requests.get(url, headers=request_headers, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Request failed [{url}]: {e}")
        return None


async def fetch_html_async(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    **kwargs
) -> Optional[str]:
    """
    异步获取网页 HTML（推荐在异步代码中使用）
    
    Args:
        url: 目标 URL
        headers: 自定义请求头
        timeout: 超时时间（秒）
        **kwargs: 其他 httpx 参数
    
    Returns:
        HTML 文本，失败返回 None
    
    Example:
        >>> html = await fetch_html_async("https://example.com")
        >>> if html:
        ...     print(html[:100])
    """
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        async with httpx.AsyncClient(headers=request_headers, timeout=timeout) as client:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        logger.error(f"Async request failed [{url}]: {e}")
        return None


async def fetch_binary_async(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    **kwargs
) -> Optional[bytes]:
    """
    异步获取二进制数据（推荐在异步代码中使用）
    
    Returns:
        二进制数据，失败返回 None
    """
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        async with httpx.AsyncClient(headers=request_headers, timeout=timeout) as client:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as e:
        logger.error(f"Async request failed [{url}]: {e}")
        return None


async def download_file(
    url: str,
    save_path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> bool:
    """
    异步下载文件到本地
    
    Args:
        url: 文件 URL
        save_path: 保存路径
        headers: 自定义请求头
        timeout: 超时时间（秒）
    
    Returns:
        是否下载成功
    """
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        async with httpx.AsyncClient(headers=request_headers, timeout=timeout) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(save_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        logger.info(f"Downloaded file to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Download failed [{url}]: {e}")
        return False


class HttpClient:
    """
    HTTP 客户端类 - 支持连接池和复用
    
    适用于需要频繁请求同一主机的场景。
    
    Example:
        >>> client = HttpClient(timeout=10.0)
        >>> html = await client.get("https://api.example.com/data")
        >>> await client.close()
    """
    
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        follow_redirects: bool = True
    ):
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=self.follow_redirects
            )
        return self._client
    
    async def get(self, url: str, **kwargs) -> Optional[str]:
        """GET 请求，返回文本"""
        try:
            client = await self._get_client()
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"GET failed [{url}]: {e}")
            return None
    
    async def get_bytes(self, url: str, **kwargs) -> Optional[bytes]:
        """GET 请求，返回二进制"""
        try:
            client = await self._get_client()
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.error(f"GET failed [{url}]: {e}")
            return None
    
    async def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs
    ) -> Optional[httpx.Response]:
        """POST 请求"""
        try:
            client = await self._get_client()
            response = await client.post(url, data=data, json=json, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"POST failed [{url}]: {e}")
            return None
    
    async def close(self) -> None:
        """关闭客户端，释放资源"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self) -> 'HttpClient':
        """异步上下文管理器入口"""
        await self._get_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出"""
        await self.close()
