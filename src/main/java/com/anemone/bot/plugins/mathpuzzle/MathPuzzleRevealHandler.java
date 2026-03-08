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
 * 数学谜题 - 揭示答案处理器
 * 
 * 揭示答案并结束游戏。
 * 
 * 触发方式:
 * - /reveal - 揭示答案
 * - /答案 - 同上
 * - /不猜了 - 同上
 * - /揭晓 - 同上
 */
@Component
public class MathPuzzleRevealHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    @Autowired
    public MathPuzzleRevealHandler(PluginRegistry registry, BotConfig config) {
        super("数学谜题答案", "reveal", Set.of("答案", "不猜了", "揭晓"), "math_soup", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("no_active_game", "No active game. Start one with /mathpuzzle first.");
        errorMessages.put("game_state_error", "Game state error.");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "揭示答案并结束游戏", 
                "/reveal (答案/不猜了/揭晓) - 显示答案并结束当前游戏");
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
        
        // 获取游戏并验证状态
        MathPuzzleState game = service.getGame(groupId);
        if (game == null || !game.isActive) {
            return reply(bot, event, getErrorMessage("no_active_game"));
        }
        
        if (game.getConcept() == null) {
            return reply(bot, event, getErrorMessage("game_state_error"));
        }
        
        MathConcept concept = game.getConcept();
        
        // 结束游戏
        service.endGame(groupId);
        
        // 构建回复
        StringBuilder msg = new StringBuilder();
        msg.append(String.format("Answer: %s\n", concept.getAnswer()));
        
        if (!concept.getDescription().isEmpty()) {
            msg.append(concept.getDescription()).append("\n");
        }
        
        msg.append(game.getStats());
        
        return reply(bot, event, msg.toString());
    }
}
