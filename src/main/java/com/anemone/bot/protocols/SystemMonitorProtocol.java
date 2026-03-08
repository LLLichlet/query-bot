package com.anemone.bot.protocols;

import java.util.Map;

/**
 * 系统监控协议
 * 
 * 提供系统状态监控功能，包括 CPU、内存、JVM 等信息。
 * 
 * Example:
 * <pre>{@code
 * SystemMonitorProtocol monitor = ServiceLocator.get(SystemMonitorProtocol.class);
 * Map<String, Object> status = monitor.getSystemStatus();
 * String text = monitor.getStatusText();
 * }</pre>
 */
public interface SystemMonitorProtocol {
    
    /**
     * 获取系统状态信息
     * 
     * @return 系统状态字典
     */
    Map<String, Object> getSystemStatus();
    
    /**
     * 获取格式化的状态文本
     * 
     * @return 系统状态文本
     */
    String getStatusText();
    
    /**
     * 获取 JVM 内存信息
     * 
     * @return 内存信息字典
     */
    Map<String, Long> getMemoryInfo();
    
    /**
     * 获取 CPU 使用率
     * 
     * @return CPU 使用率（百分比）
     */
    double getCpuUsage();
    
    /**
     * 获取运行时间
     * 
     * @return 运行时间（毫秒）
     */
    long getUptime();
}
