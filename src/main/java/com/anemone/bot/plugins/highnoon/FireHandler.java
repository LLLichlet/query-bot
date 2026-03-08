package com.anemone.bot.plugins.highnoon;

import java.util.Set;
import java.util.concurrent.CompletableFuture;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.protocols.BotServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;

import jakarta.annotation.PostConstruct;

/**
 * 午时已到 - 开枪处理器
 * 
 * 触发方式:
 * - /fire - 参与游戏并开枪
 * - /开枪 - 同上
 * 
 * 游戏流程:
 * 1. 先发送 /highnoon 开始游戏
 * 2. 参与者发送 /fire 轮流开枪
 * 3. 中弹者被禁言
 */
@Component
public class FireHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    @Autowired
    public FireHandler(PluginRegistry registry, BotConfig config) {
        super("开枪", "fire", Set.of("开枪"), "highnoon", 5, false, false);
        this.registry = registry;
        this.config = config;
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "午时已到游戏开枪命令", 
                "/fire (开枪) - 在已经开始的午时已到游戏中开枪");
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
        long userId = event.getUserId();
        String rawUsername = event.getSender().getCard();
        if (rawUsername == null || rawUsername.isEmpty()) {
            rawUsername = event.getSender().getNickname();
        }
        if (rawUsername == null || rawUsername.isEmpty()) {
            rawUsername = "User" + userId;
        }
        final String username = rawUsername;
        
        HighNoonService service = HighNoonService.getInstance();
        
        // 检查是否有活跃游戏
        if (!service.hasActiveGame(groupId)) {
            return reply(bot, event, getErrorMessage("no_active_game"));
        }
        
        // 执行开枪
        return service.fire(groupId, userId, username)
            .thenCompose(result -> {
                if (result.isFailure()) {
                    return reply(bot, event, getErrorMessage("fire_failed"));
                }
                
                HighNoonService.FireResult fireResult = result.getValue();
                BotServiceProtocol botService = ServiceLocator.get(BotServiceProtocol.class);
                
                if (botService == null) {
                    return reply(bot, event, getErrorMessage("bot_service_unavailable"));
                }
                
                if (fireResult.isHit()) {
                    // 中弹，执行禁言（1-10分钟）
                    return botService.banRandomDuration(groupId, userId, 1, 10)
                        .thenCompose(banResult -> {
                            if (banResult.isSuccess()) {
                                return send(bot, event, fireResult.message);
                            } else {
                                return send(bot, event, username + ",哀悼的钟声为你停下……");
                            }
                        })
                        .thenCompose(v -> send(bot, event, "钟摆落地,一切归于宁静"));
                } else {
                    // 未中弹，显示台词
                    return send(bot, event, fireResult.message);
                }
            });
    }
}
