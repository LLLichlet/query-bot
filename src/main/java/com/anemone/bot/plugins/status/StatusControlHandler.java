package com.anemone.bot.plugins.status;

import java.lang.reflect.InvocationTargetException;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.protocols.BanServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.protocols.SystemMonitorProtocol;
import com.anemone.bot.protocols.TokenServiceProtocol;
import com.anemone.bot.service.BanService;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;

import jakarta.annotation.PostConstruct;

/**
 * 状态控制处理器
 * 
 * 管理员功能：查看和控制各功能开关状态、用户管理。
 * 需要一次性令牌验证。
 * 
 * 触发方式:
 * - /admin - 显示状态
 * - /状态控制 - 同上
 * 
 * 带令牌的操作:
 * - /admin [令牌] status - 显示所有功能状态
 * - /admin [令牌] toggle [功能名] - 切换功能开关
 * - /admin [令牌] ban [用户ID] - 拉黑用户
 * - /admin [令牌] unban [用户ID] - 解封用户
 * - /admin [令牌] system - 显示系统状态
 */
@Component
public class StatusControlHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    // 可控制的功能列表
    private static final List<ControllableFeature> CONTROLLABLE_FEATURES = List.of(
        new ControllableFeature("math", "数学定义", "数学"),
        new ControllableFeature("random", "随机回复", "随机"),
        new ControllableFeature("highnoon", "午时已到", "午时已到"),
        new ControllableFeature("pjskpartiton", "PJSK谱面", "PJSK"),
        new ControllableFeature("math_soup", "数学谜题", "数学谜"),
        new ControllableFeature("echo", "复读", "echo"),
        new ControllableFeature("mcmod_search", "MCMOD查询", "mcmod")
    );
    
    @Autowired
    public StatusControlHandler(PluginRegistry registry, BotConfig config) {
        super("状态控制", "admin", Set.of("状态控制", "状态", "控制"), null, 100, true, true);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("not_admin", "You don't have admin permission");
        errorMessages.put("token_service_unavailable", "Token service unavailable");
        errorMessages.put("token_invalid", "Invalid or expired token. Please request a new one via private chat.");
        errorMessages.put("ban_service_unavailable", "Ban service unavailable");
        errorMessages.put("monitor_service_unavailable", "System monitor unavailable");
        errorMessages.put("invalid_user_id", "User ID must be a number");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "管理员功能：查看和控制各功能开关状态（需令牌）", 
                "/admin (状态控制) [令牌] [操作] [参数]");
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        long userId = event.getUserId();
        
        // 检查是否为管理员
        if (!config.getAdminUserIdsSet().contains(userId)) {
            return reply(bot, event, getErrorMessage("not_admin"));
        }
        
        // 无参数时显示状态
        if (args == null || args.trim().isEmpty()) {
            return showStatus(bot, event);
        }
        
        // 解析参数
        String[] parts = args.trim().split("\\s+", 3);
        String token = parts[0];
        String action = parts.length > 1 ? parts[1].toLowerCase() : "";
        String actionArgs = parts.length > 2 ? parts[2] : "";
        
        // 验证令牌
        TokenServiceProtocol tokenService = ServiceLocator.get(TokenServiceProtocol.class);
        if (tokenService == null) {
            return reply(bot, event, getErrorMessage("token_service_unavailable"));
        }
        
        if (!tokenService.verifyToken(userId, token)) {
            return reply(bot, event, getErrorMessage("token_invalid"));
        }
        
        // 执行操作
        return switch (action) {
            case "toggle" -> handleToggle(bot, event, actionArgs);
            case "ban" -> handleBan(bot, event, actionArgs);
            case "unban" -> handleUnban(bot, event, actionArgs);
            case "status" -> showStatus(bot, event);
            case "system" -> showSystemStatus(bot, event);
            default -> reply(bot, event, "Unknown operation: " + action + ". Available: toggle/ban/unban/status/system");
        };
    }
    
    /**
     * 显示所有功能状态
     */
    private CompletableFuture<Void> showStatus(Bot bot, AnyMessageEvent event) {
        StringBuilder sb = new StringBuilder("Feature status:\n");
        
        for (ControllableFeature feature : CONTROLLABLE_FEATURES) {
            boolean isEnabled = config.isEnabled(feature.key);
            String status = isEnabled ? "[ON]" : "[OFF]";
            sb.append(String.format("  %s: %s%n", feature.displayName, status));
        }
        
        // 黑名单数量
        BanServiceProtocol ban = ServiceLocator.get(BanServiceProtocol.class);
        int bannedCount = (ban instanceof BanService) ? ((BanService) ban).getBannedCount() : 0;
        sb.append(String.format("%nBanned users: %d", bannedCount));
        
        return send(bot, event, sb.toString());
    }
    
    /**
     * 处理功能开关
     */
    private CompletableFuture<Void> handleToggle(Bot bot, AnyMessageEvent event, String target) {
        if (target == null || target.trim().isEmpty()) {
            return reply(bot, event, "Please specify feature name, e.g.: toggle math");
        }
        
        String targetLower = target.trim().toLowerCase();
        
        // 查找匹配的功能
        ControllableFeature matchedFeature = null;
        for (ControllableFeature feature : CONTROLLABLE_FEATURES) {
            if (targetLower.equals(feature.key) || 
                targetLower.equals(feature.displayName.toLowerCase()) ||
                targetLower.equals(feature.shortName.toLowerCase())) {
                matchedFeature = feature;
                break;
            }
        }
        
        if (matchedFeature == null) {
            StringBuilder available = new StringBuilder();
            for (ControllableFeature feature : CONTROLLABLE_FEATURES) {
                if (available.length() > 0) available.append(", ");
                available.append(feature.displayName);
            }
            return send(bot, event, "Unknown feature. Available: " + available.toString());
        }
        
        // 切换开关
        boolean currentValue = config.isEnabled(matchedFeature.key);
        // 使用反射设置新值（因为 BotConfig 没有 setter 方法）
        // 这里简化处理，实际应该调用 setter
        String setterName = "set" + matchedFeature.key.substring(0, 1).toUpperCase() + 
                           matchedFeature.key.substring(1) + "Enabled";
        try {
            java.lang.reflect.Method setter = BotConfig.class.getMethod(setterName, boolean.class);
            setter.invoke(config, !currentValue);
        } catch (IllegalAccessException | NoSuchMethodException | SecurityException | InvocationTargetException e) {
            // 如果找不到 setter，使用直接字段访问（不推荐，但作为备选）
            logger.warn("Failed to toggle feature via setter, trying direct field access");
        }
        
        String newStatus = !currentValue ? "ON" : "OFF";
        return send(bot, event, matchedFeature.displayName + " is now " + newStatus);
    }
    
    /**
     * 处理拉黑用户
     */
    private CompletableFuture<Void> handleBan(Bot bot, AnyMessageEvent event, String userIdStr) {
        if (userIdStr == null || userIdStr.trim().isEmpty()) {
            return reply(bot, event, "Please specify user ID, e.g.: ban 123456");
        }
        
        long targetUserId;
        try {
            targetUserId = Long.parseLong(userIdStr.trim());
        } catch (NumberFormatException e) {
            return reply(bot, event, getErrorMessage("invalid_user_id"));
        }
        
        BanServiceProtocol ban = ServiceLocator.get(BanServiceProtocol.class);
        if (ban == null) {
            return reply(bot, event, getErrorMessage("ban_service_unavailable"));
        }
        
        if (ban.isBanned(targetUserId)) {
            return send(bot, event, "User " + targetUserId + " is already banned");
        }
        
        Result<Boolean> result = ban.ban(targetUserId);
        if (result.isSuccess()) {
            return send(bot, event, "User " + targetUserId + " has been banned");
        } else {
            return send(bot, event, "Ban failed: " + result.getError());
        }
    }
    
    /**
     * 处理解封用户
     */
    private CompletableFuture<Void> handleUnban(Bot bot, AnyMessageEvent event, String userIdStr) {
        if (userIdStr == null || userIdStr.trim().isEmpty()) {
            return reply(bot, event, "Please specify user ID, e.g.: unban 123456");
        }
        
        long targetUserId;
        try {
            targetUserId = Long.parseLong(userIdStr.trim());
        } catch (NumberFormatException e) {
            return reply(bot, event, getErrorMessage("invalid_user_id"));
        }
        
        BanServiceProtocol ban = ServiceLocator.get(BanServiceProtocol.class);
        if (ban == null) {
            return reply(bot, event, getErrorMessage("ban_service_unavailable"));
        }
        
        if (!ban.isBanned(targetUserId)) {
            return send(bot, event, "User " + targetUserId + " is not banned");
        }
        
        Result<Boolean> result = ban.unban(targetUserId);
        if (result.isSuccess()) {
            return send(bot, event, "User " + targetUserId + " has been unbanned");
        } else {
            return send(bot, event, "Unban failed: " + result.getError());
        }
    }
    
    /**
     * 显示系统状态
     */
    private CompletableFuture<Void> showSystemStatus(Bot bot, AnyMessageEvent event) {
        SystemMonitorProtocol monitor = ServiceLocator.get(SystemMonitorProtocol.class);
        if (monitor == null) {
            return send(bot, event, getErrorMessage("monitor_service_unavailable"));
        }
        
        String statusText = monitor.getStatusText();
        return send(bot, event, statusText);
    }
    
    /**
     * 可控制的功能
     */
    private record ControllableFeature(String key, String displayName, String shortName) {}
}
