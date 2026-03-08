package com.anemone.bot.handler;

import com.anemone.bot.base.Result;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.protocols.BotServiceProtocol;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * 插件业务逻辑处理器基类
 * 
 * 子类通过实现 handle 方法处理命令，使用 send/reply 方法发送消息。
 * 每个 Handler 对应一个命令或功能。
 * 
 * Example:
 * <pre>{@code
 * public class MyHandler extends PluginHandler {
 *     public MyHandler() {
 *         super("我的插件", "mycommand", Set.of("alias1", "alias2"), "myfeature", 10, true);
 *     }
 *     
 *     @Override
 *     public CompletableFuture<Void> handle(AnyMessageEvent event, String args) {
 *         return reply(event, "收到: " + args);
 *     }
 * }
 * }</pre>
 */
public abstract class PluginHandler {
    
    protected final Logger logger = LoggerFactory.getLogger(getClass());
    
    // 元数据
    protected final String name;
    protected final String command;
    protected final Set<String> aliases;
    protected final String featureName;
    protected final int priority;
    protected final boolean block;
    protected final boolean hiddenInHelp;
    
    // 错误消息映射
    protected final Map<String, String> errorMessages = new HashMap<>();
    
    /**
     * 创建处理器
     * 
     * @param name 插件名称
     * @param command 命令名（不带/）
     * @param aliases 命令别名
     * @param featureName 功能开关名
     * @param priority 命令优先级
     * @param block 是否阻断后续处理器
     * @param hiddenInHelp 是否在帮助中隐藏
     */
    public PluginHandler(
            String name,
            String command,
            Set<String> aliases,
            String featureName,
            int priority,
            boolean block,
            boolean hiddenInHelp
    ) {
        this.name = name;
        this.command = command;
        this.aliases = aliases != null ? aliases : Set.of();
        this.featureName = featureName;
        this.priority = priority;
        this.block = block;
        this.hiddenInHelp = hiddenInHelp;
    }
    
    /**
     * 简化的构造方法
     */
    public PluginHandler(String name, String command, Set<String> aliases, String featureName) {
        this(name, command, aliases, featureName, 10, true, false);
    }
    
    /**
     * 处理命令（子类必须实现）
     * 
     * @param bot cq-bot 实例
     * @param event 消息事件
     * @param args 命令参数（已去除命令名）
     * @return 异步操作结果
     */
    public abstract CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args);
    
    // ==================== Getter ====================
    
    public String getName() { return name; }
    public String getCommand() { return command; }
    public Set<String> getAliases() { return aliases; }
    public String getFeatureName() { return featureName; }
    public int getPriority() { return priority; }
    public boolean isBlock() { return block; }
    public boolean isHiddenInHelp() { return hiddenInHelp; }
    
    /**
     * 获取错误消息
     * 
     * @param error 错误类型
     * @return 对应的错误消息
     */
    protected String getErrorMessage(String error) {
        return errorMessages.getOrDefault(error, "Operation failed: " + error);
    }
    
    /**
     * 获取错误消息（支持格式化）
     * 
     * @param error 错误类型
     * @param context 格式化参数
     * @return 格式化后的错误消息
     */
    protected String getErrorMessage(String error, Map<String, Object> context) {
        String message = errorMessages.get(error);
        if (message == null) {
            return "Operation failed: " + error;
        }
        if (context != null) {
            for (Map.Entry<String, Object> entry : context.entrySet()) {
                message = message.replace("{" + entry.getKey() + "}", String.valueOf(entry.getValue()));
            }
        }
        return message;
    }
    
    /**
     * 创建成功的 Result
     */
    protected <T> Result<T> ok(T value) {
        return Result.ok(value);
    }
    
    /**
     * 创建失败的 Result
     */
    protected <T> Result<T> err(String error) {
        return Result.err(error);
    }
    
    /**
     * 条件检查，快速创建 Result
     */
    protected <T> Result<T> check(boolean condition, String error, T value) {
        return Result.check(condition, error, value);
    }
    
    // ==================== 消息发送 ====================
    
    /**
     * 发送消息
     * 
     * @param bot cq-bot 实例
     * @param event 消息事件
     * @param message 消息内容
     * @param at 是否@发送者
     * @return 异步操作
     */
    protected CompletableFuture<Void> send(Bot bot, AnyMessageEvent event, String message, boolean at) {
        BotServiceProtocol botService = ServiceLocator.get(BotServiceProtocol.class);
        if (botService == null) {
            logger.error("BotService not registered");
            return CompletableFuture.completedFuture(null);
        }
        
        long groupId = event.getGroupId() != null ? event.getGroupId() : 0;
        if (groupId > 0) {
            return botService.sendGroupMessage(groupId, message, at)
                    .thenApply(result -> null);
        } else {
            // 私聊消息
            bot.sendPrivateMsg(event.getUserId(), message, false);
            return CompletableFuture.completedFuture(null);
        }
    }
    
    /**
     * 发送消息（不@）
     */
    protected CompletableFuture<Void> send(Bot bot, AnyMessageEvent event, String message) {
        return send(bot, event, message, false);
    }
    
    /**
     * 回复用户（自动@）
     * 
     * @param bot cq-bot 实例
     * @param event 消息事件
     * @param message 消息内容
     * @return 异步操作
     */
    protected CompletableFuture<Void> reply(Bot bot, AnyMessageEvent event, String message) {
        return send(bot, event, message, true);
    }
    
    /**
     * 判断是否为群聊
     */
    protected boolean isGroup(AnyMessageEvent event) {
        return event.getGroupId() != null && event.getGroupId() > 0;
    }
    
    /**
     * 处理错误（可重写）
     * 
     * 当 handle 方法抛出异常时调用，默认发送错误信息。
     * 
     * @param bot cq-bot 实例
     * @param event 消息事件
     * @param error 异常对象
     * @return 异步操作
     */
    public CompletableFuture<Void> handleError(Bot bot, AnyMessageEvent event, Throwable error) {
        logger.error("Handler error in {}", this.getClass().getSimpleName(), error);
        return reply(bot, event, "处理出错: " + error.getMessage());
    }
}
