package com.anemone.bot.protocols;

import com.anemone.bot.base.Result;

import java.util.concurrent.CompletableFuture;

/**
 * Bot API 服务协议
 * 
 * 封装 cq-bot 的群管理 API 调用。
 * 
 * Example:
 * <pre>{@code
 * BotServiceProtocol bot = ServiceLocator.get(BotServiceProtocol.class);
 * bot.sendMessage(groupId, "Hello", true);
 * bot.banUser(groupId, userId, 300);  // 禁言5分钟
 * }</pre>
 */
public interface BotServiceProtocol {
    
    /**
     * 发送群消息
     * 
     * @param groupId 群号
     * @param message 消息内容
     * @param atUser 是否@发送者
     * @return 发送结果
     */
    CompletableFuture<Result<Boolean>> sendGroupMessage(long groupId, String message, boolean atUser);
    
    /**
     * 发送群消息（不@）
     * 
     * @param groupId 群号
     * @param message 消息内容
     * @return 发送结果
     */
    default CompletableFuture<Result<Boolean>> sendGroupMessage(long groupId, String message) {
        return sendGroupMessage(groupId, message, false);
    }
    
    /**
     * 禁言用户
     * 
     * @param groupId 群号
     * @param userId 用户 QQ 号
     * @param duration 禁言时长（秒）
     * @return 操作结果
     */
    CompletableFuture<Result<Boolean>> banUser(long groupId, long userId, int duration);
    
    /**
     * 随机时长禁言用户
     * 
     * @param groupId 群号
     * @param userId 用户 QQ 号
     * @param minMinutes 最小分钟数
     * @param maxMinutes 最大分钟数
     * @return 操作结果
     */
    CompletableFuture<Result<Integer>> banRandomDuration(long groupId, long userId, int minMinutes, int maxMinutes);
}
