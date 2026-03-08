package com.anemone.bot.service;

import com.anemone.bot.protocols.ChatServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 聊天服务实现 - 群聊历史记录管理
 * 
 * 服务层 - 实现 ChatServiceProtocol 协议
 * 
 * 管理群聊消息历史记录，用于随机回复功能的上下文获取。
 * 每个群聊独立维护消息历史，支持多群并发。
 * 
 * Example:
 * <pre>{@code
 * ChatServiceProtocol chat = ServiceLocator.get(ChatServiceProtocol.class);
 * chat.recordMessage(123456L, 789L, "用户", "Hello", false);
 * String context = chat.getContext(123456L, 10);
 * }</pre>
 */
@Service
public class ChatService implements ChatServiceProtocol {
    
    /**
     * 消息记录
     */
    public static class MessageRecord {
        public final long userId;
        public final String username;
        public final String message;
        public final boolean isBot;
        public final long timestamp;
        
        public MessageRecord(long userId, String username, String message, boolean isBot) {
            this.userId = userId;
            this.username = username;
            this.message = message;
            this.isBot = isBot;
            this.timestamp = Instant.now().getEpochSecond();
        }
    }
    
    // 群聊消息历史: groupId -> 消息列表
    private final Map<Long, List<MessageRecord>> messageHistory = new ConcurrentHashMap<>();
    
    // 每个群聊最大保留消息数
    private static final int MAX_HISTORY_PER_GROUP = 50;
    
    /**
     * 初始化完成后注册到 ServiceLocator
     */
    @PostConstruct
    public void init() {
        ServiceLocator.register(ChatServiceProtocol.class, this);
    }
    
    @Override
    public void recordMessage(long groupId, long userId, String username, String message, boolean isBot) {
        if (groupId <= 0) {
            return; // 私聊不记录
        }
        
        List<MessageRecord> history = messageHistory.computeIfAbsent(groupId, k -> new ArrayList<>());
        
        synchronized (history) {
            history.add(new MessageRecord(userId, username, message, isBot));
            
            // 限制历史记录数量
            if (history.size() > MAX_HISTORY_PER_GROUP) {
                history.remove(0);
            }
        }
    }
    
    @Override
    public String getContext(long groupId, int limit) {
        List<MessageRecord> history = messageHistory.get(groupId);
        if (history == null || history.isEmpty()) {
            return "";
        }
        
        StringBuilder context = new StringBuilder();
        
        synchronized (history) {
            int start = Math.max(0, history.size() - limit);
            for (int i = start; i < history.size(); i++) {
                MessageRecord record = history.get(i);
                String prefix = record.isBot ? "Bot" : record.username;
                context.append(prefix).append("说:").append(record.message).append("|");
            }
        }
        
        // 移除末尾的 |
        if (context.length() > 0 && context.charAt(context.length() - 1) == '|') {
            context.setLength(context.length() - 1);
        }
        
        return context.toString();
    }
    
    /**
     * 获取群聊历史记录（用于调试）
     * 
     * @param groupId 群号
     * @return 消息记录列表
     */
    public List<MessageRecord> getHistory(long groupId) {
        List<MessageRecord> history = messageHistory.get(groupId);
        if (history == null) {
            return new ArrayList<>();
        }
        synchronized (history) {
            return new ArrayList<>(history);
        }
    }
    
    /**
     * 清除群聊历史记录
     * 
     * @param groupId 群号
     */
    public void clearHistory(long groupId) {
        messageHistory.remove(groupId);
    }
    
    /**
     * 获取所有活跃的群聊ID
     * 
     * @return 群号列表
     */
    public List<Long> getActiveGroups() {
        return new ArrayList<>(messageHistory.keySet());
    }
}
