"""
网络请求工具 - HTTP 客户端封装

提供异步 HTTP 请求工具，支持重试机制和错误处理。

使用方式:
    >>> from plugins.utils import fetch_html, HttpClient
    >>> 
    >>> # 简单请求
    >>> html = await fetch_html("https://example.com")
    >>> 
    >>> # 使用连接池客户端
    >>> async with HttpClient() as client:
    ...     data = await client.get("https://api.example.com/data")

注意：此模块需要 httpx，导入失败时相关函数不可用。
"""

from typing import Optional, Dict
import logging

# 导入保护
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore

logger = logging.getLogger("plugins.utils.network")


def _check_httpx():
    """检查 httpx 是否可用"""
    if not HTTPX_AVAILABLE:
        raise ImportError("httpx is not available. Install with: pip install httpx")

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


async def fetch_html(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    **kwargs
) -> Optional[str]:
    """
    异步获取网页 HTML
    
    发送 GET 请求并返回响应文本内容。
    
    Args:
        url: 目标 URL
        headers: 自定义请求头（覆盖默认头）
        timeout: 请求超时时间（秒）
        **kwargs: 传递给 httpx 的额外参数
        
    Returns:
        HTML 文本内容，请求失败时返回 None
        
    Example:
        >>> html = await fetch_html("https://example.com")
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
        logger.error(f"Request failed [{url}]: {e}")
        return None


async def fetch_binary(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
    **kwargs
) -> Optional[bytes]:
    """
    异步获取二进制数据
    
    发送 GET 请求并返回响应的二进制内容。
    
    Args:
        url: 目标 URL
        headers: 自定义请求头（覆盖默认头）
        timeout: 请求超时时间（秒）
        **kwargs: 传递给 httpx 的额外参数
        
    Returns:
        二进制数据，请求失败时返回 None
        
    Example:
        >>> data = await fetch_binary("https://example.com/image.png")
        >>> if data:
        ...     print(f"Downloaded {len(data)} bytes")
    """
    try:
        request_headers = headers if headers is not None else DEFAULT_HEADERS
        async with httpx.AsyncClient(headers=request_headers, timeout=timeout) as client:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.content
    except httpx.HTTPError as e:
        logger.error(f"Request failed [{url}]: {e}")
        return None


async def download_file(
    url: str,
    save_path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> bool:
    """
    异步下载文件到本地
    
    使用流式下载方式，适合大文件下载。
    
    Args:
        url: 文件 URL
        save_path: 保存路径
        headers: 自定义请求头（覆盖默认头）
        timeout: 请求超时时间（秒）
        
    Returns:
        下载成功返回 True，失败返回 False
        
    Example:
        >>> success = await download_file(
        ...     "https://example.com/file.zip",
        ...     "/tmp/file.zip"
        ... )
        >>> if success:
        ...     print("Download complete")
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
    支持异步上下文管理器（async with）。
    
    Attributes:
        headers: 默认请求头
        timeout: 超时时间（秒）
        follow_redirects: 是否跟随重定向
        _client: httpx.AsyncClient 实例
        
    Example:
        >>> async with HttpClient(timeout=10.0) as client:
        ...     html = await client.get("https://api.example.com/data")
        ...     # 自动关闭连接
    """
    
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        follow_redirects: bool = True
    ):
        """
        初始化 HTTP 客户端
        
        Args:
            headers: 自定义请求头（覆盖默认头）
            timeout: 请求超时时间（秒）
            follow_redirects: 是否跟随重定向
        """
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        获取或创建 httpx 客户端实例
        
        Returns:
            httpx.AsyncClient 实例
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=self.follow_redirects
            )
        return self._client
    
    async def get(self, url: str, **kwargs) -> Optional[str]:
        """
        发送 GET 请求，返回文本
        
        Args:
            url: 目标 URL
            **kwargs: 传递给 httpx 的额外参数
            
        Returns:
            响应文本内容，请求失败时返回 None
            
        Example:
            >>> client = HttpClient()
            >>> html = await client.get("https://example.com")
            >>> await client.close()
        """
        try:
            client = await self._get_client()
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"GET failed [{url}]: {e}")
            return None
    
    async def get_bytes(self, url: str, **kwargs) -> Optional[bytes]:
        """
        发送 GET 请求，返回二进制数据
        
        Args:
            url: 目标 URL
            **kwargs: 传递给 httpx 的额外参数
            
        Returns:
            响应二进制内容，请求失败时返回 None
            
        Example:
            >>> client = HttpClient()
            >>> data = await client.get_bytes("https://example.com/image.png")
            >>> await client.close()
        """
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
        """
        发送 POST 请求
        
        Args:
            url: 目标 URL
            data: 表单数据
            json: JSON 数据
            **kwargs: 传递给 httpx 的额外参数
            
        Returns:
            httpx.Response 对象，请求失败时返回 None
            
        Example:
            >>> client = HttpClient()
            >>> response = await client.post(
            ...     "https://api.example.com/login",
            ...     json={"username": "admin", "password": "123456"}
            ... )
            >>> await client.close()
        """
        try:
            client = await self._get_client()
            response = await client.post(url, data=data, json=json, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"POST failed [{url}]: {e}")
            return None
    
    async def close(self) -> None:
        """
        关闭客户端，释放资源
        
        关闭底层的 httpx.AsyncClient 连接池。
        
        Example:
            >>> client = HttpClient()
            >>> await client.close()
        """
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
