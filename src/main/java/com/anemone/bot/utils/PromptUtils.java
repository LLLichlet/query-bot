package com.anemone.bot.utils;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Prompt 文件工具类
 * 
 * 用于从 resources/prompts 目录读取系统提示词文件。
 * 
 * Example:
 * <pre>{@code
 * String prompt = PromptUtils.readPrompt("math_def");
 * if (prompt != null) {
 *     // 使用提示词
 * }
 * }</pre>
 */
public class PromptUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(PromptUtils.class);
    
    private static final String PROMPTS_DIR = "prompts/";
    
    /**
     * 读取 prompt 文件内容
     * 
     * @param name prompt 文件名（不含扩展名）
     * @return 文件内容，如果读取失败返回 null
     */
    public static String readPrompt(String name) {
        String resourcePath = PROMPTS_DIR + name + ".txt";
        
        try {
            ClassPathResource resource = new ClassPathResource(resourcePath);
            if (!resource.exists()) {
                logger.error("Prompt file not found: {}", resourcePath);
                return null;
            }
            
            try (InputStream is = resource.getInputStream()) {
                String content = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                logger.debug("Loaded prompt file: {} ({} chars)", resourcePath, content.length());
                return content;
            }
        } catch (IOException e) {
            logger.error("Failed to read prompt file: {}" , resourcePath, e);
            return null;
        }
    }
    
    /**
     * 检查 prompt 文件是否存在
     * 
     * @param name prompt 文件名（不含扩展名）
     * @return 是否存在
     */
    public static boolean exists(String name) {
        String resourcePath = PROMPTS_DIR + name + ".txt";
        ClassPathResource resource = new ClassPathResource(resourcePath);
        return resource.exists();
    }
}
