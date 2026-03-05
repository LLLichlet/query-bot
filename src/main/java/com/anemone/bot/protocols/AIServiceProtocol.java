package com.anemone.bot.protocols;

import com.anemone.bot.base.Result;

import java.util.concurrent.CompletableFuture;

/**
 * AI 服务协议 - 插件层通过此接口使用 AI 能力
 * 
 * 封装 AI API 调用，提供统一的对话接口。
 * 
 * Example:
 * <pre>{@code
 * AIServiceProtocol ai = ServiceLocator.get(AIServiceProtocol.class);
 * if (ai != null && ai.isAvailable()) {
 *     ai.chat("你是助手", "你好", 0.7, 1024, 0.9)
 *       .thenAccept(result -> {
 *           if (result.isSuccess()) {
 *               System.out.println(result.getValue());
 *           }
 *       });
 * }
 * }</pre>
 */
public interface AIServiceProtocol {
    
    /**
     * AI 服务是否可用
     * 
     * @return True 如果 API 密钥已配置且服务可用
     */
    boolean isAvailable();
    
    /**
     * 调用 AI 对话
     * 
     * @param systemPrompt 系统提示词
     * @param userInput 用户输入
     * @param temperature 温度参数（创造性）
     * @param maxTokens 最大生成 token 数
     * @param topP 核采样参数
     * @return 包含 AI 回复内容或错误信息的 Future
     */
    CompletableFuture<Result<String>> chat(
            String systemPrompt,
            String userInput,
            double temperature,
            int maxTokens,
            double topP
    );
    
    /**
     * 调用 AI 对话（使用默认参数）
     * 
     * @param systemPrompt 系统提示词
     * @param userInput 用户输入
     * @return 包含 AI 回复内容或错误信息的 Future
     */
    default CompletableFuture<Result<String>> chat(String systemPrompt, String userInput) {
        return chat(systemPrompt, userInput, 0.7, 1024, 0.9);
    }
}
