package com.anemone.bot.plugins.echo;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.MessageHandler;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.Random;
import java.util.concurrent.CompletableFuture;

/**
 * 复读插件
 * 
 * 自动复读群聊消息，支持随机概率触发和倒序复读。
 * 
 * 触发方式:
 * - 概率触发：消息有 1% 概率被复读
 * - 倒序复读：复读时有 20% 概率倒序显示消息
 * 
 * 配置:
 * anemone.bot.echo-probability=0.01
 * anemone.bot.echo-reverse-probability=0.2
 */
@Component
public class EchoHandler extends MessageHandler {
    
    private final BotConfig config;
    private final PluginRegistry registry;
    private final Random random = new Random();
    
    @Autowired
    public EchoHandler(BotConfig config, PluginRegistry registry) {
        super("复读", "echo", 2, false);
        this.config = config;
        this.registry = registry;
    }
    
    @PostConstruct
    public void init() {
        registry.registerMessage(this, "随机复读群聊消息，有概率倒着复读");
    }
    
    @Override
    public CompletableFuture<Void> handleMessage(Bot bot, AnyMessageEvent event) {
        // 检查功能开关
        if (!config.isEchoEnabled()) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 只处理群聊消息
        if (!isGroup(event)) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 不处理自己的消息
        if (event.getUserId() == event.getSelfId()) {
            return CompletableFuture.completedFuture(null);
        }
        
        String message = event.getRawMessage();
        if (message == null) {
            message = "";
        }
        message = message.trim();
        
        // 过滤命令消息
        if (message.startsWith("/")) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 过滤太短的消息
        if (message.length() < 2) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 获取配置
        double echoProb = config.getEchoProbability();
        double reverseProb = config.getEchoReverseProbability();
        
        // 判断是否复读
        if (random.nextDouble() >= echoProb) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 判断是否倒序
        boolean isReverse = random.nextDouble() < reverseProb;
        
        // 处理消息
        String reply = isReverse ? reverseString(message) : message;
        
        // 发送回复
        return send(bot, event, reply);
    }
    
    /**
     * 反转字符串
     * 
     * @param str 原字符串
     * @return 反转后的字符串
     */
    private String reverseString(String str) {
        return new StringBuilder(str).reverse().toString();
    }
}
