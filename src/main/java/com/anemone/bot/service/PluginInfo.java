package com.anemone.bot.service;

import com.anemone.bot.handler.PluginHandler;

import java.util.Set;

/**
 * 插件信息类
 * 
 * 封装插件的元数据，用于帮助系统和插件管理。
 */
public class PluginInfo {
    
    private final String name;
    private final String command;
    private final Set<String> aliases;
    private final String description;
    private final String featureName;
    private final String usage;
    private final boolean hidden;
    private final PluginHandler handler;
    
    public PluginInfo(
            String name,
            String command,
            Set<String> aliases,
            String description,
            String featureName,
            String usage,
            boolean hidden,
            PluginHandler handler
    ) {
        this.name = name;
        this.command = command;
        this.aliases = aliases != null ? aliases : Set.of();
        this.description = description;
        this.featureName = featureName;
        this.usage = usage;
        this.hidden = hidden;
        this.handler = handler;
    }
    
    // ==================== Getter ====================
    
    public String getName() { return name; }
    public String getCommand() { return command; }
    public Set<String> getAliases() { return aliases; }
    public String getDescription() { return description; }
    public String getFeatureName() { return featureName; }
    public String getUsage() { return usage; }
    public boolean isHidden() { return hidden; }
    public PluginHandler getHandler() { return handler; }
    
    /**
     * 检查是否匹配命令（包括别名）
     * 
     * @param query 查询的命令
     * @return 是否匹配
     */
    public boolean matchesCommand(String query) {
        if (query == null || query.isEmpty()) {
            return false;
        }
        String normalizedQuery = query.toLowerCase().replaceFirst("^/", "");
        if (command != null && command.equalsIgnoreCase(normalizedQuery)) {
            return true;
        }
        return aliases.stream()
                .anyMatch(alias -> alias.equalsIgnoreCase(normalizedQuery));
    }
}
