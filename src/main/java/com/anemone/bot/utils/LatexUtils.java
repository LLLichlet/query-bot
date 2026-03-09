package com.anemone.bot.utils;

import org.scilab.forge.jlatexmath.TeXConstants;
import org.scilab.forge.jlatexmath.TeXFormula;
import org.scilab.forge.jlatexmath.TeXIcon;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;

/**
 * LaTeX 渲染工具类
 * 
 * 提供将 LaTeX 数学表达式渲染为图片的纯函数工具。
 * 使用 JLaTeXMath 库实现。
 * 
 * 对应功能：将 LaTeX 字符串 → BufferedImage
 */
public class LatexUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(LatexUtils.class);
    
    /** 默认字体大小 */
    public static final int DEFAULT_FONT_SIZE = 20;
    
    /** 默认样式（0=普通, 1=粗体, 2=意大利, 3=粗斜体） */
    public static final int DEFAULT_STYLE = TeXConstants.STYLE_DISPLAY;
    
    /** 默认背景颜色 */
    public static final Color DEFAULT_BG_COLOR = Color.WHITE;
    
    /** 默认前景颜色 */
    public static final Color DEFAULT_FG_COLOR = Color.BLACK;
    
    /** 图片边距（像素） */
    public static final int DEFAULT_PADDING = 10;
    
    /**
     * 将 LaTeX 表达式渲染为图片（纯函数）
     * 
     * 输入 LaTeX 数学表达式字符串，输出渲染后的 BufferedImage。
     * 这是一个纯函数，无副作用，相同输入必得相同输出。
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
     * 将 LaTeX 表达式渲染为图片（完整参数）
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
        
        try {
            // 创建 LaTeX 公式对象
            TeXFormula formula = new TeXFormula(latex);
            
            // 创建图标（渲染公式）
            TeXIcon icon = formula.createTeXIcon(DEFAULT_STYLE, fontSize);
            
            // 计算图片尺寸（加上边距）
            int width = icon.getIconWidth() + 2 * DEFAULT_PADDING;
            int height = icon.getIconHeight() + 2 * DEFAULT_PADDING;
            
            // 创建图片
            BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g2d = image.createGraphics();
            
            // 设置抗锯齿
            g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g2d.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
            
            // 填充背景
            g2d.setColor(bgColor);
            g2d.fillRect(0, 0, width, height);
            
            // 绘制公式
            g2d.setColor(fgColor);
            icon.paintIcon(new JLabel(), g2d, DEFAULT_PADDING, DEFAULT_PADDING);
            
            g2d.dispose();
            
            logger.debug("LaTeX rendered successfully: {} -> {}x{}px", latex, width, height);
            return image;
            
        } catch (Exception e) {
            logger.error("Failed to render LaTeX: {}", latex, e);
            return null;
        }
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
            new TeXFormula(latex);
            return true;
        } catch (Exception e) {
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
