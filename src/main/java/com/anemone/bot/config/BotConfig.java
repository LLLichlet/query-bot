package com.anemone.bot.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 机器人配置类 - 统一管理所有配置
 * 
 * 从 application.yaml 或环境变量加载配置。
 * 配置项前缀: anemone.bot
 * 
 * Example:
 * <pre>{@code
 * anemone:
 *   bot:
 *     deepseek-api-key: your-api-key
 *     math-enabled: true
 * }</pre>
 */
@Component
@ConfigurationProperties(prefix = "anemone.bot")
public class BotConfig {
    
    // ==================== AI API 配置 ====================
    private String deepseekApiKey = "";
    private String deepseekBaseUrl = "https://api.deepseek.com";
    private String deepseekModel = "deepseek-chat";
    
    // ==================== 功能开关 ====================
    private boolean mathEnabled = true;
    private boolean randomEnabled = true;
    private boolean highnoonEnabled = true;
    private boolean pjskpartitonEnabled = true;
    private boolean mathSoupEnabled = true;
    private boolean echoEnabled = true;
    private boolean mcmodSearchEnabled = true;
    private boolean latexEnabled = true;
    
    // ==================== 调试配置 ====================
    private boolean debugMode = false;
    private boolean debugHighnoon = false;
    private boolean debugMathSoup = false;
    private boolean debugConcurrent = false;
    
    // ==================== 路径配置 ====================
    private String dataDir = "data";
    
    // ==================== 管理员配置 ====================
    private String adminUserIds = "";
    
    // ==================== AI 参数 - 数学定义 ====================
    private double mathTemperature = 0.3;
    private int mathMaxTokens = 512;
    private double mathTopP = 0.8;
    
    // ==================== AI 参数 - 随机回复 ====================
    private double randomTemperature = 0.8;
    private int randomMaxTokensMin = 30;
    private int randomMaxTokensMax = 100;
    private double randomTopP = 0.95;
    
    // ==================== 复读配置 ====================
    private double echoProbability = 0.01;
    private double echoReverseProbability = 0.2;
    
    // ==================== 系统设置 ====================
    private int maxHistoryPerGroup = 50;
    private int maxBanPerGroup = 10;
    private double bufferIntervalMs = 800.0;
    
    // ==================== AI 参数 - 数学海龟汤 ====================
    private double mathSoupTemperature = 0.3;
    
    // ==================== MCMOD 配置 ====================
    private String mcmodCaptureSelectors = "class-title,class-text-top";
    
    // ==================== Getter / Setter ====================
    
    public String getDeepseekApiKey() { return deepseekApiKey; }
    public void setDeepseekApiKey(String deepseekApiKey) { this.deepseekApiKey = deepseekApiKey; }
    
    public String getDeepseekBaseUrl() { return deepseekBaseUrl; }
    public void setDeepseekBaseUrl(String deepseekBaseUrl) { this.deepseekBaseUrl = deepseekBaseUrl; }
    
    public String getDeepseekModel() { return deepseekModel; }
    public void setDeepseekModel(String deepseekModel) { this.deepseekModel = deepseekModel; }
    
    public boolean isMathEnabled() { return mathEnabled; }
    public void setMathEnabled(boolean mathEnabled) { this.mathEnabled = mathEnabled; }
    
    public boolean isRandomEnabled() { return randomEnabled; }
    public void setRandomEnabled(boolean randomEnabled) { this.randomEnabled = randomEnabled; }
    
    public boolean isHighnoonEnabled() { return highnoonEnabled; }
    public void setHighnoonEnabled(boolean highnoonEnabled) { this.highnoonEnabled = highnoonEnabled; }
    
    public boolean isPjskpartitonEnabled() { return pjskpartitonEnabled; }
    public void setPjskpartitonEnabled(boolean pjskpartitonEnabled) { this.pjskpartitonEnabled = pjskpartitonEnabled; }
    
    public boolean isMathSoupEnabled() { return mathSoupEnabled; }
    public void setMathSoupEnabled(boolean mathSoupEnabled) { this.mathSoupEnabled = mathSoupEnabled; }
    
    public boolean isEchoEnabled() { return echoEnabled; }
    public void setEchoEnabled(boolean echoEnabled) { this.echoEnabled = echoEnabled; }
    
    public boolean isMcmodSearchEnabled() { return mcmodSearchEnabled; }
    public void setMcmodSearchEnabled(boolean mcmodSearchEnabled) { this.mcmodSearchEnabled = mcmodSearchEnabled; }
    
    public boolean isLatexEnabled() { return latexEnabled; }
    public void setLatexEnabled(boolean latexEnabled) { this.latexEnabled = latexEnabled; }
    
    public boolean isDebugMode() { return debugMode; }
    public void setDebugMode(boolean debugMode) { this.debugMode = debugMode; }
    
    public boolean isDebugHighnoon() { return debugHighnoon; }
    public void setDebugHighnoon(boolean debugHighnoon) { this.debugHighnoon = debugHighnoon; }
    
    public boolean isDebugMathSoup() { return debugMathSoup; }
    public void setDebugMathSoup(boolean debugMathSoup) { this.debugMathSoup = debugMathSoup; }
    
    public boolean isDebugConcurrent() { return debugConcurrent; }
    public void setDebugConcurrent(boolean debugConcurrent) { this.debugConcurrent = debugConcurrent; }
    
    public String getDataDir() { return dataDir; }
    public void setDataDir(String dataDir) { this.dataDir = dataDir; }
    
    public String getAdminUserIds() { return adminUserIds; }
    public void setAdminUserIds(String adminUserIds) { this.adminUserIds = adminUserIds; }
    
    public Set<Long> getAdminUserIdsSet() {
        if (adminUserIds == null || adminUserIds.isEmpty()) {
            return new HashSet<>();
        }
        return Arrays.stream(adminUserIds.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Long::parseLong)
                .collect(Collectors.toSet());
    }
    
    public double getMathTemperature() { return mathTemperature; }
    public void setMathTemperature(double mathTemperature) { this.mathTemperature = mathTemperature; }
    
    public int getMathMaxTokens() { return mathMaxTokens; }
    public void setMathMaxTokens(int mathMaxTokens) { this.mathMaxTokens = mathMaxTokens; }
    
    public double getMathTopP() { return mathTopP; }
    public void setMathTopP(double mathTopP) { this.mathTopP = mathTopP; }
    
    public double getRandomTemperature() { return randomTemperature; }
    public void setRandomTemperature(double randomTemperature) { this.randomTemperature = randomTemperature; }
    
    public int getRandomMaxTokensMin() { return randomMaxTokensMin; }
    public void setRandomMaxTokensMin(int randomMaxTokensMin) { this.randomMaxTokensMin = randomMaxTokensMin; }
    
    public int getRandomMaxTokensMax() { return randomMaxTokensMax; }
    public void setRandomMaxTokensMax(int randomMaxTokensMax) { this.randomMaxTokensMax = randomMaxTokensMax; }
    
    public double getRandomTopP() { return randomTopP; }
    public void setRandomTopP(double randomTopP) { this.randomTopP = randomTopP; }
    
    public double getEchoProbability() { return echoProbability; }
    public void setEchoProbability(double echoProbability) { this.echoProbability = echoProbability; }
    
    public double getEchoReverseProbability() { return echoReverseProbability; }
    public void setEchoReverseProbability(double echoReverseProbability) { this.echoReverseProbability = echoReverseProbability; }
    
    public int getMaxHistoryPerGroup() { return maxHistoryPerGroup; }
    public void setMaxHistoryPerGroup(int maxHistoryPerGroup) { this.maxHistoryPerGroup = maxHistoryPerGroup; }
    
    public int getMaxBanPerGroup() { return maxBanPerGroup; }
    public void setMaxBanPerGroup(int maxBanPerGroup) { this.maxBanPerGroup = maxBanPerGroup; }
    
    public double getBufferIntervalMs() { return bufferIntervalMs; }
    public void setBufferIntervalMs(double bufferIntervalMs) { this.bufferIntervalMs = bufferIntervalMs; }
    
    public double getMathSoupTemperature() { return mathSoupTemperature; }
    public void setMathSoupTemperature(double mathSoupTemperature) { this.mathSoupTemperature = mathSoupTemperature; }
    
    public String getMcmodCaptureSelectors() { return mcmodCaptureSelectors; }
    public void setMcmodCaptureSelectors(String mcmodCaptureSelectors) { this.mcmodCaptureSelectors = mcmodCaptureSelectors; }
    
    /**
     * 检查功能是否开启
     * 
     * @param feature 功能名称，如 "math", "highnoon"
     * @return 功能是否开启（默认 true）
     */
    public boolean isEnabled(String feature) {
        if (feature == null || feature.isEmpty()) {
            return true;
        }
        return switch (feature) {
            case "math" -> mathEnabled;
            case "random" -> randomEnabled;
            case "highnoon" -> highnoonEnabled;
            case "pjskpartiton" -> pjskpartitonEnabled;
            case "math_soup" -> mathSoupEnabled;
            case "echo" -> echoEnabled;
            case "mcmod_search" -> mcmodSearchEnabled;
            case "latex" -> latexEnabled;
            default -> true;
        };
    }
}
