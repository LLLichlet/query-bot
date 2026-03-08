package com.anemone.bot.service;

import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.protocols.TokenServiceProtocol;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 令牌服务实现 - 一次性令牌管理
 * 
 * 服务层 - 实现 TokenServiceProtocol 协议
 * 
 * 使用 HMAC-SHA256 生成令牌，防止伪造。
 * 令牌有效期 5 分钟，单次使用即失效。
 * 使用 timing-safe 比较防止时序攻击。
 * 
 * Example:
 * <pre>{@code
 * TokenServiceProtocol tokenService = ServiceLocator.get(TokenServiceProtocol.class);
 * String token = tokenService.generateToken(123456L);
 * if (tokenService.verifyToken(123456L, token)) {
 *     // 验证成功，执行管理员操作
 * }
 * }</pre>
 */
@Service
public class TokenService implements TokenServiceProtocol {
    
    private static final Logger logger = LoggerFactory.getLogger(TokenService.class);
    
    // 令牌有效期：5分钟（秒）
    private static final long TOKEN_VALIDITY_SECONDS = 300;
    
    // 令牌长度
    private static final int TOKEN_LENGTH = 32;
    
    // 安全随机数生成器
    private final SecureRandom secureRandom = new SecureRandom();
    
    // HMAC 密钥（每次启动生成新的）
    private final byte[] hmacKey;
    
    // 令牌存储: userId -> TokenEntry
    private final Map<Long, TokenEntry> tokens = new ConcurrentHashMap<>();
    
    /**
     * 令牌条目
     */
    private static class TokenEntry {
        final String token;
        final long expiryTime;
        volatile boolean used;
        
        TokenEntry(String token, long expiryTime) {
            this.token = token;
            this.expiryTime = expiryTime;
            this.used = false;
        }
        
        boolean isExpired() {
            return Instant.now().getEpochSecond() > expiryTime;
        }
    }
    
    public TokenService() {
        // 生成随机 HMAC 密钥
        this.hmacKey = new byte[32];
        secureRandom.nextBytes(hmacKey);
    }
    
    /**
     * 初始化完成后注册到 ServiceLocator
     */
    @PostConstruct
    public void init() {
        ServiceLocator.register(TokenServiceProtocol.class, this);
        logger.info("TokenService initialized");
    }
    
    @Override
    public String generateToken(long userId) {
        // 生成随机令牌
        byte[] tokenBytes = new byte[TOKEN_LENGTH];
        secureRandom.nextBytes(tokenBytes);
        
        // 使用 HMAC-SHA256 签名
        String signature = hmac(tokenBytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(tokenBytes) + "." + signature;
        
        // 存储令牌
        long expiryTime = Instant.now().getEpochSecond() + TOKEN_VALIDITY_SECONDS;
        tokens.put(userId, new TokenEntry(token, expiryTime));
        
        logger.debug("Generated token for user {} (expires in {} seconds)", userId, TOKEN_VALIDITY_SECONDS);
        return token;
    }
    
    @Override
    public boolean verifyToken(long userId, String token) {
        if (token == null || token.isEmpty()) {
            return false;
        }
        
        TokenEntry entry = tokens.get(userId);
        if (entry == null) {
            logger.debug("No token found for user {}", userId);
            return false;
        }
        
        // 检查是否已使用
        if (entry.used) {
            logger.debug("Token already used for user {}", userId);
            return false;
        }
        
        // 检查是否过期
        if (entry.isExpired()) {
            logger.debug("Token expired for user {}", userId);
            tokens.remove(userId);
            return false;
        }
        
        // timing-safe 比较令牌
        if (!timingSafeCompare(entry.token, token)) {
            logger.debug("Token mismatch for user {}", userId);
            return false;
        }
        
        // 标记为已使用（单次使用）
        entry.used = true;
        tokens.remove(userId);
        
        logger.debug("Token verified successfully for user {}", userId);
        return true;
    }
    
    @Override
    public void invalidateTokens(long userId) {
        tokens.remove(userId);
        logger.debug("Invalidated tokens for user {}", userId);
    }
    
    @Override
    public void cleanupExpiredTokens() {
        int count = 0;
        
        for (Map.Entry<Long, TokenEntry> entry : tokens.entrySet()) {
            if (entry.getValue().isExpired()) {
                tokens.remove(entry.getKey());
                count++;
            }
        }
        
        if (count > 0) {
            logger.debug("Cleaned up {} expired tokens", count);
        }
    }
    
    /**
     * 计算 HMAC-SHA256 签名
     * 
     * @param data 数据
     * @return Base64 编码的签名
     */
    private String hmac(byte[] data) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec keySpec = new SecretKeySpec(hmacKey, "HmacSHA256");
            mac.init(keySpec);
            byte[] signature = mac.doFinal(data);
            return Base64.getUrlEncoder().withoutPadding().encodeToString(signature);
        } catch (java.security.NoSuchAlgorithmException | java.security.InvalidKeyException e) {
            logger.error("HMAC calculation failed", e);
            throw new RuntimeException("HMAC calculation failed", e);
        }
    }
    
    /**
     * timing-safe 字符串比较
     * 
     * 防止时序攻击，始终比较全部字符。
     * 
     * @param a 字符串 a
     * @param b 字符串 b
     * @return true 如果相等
     */
    private boolean timingSafeCompare(String a, String b) {
        if (a == null || b == null) {
            return Objects.equals(a, b);
        }
        
        byte[] aBytes = a.getBytes();
        byte[] bBytes = b.getBytes();
        
        int result = 0;
        int minLen = Math.min(aBytes.length, bBytes.length);
        
        for (int i = 0; i < minLen; i++) {
            result |= aBytes[i] ^ bBytes[i];
        }
        
        // 长度不同也影响结果
        result |= aBytes.length ^ bBytes.length;
        
        return result == 0;
    }
}
