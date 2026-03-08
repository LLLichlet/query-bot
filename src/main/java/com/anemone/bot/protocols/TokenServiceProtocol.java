package com.anemone.bot.protocols;

/**
 * 令牌服务协议
 * 
 * 管理一次性令牌的生成和验证，用于管理员身份验证。
 * 令牌有效期 5 分钟，单次使用。
 * 
 * Example:
 * <pre>{@code
 * TokenServiceProtocol tokenService = ServiceLocator.get(TokenServiceProtocol.class);
 * String token = tokenService.generateToken(123456L);
 * boolean valid = tokenService.verifyToken(123456L, token);
 * }</pre>
 */
public interface TokenServiceProtocol {
    
    /**
     * 生成一次性令牌
     * 
     * @param userId 用户 QQ 号
     * @return 令牌字符串
     */
    String generateToken(long userId);
    
    /**
     * 验证令牌是否有效
     * 
     * 验证成功后会立即使令牌失效（单次使用）。
     * 
     * @param userId 用户 QQ 号
     * @param token 令牌字符串
     * @return true 如果令牌有效且未过期
     */
    boolean verifyToken(long userId, String token);
    
    /**
     * 使指定用户的所有令牌失效
     * 
     * @param userId 用户 QQ 号
     */
    void invalidateTokens(long userId);
    
    /**
     * 清理所有过期的令牌
     */
    void cleanupExpiredTokens();
}
