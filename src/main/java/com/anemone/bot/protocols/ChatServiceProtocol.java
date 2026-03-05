package com.anemone.bot.protocols;

/**
 * 聊天服务协议
 * 
 * 管理群聊历史记录和冷却时间控制。
 * 
 * Example:
 * <pre>{@code
 * ChatServiceProtocol chat = ServiceLocator.get(ChatServiceProtocol.class);
 * chat.recordMessage(123456L, 789L, "用户", "Hello");
 * String context = chat.getContext(123456L, 10);
 * }</pre>
 */
public interface ChatServiceProtocol {
    
    /**
     * 记录消息到历史
     * 
     * @param groupId 群号
     * @param userId 用户 QQ 号
     * @param username 用户名
     * @param message 消息内容
     * @param isBot 是否为机器人消息
     */
    void recordMessage(long groupId, long userId, String username, String message, boolean isBot);
    
    /**
     * 获取群聊上下文
     * 
     * @param groupId 群号
     * @param limit 最大返回消息数
     * @return 格式化的聊天记录字符串
     */
    String getContext(long groupId, int limit);
    
    /**
     * 获取群聊上下文（默认 50 条）
     * 
     * @param groupId 群号
     * @return 格式化的聊天记录字符串
     */
    default String getContext(long groupId) {
        return getContext(groupId, 50);
    }
    
    /**
     * 检查冷却时间
     * 
     * @param groupId 群号
     * @param cooldownSeconds 冷却时间（秒）
     * @return True 如果在冷却中，False 如果可以使用
     */
    boolean checkCooldown(long groupId, int cooldownSeconds);
    
    /**
     * 设置冷却时间
     * 
     * @param groupId 群号
     */
    void setCooldown(long groupId);
}
