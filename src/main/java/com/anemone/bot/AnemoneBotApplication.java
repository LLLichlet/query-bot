package com.anemone.bot;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.protocols.BotServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.service.PluginRegistry;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ApplicationContext;

/**
 * Anemone Bot Java 版主应用类
 * 
 * 基于 Shiro 框架的 QQ 群聊机器人。
 * 支持功能：帮助系统、复读、数学定义查询等。
 * 
 * 分层架构：
 * - base: 基础层（Result, ServiceBase）
 * - config: 配置层（BotConfig）
 * - protocols: 协议层（服务接口, ServiceLocator）
 * - handler: 处理器层（PluginHandler, MessageHandler）
 * - service: 服务层（PluginRegistry, BotServiceImpl）
 * - plugins: 插件层（HelpHandler, EchoHandler 等）
 * - receiver: 接收层（BotEventListener）
 */
@SpringBootApplication
public class AnemoneBotApplication {

    public static void main(String[] args) {
        ApplicationContext context = SpringApplication.run(AnemoneBotApplication.class, args);
        
        // 注册服务到 ServiceLocator
        registerServices(context);
        
        System.out.println("""
                
                =========================================
                  Anemone Bot (Java) Started!
                =========================================
                  Version: 2.4.0
                  Framework: Shiro (OneBot v11)
                =========================================
                """);
    }
    
    /**
     * 注册服务到 ServiceLocator
     * 
     * 这样插件可以通过 ServiceLocator.get() 获取服务，
     * 而不需要直接依赖 Spring。
     */
    private static void registerServices(ApplicationContext context) {
        // 注册 BotService
        BotServiceProtocol botService = context.getBean(BotServiceProtocol.class);
        ServiceLocator.register(BotServiceProtocol.class, botService);
        
        // 注册 PluginRegistry
        PluginRegistry registry = context.getBean(PluginRegistry.class);
        ServiceLocator.register(PluginRegistry.class, registry);
        
        // 注册 BotConfig
        BotConfig config = context.getBean(BotConfig.class);
        ServiceLocator.register(BotConfig.class, config);
    }
}
