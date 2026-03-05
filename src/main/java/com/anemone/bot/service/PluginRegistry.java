package com.anemone.bot.service;

import com.anemone.bot.handler.MessageHandler;
import com.anemone.bot.handler.PluginHandler;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * 插件注册表
 * 
 * 管理所有已注册的插件，提供查询和遍历功能。
 * 用于帮助系统动态获取插件信息。
 * 
 * Example:
 * <pre>{@code
 * PluginRegistry registry = ServiceLocator.get(PluginRegistry.class);
 * List<PluginInfo> plugins = registry.getCommandPlugins();
 * }</pre>
 */
@Service
public class PluginRegistry {
    
    private final List<PluginInfo> plugins = new ArrayList<>();
    
    /**
     * 注册插件
     * 
     * @param info 插件信息
     */
    public void register(PluginInfo info) {
        plugins.add(info);
    }
    
    /**
     * 注册命令插件
     * 
     * @param handler 处理器
     * @param description 描述
     * @param usage 用法
     */
    public void registerCommand(PluginHandler handler, String description, String usage) {
        PluginInfo info = new PluginInfo(
                handler.getName(),
                handler.getCommand(),
                handler.getAliases(),
                description,
                handler.getFeatureName(),
                usage,
                handler.isHiddenInHelp(),
                handler
        );
        register(info);
    }
    
    /**
     * 注册消息插件
     * 
     * @param handler 处理器
     * @param description 描述
     */
    public void registerMessage(MessageHandler handler, String description) {
        PluginInfo info = new PluginInfo(
                handler.getName(),
                null,  // 消息处理器没有命令
                null,
                description,
                handler.getFeatureName(),
                null,
                handler.isHiddenInHelp(),
                handler
        );
        register(info);
    }
    
    /**
     * 获取所有命令插件
     * 
     * @param includeHidden 是否包含隐藏的插件
     * @return 命令插件列表
     */
    public List<PluginInfo> getCommandPlugins(boolean includeHidden) {
        return plugins.stream()
                .filter(p -> p.getCommand() != null)
                .filter(p -> includeHidden || !p.isHidden())
                .sorted(Comparator.comparing(PluginInfo::getCommand))
                .collect(Collectors.toList());
    }
    
    /**
     * 获取所有消息插件
     * 
     * @param includeHidden 是否包含隐藏的插件
     * @return 消息插件列表
     */
    public List<PluginInfo> getMessagePlugins(boolean includeHidden) {
        return plugins.stream()
                .filter(p -> p.getCommand() == null)
                .filter(p -> includeHidden || !p.isHidden())
                .sorted(Comparator.comparing(PluginInfo::getName))
                .collect(Collectors.toList());
    }
    
    /**
     * 根据命令名查找插件
     * 
     * @param command 命令名（可包含/前缀）
     * @return 插件信息（如果找到）
     */
    public Optional<PluginInfo> getPluginByCommand(String command) {
        String normalizedCommand = command.toLowerCase().replaceFirst("^/", "");
        return plugins.stream()
                .filter(p -> p.matchesCommand(normalizedCommand))
                .findFirst();
    }
    
    /**
     * 获取所有插件
     * 
     * @return 插件列表
     */
    public List<PluginInfo> getAllPlugins() {
        return new ArrayList<>(plugins);
    }
    
    /**
     * 清空注册表（主要用于测试）
     */
    public void clear() {
        plugins.clear();
    }
}
