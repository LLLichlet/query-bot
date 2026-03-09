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
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * 图片处理工具类
 * 
 * 提供图片下载、处理、转换的便捷函数。
 * 对应 Python 版本的 plugins/utils/image.py
 */
public class ImageUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(ImageUtils.class);
    
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
     * 使用 NetworkUtils 进行 HTTP 请求。
     * 
     * @param url 图片 URL
     * @param timeoutSeconds 超时时间（秒）
     * @return BufferedImage 对象，下载失败时返回 null
     */
    public static BufferedImage downloadImage(String url, int timeoutSeconds) {
        try {
            byte[] bytes = NetworkUtils.getBytes(url, timeoutSeconds);
            if (bytes != null) {
                return ImageIO.read(new ByteArrayInputStream(bytes));
            }
            return null;
        } catch (Exception e) {
            logger.error("Error downloading image from {}: {}", url, e.getMessage());
            return null;
        }
    }
    
    /**
     * 异步下载图片
     * 
     * @param url 图片 URL
     * @return CompletableFuture<BufferedImage>
     */
    public static CompletableFuture<BufferedImage> downloadImageAsync(String url) {
        return downloadImageAsync(url, 10);
    }
    
    /**
     * 异步下载图片（带超时）
     * 
     * 使用 NetworkUtils 进行异步 HTTP 请求。
     * 
     * @param url 图片 URL
     * @param timeoutSeconds 超时时间（秒）
     * @return CompletableFuture<BufferedImage>
     */
    public static CompletableFuture<BufferedImage> downloadImageAsync(String url, int timeoutSeconds) {
        return NetworkUtils.getBytesAsync(url, timeoutSeconds)
                .thenApply(bytes -> {
                    if (bytes != null) {
                        try {
                            return ImageIO.read(new ByteArrayInputStream(bytes));
                        } catch (IOException e) {
                            logger.error("Error reading image from bytes: {}", e.getMessage());
                            return null;
                        }
                    }
                    return null;
                })
                .exceptionally(e -> {
                    logger.error("Error downloading image from {}: {}", url, e.getMessage());
                    return null;
                });
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
     * 将 BufferedImage 直接转为 CQ 码图片消息（纯函数）
     * 
     * 将图片编码为 Base64 并包装为 QQ 的 CQ 码格式。
     * 返回的字符串可直接通过 bot.sendGroupMsg() 或 bot.sendPrivateMsg() 发送。
     * 
     * @param image 图片对象
     * @return CQ 码字符串，转换失败返回 null
     */
    public static String imageToCQCode(BufferedImage image) {
        if (image == null) {
            return null;
        }
        String base64 = imageToBase64(image);
        if (base64 == null) {
            return null;
        }
        return createCQImage(base64);
    }
    
    /**
     * 将 BufferedImage 转为 CQ 码（指定格式）
     * 
     * @param image 图片对象
     * @param format 图片格式（PNG, JPEG 等）
     * @return CQ 码字符串，转换失败返回 null
     */
    public static String imageToCQCode(BufferedImage image, String format) {
        if (image == null) {
            return null;
        }
        String base64 = imageToBase64(image, format);
        if (base64 == null) {
            return null;
        }
        return createCQImage(base64);
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
     * 垂直合并多张图片
     * 
     * 将多张图片按垂直方向拼接，每张图片居中显示，背景填充白色。
     * 
     * @param images 图片列表
     * @return 合并后的图片，如果输入为空则返回 null
     */
    public static BufferedImage combineImagesVertically(List<BufferedImage> images) {
        if (images == null || images.isEmpty()) {
            return null;
        }
        
        // 过滤掉 null 图片
        List<BufferedImage> validImages = new ArrayList<>();
        for (BufferedImage img : images) {
            if (img != null) {
                validImages.add(img);
            }
        }
        
        if (validImages.isEmpty()) {
            return null;
        }
        
        if (validImages.size() == 1) {
            return validImages.get(0);
        }
        
        // 计算合并后的尺寸
        int width = 0;
        int totalHeight = 0;
        for (BufferedImage img : validImages) {
            width = Math.max(width, img.getWidth());
            totalHeight += img.getHeight();
        }
        
        // 创建新图片
        BufferedImage combined = new BufferedImage(
            width, totalHeight, BufferedImage.TYPE_INT_ARGB
        );
        
        Graphics2D g = combined.createGraphics();
        g.setColor(java.awt.Color.WHITE);
        g.fillRect(0, 0, width, totalHeight);
        
        // 绘制每张图片（居中）
        int yOffset = 0;
        for (BufferedImage img : validImages) {
            int x = (width - img.getWidth()) / 2;
            g.drawImage(img, x, yOffset, null);
            yOffset += img.getHeight();
        }
        
        g.dispose();
        return combined;
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
