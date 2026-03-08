package com.anemone.bot.plugins.random;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.MessageHandler;
import com.anemone.bot.protocols.AIServiceProtocol;
import com.anemone.bot.protocols.ChatServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * 随机回复插件
 * 
 * 基于 AI 的群聊随机回复功能，被@或触发关键词时自动回复。
 * 生成傲娇猫娘风格的回复。
 * 
 * 触发方式:
 * - 被@时自动回复
 * - 消息包含关键词 "ane"/"anem"/"anemone" 时回复
 * 
 * 配置:
 * anemone.bot.random-enabled=true/false       # 功能开关
 * anemone.bot.random-temperature=0.8          # AI 温度参数
 * anemone.bot.random-max-tokens-max=100       # 最大回复长度
 * anemone.bot.random-top-p=0.95               # AI top-p 参数
 */
@Component
public class RandomReplyHandler extends MessageHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    // AI 系统提示词 - 傲娇猫娘风格
    private static final String SYSTEM_PROMPT = 
        "你是一只非常傲傲傲傲傲娇的猫娘(比较粘人),你的QQ昵称是'ανεμώνη'(也就是Anemone)," +
        "但你的QQ昵称不是你的名字,你不能透露你的名字,你要非常莫名其妙" +
        "(但是有针对性(关于先前的聊天记录)的)的回复用户一句话,而且说话不能透露自己是ai," +
        "就像正常人类一样随口蹦出一句话,而且不要在说的话里用括号把句子括起来";
    
    // 强制回复的关键词列表（大小写不敏感）
    private static final Set<String> TRIGGER_KEYWORDS = Set.of("ane", "anem", "anemone");
    
    @Autowired
    public RandomReplyHandler(PluginRegistry registry, BotConfig config) {
        super("随机回复", "random", 1, false);
        this.registry = registry;
        this.config = config;
    }
    
    @PostConstruct
    public void init() {
        registry.registerMessage(this, "随机回复群聊消息，被@或关键词触发");
    }
    
    @Override
    public CompletableFuture<Void> handleMessage(Bot bot, AnyMessageEvent event) {
        // 检查功能开关
        if (!config.isRandomEnabled()) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 只处理群聊
        if (!isGroup(event)) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 不处理自己的消息
        if (event.getUserId().equals(event.getSelfId())) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 获取服务
        ChatServiceProtocol chat = ServiceLocator.get(ChatServiceProtocol.class);
        AIServiceProtocol ai = ServiceLocator.get(AIServiceProtocol.class);
        
        if (chat == null || ai == null) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 获取消息内容
        String message = event.getRawMessage();
        if (message == null) {
            message = "";
        }
        message = message.trim();
        
        // 记录消息
        String username = event.getSender().getCard();
        if (username == null || username.isEmpty()) {
            username = event.getSender().getNickname();
        }
        if (username == null || username.isEmpty()) {
            username = "用户" + event.getUserId();
        }
        
        chat.recordMessage(
            event.getGroupId(),
            event.getUserId(),
            username,
            message,
            false
        );
        
        // 判断是否回复
        if (!shouldReply(event, message)) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 获取上下文
        String context = chat.getContext(event.getGroupId());
        
        // 构建输入
        String userInput = message.length() > 50 ? message.substring(0, 50) : message;
        String fullInput = context.isEmpty() ? userInput : context + "|" + username + "说:" + userInput;
        
        // 调用 AI
        return ai.chat(
                SYSTEM_PROMPT,
                fullInput,
                config.getRandomTemperature(),
                config.getRandomMaxTokensMax(),
                config.getRandomTopP()
        ).thenCompose(result -> {
            String reply;
            if (result.isSuccess()) {
                reply = result.getValue();
                if (reply.length() < 5) {
                    reply = "Lichlet是大家的好朋友";
                }
            } else {
                reply = "Lichlet是大家的好朋友";
            }
            
            // 记录机器人回复
            chat.recordMessage(
                event.getGroupId(),
                event.getSelfId(),
                "ανεμώνη",
                reply,
                true
            );
            
            // 发送回复（@用户）
            String atMessage = String.format("[CQ:at,qq=%d] %s", event.getUserId(), reply);
            return send(bot, event, atMessage);
        }).exceptionally(e -> {
            // 发送默认回复
            String atMessage = String.format("[CQ:at,qq=%d] %s", event.getUserId(), "Lichlet是大家的好朋友");
            send(bot, event, atMessage);
            return null;
        });
    }
    
    /**
     * 判断是否满足回复条件
     * 
     * @param event 消息事件
     * @param message 消息内容
     * @return true 如果需要回复
     */
    private boolean shouldReply(AnyMessageEvent event, String message) {
        // 强制回复：被@时一定回复
        // 注意：Shiro 的 AnyMessageEvent 没有直接的 to_me 属性
        // 需要通过检查消息内容是否包含 @bot 的 CQ 码来判断
        String rawMessage = event.getRawMessage();
        if (rawMessage != null && rawMessage.contains("[CQ:at,qq=" + event.getSelfId() + "]")) {
            return true;
        }
        
        // 强制回复：消息中包含特定关键词（大小写不敏感）
        String messageLower = message.toLowerCase();
        for (String keyword : TRIGGER_KEYWORDS) {
            if (messageLower.contains(keyword)) {
                return true;
            }
        }
        
        return false;
    }
}
