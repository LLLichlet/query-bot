package com.anemone.bot.protocols;

import com.anemone.bot.base.Result;

/**
 * 黑名单服务协议
 * 
 * 管理用户黑名单，支持拉黑、解封和检查操作。
 * 
 * Example:
 * <pre>{@code
 * BanServiceProtocol ban = ServiceLocator.get(BanServiceProtocol.class);
 * if (ban.isBanned(123456L)) {
 *     System.out.println("用户已被拉黑");
 * }
 * }</pre>
 */
public interface BanServiceProtocol {
    
    /**
     * 检查用户是否被拉黑
     * 
     * @param userId 用户 QQ 号
     * @return True 如果用户已被拉黑
     */
    boolean isBanned(long userId);
    
    /**
     * 拉黑用户
     * 
     * @param userId 用户 QQ 号
     * @return 操作结果
     */
    Result<Boolean> ban(long userId);
    
    /**
     * 解封用户
     * 
     * @param userId 用户 QQ 号
     * @return 操作结果
     */
    Result<Boolean> unban(long userId);
}
