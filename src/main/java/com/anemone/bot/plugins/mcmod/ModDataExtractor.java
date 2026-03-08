package com.anemone.bot.plugins.mcmod;

import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.edge.EdgeOptions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;

import java.util.ArrayList;
import java.util.List;

/**
 * MCMOD 模组数据提取器
 * 
 * 使用 Selenium 无头浏览器访问 MCMOD 网页，
 * 截取配置中指定的 CSS 选择器元素的截图。
 * 
 * 注意：需要 Chrome/Chromium 浏览器和 ChromeDriver 才能正常工作。
 */
public class ModDataExtractor {
    
    private static final Logger logger = LoggerFactory.getLogger(ModDataExtractor.class);
    
    private final String captureSelectors;
    private final List<String> selectors;
    
    public ModDataExtractor(BotConfig config) {
        String selectorsStr = config.getMcmodCaptureSelectors();
        this.captureSelectors = selectorsStr;
        String actualSelectors = (selectorsStr == null || selectorsStr.isEmpty()) 
            ? "class-title,class-text-top" 
            : selectorsStr;
        this.selectors = List.of(actualSelectors.split(","));
    }
    
    /**
     * 提取模组页面截图
     * 
     * @param modId 模组 ID
     * @return 截图列表
     */
    public Result<List<BufferedImage>> extract(int modId) {
        WebDriver driver = null;
        
        try {
            driver = createDriver();
            if (driver == null) {
                return Result.err("WebDriver not available");
            }
            
            String url = String.format("https://www.mcmod.cn/class/%d.html", modId);
            logger.debug("Accessing MCMOD page: {}", url);
            
            driver.get(url);
            
            // 等待页面加载
            Thread.sleep(2000);
            
            // 隐藏顶部导航栏
            try {
                List<WebElement> headers = driver.findElements(By.className("header-container"));
                for (WebElement header : headers) {
                    ((org.openqa.selenium.JavascriptExecutor) driver).executeScript(
                        "arguments[0].style.display='none';", header
                    );
                }
            } catch (Exception e) {
                logger.debug("Failed to hide header: {}", e.getMessage());
            }
            
            // 等待元素渲染
            Thread.sleep(1000);
            
            // 截取指定元素
            List<BufferedImage> images = new ArrayList<>();
            
            for (String selector : selectors) {
                BufferedImage img = captureElement(driver, selector.trim());
                if (img != null) {
                    images.add(img);
                }
            }
            
            if (images.isEmpty()) {
                return Result.err("screenshot_failed");
            }
            
            return Result.ok(images);
            
        } catch (Exception e) {
            logger.error("Failed to extract mod data", e);
            return Result.err("screenshot_failed: " + e.getMessage());
        } finally {
            if (driver != null) {
                try {
                    driver.quit();
                } catch (Exception e) {
                    logger.debug("Failed to quit WebDriver", e);
                }
            }
        }
    }
    
    /**
     * 创建 WebDriver (Edge)
     */
    private WebDriver createDriver() {
        try {
            EdgeOptions options = new EdgeOptions();
            options.addArguments("--headless=new");
            options.addArguments("--no-sandbox");
            options.addArguments("--disable-dev-shm-usage");
            options.addArguments("--disable-gpu");
            options.addArguments("--window-size=1920,2000");
            options.addArguments("--log-level=3");
            
            return new EdgeDriver(options);
        } catch (Exception e) {
            logger.error("Failed to create WebDriver", e);
            return null;
        }
    }
    
    /**
     * 截取元素截图
     */
    private BufferedImage captureElement(WebDriver driver, String className) {
        try {
            List<WebElement> elements = driver.findElements(By.className(className));
            if (elements.isEmpty()) {
                logger.debug("Element not found: {}", className);
                return null;
            }
            
            WebElement element = elements.get(0);
            
            // 滚动到元素位置
            ((org.openqa.selenium.JavascriptExecutor) driver).executeScript(
                "arguments[0].scrollIntoView({block: 'start'});", element
            );
            Thread.sleep(500);
            
            // 获取截图
            byte[] screenshot = element.getScreenshotAs(org.openqa.selenium.OutputType.BYTES);
            
            return ImageIO.read(new ByteArrayInputStream(screenshot));
            
        } catch (Exception e) {
            logger.debug("Failed to capture element {}: {}", className, e.getMessage());
            return null;
        }
    }
}
