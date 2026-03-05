package com.anemone.bot.handler;

import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;

import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * 消息处理器基类 - 处理所有消息
 * 
 * 用于监听所有群聊/私聊消息，不需要特定命令触发。
 * 子类重写 handleMessage 方法实现消息处理逻辑。
 * 
 * Example:
 * <pre>{@code
 * public class MyMessageHandler extends MessageHandler {
 *     public MyMessageHandler() {
 *         super("消息监听", "myfeature", 1, false);
 *     }
 *     
 *     @Override
 *     public CompletableFuture<Void> handleMessage(Bot bot, AnyMessageEvent event) {
 *         String text = event.getRawMessage();
 *         if (text.contains("关键词")) {
 *             return reply(bot, event, "收到关键词");
 *         }
 *         return CompletableFuture.completedFuture(null);
 *     }
 * }
 * }</pre>
 */
public abstract class MessageHandler extends PluginHandler {
    
    protected final int messagePriority;
    protected final boolean messageBlock;
    
    /**
     * 创建消息处理器
     * 
     * @param name 插件名称
     * @param featureName 功能开关名
     * @param messagePriority 消息处理优先级
     * @param messageBlock 是否阻断后续处理器
     */
    public MessageHandler(String name, String featureName, int messagePriority, boolean messageBlock) {
        super(name, null, Set.of(), featureName, messagePriority, messageBlock, false);
        this.messagePriority = messagePriority;
        this.messageBlock = messageBlock;
    }
    
    /**
     * 简化构造方法
     */
    public MessageHandler(String name, String featureName) {
        this(name, featureName, 1, false);
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 消息处理器默认调用 handleMessage
        return handleMessage(bot, event);
    }
    
    /**
     * 处理消息（子类重写）
     * 
     * @param bot cq-bot 实例
     * @param event 消息事件
     * @return 异步操作
     */
    public abstract CompletableFuture<Void> handleMessage(Bot bot, AnyMessageEvent event);
    
    public int getMessagePriority() { return messagePriority; }
    public boolean isMessageBlock() { return messageBlock; }
}
