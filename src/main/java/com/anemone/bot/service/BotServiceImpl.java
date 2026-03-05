package com.anemone.bot.service;

import com.anemone.bot.base.Result;
import com.anemone.bot.protocols.BotServiceProtocol;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.core.BotContainer;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Random;
import java.util.concurrent.CompletableFuture;

/**
 * Bot API 服务实现
 * 
 * 封装 cq-bot 的群管理 API 调用。
 */
@Service
public class BotServiceImpl implements BotServiceProtocol {
    
    private final BotContainer botContainer;
    private final Random random = new Random();
    
    @Autowired
    public BotServiceImpl(BotContainer botContainer) {
        this.botContainer = botContainer;
    }
    
    @Override
    public CompletableFuture<Result<Boolean>> sendGroupMessage(long groupId, String message, boolean atUser) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 获取 Bot 实例（假设只有一个 Bot）
                Bot bot = botContainer.robots.values().stream().findFirst().orElse(null);
                if (bot == null) {
                    return Result.err("Bot not connected");
                }
                
                String msg = message;
                // 注意：@全体成员 [CQ:at,qq=all] 需要管理员权限，容易风控
                // 建议使用普通消息或只 @ 发送者
                
                bot.sendGroupMsg(groupId, msg, false);
                return Result.ok(true);
            } catch (Exception e) {
                return Result.err("Failed to send message: " + e.getMessage());
            }
        });
    }
    
    @Override
    public CompletableFuture<Result<Boolean>> banUser(long groupId, long userId, int duration) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                Bot bot = botContainer.robots.values().stream().findFirst().orElse(null);
                if (bot == null) {
                    return Result.err("Bot not connected");
                }
                
                bot.setGroupBan(groupId, userId, duration);
                return Result.ok(true);
            } catch (Exception e) {
                return Result.err("Failed to ban user: " + e.getMessage());
            }
        });
    }
    
    @Override
    public CompletableFuture<Result<Integer>> banRandomDuration(long groupId, long userId, int minMinutes, int maxMinutes) {
        int durationSeconds = (random.nextInt(maxMinutes - minMinutes + 1) + minMinutes) * 60;
        return banUser(groupId, userId, durationSeconds)
                .thenApply(result -> result.isSuccess() ? Result.ok(durationSeconds) : Result.err(result.getError()));
    }
}
