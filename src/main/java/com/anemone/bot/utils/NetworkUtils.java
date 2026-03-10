package com.anemone.bot.utils;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 网络请求工具类
 * 
 * 提供HTTP请求的纯函数工具方法。
 * 支持同步和异步请求，GET/POST等方法。
 * 
 * 对应 Python 版本的 httpx/aiohttp 功能
 */
public class NetworkUtils {
    
    private static final Logger logger = LoggerFactory.getLogger(NetworkUtils.class);
    
    /** 默认超时时间（秒） */
    private static final int DEFAULT_TIMEOUT_SECONDS = 30;
    
    /** 共享的 HttpClient 实例 */
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(DEFAULT_TIMEOUT_SECONDS))
            .build();
    
    // ========== GET 请求 ==========
    
    /**
     * 发送 GET 请求，返回字符串响应
     * 
     * @param url 请求URL
     * @return 响应体字符串，失败返回 null
     */
    public static String get(String url) {
        return get(url, null, DEFAULT_TIMEOUT_SECONDS);
    }
    
    /**
     * 发送 GET 请求，带超时
     * 
     * @param url 请求URL
     * @param timeoutSeconds 超时时间（秒）
     * @return 响应体字符串，失败返回 null
     */
    public static String get(String url, int timeoutSeconds) {
        return get(url, null, timeoutSeconds);
    }
    
    /**
     * 发送 GET 请求，带请求头
     * 
     * @param url 请求URL
     * @param headers 请求头Map
     * @return 响应体字符串，失败返回 null
     */
    public static String get(String url, Map<String, String> headers) {
        return get(url, headers, DEFAULT_TIMEOUT_SECONDS);
    }
    
    /**
     * 发送 GET 请求，带请求头和超时
     * 
     * @param url 请求URL
     * @param headers 请求头Map
     * @param timeoutSeconds 超时时间（秒）
     * @return 响应体字符串，失败返回 null
     */
    public static String get(String url, Map<String, String> headers, int timeoutSeconds) {
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .GET();
            
            // 添加默认 User-Agent
            builder.header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
            
            // 添加自定义请求头
            if (headers != null) {
                headers.forEach(builder::header);
            }
            
            HttpRequest request = builder.build();
            HttpResponse<String> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            
            if (response.statusCode() == 200) {
                return response.body();
            } else {
                logger.warn("GET request failed: {} - HTTP {}", url, response.statusCode());
                return null;
            }
        } catch (IOException | InterruptedException e) {
            logger.error("GET request error: {} - {}", url, e.getMessage());
            return null;
        }
    }
    
    // ========== POST 请求 ==========
    
    /**
     * 发送 POST 请求（JSON 内容）
     * 
     * @param url 请求URL
     * @param body 请求体（JSON字符串）
     * @return 响应体字符串，失败返回 null
     */
    public static String postJson(String url, String body) {
        return postJson(url, body, null, DEFAULT_TIMEOUT_SECONDS);
    }
    
    /**
     * 发送 POST 请求（JSON 内容），带超时
     * 
     * @param url 请求URL
     * @param body 请求体（JSON字符串）
     * @param timeoutSeconds 超时时间（秒）
     * @return 响应体字符串，失败返回 null
     */
    public static String postJson(String url, String body, int timeoutSeconds) {
        return postJson(url, body, null, timeoutSeconds);
    }
    
    /**
     * 发送 POST 请求（JSON 内容），带请求头
     * 
     * @param url 请求URL
     * @param body 请求体（JSON字符串）
     * @param headers 请求头Map
     * @return 响应体字符串，失败返回 null
     */
    public static String postJson(String url, String body, Map<String, String> headers) {
        return postJson(url, body, headers, DEFAULT_TIMEOUT_SECONDS);
    }
    
    /**
     * 发送 POST 请求（JSON 内容），带请求头和超时
     * 
     * @param url 请求URL
     * @param body 请求体（JSON字符串）
     * @param headers 请求头Map
     * @param timeoutSeconds 超时时间（秒）
     * @return 响应体字符串，失败返回 null
     */
    public static String postJson(String url, String body, Map<String, String> headers, int timeoutSeconds) {
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .header("Content-Type", "application/json")
                    .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    .POST(HttpRequest.BodyPublishers.ofString(body != null ? body : "", StandardCharsets.UTF_8));
            
            // 添加自定义请求头
            if (headers != null) {
                headers.forEach(builder::header);
            }
            
            HttpRequest request = builder.build();
            HttpResponse<String> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            
            if (response.statusCode() == 200) {
                return response.body();
            } else {
                logger.warn("POST request failed: {} - HTTP {}", url, response.statusCode());
                return null;
            }
        } catch (IOException | InterruptedException e) {
            logger.error("POST request error: {} - {}", url, e.getMessage());
            return null;
        }
    }
    
    // ========== 异步请求 ==========
    
    /**
     * 异步发送 GET 请求
     * 
     * @param url 请求URL
     * @return CompletableFuture<响应体字符串>
     */
    public static CompletableFuture<String> getAsync(String url) {
        return getAsync(url, null, DEFAULT_TIMEOUT_SECONDS);
    }
    
    /**
     * 异步发送 GET 请求，带超时
     * 
     * @param url 请求URL
     * @param timeoutSeconds 超时时间（秒）
     * @return CompletableFuture<响应体字符串>
     */
    public static CompletableFuture<String> getAsync(String url, int timeoutSeconds) {
        return getAsync(url, null, timeoutSeconds);
    }
    
    /**
     * 异步发送 GET 请求，带请求头
     * 
     * @param url 请求URL
     * @param headers 请求头Map
     * @return CompletableFuture<响应体字符串>
     */
    public static CompletableFuture<String> getAsync(String url, Map<String, String> headers) {
        return getAsync(url, headers, DEFAULT_TIMEOUT_SECONDS);
    }
    
    /**
     * 异步发送 GET 请求
     * 
     * @param url 请求URL
     * @param headers 请求头Map
     * @param timeoutSeconds 超时时间（秒）
     * @return CompletableFuture<响应体字符串>
     */
    public static CompletableFuture<String> getAsync(String url, Map<String, String> headers, int timeoutSeconds) {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .GET();
        
        // 添加默认 User-Agent
        builder.header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
        
        // 添加自定义请求头
        if (headers != null) {
            headers.forEach(builder::header);
        }
        
        HttpRequest request = builder.build();
        
        return HTTP_CLIENT.sendAsync(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8))
                .thenApply(response -> {
                    if (response.statusCode() == 200) {
                        return response.body();
                    } else {
                        logger.warn("Async GET request failed: {} - HTTP {}", url, response.statusCode());
                        return null;
                    }
                })
                .exceptionally(e -> {
                    logger.error("Async GET request error: {} - {}", url, e.getMessage());
                    return null;
                });
    }
    
    /**
     * 异步发送 POST 请求（JSON 内容）
     * 
     * @param url 请求URL
     * @param body 请求体（JSON字符串）
     * @param headers 请求头Map
     * @param timeoutSeconds 超时时间（秒）
     * @return CompletableFuture<响应体字符串>
     */
    public static CompletableFuture<String> postJsonAsync(String url, String body, Map<String, String> headers, int timeoutSeconds) {
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .header("Content-Type", "application/json")
                .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .POST(HttpRequest.BodyPublishers.ofString(body != null ? body : "", StandardCharsets.UTF_8));
        
        // 添加自定义请求头
        if (headers != null) {
            headers.forEach(builder::header);
        }
        
        HttpRequest request = builder.build();
        
        return HTTP_CLIENT.sendAsync(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8))
                .thenApply(response -> {
                    if (response.statusCode() == 200) {
                        return response.body();
                    } else {
                        logger.warn("Async POST request failed: {} - HTTP {}", url, response.statusCode());
                        return null;
                    }
                })
                .exceptionally(e -> {
                    logger.error("Async POST request error: {} - {}", url, e.getMessage());
                    return null;
                });
    }
    
    // ========== 字节流请求 ==========
    
    /**
     * 发送 GET 请求，返回字节数组
     * 
     * @param url 请求URL
     * @return 响应字节数组，失败返回 null
     */
    public static byte[] getBytes(String url) {
        return getBytes(url, DEFAULT_TIMEOUT_SECONDS);
    }
    
    /**
     * 发送 GET 请求，返回字节数组
     * 
     * @param url 请求URL
     * @param timeoutSeconds 超时时间（秒）
     * @return 响应字节数组，失败返回 null
     */
    public static byte[] getBytes(String url, int timeoutSeconds) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(url))
                    .timeout(Duration.ofSeconds(timeoutSeconds))
                    .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    .GET()
                    .build();
            
            HttpResponse<byte[]> response = HTTP_CLIENT.send(request, HttpResponse.BodyHandlers.ofByteArray());
            
            if (response.statusCode() == 200) {
                return response.body();
            } else {
                logger.warn("GET bytes request failed: {} - HTTP {}", url, response.statusCode());
                return null;
            }
        } catch (IOException | InterruptedException e) {
            logger.error("GET bytes request error: {} - {}", url, e.getMessage());
            return null;
        }
    }
    
    /**
     * 异步发送 GET 请求，返回字节数组
     * 
     * @param url 请求URL
     * @param timeoutSeconds 超时时间（秒）
     * @return CompletableFuture<字节数组>
     */
    public static CompletableFuture<byte[]> getBytesAsync(String url, int timeoutSeconds) {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .GET()
                .build();
        
        return HTTP_CLIENT.sendAsync(request, HttpResponse.BodyHandlers.ofByteArray())
                .thenApply(response -> {
                    if (response.statusCode() == 200) {
                        return response.body();
                    } else {
                        logger.warn("Async GET bytes request failed: {} - HTTP {}", url, response.statusCode());
                        return null;
                    }
                })
                .exceptionally(e -> {
                    logger.error("Async GET bytes request error: {} - {}", url, e.getMessage());
                    return null;
                });
    }
}
