package com.anemone.bot.protocols;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.ConcurrentHashMap;

/**
 * 服务定位器 - 解耦服务的获取与实现
 * 
 * 上层通过 locator 获取服务接口，不关心具体实现。
 * 下层在初始化完成后注册到 locator。
 * 
 * 采用类级别存储，全局统一管理所有服务注册。
 * 
 * Example:
 * <pre>{@code
 * // 服务层初始化完成后注册
 * aiService.initialize();
 * ServiceLocator.register(AIServiceProtocol.class, aiService);
 * 
 * // 插件层通过 locator 获取
 * AIServiceProtocol ai = ServiceLocator.get(AIServiceProtocol.class);
 * if (ai != null) {
 *     ai.chat(...);
 * }
 * }</pre>
 */
public class ServiceLocator {
    
    private static final Logger logger = LoggerFactory.getLogger(ServiceLocator.class);
    
    private static final ConcurrentHashMap<Class<?>, Object> services = new ConcurrentHashMap<>();
    
    /**
     * 注册服务实现
     * 
     * @param protocol 协议接口类
     * @param implementation 协议实现实例
     * @param <T> 服务类型
     */
    public static <T> void register(Class<T> protocol, T implementation) {
        services.put(protocol, implementation);
        logger.info("Registered service: {} -> {}", protocol.getSimpleName(), implementation.getClass().getSimpleName());
    }
    
    /**
     * 获取服务实现
     * 
     * @param protocol 协议接口类
     * @param <T> 服务类型
     * @return 协议实现实例，如果未注册返回 null
     */
    @SuppressWarnings("unchecked")
    public static <T> T get(Class<T> protocol) {
        return (T) services.get(protocol);
    }
    
    /**
     * 检查是否已注册某协议
     * 
     * @param protocol 协议接口类
     * @return True 如果该协议已有实现注册
     */
    public static boolean has(Class<?> protocol) {
        return services.containsKey(protocol);
    }
    
    /**
     * 注销服务
     * 
     * @param protocol 协议接口类
     */
    public static void unregister(Class<?> protocol) {
        services.remove(protocol);
        logger.info("Unregistered service: {}", protocol.getSimpleName());
    }
    
    /**
     * 清空所有服务（主要用于测试）
     */
    public static void clear() {
        services.clear();
        logger.info("Cleared all services");
    }
}
