package com.anemone.bot.utils;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;

import javax.swing.JLabel;

import cn.hutool.http.HtmlUtil;

import org.scilab.forge.jlatexmath.ParseException;
import org.scilab.forge.jlatexmath.TeXConstants;
import org.scilab.forge.jlatexmath.TeXFormula;
import org.scilab.forge.jlatexmath.TeXIcon;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * LaTeX 渲染工具类
 * 
 * 提供将 LaTeX 数学表达式渲染为图片的纯函数工具。
 * 使用 JLaTeXMath 库实现，采用 2x 超采样技术提高清晰度。
 * 
 * 对应功能：将 LaTeX 字符串 → BufferedImage
 */
public class LatexUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(LatexUtils.class);
    
    /** 默认字体大小（增大以提高清晰度） */
    public static final int DEFAULT_FONT_SIZE = 48;
    
    /** 默认样式（0=普通, 1=粗体, 2=意大利, 3=粗斜体） */
    public static final int DEFAULT_STYLE = TeXConstants.STYLE_DISPLAY;
    
    /** 默认背景颜色 */
    public static final Color DEFAULT_BG_COLOR = Color.WHITE;
    
    /** 默认前景颜色 */
    public static final Color DEFAULT_FG_COLOR = Color.BLACK;
    
    /** 图片边距（像素） */
    public static final int DEFAULT_PADDING = 10;
    
    /** 超采样倍数（4x 超采样，显著提升清晰度） */
    private static final int SUPER_SAMPLING_SCALE = 4;
    
    /**
     * 将 LaTeX 表达式渲染为图片（纯函数）
     * 
     * 输入 LaTeX 数学表达式字符串，输出渲染后的 BufferedImage。
     * 使用 2x 超采样技术提高渲染清晰度。
     * 
     * @param latex LaTeX 表达式（如 "x^2 + y^2 = z^2"）
     * @return 渲染后的图片，失败返回 null
     */
    public static BufferedImage latexToImage(String latex) {
        return latexToImage(latex, DEFAULT_FONT_SIZE, DEFAULT_BG_COLOR, DEFAULT_FG_COLOR);
    }
    
    /**
     * 将 LaTeX 表达式渲染为图片（自定义字体大小）
     * 
     * @param latex LaTeX 表达式
     * @param fontSize 字体大小
     * @return 渲染后的图片，失败返回 null
     */
    public static BufferedImage latexToImage(String latex, int fontSize) {
        return latexToImage(latex, fontSize, DEFAULT_BG_COLOR, DEFAULT_FG_COLOR);
    }
    
    /**
     * 将 LaTeX 表达式渲染为图片（完整参数，使用 2x 超采样）
     * 
     * @param latex LaTeX 表达式
     * @param fontSize 字体大小
     * @param bgColor 背景颜色
     * @param fgColor 前景（文字）颜色
     * @return 渲染后的图片，失败返回 null
     */
    public static BufferedImage latexToImage(String latex, int fontSize, Color bgColor, Color fgColor) {
        if (latex == null || latex.trim().isEmpty()) {
            logger.warn("LaTeX expression is empty");
            return null;
        }
        
        // HTML 实体解码（处理 &amp;, &lt;, &gt; 等）
        latex = HtmlUtil.unescape(latex);
        
        try {
            // 以 2x 分辨率渲染（超采样）
            int superFontSize = fontSize * SUPER_SAMPLING_SCALE;
            int superPadding = DEFAULT_PADDING * SUPER_SAMPLING_SCALE;
            
            // 创建 LaTeX 公式对象
            TeXFormula formula = new TeXFormula(latex);
            
            // 创建图标（以高分辨率渲染）
            TeXIcon icon = formula.createTeXIcon(DEFAULT_STYLE, superFontSize);
            
            // 计算高分辨率图片尺寸
            int superWidth = icon.getIconWidth() + 2 * superPadding;
            int superHeight = icon.getIconHeight() + 2 * superPadding;
            
            // 计算目标尺寸
            int targetWidth = superWidth / SUPER_SAMPLING_SCALE;
            int targetHeight = superHeight / SUPER_SAMPLING_SCALE;
            
            // 创建高分辨率图片
            BufferedImage highResImage = new BufferedImage(superWidth, superHeight, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g2d = highResImage.createGraphics();
            
            // 设置高质量渲染参数
            setupHighQualityRendering(g2d);
            
            // 填充背景
            g2d.setColor(bgColor);
            g2d.fillRect(0, 0, superWidth, superHeight);
            
            // 绘制公式
            g2d.setColor(fgColor);
            icon.paintIcon(new JLabel(), g2d, superPadding, superPadding);
            
            g2d.dispose();
            
            // 高质量缩放到目标尺寸
            BufferedImage finalImage = resizeImageHighQuality(highResImage, targetWidth, targetHeight);
            
            logger.debug("LaTeX rendered with supersampling: {} -> {}x{}px (target: {}x{}px)", 
                latex, superWidth, superHeight, targetWidth, targetHeight);
            return finalImage;
            
        } catch (ParseException e) {
            logger.error("Failed to render LaTeX: {}", latex, e);
            return null;
        }
    }
    
    /**
     * 设置高质量渲染参数
     */
    private static void setupHighQualityRendering(Graphics2D g2d) {
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_LCD_HRGB);
        g2d.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        g2d.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);
        g2d.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON);
    }
    
    /**
     * 高质量图片缩放（使用双三次插值）
     */
    private static BufferedImage resizeImageHighQuality(BufferedImage source, int targetWidth, int targetHeight) {
        // 使用多步缩放以获得更好的质量（4x -> 2x -> 1x）
        BufferedImage tempImage = source;
        int currentWidth = source.getWidth();
        int currentHeight = source.getHeight();
        
        // 逐步缩放，每次最多缩小一半
        while (currentWidth > targetWidth * 2 || currentHeight > targetHeight * 2) {
            int nextWidth = Math.max(currentWidth / 2, targetWidth);
            int nextHeight = Math.max(currentHeight / 2, targetHeight);
            
            BufferedImage nextImage = new BufferedImage(nextWidth, nextHeight, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g2d = nextImage.createGraphics();
            g2d.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            g2d.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2d.drawImage(tempImage, 0, 0, nextWidth, nextHeight, null);
            g2d.dispose();
            
            if (tempImage != source) {
                tempImage.flush();
            }
            tempImage = nextImage;
            currentWidth = nextWidth;
            currentHeight = nextHeight;
        }
        
        // 最后一步缩放到目标尺寸
        if (currentWidth != targetWidth || currentHeight != targetHeight) {
            BufferedImage finalImage = new BufferedImage(targetWidth, targetHeight, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g2d = finalImage.createGraphics();
            g2d.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            g2d.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2d.drawImage(tempImage, 0, 0, targetWidth, targetHeight, null);
            g2d.dispose();
            
            if (tempImage != source) {
                tempImage.flush();
            }
            return finalImage;
        }
        
        return tempImage;
    }
    
    /**
     * 验证 LaTeX 表达式是否有效
     * 
     * @param latex LaTeX 表达式
     * @return true 如果表达式可以被渲染
     */
    public static boolean isValidLatex(String latex) {
        if (latex == null || latex.trim().isEmpty()) {
            return false;
        }
        try {
            // create formula object to validate syntax (warning: new instance ignored)
            @SuppressWarnings("unused")
            TeXFormula formula = new TeXFormula(latex);
            // formula variable is intentionally unused beyond validation
            return true;
        } catch (ParseException e) {
            return false;
        }
    }
    
    /**
     * 清理 LaTeX 表达式（去除可能导致问题的字符）
     * 
     * @param latex 原始表达式
     * @return 清理后的表达式
     */
    public static String sanitizeLatex(String latex) {
        if (latex == null) {
            return "";
        }
        // 移除可能导致安全问题的命令
        return latex.trim()
                .replaceAll("\\\\input\\{[^}]*\\}", "")  // 移除 \input{}
                .replaceAll("\\\\include\\{[^}]*\\}", "") // 移除 \include{}
                .replaceAll("\\\\write\\{[^}]*\\}", "")   // 移除 \write{}
                .replaceAll("\\\\openout[^\\s]*", "");    // 移除 \openout
    }
}
