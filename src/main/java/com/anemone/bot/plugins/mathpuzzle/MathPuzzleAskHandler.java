package com.anemone.bot.plugins.mathpuzzle;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * 数学谜题 - 提问处理器
 * 
 * 在游戏中提出是非问题来推理答案。
 * 
 * 触发方式:
 * - /ask [问题] - 提问
 * - /问 [问题] - 同上
 * 
 * Example:
 * /ask 这是一个数论概念吗？
 * /问 这个定理和费马有关吗？
 */
@Component
public class MathPuzzleAskHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    @Autowired
    public MathPuzzleAskHandler(PluginRegistry registry, BotConfig config) {
        super("数学谜题提问", "ask", Set.of("问"), "math_soup", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("empty_question", "Please enter a question, e.g., /ask Is this about geometry?");
        errorMessages.put("no_active_game", "No active game. Start one with /mathpuzzle first.");
        errorMessages.put("ask_failed", "Failed to process your question. Please try again later.");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "提出是非问题来推理答案", 
                "/ask (问) [问题] - 例如：/ask 这是一个数论概念吗？");
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 检查功能开关
        if (!config.isMathSoupEnabled()) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 只处理群聊
        if (!isGroup(event)) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 验证输入
        String question = args != null ? args.trim() : "";
        if (question.isEmpty()) {
            return reply(bot, event, getErrorMessage("empty_question"));
        }
        
        long groupId = event.getGroupId();
        MathPuzzleService service = MathPuzzleService.getInstance();
        
        // 检查游戏存在
        if (!service.hasActiveGame(groupId)) {
            return reply(bot, event, getErrorMessage("no_active_game"));
        }
        
        // 处理问题
        return service.askQuestion(groupId, question)
            .thenCompose(result -> {
                if (result.isFailure()) {
                    return reply(bot, event, getErrorMessage("ask_failed"));
                }
                
                return reply(bot, event, result.getValue());
            });
    }
}
