package com.anemone.bot.utils;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.imageio.ImageIO;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Base64;

/**
 * 图片处理工具类
 * 
 * 提供图片下载、处理、转换的便捷函数。
 * 对应 Python 版本的 plugins/utils/image.py
 */
public class ImageUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(ImageUtils.class);
    
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    
    /**
     * 下载图片
     * 
     * @param url 图片 URL
     * @return BufferedImage 对象，下载失败时返回 null
     */
    public static BufferedImage downloadImage(String url) {
        return downloadImage(url, 10);
    }
    
    /**
     * 下载图片（带超时）
     * 
     * @param url 图片 URL
     * @param timeoutSeconds 超时时间（秒）
     * @return BufferedImage 对象，下载失败时返回 null
     */
    public static BufferedImage downloadImage(String url, int timeoutSeconds) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    .GET()
                    .build();
            
            HttpResponse<byte[]> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofByteArray());
            
            if (response.statusCode() == 200) {
                return ImageIO.read(new ByteArrayInputStream(response.body()));
            } else {
                logger.warn("Failed to download image from {}: HTTP {}", url, response.statusCode());
                return null;
            }
        } catch (Exception e) {
            logger.error("Error downloading image from {}: {}", url, e.getMessage());
            return null;
        }
    }
    
    /**
     * 将 BufferedImage 转为 Base64 字符串
     * 
     * @param image 图片
     * @param format 图片格式（PNG, JPEG 等）
     * @return Base64 编码的字符串
     */
    public static String imageToBase64(BufferedImage image, String format) {
        try {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, format, baos);
            byte[] imageBytes = baos.toByteArray();
            return Base64.getEncoder().encodeToString(imageBytes);
        } catch (IOException e) {
            logger.error("Failed to convert image to base64", e);
            return null;
        }
    }
    
    /**
     * 将 BufferedImage 转为 Base64 字符串（默认 PNG 格式）
     */
    public static String imageToBase64(BufferedImage image) {
        return imageToBase64(image, "PNG");
    }
    
    /**
     * 生成 CQ 码图片消息
     * 
     * @param base64Image Base64 编码的图片
     * @return CQ 码字符串
     */
    public static String createCQImage(String base64Image) {
        return "[CQ:image,file=base64://" + base64Image + "]";
    }
    
    /**
     * 合并多张图片（Alpha 通道合成）
     * 
     * @param baseImage 底图
     * @param overlays 要叠加的图片
     * @return 合并后的图片
     */
    public static BufferedImage mergeImages(BufferedImage baseImage, BufferedImage... overlays) {
        BufferedImage result = baseImage;
        for (BufferedImage overlay : overlays) {
            if (overlay != null) {
                result = alphaComposite(result, overlay);
            }
        }
        return result;
    }
    
    /**
     * Alpha 通道合成两张图片
     * 
     * @param bottom 底图
     * @param top 上层图
     * @return 合成后的图片
     */
    public static BufferedImage alphaComposite(BufferedImage bottom, BufferedImage top) {
        // 如果尺寸不同，调整上层图尺寸
        BufferedImage scaledTop = top;
        if (top.getWidth() != bottom.getWidth() || top.getHeight() != bottom.getHeight()) {
            scaledTop = resizeImage(top, bottom.getWidth(), bottom.getHeight());
        }
        
        // 创建新图片
        BufferedImage result = new BufferedImage(
                bottom.getWidth(), bottom.getHeight(), BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = result.createGraphics();
        
        // 绘制底图
        g.drawImage(bottom, 0, 0, null);
        
        // 绘制上层图
        g.drawImage(scaledTop, 0, 0, null);
        
        g.dispose();
        return result;
    }
    
    /**
     * 调整图片大小
     * 
     * @param image 原图
     * @param width 目标宽度
     * @param height 目标高度
     * @return 调整后的图片
     */
    public static BufferedImage resizeImage(BufferedImage image, int width, int height) {
        BufferedImage result = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = result.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g.drawImage(image, 0, 0, width, height, null);
        g.dispose();
        return result;
    }
    
    /**
     * 裁剪图片
     * 
     * @param image 原图
     * @param x 起始 X
     * @param y 起始 Y
     * @param width 宽度
     * @param height 高度
     * @return 裁剪后的图片
     */
    public static BufferedImage cropImage(BufferedImage image, int x, int y, int width, int height) {
        return image.getSubimage(x, y, width, height);
    }
    
    /**
     * 创建空白图片
     * 
     * @param width 宽度
     * @param height 高度
     * @return 空白图片
     */
    public static BufferedImage createEmptyImage(int width, int height) {
        return new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
    }
    
    /**
     * 图片处理器类 - 链式操作
     */
    public static class ImageProcessor {
        private BufferedImage image;
        
        public ImageProcessor(BufferedImage image) {
            this.image = image;
        }
        
        /**
         * 调整大小
         */
        public ImageProcessor resize(int width, int height) {
            this.image = resizeImage(this.image, width, height);
            return this;
        }
        
        /**
         * 裁剪
         */
        public ImageProcessor crop(int x, int y, int width, int height) {
            this.image = cropImage(this.image, x, y, width, height);
            return this;
        }
        
        /**
         * 合并其他图片
         */
        public ImageProcessor merge(BufferedImage... overlays) {
            this.image = mergeImages(this.image, overlays);
            return this;
        }
        
        /**
         * 转为 Base64
         */
        public String toBase64(String format) {
            return imageToBase64(this.image, format);
        }
        
        /**
         * 转为 Base64（默认 PNG）
         */
        public String toBase64() {
            return toBase64("PNG");
        }
        
        /**
         * 生成 CQ 码
         */
        public String toCQCode() {
            return createCQImage(toBase64());
        }
        
        /**
         * 获取图片
         */
        public BufferedImage getImage() {
            return this.image;
        }
    }
}
