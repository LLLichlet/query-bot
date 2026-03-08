package com.anemone.bot.base;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.ConcurrentHashMap;

/**
 * 服务基类 - 统一管理单例模式和生命周期
 * 
 * 所有服务应继承此类，自动获得：
 * - 单例模式管理（全局唯一实例）
 * - 延迟初始化（首次使用时初始化）
 * - 日志记录器
 * - 初始化状态追踪
 * 
 * @param <T> 服务具体类型，用于类型安全的单例获取
 * 
 * Example:
 * <pre>{@code
 * public class MyService extends ServiceBase<MyService> {
 *     private String data;
 *     
 *     @Override
 *     protected void initialize() {
 *         data = "initialized";
 *     }
 *     
 *     public String getData() {
 *         return data;
 *     }
 * }
 * 
 * // 使用
 * MyService service = MyService.getInstance();
 * }</pre>
 */
public abstract class ServiceBase<T extends ServiceBase<T>> {
    
    private static final ConcurrentHashMap<Class<?>, ServiceBase<?>> instances = new ConcurrentHashMap<>();
    
    protected final Logger logger = LoggerFactory.getLogger(getClass());
    
    private volatile boolean initialized = false;
    private final Object initLock = new Object();
    
    /**
     * 获取服务单例实例
     * 
     * 这是获取服务实例的唯一方式，确保全局只有一个实例。
     * 首次调用时会创建实例并初始化，后续调用返回已创建的实例。
     * 
     * @return 服务的单例实例
     */
    @SuppressWarnings("unchecked")
    public static <S extends ServiceBase<S>> S getInstance(Class<S> clazz) {
        return (S) instances.computeIfAbsent(clazz, k -> {
            try {
                S instance = clazz.getDeclaredConstructor().newInstance();
                instance.ensureInitialized();
                return instance;
            } catch (Exception e) {
                throw new RuntimeException("Failed to create service instance: " + clazz.getName(), e);
            }
        });
    }
    
    /**
     * 子类使用的获取实例方法（需要在子类中覆盖为 public static）
     */
    protected static <S extends ServiceBase<S>> S getInstanceInternal(Class<S> clazz) {
        return getInstance(clazz);
    }
    
    /**
     * 检查服务是否已初始化
     */
    public boolean isInitialized() {
        return initialized;
    }
    
    /**
     * 确保服务已初始化
     * 
     * 如果未初始化，自动调用 initialize() 方法。
     * 线程安全，多次调用无影响。
     */
    public void ensureInitialized() {
        if (!initialized) {
            synchronized (initLock) {
                if (!initialized) {
                    initialize();
                    initialized = true;
                    logger.info("Service initialized: {}", getClass().getSimpleName());
                }
            }
        }
    }
    
    /**
     * 初始化服务（子类应重写）
     * 
     * 在这里执行实际的初始化逻辑，如连接数据库、加载配置等。
     * 此方法会被 ensureInitialized() 自动调用，不需要手动调用。
     * 
     * 注意：
     * - 多次调用应无副作用（幂等）
     * - 不要在此执行耗时操作，如需异步初始化请使用 @PostConstruct
     */
    protected void initialize() {
        // 子类重写
    }
    
    /**
     * 重置服务状态（用于测试）
     * 
     * 警告：生产环境慎用，可能导致状态丢失。
     */
    public void reset() {
        synchronized (initLock) {
            initialized = false;
            instances.remove(getClass());
        }
    }
}
