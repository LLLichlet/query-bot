package com.anemone.bot.plugins.math;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.protocols.AIServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.service.PluginRegistry;
import com.anemone.bot.utils.PromptUtils;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * 数学定义查询插件
 * 
 * 查询数学名词的定义和解释，使用香蕉空间风格。
 * 支持中英法德俄日多语言回复。
 * 
 * 触发方式:
 * - /define [数学名词] - 查询数学定义
 * - /定义 [数学名词] - 同上
 * 
 * 配置:
 * anemone.bot.math-enabled=true/false  # 功能开关
 * anemone.bot.math-temperature=0.3     # AI 温度
 * anemone.bot.math-max-tokens=512      # 最大 token
 * anemone.bot.math-top-p=0.8           # Top-p 参数
 */
@Component
public class MathDefinitionHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    /**
     * 系统提示词缓存
     */
    private String systemPrompt;
    
    @Autowired
    public MathDefinitionHandler(PluginRegistry registry, BotConfig config) {
        super("数学定义查询", "define", Set.of("定义"), "math", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("empty_input", "请输入要查询的数学名词");
        errorMessages.put("prompt_not_found", "系统提示词文件不存在，请联系管理员");
        errorMessages.put("ai_not_initialized", "AI 服务未初始化");
        errorMessages.put("ai_not_configured", "AI 服务未配置，无法查询");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "查询数学名词的定义和解释，支持多语言", 
                "/define [数学名词]");
        
        // 预加载提示词
        loadPrompt();
    }
    
    /**
     * 加载系统提示词
     */
    private void loadPrompt() {
        systemPrompt = PromptUtils.readPrompt("math_def");
        if (systemPrompt == null) {
            logger.error("Failed to load math_def prompt");
        } else {
            logger.info("Loaded math_def prompt ({} chars)", systemPrompt.length());
        }
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 检查功能开关
        if (!config.isEnabled("math")) {
            logger.debug("Math definition feature is disabled");
            return CompletableFuture.completedFuture(null);
        }
        
        // 验证输入
        if (args == null || args.trim().isEmpty()) {
            return reply(bot, event, getErrorMessage("empty_input"));
        }
        
        String query = args.trim();
        
        // 检查提示词
        if (systemPrompt == null) {
            // 尝试重新加载
            loadPrompt();
            if (systemPrompt == null) {
                return reply(bot, event, getErrorMessage("prompt_not_found"));
            }
        }
        
        // 获取 AI 服务
        AIServiceProtocol ai = ServiceLocator.get(AIServiceProtocol.class);
        if (ai == null) {
            return reply(bot, event, getErrorMessage("ai_not_initialized"));
        }
        if (!ai.isAvailable()) {
            return reply(bot, event, getErrorMessage("ai_not_configured"));
        }
        
        // 调用 AI
        return ai.chat(
                systemPrompt,
                query,
                config.getMathTemperature(),
                config.getMathMaxTokens(),
                config.getMathTopP()
        ).thenCompose(result -> {
            if (result.isSuccess()) {
                return reply(bot, event, result.getValue());
            } else {
                return reply(bot, event, "查询失败: " + result.getError());
            }
        }).exceptionally(e -> {
            logger.error("Math definition query failed", e);
            reply(bot, event, "查询失败: " + e.getMessage());
            return null;
        });
    }
}
