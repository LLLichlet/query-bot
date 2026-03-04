"""
图片处理工具 - PIL 封装

提供图片下载、处理、转换的便捷函数。

使用方式:
    >>> from plugins.utils import download_image, ImageProcessor
    >>> 
    >>> # 下载图片
    >>> img = await download_image("https://example.com/photo.png")
    >>> 
    >>> # 使用链式处理器
    >>> if img:
    ...     msg = (ImageProcessor(img)
    ...         .resize((800, 600), keep_aspect=True)
    ...         .to_message())

注意：此模块需要 PIL 和 NoneBot 环境，导入失败时相关函数不可用。
"""

import io
import base64
from typing import Optional, List, Tuple, Union
import logging

# 导入保护 - 避免 PIL 或 NoneBot 不存在时导致模块加载失败
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

try:
    from nonebot.adapters.onebot.v11 import MessageSegment
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    MessageSegment = None  # type: ignore

from .network import fetch_binary

logger = logging.getLogger("plugins.utils.image")


# 检查依赖是否可用
def _check_pil():
    """检查 PIL 是否可用"""
    if not PIL_AVAILABLE:
        raise ImportError("PIL is not available. Install with: pip install Pillow")


def _check_nonebot():
    """检查 NoneBot 是否可用"""
    if not NONEBOT_AVAILABLE:
        raise ImportError("NoneBot is not available.")


def _check_httpx():
    """检查 httpx 是否可用"""
    from .network import HTTPX_AVAILABLE
    if not HTTPX_AVAILABLE:
        raise ImportError("httpx is not available. Install with: pip install httpx")


async def download_image(url: str, timeout: float = 10.0) -> Optional[Image.Image]:
    """
    异步下载图片（推荐）
    
    从 URL 下载图片并返回 PIL Image 对象。
    
    Args:
        url: 图片 URL
        timeout: 下载超时（秒）
        
    Returns:
        PIL Image 对象，下载失败时返回 None
        
    Example:
        >>> img = await download_image("https://example.com/photo.png")
        >>> if img:
        ...     print(f"Size: {img.size}")
    """
    _check_pil()
    _check_httpx()
    try:
        data = await fetch_binary(url, timeout=timeout)
        if data is None:
            return None
        return Image.open(io.BytesIO(data))
    except Exception as e:
        logger.error(f"Download failed [{url}]: {e}")
        return None


def image_to_message(image: Image.Image, format: str = 'PNG') -> MessageSegment:
    """
    将 PIL Image 转为 QQ 消息图片段
    
    将图片转换为 base64 编码的 MessageSegment.image。
    
    Args:
        image: PIL Image 对象
        format: 图片格式，默认 PNG
        
    Returns:
        MessageSegment.image 对象
        
    Example:
        >>> img = Image.new('RGB', (100, 100), color='red')
        >>> msg = image_to_message(img)
    """
    _check_pil()
    _check_nonebot()
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    img_bytes = buffer.getvalue()
    buffer.close()
    
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return MessageSegment.image(f"base64://{img_base64}")


def merge_images(
    base_image: Image.Image,
    *overlays: Image.Image
) -> Image.Image:
    """
    合并多张图片（Alpha 通道合成）
    
    按顺序将多张图片叠加到底图上。
    
    Args:
        base_image: 底图
        *overlays: 要叠加的图片
        
    Returns:
        合并后的 PIL Image 对象
        
    Example:
        >>> base = Image.new('RGBA', (100, 100), (255, 0, 0, 255))
        >>> overlay = Image.new('RGBA', (100, 100), (0, 0, 255, 128))
        >>> result = merge_images(base, overlay)
    """
    _check_pil()
    result = base_image
    for overlay in overlays:
        if overlay.size != result.size:
            overlay = overlay.resize(result.size, Image.Resampling.LANCZOS)
        result = Image.alpha_composite(result, overlay)
    return result


def resize_image(
    image: Image.Image,
    size: Tuple[int, int],
    keep_aspect: bool = True
) -> Image.Image:
    """
    调整图片大小
    
    Args:
        image: 原图
        size: 目标尺寸 (width, height)
        keep_aspect: 是否保持宽高比，默认 True
        
    Returns:
        调整后的图片
        
    Example:
        >>> img = Image.new('RGB', (800, 600))
        >>> small = resize_image(img, (400, 300), keep_aspect=True)
    """
    _check_pil()
    if keep_aspect:
        image.thumbnail(size, Image.Resampling.LANCZOS)
        return image
    return image.resize(size, Image.Resampling.LANCZOS)


def crop_image(
    image: Image.Image,
    box: Tuple[int, int, int, int]
) -> Image.Image:
    """
    裁剪图片
    
    Args:
        image: 原图
        box: 裁剪区域 (left, top, right, bottom)
        
    Returns:
        裁剪后的图片
        
    Example:
        >>> img = Image.new('RGB', (800, 600))
        >>> cropped = crop_image(img, (100, 100, 500, 400))
    """
    _check_pil()
    return image.crop(box)


def create_placeholder_image(
    width: int = 1,
    height: int = 1,
    color: Tuple[int, int, int, int] = (0, 0, 0, 0)
) -> Image.Image:
    """
    创建占位图片
    
    创建指定尺寸的纯色透明图片。
    
    Args:
        width: 图片宽度，默认 1
        height: 图片高度，默认 1
        color: 填充颜色 (R, G, B, A)，默认透明
        
    Returns:
        RGBA 模式的 PIL Image 对象
        
    Example:
        >>> placeholder = create_placeholder_image(100, 100, (255, 0, 0, 128))
    """
    _check_pil()
    return Image.new('RGBA', (width, height), color)


def compress_image(
    image: Image.Image,
    quality: int = 85,
    max_size: Optional[Tuple[int, int]] = None
) -> Image.Image:
    """
    压缩图片
    
    调整图片尺寸并转换为 RGB 模式以减小文件大小。
    
    Args:
        image: 原图
        quality: JPEG 质量 (1-100)，默认 85
        max_size: 最大尺寸 (width, height)，None 表示不调整
        
    Returns:
        压缩后的 RGB 模式图片
        
    Example:
        >>> img = Image.new('RGBA', (2000, 1500))
        >>> compressed = compress_image(img, quality=75, max_size=(800, 600))
    """
    _check_pil()
    result = image.copy()
    
    if max_size:
        result.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # 转换为 RGB 以支持 JPEG 压缩
    if result.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', result.size, (255, 255, 255))
        if result.mode == 'P':
            result = result.convert('RGBA')
        if result.mode in ('RGBA', 'LA'):
            background.paste(result, mask=result.split()[-1] if result.mode in ('RGBA', 'LA') else None)
            result = background
    
    return result


class ImageProcessor:
    """
    图片处理器类 - 链式操作
    
    支持链式调用进行多次图片处理，简化图片操作流程。
    
    Attributes:
        image: 当前处理的 PIL Image 对象
        
    Example:
        >>> processor = ImageProcessor(image)
        >>> result = (processor
        ...     .resize((800, 600))
        ...     .crop((100, 100, 500, 400))
        ...     .to_message())
    """
    
    def __init__(self, image: Image.Image):
        """
        初始化图片处理器
        
        Args:
            image: PIL Image 对象
        """
        _check_pil()
        self.image = image.copy()
    
    def resize(self, size: Tuple[int, int], keep_aspect: bool = False) -> 'ImageProcessor':
        """
        调整图片大小
        
        Args:
            size: 目标尺寸 (width, height)
            keep_aspect: 是否保持宽高比
            
        Returns:
            self，支持链式调用
            
        Example:
            >>> processor = ImageProcessor(img).resize((800, 600), keep_aspect=True)
        """
        if keep_aspect:
            self.image.thumbnail(size, Image.Resampling.LANCZOS)
        else:
            self.image = self.image.resize(size, Image.Resampling.LANCZOS)
        return self
    
    def crop(self, box: Tuple[int, int, int, int]) -> 'ImageProcessor':
        """
        裁剪图片
        
        Args:
            box: 裁剪区域 (left, top, right, bottom)
            
        Returns:
            self，支持链式调用
            
        Example:
            >>> processor = ImageProcessor(img).crop((100, 100, 500, 400))
        """
        self.image = self.image.crop(box)
        return self
    
    def merge(self, *overlays: Image.Image) -> 'ImageProcessor':
        """
        合并其他图片
        
        将其他图片叠加到当前图片上。
        
        Args:
            *overlays: 要叠加的图片
            
        Returns:
            self，支持链式调用
            
        Example:
            >>> overlay = Image.new('RGBA', (100, 100), (0, 0, 255, 128))
            >>> processor = ImageProcessor(img).merge(overlay)
        """
        self.image = merge_images(self.image, *overlays)
        return self
    
    def compress(self, quality: int = 85) -> 'ImageProcessor':
        """
        压缩图片
        
        Args:
            quality: JPEG 质量 (1-100)
            
        Returns:
            self，支持链式调用
            
        Example:
            >>> processor = ImageProcessor(img).compress(quality=75)
        """
        self.image = compress_image(self.image, quality)
        return self
    
    def to_message(self, format: str = 'PNG') -> MessageSegment:
        """
        转为 QQ 消息图片段
        
        Args:
            format: 图片格式，默认 PNG
            
        Returns:
            MessageSegment.image 对象
            
        Example:
            >>> msg = ImageProcessor(img).resize((400, 300)).to_message()
        """
        return image_to_message(self.image, format)
    
    def save(self, path: str, format: Optional[str] = None) -> 'ImageProcessor':
        """
        保存到文件
        
        Args:
            path: 保存路径
            format: 图片格式，None 表示从扩展名推断
            
        Returns:
            self，支持链式调用
            
        Example:
            >>> ImageProcessor(img).resize((800, 600)).save("output.png")
        """
        self.image.save(path, format=format)
        return self
