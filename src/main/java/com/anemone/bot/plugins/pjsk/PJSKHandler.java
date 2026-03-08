package com.anemone.bot.plugins.pjsk;

import com.anemone.bot.config.BotConfig;
import com.anemone.bot.handler.PluginHandler;
import com.anemone.bot.service.PluginRegistry;
import com.anemone.bot.utils.ImageUtils;
import com.anemone.bot.utils.TextUtils;
import com.mikuac.shiro.core.Bot;
import com.mikuac.shiro.dto.event.message.AnyMessageEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.awt.image.BufferedImage;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * PJSK 谱面插件
 * 
 * Project Sekai（世界计划）游戏谱面图片查询。
 * 支持随机谱面、指定编号或歌曲名搜索。
 * 
 * 触发方式:
 * - /chart - 随机谱面
 * - /chart <编号> - 指定编号谱面（如 /chart 001）
 * - /chart <歌曲名> - 搜索歌曲谱面（如 /chart Tell Your World）
 * - /chart [编号/歌曲名] [难度] - 指定难度（exp/mst/apd）
 */
@Component
public class PJSKHandler extends PluginHandler {
    
    private final PluginRegistry registry;
    private final BotConfig config;
    
    // 歌曲数据
    private Map<String, String> idToName = new HashMap<>();
    private List<SongInfo> songs = new ArrayList<>();
    
    // 难度选项
    private static final List<String> DIFFICULTIES = Arrays.asList("exp", "mst", "apd");
    
    @Autowired
    public PJSKHandler(PluginRegistry registry, BotConfig config) {
        super("PJSK谱面", "chart", Set.of("pjsk随机谱面", "pjsk谱面"), "pjskpartiton", 10, true, false);
        this.registry = registry;
        this.config = config;
        
        // 注册错误消息
        errorMessages.put("invalid_song_id", "Song ID must be between 1 and 639");
        errorMessages.put("song_not_found", "Song not found");
        errorMessages.put("download_failed", "Network error, please try again later");
        errorMessages.put("merge_failed", "Failed to merge images");
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "pjsk谱面相关功能，支持随机、指定编号、搜索歌曲名", 
                "/chart [编号/歌曲名] [难度(exp/mst/apd)]");
        loadSongsData();
    }
    
    /**
     * 歌曲信息类
     */
    private static class SongInfo {
        final String id;
        final String name;
        
        SongInfo(String id, String name) {
            this.id = id;
            this.name = name;
        }
    }
    
    /**
     * 加载歌曲数据
     */
    private void loadSongsData() {
        try {
            InputStream is = getClass().getClassLoader().getResourceAsStream("pjsk_songs.json");
            if (is == null) {
                logger.warn("pjsk_songs.json not found in classpath");
                return;
            }
            
            String json = new String(is.readAllBytes(), StandardCharsets.UTF_8);
            parseSongsJson(json);
            
            logger.info("Loaded {} PJSK songs", songs.size());
        } catch (Exception e) {
            logger.error("Failed to load PJSK songs data", e);
        }
    }
    
    /**
     * 解析歌曲 JSON
     */
    private void parseSongsJson(String json) {
        // 简单解析：提取 id_str 和 name
        Pattern songPattern = Pattern.compile("\\{[^}]*\"id_str\"\\s*:\\s*\"([^\"]+)\"[^}]*\"name\"\\s*:\\s*\"([^\"]+)\"");
        Matcher matcher = songPattern.matcher(json);
        
        while (matcher.find()) {
            String id = matcher.group(1);
            String name = matcher.group(2);
            songs.add(new SongInfo(id, name));
            idToName.put(id, name);
        }
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        // 检查功能开关
        if (!config.isEnabled("pjskpartiton")) {
            logger.debug("PJSK feature is disabled");
            return CompletableFuture.completedFuture(null);
        }
        
        // 解析参数
        ParseResult parseResult = parseArgs(args);
        if (parseResult.songId == null) {
            return reply(bot, event, getErrorMessage(parseResult.error));
        }
        
        String songId = parseResult.songId;
        String songName = parseResult.songName;
        String difficulty = parseResult.difficulty;
        
        // 发送歌曲名（非随机模式）
        if (args != null && !args.trim().isEmpty() && songName != null) {
            reply(bot, event, songName);
        }
        
        // 下载并合并图片
        return processChart(bot, event, songId, difficulty);
    }
    
    /**
     * 解析参数结果
     */
    private static class ParseResult {
        String songId;
        String songName;
        String difficulty;
        String error;
        
        ParseResult(String songId, String songName, String difficulty) {
            this.songId = songId;
            this.songName = songName;
            this.difficulty = difficulty;
        }
        
        ParseResult(String error) {
            this.error = error;
        }
    }
    
    /**
     * 解析命令参数
     */
    private ParseResult parseArgs(String args) {
        if (args == null || args.trim().isEmpty()) {
            // 随机模式
            String songId = String.format("%03d", new Random().nextInt(639) + 1);
            String songName = idToName.getOrDefault(songId, "Unknown");
            String difficulty = DIFFICULTIES.get(new Random().nextInt(DIFFICULTIES.size()));
            return new ParseResult(songId, songName, difficulty);
        }
        
        String input = args.trim();
        
        // 检查难度参数
        Pattern diffPattern = Pattern.compile("\\s+(exp|mst|apd)$", Pattern.CASE_INSENSITIVE);
        Matcher diffMatcher = diffPattern.matcher(input);
        String difficulty;
        if (diffMatcher.find()) {
            difficulty = diffMatcher.group(1).toLowerCase();
            input = input.substring(0, diffMatcher.start()).trim();
        } else {
            difficulty = DIFFICULTIES.get(new Random().nextInt(DIFFICULTIES.size()));
        }
        
        // 判断是编号还是歌曲名
        if (input.matches("\\d+")) {
            int num = Integer.parseInt(input);
            if (num >= 1 && num <= 639) {
                String songId = String.format("%03d", num);
                String songName = idToName.get(songId);
                return new ParseResult(songId, songName, difficulty);
            } else {
                return new ParseResult("invalid_song_id");
            }
        } else {
            // 使用 TextUtils 进行歌曲名模糊搜索
            SongMatch match = findSong(input);
            if (match != null) {
                return new ParseResult(match.id, match.name, difficulty);
            } else {
                return new ParseResult("song_not_found");
            }
        }
    }
    
    /**
     * 歌曲匹配结果
     */
    private static class SongMatch {
        String id;
        String name;
        
        SongMatch(String id, String name) {
            this.id = id;
            this.name = name;
        }
    }
    
    /**
     * 根据歌曲名搜索（使用 TextUtils 的相似度计算）
     */
    private SongMatch findSong(String query) {
        SongMatch bestMatch = null;
        double bestScore = 0.0;
        
        for (SongInfo song : songs) {
            // 完全匹配
            if (query.equalsIgnoreCase(song.name)) {
                return new SongMatch(song.id, song.name);
            }
            
            // 使用 TextUtils 计算相似度
            double score = TextUtils.calculateSimilarity(query, song.name);
            if (score > bestScore) {
                bestScore = score;
                bestMatch = new SongMatch(song.id, song.name);
            }
        }
        
        // 相似度阈值 40（TextUtils 返回 0-100）
        if (bestMatch != null && bestScore > 40.0) {
            logger.debug("Found song match: {} with score {}", bestMatch.name, bestScore);
            return bestMatch;
        }
        return null;
    }
    
    /**
     * 处理谱面图片下载和发送
     */
    private CompletableFuture<Void> processChart(Bot bot, AnyMessageEvent event, String songId, String difficulty) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 构建 URL
                String bgUrl = "https://sdvx.in/prsk/bg/" + songId + "bg.png";
                String barUrl = "https://sdvx.in/prsk/bg/" + songId + "bar.png";
                String dataUrl = "https://sdvx.in/prsk/obj/data" + songId + difficulty + ".png";
                
                logger.debug("Downloading images for song {}: bg={}, data={}", songId, bgUrl, dataUrl);
                
                // 使用 ImageUtils 下载图片
                BufferedImage bg = ImageUtils.downloadImage(bgUrl);
                BufferedImage bar = ImageUtils.downloadImage(barUrl);
                BufferedImage data = ImageUtils.downloadImage(dataUrl);
                
                if (bg == null || bar == null || data == null) {
                    throw new RuntimeException("download_failed");
                }
                
                // 使用 ImageUtils 合并图片
                BufferedImage merged = ImageUtils.mergeImages(bg, data, bar);
                if (merged == null) {
                    throw new RuntimeException("merge_failed");
                }
                
                // 生成 CQ 码
                String base64Image = ImageUtils.imageToBase64(merged);
                if (base64Image == null) {
                    throw new RuntimeException("merge_failed");
                }
                
                return ImageUtils.createCQImage(base64Image);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }).thenCompose(cqCode -> {
            // 发送图片
            try {
                Long groupId = event.getGroupId();
                if (groupId != null && groupId > 0) {
                    bot.sendGroupMsg(groupId, cqCode, false);
                } else {
                    bot.sendPrivateMsg(event.getUserId(), cqCode, false);
                }
                return CompletableFuture.completedFuture(null);
            } catch (Exception e) {
                logger.error("Failed to send image", e);
                return reply(bot, event, getErrorMessage("merge_failed"));
            }
        }).exceptionally(e -> {
            logger.error("Failed to process chart", e);
            String errorMsg = e.getCause() != null && e.getCause().getMessage() != null 
                    ? getErrorMessage(e.getCause().getMessage()) 
                    : getErrorMessage("download_failed");
            reply(bot, event, errorMsg);
            return null;
        });
    }
}
