package com.anemone.bot.plugins.help;

import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.service.PluginInfo;
import com.anemone.bot.service.PluginRegistry;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * 帮助插件
 * 
 * 自动从 PluginRegistry 读取插件元数据，动态生成帮助信息。
 * 支持查看功能列表和指定指令的详细用法。
 * 
 * 触发方式:
 * - /help - 显示所有可用功能列表
 * - /help [指令名] - 查看指定指令的详细用法
 */
@Component
public class HelpHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    @Autowired
    public HelpHandler(PluginRegistry registry, BotConfig config) {
        super("帮助", "help", Set.of("帮助"), null, 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("command_not_found", "Command not found");
        errorMessages.put("feature_disabled", "Feature is currently disabled");
        errorMessages.put("no_features_available", "All features are currently disabled. Please contact the administrator.");
    }
    
    @PostConstruct
    public void init() {
        // 注册到 PluginRegistry
        registry.registerCommand(this, "查看插件使用帮助", "/help [command] - Show feature list or specific command details");
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        if (args != null && !args.trim().isEmpty()) {
            // 显示特定指令详情
            Result<Void> result = showPluginDetail(args.trim(), bot, event);
            if (result.isFailure()) {
                return reply(bot, event, getErrorMessage(result.getError()) + ": /" + args.trim());
            }
            return CompletableFuture.completedFuture(null);
        } else {
            // 显示功能列表
            Result<Void> result = showPluginList(bot, event);
            if (result.isFailure()) {
                return reply(bot, event, getErrorMessage(result.getError()));
            }
            return CompletableFuture.completedFuture(null);
        }
    }
    
    /**
     * 显示特定插件的详细信息
     */
    private Result<Void> showPluginDetail(String query, Bot bot, AnyMessageEvent event) {
        // 去掉可能的前导 /
        String normalizedQuery = query.toLowerCase().replaceFirst("^/", "");
        
        // 特殊处理 help 自身
        if (normalizedQuery.equals("help") || normalizedQuery.equals("帮助")) {
            StringBuilder sb = new StringBuilder();
            sb.append("/help 帮助\n");
            sb.append("Aliases: /帮助\n");
            sb.append("Description: 查看插件使用帮助\n");
            sb.append("Usage: /help [command] - Show feature list or specific command details");
            reply(bot, event, sb.toString());
            return Result.ok(null);
        }
        
        // 通过命令名查找插件
        var pluginOpt = registry.getPluginByCommand(normalizedQuery);
        
        if (pluginOpt.isEmpty() || pluginOpt.get().isHidden()) {
            return Result.err("command_not_found");
        }
        
        PluginInfo plugin = pluginOpt.get();
        
        // 检查功能开关
        if (plugin.getFeatureName() != null && !config.isEnabled(plugin.getFeatureName())) {
            return Result.err("feature_disabled");
        }
        
        StringBuilder sb = new StringBuilder();
        sb.append("/").append(plugin.getCommand()).append(" ").append(plugin.getName());
        
        if (!plugin.getAliases().isEmpty()) {
            String aliasesText = plugin.getAliases().stream()
                    .map(a -> "/" + a)
                    .sorted()
                    .collect(Collectors.joining(", "));
            sb.append("\nAliases: ").append(aliasesText);
        }
        
        if (plugin.getDescription() != null) {
            sb.append("\nDescription: ").append(plugin.getDescription());
        }
        
        if (plugin.getUsage() != null) {
            sb.append("\nUsage: ").append(plugin.getUsage());
        }
        
        reply(bot, event, sb.toString());
        return Result.ok(null);
    }
    
    /**
     * 显示所有可用功能列表
     */
    private Result<Void> showPluginList(Bot bot, AnyMessageEvent event) {
        List<PluginInfo> plugins = registry.getCommandPlugins(false);
        
        if (plugins.isEmpty()) {
            reply(bot, event, "Welcome to Anemone bot!\n\nNo features available");
            return Result.err("no_features_available");
        }
        
        StringBuilder sb = new StringBuilder();
        sb.append("Welcome to Anemone bot!");
        
        // 命令插件
        boolean hasEnabledPlugin = false;
        for (PluginInfo plugin : plugins) {
            if (plugin.getCommand() == null || "help".equals(plugin.getCommand())) {
                continue;
            }
            
            // 检查功能开关
            if (plugin.getFeatureName() != null && !config.isEnabled(plugin.getFeatureName())) {
                continue;
            }
            
            hasEnabledPlugin = true;
            sb.append("\n/").append(plugin.getCommand()).append(" ").append(plugin.getName());
        }
        
        // 消息插件
        List<PluginInfo> messagePlugins = registry.getMessagePlugins(false);
        for (PluginInfo plugin : messagePlugins) {
            if (plugin.getFeatureName() != null && !config.isEnabled(plugin.getFeatureName())) {
                continue;
            }
            sb.append("\n(Auto) ").append(plugin.getName());
        }
        
        if (!hasEnabledPlugin) {
            sb.append("\nAll features are currently disabled, please contact the administrator");
        }
        
        sb.append("\n\nUse /help [command] to view detailed usage");
        
        reply(bot, event, sb.toString());
        return Result.ok(null);
    }
}
