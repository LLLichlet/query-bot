package com.anemone.bot.plugins.highnoon;

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
 * 午时已到 - 开始游戏处理器
 * 
 * 触发方式:
 * - /highnoon - 开始新游戏
 * - /午时已到 - 同上
 * 
 * 游戏说明:
 * - 子弹随机装载在 1-6 的某个位置
 * - 参与者轮流开枪，每次扣动扳机
 * - 中弹者被随机禁言 1-10 分钟
 * - 最多 5 轮安全射击（第 6 轮必中）
 */
@Component
public class HighNoonStartHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    @Autowired
    public HighNoonStartHandler(PluginRegistry registry, BotConfig config) {
        super("决斗", "highnoon", Set.of("午时已到"), "highnoon", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("game_in_progress", "A game is already in progress. Use /reveal to end it first.");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "俄罗斯轮盘赌禁言游戏", 
                "/highnoon (午时已到) - 开始游戏，/fire (开枪) - 参与");
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 检查功能开关
        if (!config.isHighnoonEnabled()) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 只处理群聊
        if (!isGroup(event)) {
            return CompletableFuture.completedFuture(null);
        }
        
        long groupId = event.getGroupId();
        HighNoonService service = HighNoonService.getInstance();
        
        // 检查是否已有游戏在进行
        if (service.hasActiveGame(groupId)) {
            return reply(bot, event, getErrorMessage("game_in_progress"));
        }
        
        // 开始新游戏
        return service.startGame(groupId)
            .thenCompose(result -> {
                if (result.isFailure()) {
                    return reply(bot, event, "Failed to start game: " + result.getError());
                }
                
                HighNoonState game = result.getValue();
                
                // 调试模式显示子弹位置
                if (config.isDebugMode() || config.isDebugHighnoon()) {
                    String msg = String.format("午时已到\n（调试：子弹位置=%d）", game.bulletPos);
                    return send(bot, event, msg);
                } else {
                    return send(bot, event, "午时已到");
                }
            });
    }
}
