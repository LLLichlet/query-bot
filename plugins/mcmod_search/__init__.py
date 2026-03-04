"""
MCMOD 模组查询插件

查询 Minecraft 模组信息，从 MCMOD 百科获取模组详情截图。
支持模组名搜索、缩写搜索。

触发方式:
    - /mcmod - 随机模组
    - /mcmod <模组ID> - 通过ID查询（如 /mcmod 2）
    - /mcmod <模组名> - 通过名称搜索（如 /mcmod 工业时代2）
    - /mcmod <缩写> - 通过缩写搜索（如 /mcmod IC2）

配置:
    QUERY_MCMOD_SEARCH_ENABLED=True/False    # 功能开关
    QUERY_MCMOD_CAPTURE_SELECTORS=class-title,class-text-top  # 截图选择器

数据来源:
    模组数据从 mcmod_data.json 获取
    截图从 https://www.mcmod.cn/class/<id>.html 获取

使用方式:
    /mcmod [模组ID/模组名/缩写]
"""
import json
import os
import io
import asyncio
import random
from typing import Optional
from dataclasses import dataclass

try:
    from nonebot.adapters.onebot.v11 import MessageEvent
    from nonebot.plugin import PluginMetadata
    NONEBOT_AVAILABLE = True
except ImportError:
    NONEBOT_AVAILABLE = False
    class MessageEvent: pass
    class PluginMetadata:
        def __init__(self, **kwargs): pass

from plugins.common import PluginHandler, CommandReceiver, config
from plugins.common.base import Result

try:
    from plugins.utils import (
        calculate_similarity, 
        image_to_message
    )
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

# Selenium 导入保护
try:
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None
    EdgeOptions = None
    By = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


@dataclass
class ModInfo:
    """模组信息数据类"""
    id: int
    name: str
    name_cn: str
    name_en: str
    abbreviation: str


class McmodSearchHandler(PluginHandler):
    """
    MCMOD 模组查询处理器
    
    处理模组查询命令，支持ID、模组名和缩写搜索。
    所有可能失败的操作返回 Result[T] 类型。
    
    Attributes:
        name: 插件名称
        description: 功能描述
        command: 命令名称
        aliases: 命令别名集合
        feature_name: 功能开关名
        priority: 命令处理优先级
        ERROR_MESSAGES: 错误消息映射
    """
    
    name = "MCMOD模组查询"
    description = "查询MCMOD百科的模组信息，支持ID、模组名和缩写搜索，无参数时随机返回"
    command = "mcmod"
    aliases = {"模组查询", "mcmod搜索"}
    feature_name = "mcmod_search"
    priority = 10
    
    ERROR_MESSAGES = {
        "utils_not_available": "Image processing module not available",
        "selenium_not_available": "Selenium not installed, cannot capture screenshot",
        "pil_not_available": "PIL not installed, cannot process image",
        "mod_not_found": "Mod not found",
        "data_load_failed": "Failed to load mod data",
        "screenshot_failed": "Failed to capture screenshot, please try again later",
        "image_process_failed": "Image processing failed",
        "browser_error": "Browser operation failed, please try again later",
    }
    
    def __init__(self):
        super().__init__()
        self._mods_data: Optional[dict] = None
    
    @property
    def mods_data(self) -> dict:
        """懒加载模组数据"""
        if self._mods_data is None:
            self._mods_data = self._load_mods_data()
        return self._mods_data
    
    def _load_mods_data(self) -> dict:
        """加载模组数据"""
        json_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "mcmod_data.json"
        )
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            mods = data.get("mods", [])
            name_to_id = {}
            abbr_to_id = {}
            
            for mod in mods:
                mod_id = mod.get("id")
                if not mod_id:
                    continue
                
                name_cn = mod.get("name_cn", "").strip()
                if name_cn:
                    name_to_id[name_cn.lower()] = mod_id
                
                name_en = mod.get("name_en", "").strip()
                if name_en:
                    name_to_id[name_en.lower()] = mod_id
                
                abbr = mod.get("abbreviation", "").strip()
                if abbr:
                    abbr_to_id[abbr.lower()] = mod_id
            
            return {
                "mods": mods,
                "name_to_id": name_to_id,
                "abbr_to_id": abbr_to_id,
            }
        except Exception:
            return {"mods": [], "name_to_id": {}, "abbr_to_id": {}}
    
    def _validate_environment(self) -> Result[bool]:
        """验证运行环境"""
        if not UTILS_AVAILABLE:
            return self.err("utils_not_available")
        if not SELENIUM_AVAILABLE:
            return self.err("selenium_not_available")
        if not PIL_AVAILABLE:
            return self.err("pil_not_available")
        return self.ok(True)
    
    def _find_mod(self, query: str) -> Result[ModInfo]:
        """
        查找模组
        
        优先顺序：ID 精确匹配 > 缩写精确匹配 > 名称精确匹配 > 相似度匹配
        
        Args:
            query: 查询词（模组ID、模组名或缩写）
            
        Returns:
            成功返回 ModInfo，失败包含错误信息
        """
        if not query:
            return self.err("empty_query")
        
        query_lower = query.lower().strip()
        mods = self.mods_data.get("mods", [])
        
        # 1. ID 精确匹配
        if query.isdigit():
            mod_id = int(query)
            for mod in mods:
                if mod.get("id") == mod_id:
                    return self.ok(self._to_mod_info(mod))
            return self.err("mod_not_found")
        
        # 2. 缩写精确匹配
        abbr_to_id = self.mods_data.get("abbr_to_id", {})
        if query_lower in abbr_to_id:
            mod_id = abbr_to_id[query_lower]
            for mod in mods:
                if mod.get("id") == mod_id:
                    return self.ok(self._to_mod_info(mod))
        
        # 3. 名称精确匹配
        name_to_id = self.mods_data.get("name_to_id", {})
        if query_lower in name_to_id:
            mod_id = name_to_id[query_lower]
            for mod in mods:
                if mod.get("id") == mod_id:
                    return self.ok(self._to_mod_info(mod))
        
        # 4. 相似度匹配
        if UTILS_AVAILABLE:
            best_match = None
            best_score = 0.0
            
            for name, mod_id in name_to_id.items():
                score = calculate_similarity(query_lower, name)
                if score > best_score:
                    best_score = score
                    best_match = mod_id
            
            if best_match and best_score > 0.5:
                for mod in mods:
                    if mod.get("id") == best_match:
                        return self.ok(self._to_mod_info(mod))
        
        return self.err("mod_not_found")
    
    def _get_random_mod(self) -> Result[ModInfo]:
        """获取随机模组"""
        mods = self.mods_data.get("mods", [])
        if not mods:
            return self.err("data_load_failed")
        mod = random.choice(mods)
        return self.ok(self._to_mod_info(mod))
    
    def _to_mod_info(self, mod: dict) -> ModInfo:
        """转换为 ModInfo"""
        return ModInfo(
            id=mod.get("id", 0),
            name=mod.get("name_cn") or mod.get("name_en", "未知模组"),
            name_cn=mod.get("name_cn", ""),
            name_en=mod.get("name_en", ""),
            abbreviation=mod.get("abbreviation", "")
        )
    
    def _capture_mod_page(self, mod_id: int) -> Result[list]:
        """捕获模组页面截图"""
        extractor = ModDataExtractor(self.ERROR_MESSAGES)
        
        start_result = extractor.start()
        if start_result.is_failure:
            return start_result
        
        try:
            return extractor.extract(mod_id)
        finally:
            extractor.stop()
    
    def _combine_images(self, images: list) -> Result[Image.Image]:
        """合并多张图片"""
        valid_images = [img for img in images if img is not None]
        if not valid_images:
            return self.err("image_process_failed")
        
        if len(valid_images) == 1:
            return self.ok(valid_images[0])
        
        try:
            width = max(img.width for img in valid_images)
            total_height = sum(img.height for img in valid_images)
            
            combined = Image.new('RGBA', (width, total_height), (255, 255, 255, 255))
            
            y_offset = 0
            for img in valid_images:
                x = (width - img.width) // 2
                combined.paste(img, (x, y_offset))
                y_offset += img.height
            
            return self.ok(combined)
        except Exception as e:
            return self.err(f"image_process_failed: {e}")
    
    async def handle(self, event: MessageEvent, args: str) -> None:
        """
        处理模组查询命令
        
        Args:
            event: 消息事件对象
            args: 用户输入的参数（模组ID/模组名/缩写）
        """
        # 1. 验证环境
        env_result = self._validate_environment()
        if env_result.is_failure:
            await self.reply(self.get_error_message(env_result.error))
            return
        
        # 2. 查找模组
        if args:
            mod_result = self._find_mod(args.strip())
        else:
            mod_result = self._get_random_mod()
        
        if mod_result.is_failure:
            await self.reply(self.get_error_message(mod_result.error))
            return
        
        mod = mod_result.value
        
        # 3. 发送查询提示
        await self.reply(f"Querying {mod.name}, please wait...")
        
        # 4. 截图
        try:
            images_result = await asyncio.get_event_loop().run_in_executor(
                None, self._capture_mod_page, mod.id
            )
        except Exception:
            await self.reply(self.get_error_message("browser_error"))
            return
        
        if images_result.is_failure:
            await self.reply(self.get_error_message(
                images_result.error or "screenshot_failed"
            ))
            return
        
        images = images_result.value
        if not images or all(img is None for img in images):
            await self.reply(self.get_error_message("screenshot_failed"))
            return
        
        # 5. 合并图片
        combine_result = self._combine_images(images)
        if combine_result.is_failure:
            await self.reply(self.get_error_message(combine_result.error))
            return
        
        # 6. 发送图片
        try:
            msg = image_to_message(combine_result.value)
            await self.send(msg, finish=True)
        except Exception:
            await self.reply(self.get_error_message("image_process_failed"))


class ModDataExtractor:
    """
    MCMOD 模组数据提取器
    
    使用 Selenium 无头浏览器访问 MCMOD 网页，
    截取配置中指定的 CSS 选择器元素的截图。
    
    Attributes:
        driver: WebDriver 实例
        selectors: 要截取的 CSS 选择器列表
        error_messages: 错误消息映射
    """
    
    def __init__(self, error_messages: dict):
        self.driver = None
        self.error_messages = error_messages
        selectors_str = getattr(config, 'mcmod_capture_selectors', 'class-title,class-text-top')
        self.selectors = [s.strip() for s in selectors_str.split(',') if s.strip()]
    
    def start(self) -> Result[bool]:
        """启动浏览器"""
        if not SELENIUM_AVAILABLE:
            return Result.err("selenium_not_available")
        
        try:
            edge_options = EdgeOptions()
            edge_options.add_argument("--headless=new")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1920,2000")
            edge_options.add_argument("--log-level=3")
            
            self.driver = webdriver.Edge(options=edge_options)
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"browser_error: {e}")
    
    def stop(self) -> None:
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
    
    def extract(self, mod_id: int) -> Result[list]:
        """
        提取模组页面截图
        
        Args:
            mod_id: 模组 ID
            
        Returns:
            成功返回截图列表（PIL Image 对象）
        """
        if not self.driver:
            return Result.err("browser_error")
        
        url = f"https://www.mcmod.cn/class/{mod_id}.html"
        images = []
        import time
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # 隐藏顶部导航栏
            try:
                headers = self.driver.find_elements(By.CLASS_NAME, "header-container")
                for header in headers:
                    self.driver.execute_script("arguments[0].style.display='none';", header)
            except Exception:
                pass
            
            # 等待元素渲染
            max_wait = 15
            found_any = False
            for _ in range(max_wait):
                for selector in self.selectors:
                    elements = self.driver.find_elements(By.CLASS_NAME, selector)
                    if elements:
                        found_any = True
                        break
                if found_any:
                    break
                time.sleep(1)
            
            if found_any:
                time.sleep(1)
            
            # 截图
            for selector in self.selectors:
                img = None
                try:
                    element = None
                    for _ in range(3):
                        elements = self.driver.find_elements(By.CLASS_NAME, selector)
                        if elements:
                            element = elements[0]
                            break
                        time.sleep(1)
                    
                    if element:
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'start'});", element
                        )
                        time.sleep(0.5)
                        png_data = element.screenshot_as_png
                        img = Image.open(io.BytesIO(png_data))
                except Exception:
                    pass
                images.append(img)
            
            return Result.ok(images)
            
        except Exception as e:
            return Result.err(f"screenshot_failed: {e}")


# 创建处理器和接收器
handler = McmodSearchHandler()
receiver = CommandReceiver(handler)


# 导出元数据
if NONEBOT_AVAILABLE:
    __plugin_meta__ = PluginMetadata(
        name=handler.name,
        description=handler.description,
        usage="/mcmod [模组ID/模组名/缩写]",
        extra={"author": "Lichlet", "version": "2.4.0"}
    )
