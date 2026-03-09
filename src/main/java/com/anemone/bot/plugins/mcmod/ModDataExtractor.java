package com.anemone.bot.plugins.mcmod;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

import javax.imageio.ImageIO;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebDriverException;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.edge.EdgeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;

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
    
    private final List<String> selectors;
    
    // 超时配置
    private static final Duration PAGE_LOAD_TIMEOUT = Duration.ofSeconds(10);
    private static final Duration IMPLICIT_WAIT = Duration.ofSeconds(5);
    
    public ModDataExtractor(BotConfig config) {
        String selectorsStr = config.getMcmodCaptureSelectors();
        String actualSelectors = (selectorsStr == null || selectorsStr.isEmpty()) 
            ? "class-title,class-text-top" 
            : selectorsStr;
        this.selectors = List.of(actualSelectors.split(","));
    }
    
    /**
     * 提取模组页面截图（同步方法）
     * 
     * 使用显式等待替代 Thread.sleep，提高效率。
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
            
            // 使用显式等待替代 Thread.sleep
            WebDriverWait wait = new WebDriverWait(driver, PAGE_LOAD_TIMEOUT);
            
            // 等待页面主体加载完成
            try {
                wait.until(ExpectedConditions.presenceOfElementLocated(By.tagName("body")));
            } catch (Exception e) {
                logger.warn("Page body not loaded within timeout, continuing anyway");
            }
            
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
            
            // 等待并截图每个元素
            List<BufferedImage> images = new ArrayList<>();
            
            for (String selector : selectors) {
                BufferedImage img = captureElement(driver, selector.trim(), wait);
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
            
            EdgeDriver driver = new EdgeDriver(options);
            driver.manage().timeouts().implicitlyWait(IMPLICIT_WAIT);
            
            return driver;
        } catch (Exception e) {
            logger.error("Failed to create WebDriver", e);
            return null;
        }
    }
    
    /**
     * 截取元素截图（使用显式等待）
     */
    private BufferedImage captureElement(WebDriver driver, String className, WebDriverWait wait) {
        try {
            // 等待元素存在
            List<WebElement> elements;
            try {
                wait.until(ExpectedConditions.presenceOfElementLocated(By.className(className)));
                elements = driver.findElements(By.className(className));
            } catch (Exception e) {
                logger.debug("Element not found after wait: {}", className);
                return null;
            }
            
            if (elements.isEmpty()) {
                logger.debug("Element not found: {}", className);
                return null;
            }
            
            WebElement element = elements.get(0);
            
            // 滚动到元素位置
            ((org.openqa.selenium.JavascriptExecutor) driver).executeScript(
                "arguments[0].scrollIntoView({block: 'start'});", element
            );
            
            // 等待元素可见
            try {
                wait.until(ExpectedConditions.visibilityOf(element));
            } catch (Exception e) {
                logger.debug("Element not visible: {}", className);
            }
            
            // 获取截图
            byte[] screenshot = element.getScreenshotAs(org.openqa.selenium.OutputType.BYTES);
            
            return ImageIO.read(new ByteArrayInputStream(screenshot));
            
        } catch (IOException | WebDriverException e) {
            logger.debug("Failed to capture element {}: {}", className, e.getMessage());
            return null;
        }
    }
}
