package com.anemone.bot.plugins.mcmod;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.service.PluginRegistry;
import com.anemone.bot.utils.ImageUtils;
import com.anemone.bot.utils.TextUtils;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import jakarta.annotation.PostConstruct;

/**
 * MCMOD 模组查询处理器
 * 
 * 查询 Minecraft 模组信息，从 MCMOD 百科获取模组详情。
 * 支持模组名搜索、缩写搜索。
 * 
 * 触发方式:
 * - /mcmod - 随机模组
 * - /mcmod <模组ID> - 通过ID查询（如 /mcmod 2）
 * - /mcmod <模组名> - 通过名称搜索（如 /mcmod 工业时代2）
 * - /mcmod <缩写> - 通过缩写搜索（如 /mcmod IC2）
 * 
 * 配置:
 * anemone.bot.mcmod-search-enabled=true/false    # 功能开关
 * anemone.bot.mcmod-capture-selectors=class-title,class-text-top  # 截图选择器
 */
@Component
public class McmodSearchHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    // 模组数据
    private final List<ModInfo> modsList = new ArrayList<>();
    private final Map<String, Integer> nameToId = new HashMap<>();
    private final Map<String, Integer> abbrToId = new HashMap<>();
    
    // Selenium 操作使用专用线程池（阻塞时间长，避免占用 common pool）
    private final ExecutorService seleniumExecutor = Executors.newFixedThreadPool(2, r -> {
        Thread t = new Thread(r, "mcmod-selenium-" + System.nanoTime());
        t.setDaemon(true);
        return t;
    });
    
    @Autowired
    public McmodSearchHandler(PluginRegistry registry, BotConfig config) {
        super("MCMOD模组查询", "mcmod", Set.of("模组查询", "mcmod搜索"), "mcmod_search", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("mod_not_found", "Mod not found");
        errorMessages.put("data_load_failed", "Failed to load mod data");
        errorMessages.put("screenshot_failed", "Failed to capture screenshot, please try again later");
        errorMessages.put("image_process_failed", "Image processing failed");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "查询MCMOD百科的模组信息，支持ID、模组名和缩写搜索，无参数时随机返回", 
                "/mcmod [模组ID/模组名/缩写]");
        
        // 加载模组数据
        loadModData();
    }
    
    /**
     * 应用关闭时清理线程池
     */
    @jakarta.annotation.PreDestroy
    public void destroy() {
        seleniumExecutor.shutdown();
    }
    
    /**
     * 加载模组数据
     */
    private void loadModData() {
        try {
            ClassPathResource resource = new ClassPathResource("mcmod_data.json");
            if (!resource.exists()) {
                logger.error("mcmod_data.json not found in classpath");
                return;
            }
            
            try (InputStream is = resource.getInputStream()) {
                String content = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                JSONObject json = JSONUtil.parseObj(content);
                JSONArray modsArray = json.getJSONArray("mods");
                
                if (modsArray != null) {
                    for (int i = 0; i < modsArray.size(); i++) {
                        JSONObject obj = modsArray.getJSONObject(i);
                        int id = obj.getInt("id");
                        String nameCn = obj.getStr("name_cn", "");
                        String nameEn = obj.getStr("name_en", "");
                        String abbr = obj.getStr("abbreviation", "");
                        
                        ModInfo mod = new ModInfo(id, nameCn, nameEn, abbr);
                        modsList.add(mod);
                        
                        // 建立索引
                        if (!nameCn.isEmpty()) {
                            nameToId.put(nameCn.toLowerCase(), id);
                        }
                        if (!nameEn.isEmpty()) {
                            nameToId.put(nameEn.toLowerCase(), id);
                        }
                        if (!abbr.isEmpty()) {
                            abbrToId.put(abbr.toLowerCase(), id);
                        }
                    }
                }
                
                logger.info("Loaded {} mods from mcmod_data.json", modsList.size());
            }
        } catch (IOException e) {
            logger.error("Failed to load mcmod_data.json", e);
        }
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 检查功能开关
        if (!config.isMcmodSearchEnabled()) {
            return CompletableFuture.completedFuture(null);
        }
        
        // 查找模组
        final ModInfo mod;
        if (args == null || args.trim().isEmpty()) {
            // 随机模组
            mod = getRandomMod();
        } else {
            mod = findMod(args.trim());
        }
        
        if (mod == null) {
            return reply(bot, event, getErrorMessage("mod_not_found"));
        }
        
        // 发送查询提示
        return reply(bot, event, String.format("Querying %s, please wait...", mod.getDisplayName()))
            .thenCompose(v -> processModQuery(bot, event, mod));
    }
    
    /**
     * 处理模组查询（使用专用线程池执行 Selenium 操作）
     */
    private CompletableFuture<Void> processModQuery(Bot bot, AnyMessageEvent event, ModInfo mod) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 使用 ModDataExtractor 提取网页数据
                ModDataExtractor extractor = new ModDataExtractor(config);
                Result<List<java.awt.image.BufferedImage>> result = extractor.extract(mod.getId());
                
                if (result.isFailure()) {
                    return Result.err(result.getError());
                }
                
                List<java.awt.image.BufferedImage> images = result.getValue();
                if (images == null || images.isEmpty()) {
                    return Result.err("screenshot_failed");
                }
                
                // 合并图片
                java.awt.image.BufferedImage combined = ImageUtils.combineImagesVertically(images);
                if (combined == null) {
                    return Result.err("image_process_failed");
                }
                
                return Result.ok(combined);
            } catch (Exception e) {
                logger.error("Failed to process mod query", e);
                return Result.err("screenshot_failed");
            }
        }, seleniumExecutor).thenCompose(result -> handleImageResult(bot, event, result));
    }
    
    /**
     * 处理图片结果
     */
    @SuppressWarnings("unchecked")
    private CompletableFuture<Void> handleImageResult(Bot bot, AnyMessageEvent event, Object resultObj) {
        Result<java.awt.image.BufferedImage> result = (Result<java.awt.image.BufferedImage>) resultObj;
        
        if (result.isFailure()) {
            return reply(bot, event, getErrorMessage(result.getError()));
        }
        
        java.awt.image.BufferedImage image = result.getValue();
        
        // 转换为 CQ 码并发送（纯函数）
        String cqCode = ImageUtils.imageToCQCode(image);
        if (cqCode == null) {
            return reply(bot, event, getErrorMessage("image_process_failed"));
        }
        return send(bot, event, cqCode);
    }
    
    /**
     * 查找模组
     */
    private ModInfo findMod(String query) {
        String queryLower = query.toLowerCase().trim();
        
        // 1. ID 精确匹配
        if (query.matches("\\d+")) {
            int id = Integer.parseInt(query);
            for (ModInfo mod : modsList) {
                if (mod.getId() == id) {
                    return mod;
                }
            }
            return null;
        }
        
        // 2. 缩写精确匹配
        if (abbrToId.containsKey(queryLower)) {
            int id = abbrToId.get(queryLower);
            return findModById(id);
        }
        
        // 3. 名称精确匹配
        if (nameToId.containsKey(queryLower)) {
            int id = nameToId.get(queryLower);
            return findModById(id);
        }
        
        // 4. 相似度匹配
        ModInfo bestMatch = null;
        double bestScore = 0.0;
        
        for (ModInfo mod : modsList) {
            // 中文名称相似度
            if (!mod.getNameCn().isEmpty()) {
                double score = TextUtils.calculateSimilarity(queryLower, mod.getNameCn().toLowerCase());
                if (score > bestScore) {
                    bestScore = score;
                    bestMatch = mod;
                }
            }
            
            // 英文名称相似度
            if (!mod.getNameEn().isEmpty()) {
                double score = TextUtils.calculateSimilarity(queryLower, mod.getNameEn().toLowerCase());
                if (score > bestScore) {
                    bestScore = score;
                    bestMatch = mod;
                }
            }
        }
        
        // 相似度阈值 50
        if (bestMatch != null && bestScore > 50.0) {
            return bestMatch;
        }
        
        return null;
    }
    
    /**
     * 根据 ID 查找模组
     */
    private ModInfo findModById(int id) {
        for (ModInfo mod : modsList) {
            if (mod.getId() == id) {
                return mod;
            }
        }
        return null;
    }
    
    /**
     * 获取随机模组
     */
    private ModInfo getRandomMod() {
        if (modsList.isEmpty()) {
            return null;
        }
        return modsList.get(new Random().nextInt(modsList.size()));
    }
}
