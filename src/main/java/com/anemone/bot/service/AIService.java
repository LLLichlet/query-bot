package com.anemone.bot.service;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;
import com.anemone.bot.protocols.AIServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.utils.NetworkUtils;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * AI 服务实现 - DeepSeek API 封装
 * 
 * 服务层 - 实现 AIServiceProtocol 协议
 * 
 * 提供 DeepSeek API 的异步调用封装，支持对话生成、参数调优等功能。
 * 在初始化完成后自动注册到 ServiceLocator。
 * 
 * Example:
 * <pre>{@code
 * AIServiceProtocol ai = ServiceLocator.get(AIServiceProtocol.class);
 * if (ai != null && ai.isAvailable()) {
 *     ai.chat("你是数学家", "解释群论", 0.3, 512, 0.8)
 *       .thenAccept(result -> {
 *           if (result.isSuccess()) {
 *               System.out.println(result.getValue());
 *           }
 *       });
 * }
 * }</pre>
 */
@Service
public class AIService implements AIServiceProtocol {
    
    private static final Logger logger = LoggerFactory.getLogger(AIService.class);
    
    private final BotConfig config;
    
    /**
     * 创建 AI 服务
     * 
     * @param config 机器人配置
     */
    @Autowired
    public AIService(BotConfig config) {
        this.config = config;
    }
    
    /**
     * 初始化完成后注册到 ServiceLocator
     */
    @PostConstruct
    public void init() {
        ServiceLocator.register(AIServiceProtocol.class, this);
        if (isAvailable()) {
            logger.info("AI Service initialized with model: {}", config.getDeepseekModel());
        } else {
            logger.warn("AI Service not available: API key not configured");
        }
    }
    
    @Override
    public boolean isAvailable() {
        return config.getDeepseekApiKey() != null 
               && !config.getDeepseekApiKey().isEmpty();
    }
    
    @Override
    public CompletableFuture<Result<String>> chat(
            String systemPrompt,
            String userInput,
            double temperature,
            int maxTokens,
            double topP) {
        
        return CompletableFuture.supplyAsync(() -> {
            if (!isAvailable()) {
                return Result.err("AI service not configured");
            }
            
            try {
                // 构建请求体
                JSONObject requestBody = new JSONObject();
                requestBody.set("model", config.getDeepseekModel());
                
                // 构建消息数组
                JSONArray messages = new JSONArray();
                
                JSONObject systemMessage = new JSONObject();
                systemMessage.set("role", "system");
                systemMessage.set("content", systemPrompt);
                messages.add(systemMessage);
                
                JSONObject userMessage = new JSONObject();
                userMessage.set("role", "user");
                userMessage.set("content", userInput);
                messages.add(userMessage);
                
                requestBody.set("messages", messages);
                requestBody.set("temperature", temperature);
                requestBody.set("max_tokens", maxTokens);
                requestBody.set("top_p", topP);
                
                // 发送请求
                String url = config.getDeepseekBaseUrl() + "/chat/completions";
                
                logger.debug("Sending AI request to {} with model {}", url, config.getDeepseekModel());
                
                // 使用 NetworkUtils 发送请求
                Map<String, String> headers = Map.of(
                    "Authorization", "Bearer " + config.getDeepseekApiKey()
                );
                
                String responseBody = NetworkUtils.postJson(url, requestBody.toString(), headers, 60);
                
                if (responseBody == null) {
                    logger.error("AI API request failed");
                    return Result.err("AI service error: request failed");
                }
                
                // 解析响应
                JSONObject responseJson = new JSONObject(responseBody);
                JSONArray choices = responseJson.getJSONArray("choices");
                
                if (choices == null || choices.isEmpty()) {
                    return Result.err("AI response empty");
                }
                
                JSONObject choice = choices.getJSONObject(0);
                JSONObject message = choice.getJSONObject("message");
                String content = message.getStr("content");
                
                if (content == null || content.isEmpty()) {
                    return Result.err("AI response content empty");
                }
                
                logger.debug("AI response received, length: {}", content.length());
                return Result.ok(content.trim());
                
            } catch (Exception e) {
                logger.error("AI API call failed", e);
                return Result.err("AI service temporarily unavailable: " + e.getMessage());
            }
        });
    }
}
