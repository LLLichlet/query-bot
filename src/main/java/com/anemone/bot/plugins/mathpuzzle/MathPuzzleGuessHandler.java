package com.anemone.bot.plugins.mathpuzzle;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * 数学谜题 - 猜测处理器
 * 
 * 直接猜测答案。
 * 
 * 触发方式:
 * - /guess [答案] - 猜测
 * - /猜 [答案] - 同上
 * 
 * Example:
 * /guess 费马大定理
 * /猜 欧拉公式
 */
@Component
public class MathPuzzleGuessHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    @Autowired
    public MathPuzzleGuessHandler(PluginRegistry registry, BotConfig config) {
        super("数学谜题猜测", "guess", Set.of("猜"), "math_soup", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("empty_guess", "Please enter your guess, e.g., /guess Euler's formula");
        errorMessages.put("no_active_game", "No active game. Start one with /mathpuzzle first.");
        errorMessages.put("guess_failed", "Failed to process your guess. Please try again later.");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "直接猜测答案", 
                "/guess (猜) [答案] - 例如：/guess 费马大定理");
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
        String guess = args != null ? args.trim() : "";
        if (guess.isEmpty()) {
            return reply(bot, event, getErrorMessage("empty_guess"));
        }
        
        long groupId = event.getGroupId();
        MathPuzzleService service = MathPuzzleService.getInstance();
        
        // 检查游戏存在
        if (!service.hasActiveGame(groupId)) {
            return reply(bot, event, getErrorMessage("no_active_game"));
        }
        
        // 处理猜测
        return service.makeGuess(groupId, guess)
            .thenCompose(result -> {
                if (result.isFailure()) {
                    return reply(bot, event, getErrorMessage("guess_failed"));
                }
                
                Map<String, Object> data = result.getValue();
                boolean correct = (Boolean) data.get("correct");
                
                if (correct) {
                    String answer = (String) data.get("answer");
                    String description = (String) data.get("description");
                    
                    StringBuilder msg = new StringBuilder();
                    msg.append(String.format("Correct! The answer is %s.\n", answer));
                    if (description != null && !description.isEmpty()) {
                        msg.append(description);
                    }
                    
                    return reply(bot, event, msg.toString());
                } else {
                    double similarity = (Double) data.get("similarity");
                    if (similarity > 50) {
                        return reply(bot, event, String.format("Close! Similarity: %.0f%%", similarity));
                    } else {
                        return reply(bot, event, "Wrong.");
                    }
                }
            });
    }
}
