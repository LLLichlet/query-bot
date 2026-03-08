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
 * 数学谜题 - 开始游戏处理器
 * 
 * AI 在心中选定一个数学概念（定理、公式、人物或对象），
 * 玩家通过最多 20 个是非问题来推理出答案。
 * 
 * 触发方式:
 * - /mathpuzzle - 开始新游戏
 * - /数学谜 - 同上
 * 
 * 相关命令:
 * - /ask (问) [问题] - 提问
 * - /guess (猜) [答案] - 猜测
 * - /reveal (答案) - 揭示答案
 */
@Component
public class MathPuzzleStartHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    private final ConceptRepository repository;
    
    @Autowired
    public MathPuzzleStartHandler(PluginRegistry registry, BotConfig config, ConceptRepository repository) {
        super("数学谜题", "mathpuzzle", Set.of("数学谜"), "math_soup", 10, true, false);
        this.registry = registry;
        this.config = config;
        this.repository = repository;
        
        // 注册错误消息
        errorMessages.put("game_in_progress", "A game is already in progress! Use /reveal to end it before starting a new one.");
        errorMessages.put("start_game_failed", "Failed to start game. Please try again later.");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "通过是非问题猜测数学概念的猜谜游戏", 
                "/mathpuzzle (数学谜) - 开始游戏，/ask (问) [问题] - 提问，/guess (猜) [答案] - 猜测");
        
        // 设置 MathPuzzleService 的依赖
        MathPuzzleService.getInstance().setDependencies(repository, config);
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
        
        long groupId = event.getGroupId();
        MathPuzzleService service = MathPuzzleService.getInstance();
        
        // 检查是否已有游戏在进行
        if (service.hasActiveGame(groupId)) {
            return reply(bot, event, getErrorMessage("game_in_progress"));
        }
        
        // 开始新游戏
        return service.startGame(groupId)
            .thenCompose(result -> {
                if (result.isFailure()) {
                    return reply(bot, event, getErrorMessage("start_game_failed"));
                }
                
                MathPuzzleState game = result.getValue();
                StringBuilder msg = new StringBuilder("Math puzzle started!");
                
                // 调试模式：显示答案
                if (config.isDebugMode() || config.isDebugMathSoup()) {
                    if (game.getConcept() != null) {
                        msg.append(String.format(" [Debug: %s]", game.getConcept().getAnswer()));
                    }
                }
                
                return reply(bot, event, msg.toString());
            });
    }
}
