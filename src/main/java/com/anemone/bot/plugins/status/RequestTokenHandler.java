package com.anemone.bot.plugins.status;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.protocols.TokenServiceProtocol;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * 申请令牌处理器（私聊）
 * 
 * 管理员私聊申请管理员操作令牌，5分钟内有效。
 * 
 * 触发方式:
 * - /token - 申请令牌（仅私聊）
 * - /申请令牌 - 同上
 * 
 * 使用方式:
 * 1. 私聊发送 /token
 * 2. 获取令牌后在群内发送: /admin [令牌] [操作] [参数]
 */
@Component
public class RequestTokenHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    @Autowired
    public RequestTokenHandler(PluginRegistry registry, BotConfig config) {
        super("申请令牌", "token", Set.of("申请令牌"), null, 10, true, true);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("not_private_chat", "Please send this command in private chat");
        errorMessages.put("not_admin", "You don't have admin permission");
        errorMessages.put("token_service_unavailable", "Token service unavailable");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "私聊申请管理员操作令牌（5分钟有效）", 
                "私聊: /token (申请令牌)");
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 只处理私聊（群号为空或为0表示私聊）
        Long groupId = event.getGroupId();
        if (groupId != null && groupId > 0) {
            return reply(bot, event, getErrorMessage("not_private_chat"));
        }
        
        long userId = event.getUserId();
        
        // 检查是否为管理员
        if (!config.getAdminUserIdsSet().contains(userId)) {
            return reply(bot, event, getErrorMessage("not_admin"));
        }
        
        // 获取令牌服务
        TokenServiceProtocol tokenService = ServiceLocator.get(TokenServiceProtocol.class);
        if (tokenService == null) {
            return reply(bot, event, getErrorMessage("token_service_unavailable"));
        }
        
        // 生成令牌
        String token = tokenService.generateToken(userId);
        
        // 发送令牌信息
        StringBuilder msg = new StringBuilder();
        msg.append("Your token: ").append(token).append("\n");
        msg.append("Valid for: 5 minutes\n");
        msg.append("Usage: Send \"admin ").append(token).append(" [operation]\" in group\n");
        msg.append("Available: toggle/ban/unban/status/system");
        
        return send(bot, event, msg.toString());
    }
}
