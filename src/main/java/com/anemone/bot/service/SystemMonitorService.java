package com.anemone.bot.service;

import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.protocols.SystemMonitorProtocol;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;
import java.lang.management.RuntimeMXBean;
import java.text.DecimalFormat;
import java.util.HashMap;
import java.util.Map;

/**
 * 系统监控服务实现
 * 
 * 服务层 - 实现 SystemMonitorProtocol 协议
 * 
 * 提供系统状态监控功能，包括 CPU、内存、JVM 等信息。
 * 
 * Example:
 * <pre>{@code
 * SystemMonitorProtocol monitor = ServiceLocator.get(SystemMonitorProtocol.class);
 * String status = monitor.getStatusText();
 * }</pre>
 */
@Service
public class SystemMonitorService implements SystemMonitorProtocol {
    
    private static final Logger logger = LoggerFactory.getLogger(SystemMonitorService.class);
    
    private final MemoryMXBean memoryMXBean = ManagementFactory.getMemoryMXBean();
    
    // 启动时间
    private final long startTime = System.currentTimeMillis();
    
    /**
     * 初始化完成后注册到 ServiceLocator
     */
    @PostConstruct
    public void init() {
        ServiceLocator.register(SystemMonitorProtocol.class, this);
        logger.info("SystemMonitorService initialized");
    }
    
    @Override
    public Map<String, Object> getSystemStatus() {
        Map<String, Object> status = new HashMap<>();
        
        // JVM 内存
        status.put("memory", getMemoryInfo());
        
        // CPU
        status.put("cpuUsage", getCpuUsage());
        
        // 运行时间
        status.put("uptime", getUptime());
        
        // JVM 信息
        status.put("jvmName", System.getProperty("java.vm.name"));
        status.put("jvmVersion", System.getProperty("java.version"));
        
        // 线程数
        status.put("threadCount", Thread.activeCount());
        
        return status;
    }
    
    @Override
    public String getStatusText() {
        Map<String, Long> memory = getMemoryInfo();
        double cpuUsage = getCpuUsage();
        long uptime = getUptime();
        
        DecimalFormat df = new DecimalFormat("0.0");
        
        StringBuilder sb = new StringBuilder();
        sb.append("=== System Status ===\n");
        
        // 内存信息
        Long used = memory.get("used");
        Long committed = memory.get("committed");
        Long max = memory.get("max");
        
        if (used != null && committed != null && max != null) {
            long usedMB = used / 1024 / 1024;
            long committedMB = committed / 1024 / 1024;
            long maxMB = max / 1024 / 1024;
            double memoryPercent = max > 0 ? (double) used / max * 100 : 0.0;
            
            sb.append(String.format("Memory: %d MB / %d MB (Max: %d MB, %.1f%%)%n", 
                usedMB, committedMB, maxMB, memoryPercent));
        } else {
            sb.append("Memory: N/A%n");
        }
        
        // CPU 使用率
        sb.append(String.format("CPU: %s%%%n", df.format(cpuUsage)));
        
        // 运行时间
        sb.append(String.format("Uptime: %s%n", formatUptime(uptime)));
        
        // JVM 信息
        sb.append(String.format("JVM: %s %s%n", 
            System.getProperty("java.vm.name"),
            System.getProperty("java.version")));
        
        // 线程数
        sb.append(String.format("Threads: %d%n", Thread.activeCount()));
        
        return sb.toString();
    }
    
    @Override
    public Map<String, Long> getMemoryInfo() {
        Map<String, Long> info = new HashMap<>();
        
        // 堆内存
        MemoryUsage heapUsage = memoryMXBean.getHeapMemoryUsage();
        info.put("heapUsed", heapUsage.getUsed());
        info.put("heapCommitted", heapUsage.getCommitted());
        info.put("heapMax", heapUsage.getMax());
        
        // 非堆内存
        MemoryUsage nonHeapUsage = memoryMXBean.getNonHeapMemoryUsage();
        info.put("nonHeapUsed", nonHeapUsage.getUsed());
        
        // 汇总
        info.put("used", heapUsage.getUsed() + nonHeapUsage.getUsed());
        info.put("committed", heapUsage.getCommitted());
        info.put("max", heapUsage.getMax());
        
        return info;
    }
    
    @Override
    public double getCpuUsage() {
        // 使用 com.sun.management.OperatingSystemMXBean 获取进程 CPU 使用率
        // 注意：这是 Sun 的扩展 API，不是标准 Java API，但在 OpenJDK 和 Oracle JDK 中都可用
        try {
            com.sun.management.OperatingSystemMXBean osBean = 
                (com.sun.management.OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();
            
            // 获取进程 CPU 负载（0.0-1.0）
            double cpuLoad = osBean.getProcessCpuLoad();
            
            // 如果返回负值，表示数据暂时不可用
            if (cpuLoad < 0) {
                return 0.0;
            }
            
            // 转换为百分比
            return cpuLoad * 100.0;
            
        } catch (Exception e) {
            logger.debug("Failed to get CPU usage: {}", e.getMessage());
            return 0.0;
        }
    }
    
    @Override
    public long getUptime() {
        return System.currentTimeMillis() - startTime;
    }
    
    /**
     * 格式化运行时间
     * 
     * @param uptimeMillis 运行时间（毫秒）
     * @return 格式化字符串
     */
    private String formatUptime(long uptimeMillis) {
        long seconds = uptimeMillis / 1000;
        long minutes = seconds / 60;
        long hours = minutes / 60;
        long days = hours / 24;
        
        if (days > 0) {
            return String.format("%dd %dh %dm", days, hours % 24, minutes % 60);
        } else if (hours > 0) {
            return String.format("%dh %dm", hours, minutes % 60);
        } else if (minutes > 0) {
            return String.format("%dm %ds", minutes, seconds % 60);
        } else {
            return String.format("%ds", seconds);
        }
    }
}
