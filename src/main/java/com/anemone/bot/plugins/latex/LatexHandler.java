package com.anemone.bot.plugins.latex;

import java.awt.image.BufferedImage;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.service.PluginRegistry;
import com.anemone.bot.utils.ImageUtils;
import com.anemone.bot.utils.LatexUtils;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;

import jakarta.annotation.PostConstruct;

/**
 * LaTeX 公式渲染插件
 * 
 * 将 LaTeX 数学表达式渲染为图片并发送。
 * 支持数学公式、矩阵、分数、积分等各种 LaTeX 语法。
 * 
 * 触发方式:
 * - /latex <表达式> - 渲染 LaTeX 公式
 * - /公式 <表达式> - 同上
 * 
 * 示例:
 * - /latex x^2 + y^2 = z^2
 * - /latex \\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}
 * - /latex \\int_{0}^{\\infty} e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}
 * - /latex \\begin{pmatrix} a & b \\ c & d \\end{pmatrix}
 * 
 * 配置:
 * anemone.bot.latex-enabled=true/false  # 功能开关
 */
@Component
public class LatexHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    // CPU 密集型任务使用专用线程池（避免阻塞 common pool）
    private final ExecutorService renderExecutor = Executors.newFixedThreadPool(2, r -> {
        Thread t = new Thread(r, "latex-render-" + System.nanoTime());
        t.setDaemon(true);
        return t;
    });
    
    @Autowired
    public LatexHandler(PluginRegistry registry, BotConfig config) {
        super("LaTeX Renderer", "latex", Set.of("formula"), "latex", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("empty_input", """
                                         Please provide a LaTeX expression
                                         Usage: /latex [expression]
                                         Example: /latex x^2 + y^2 = z^2""");
        errorMessages.put("invalid_latex", """
                                           Invalid LaTeX syntax. Please check your expression.
                                           Common issues: unmatched braces, unknown commands""");
        errorMessages.put("render_failed", """
                                           Failed to render the formula. Please check:
                                           1. Syntax is correct (e.g., use \\frac{a}{b} for fractions)
                                           2. No unsupported commands""");
        errorMessages.put("timeout", 
            "Rendering timeout. Expression too complex or system busy.");
        errorMessages.put("unsupported", 
            "Expression contains unsupported commands or characters.");
    }
    
    /**
     * 应用关闭时清理线程池
     */
    @jakarta.annotation.PreDestroy
    public void destroy() {
        renderExecutor.shutdown();
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, 
            "Render LaTeX mathematical expressions as images", 
            "/latex [expression]\nExamples:\n/latex x^2 + y^2 = z^2\n/latex \\sum_{i=1}^{n} i^2"
        );
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 检查功能开关
        if (!config.isEnabled("latex")) {
            logger.debug("LaTeX feature is disabled");
            return CompletableFuture.completedFuture(null);
        }
        
        // 验证输入
        if (args == null || args.trim().isEmpty()) {
            return reply(bot, event, getErrorMessage("empty_input"));
        }
        
        final String latex = LatexUtils.sanitizeLatex(args.trim());
        
        // 验证 LaTeX 是否有效
        if (!LatexUtils.isValidLatex(latex)) {
            return reply(bot, event, getErrorMessage("invalid_latex"));
        }
        
        // 异步渲染（使用专用线程池，避免阻塞 common pool）
        return CompletableFuture.supplyAsync(() -> {
            // 纯函数：LaTeX 字符串 → 图片
            BufferedImage image = LatexUtils.latexToImage(latex);
            
            if (image == null) {
                throw new RuntimeException("render_failed");
            }
            
            // 纯函数：图片 → CQ 码
            String cqCode = ImageUtils.imageToCQCode(image);
            
            if (cqCode == null) {
                throw new RuntimeException("render_failed");
            }
            
            return cqCode;
        }, renderExecutor).thenCompose(cqCode -> {
            // 发送图片
            return send(bot, event, cqCode);
        }).exceptionally(e -> {
            logger.error("Failed to render LaTeX", e);
            Throwable cause = e.getCause();
            String errorMsg = cause != null && cause.getMessage() != null
                    ? getErrorMessage(cause.getMessage())
                    : getErrorMessage("render_failed");
            reply(bot, event, errorMsg);
            return null;
        });
    }
}
