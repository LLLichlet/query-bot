package com.anemone.bot.receiver;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.MessageHandler;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.annotation.AnyMessageHandler;
import com.mikuac.shiro.annotation.common.Shiro;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.core.BotContainer;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Shiro 事件监听器
 */
@Shiro
@Component
public class BotEventListener {
    
    private static final Logger logger = LoggerFactory.getLogger(BotEventListener.class);
    
    private final PluginRegistry registry;
    private final BotConfig config;
    private final BotContainer botContainer;
    
    @Lazy
    @Autowired(required = false)
    private List<PluginHandler> handlers;
    
    private final Map<String, PluginHandler> commandHandlers = new HashMap<>();
    private final Map<String, PluginHandler> aliasHandlers = new HashMap<>();
    private List<MessageHandler> messageHandlers;
    
    @Autowired
    public BotEventListener(PluginRegistry registry, BotConfig config, BotContainer botContainer) {
        this.registry = registry;
        this.config = config;
        this.botContainer = botContainer;
    }
    
    @PostConstruct
    public void init() {
        if (handlers == null || handlers.isEmpty()) {
            logger.warn("No PluginHandler beans found!");
            return;
        }
        
        logger.info("Initializing {} plugin handlers...", handlers.size());
        
        for (PluginHandler handler : handlers) {
            if (handler.getCommand() != null) {
                commandHandlers.put(handler.getCommand().toLowerCase(), handler);
                for (String alias : handler.getAliases()) {
                    aliasHandlers.put(alias.toLowerCase(), handler);
                }
                logger.info("Registered command handler: /{} (aliases: {})", handler.getCommand(), handler.getAliases());
            } else if (handler instanceof MessageHandler) {
                logger.info("Registered message handler: {}", handler.getName());
            }
        }
    }
    
    @AnyMessageHandler
    public void onAnyMessage(Bot bot, AnyMessageEvent event) {
        String message = event.getRawMessage();
        logger.info("=== Received message from {}: {} ===", event.getUserId(), message);
        
        if (message == null || message.isEmpty()) {
            logger.info("Message is null or empty, skipping");
            return;
        }
        
        logger.info("Processing message: {}", message);
        
        if (message.startsWith("/")) {
            logger.info("Handling as command");
            handleCommand(bot, event, message);
        } else {
            logger.info("Handling as regular message");
            handleMessage(bot, event, message);
        }
    }
    
    // 注意：使用 @AnyMessageHandler 统一处理所有消息
    // 不需要单独的 @GroupMessageHandler 和 @PrivateMessageHandler
    // 否则会导致消息被重复处理
    
    private void handleCommand(Bot bot, AnyMessageEvent event, String message) {
        String[] parts = message.substring(1).split("\\s+", 2);
        String command = parts[0].toLowerCase();
        String args = parts.length > 1 ? parts[1] : "";
        
        PluginHandler handler = commandHandlers.get(command);
        if (handler == null) {
            handler = aliasHandlers.get(command);
        }
        
        if (handler == null) {
            return;
        }
        
        if (handler.getFeatureName() != null && !config.isEnabled(handler.getFeatureName())) {
            logger.debug("Feature {} is disabled", handler.getFeatureName());
            return;
        }
        
        try {
            handler.handle(bot, event, args.trim())
                    .exceptionally(e -> {
                        logger.error("Error handling command /{}: {}", command, e.getMessage(), e);
                        return null;
                    });
        } catch (Exception e) {
            logger.error("Exception handling command /{}: {}", command, e.getMessage(), e);
        }
    }
    
    private void handleMessage(Bot bot, AnyMessageEvent event, String message) {
        if (messageHandlers == null) {
            messageHandlers = registry.getMessagePlugins(false).stream()
                    .filter(p -> p.getHandler() instanceof MessageHandler)
                    .map(p -> (MessageHandler) p.getHandler())
                    .sorted((a, b) -> Integer.compare(b.getMessagePriority(), a.getMessagePriority()))
                    .toList();
        }
        
        for (MessageHandler handler : messageHandlers) {
            if (handler.getFeatureName() != null && !config.isEnabled(handler.getFeatureName())) {
                continue;
            }
            
            try {
                var future = handler.handleMessage(bot, event);
                if (future != null) {
                    future.exceptionally(e -> {
                        logger.error("Error in message handler {}: {}", handler.getName(), e.getMessage(), e);
                        return null;
                    });
                }
            } catch (Exception e) {
                logger.error("Exception in message handler {}: {}", handler.getName(), e.getMessage(), e);
            }
        }
    }
}
