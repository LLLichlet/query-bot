package com.anemone.bot.service;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;
import com.anemone.bot.protocols.BanServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 黑名单服务实现 - 用户管理
 * 
 * 服务层 - 实现 BanServiceProtocol 协议
 * 
 * 管理用户黑名单，支持拉黑、解封和检查操作。
 * 黑名单数据持久化到 JSON 文件。
 * 
 * Example:
 * <pre>{@code
 * BanServiceProtocol ban = ServiceLocator.get(BanServiceProtocol.class);
 * if (ban.isBanned(123456L)) {
 *     System.out.println("用户已被拉黑");
 * }
 * ban.ban(123456L);
 * }</pre>
 */
@Service
public class BanService implements BanServiceProtocol {
    
    private static final Logger logger = LoggerFactory.getLogger(BanService.class);
    
    private final BotConfig config;
    
    // 内存中的黑名单集合
    private final Set<Long> bannedUsers = ConcurrentHashMap.newKeySet();
    
    // 数据文件路径
    private Path dataFilePath;
    
    // 是否已初始化
    private volatile boolean initialized = false;
    
    /**
     * 创建黑名单服务
     * 
     * @param config 机器人配置
     */
    @Autowired
    public BanService(BotConfig config) {
        this.config = config;
    }
    
    /**
     * 初始化服务
     */
    @PostConstruct
    public void init() {
        // 设置数据文件路径
        String dataDir = config.getDataDir();
        if (dataDir == null || dataDir.isEmpty()) {
            dataDir = "data";
        }
        this.dataFilePath = Paths.get(dataDir, "banned.json");
        
        // 加载已保存的黑名单
        loadFromFile();
        
        // 注册到 ServiceLocator
        ServiceLocator.register(BanServiceProtocol.class, this);
        
        initialized = true;
        logger.info("BanService initialized, {} users banned", bannedUsers.size());
    }
    
    @Override
    public boolean isBanned(long userId) {
        ensureInitialized();
        return bannedUsers.contains(userId);
    }
    
    @Override
    public Result<Boolean> ban(long userId) {
        ensureInitialized();
        
        if (bannedUsers.contains(userId)) {
            return Result.ok(true); // 已经是黑名单
        }
        
        bannedUsers.add(userId);
        saveToFile();
        
        logger.info("User {} has been banned", userId);
        return Result.ok(true);
    }
    
    @Override
    public Result<Boolean> unban(long userId) {
        ensureInitialized();
        
        if (!bannedUsers.contains(userId)) {
            return Result.ok(true); // 本来就不在黑名单
        }
        
        bannedUsers.remove(userId);
        saveToFile();
        
        logger.info("User {} has been unbanned", userId);
        return Result.ok(true);
    }
    
    /**
     * 获取被拉黑的用户数量
     * 
     * @return 黑名单数量
     */
    public int getBannedCount() {
        return bannedUsers.size();
    }
    
    /**
     * 获取所有被拉黑的用户ID
     * 
     * @return 用户ID集合
     */
    public Set<Long> getAllBannedUsers() {
        return new HashSet<>(bannedUsers);
    }
    
    /**
     * 从文件加载黑名单
     */
    private void loadFromFile() {
        try {
            // 确保目录存在
            Files.createDirectories(dataFilePath.getParent());
            
            if (!Files.exists(dataFilePath)) {
                // 文件不存在，创建空文件
                saveToFile();
                return;
            }
            
            String content = Files.readString(dataFilePath);
            if (content == null || content.trim().isEmpty()) {
                return;
            }
            
            JSONObject json = JSONUtil.parseObj(content);
            JSONArray users = json.getJSONArray("banned_users");
            
            if (users != null) {
                bannedUsers.clear();
                for (int i = 0; i < users.size(); i++) {
                    if (users.get(i) instanceof Number num) {
                        bannedUsers.add(num.longValue());
                    }
                }
            }
            
            logger.debug("Loaded {} banned users from {}", bannedUsers.size(), dataFilePath);
            
        } catch (IOException | cn.hutool.json.JSONException e) {
            logger.error("Failed to load banned users from file: {}", dataFilePath, e);
        }
    }
    
    /**
     * 保存黑名单到文件
     */
    private void saveToFile() {
        try {
            // 确保目录存在
            Files.createDirectories(dataFilePath.getParent());
            
            JSONObject json = new JSONObject();
            JSONArray users = new JSONArray();
            
            for (Long userId : bannedUsers) {
                users.add(userId);
            }
            
            json.set("banned_users", users);
            json.set("count", bannedUsers.size());
            json.set("version", 1);
            
            Files.writeString(dataFilePath, json.toStringPretty());
            
            logger.debug("Saved {} banned users to {}", bannedUsers.size(), dataFilePath);
            
        } catch (IOException e) {
            logger.error("Failed to save banned users to file: {}", dataFilePath, e);
        }
    }
    
    /**
     * 确保服务已初始化
     */
    private void ensureInitialized() {
        if (!initialized) {
            throw new IllegalStateException("BanService not initialized");
        }
    }
}
