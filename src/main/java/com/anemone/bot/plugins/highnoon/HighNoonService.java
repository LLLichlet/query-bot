package com.anemone.bot.plugins.highnoon;

import com.anemone.bot.base.Result;

import java.util.Map;
import java.util.Random;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 午时已到游戏服务
 * 
 * 实现俄罗斯轮盘赌禁言游戏逻辑，包括开始游戏、开枪、禁言等功能。
 * 使用单例模式管理所有群聊的游戏状态。
 * 
 * Example:
 * <pre>{@code
 * HighNoonService service = HighNoonService.getInstance();
 * service.startGame(123456L);
 * 
 * // 玩家开枪
 * Result<FireResult> result = service.fire(123456L, 789L, "玩家名").join();
 * if (result.getValue().isHit()) {
 *     // 中弹，执行禁言
 * }
 * }</pre>
 */
public class HighNoonService {
    
    private static final HighNoonService INSTANCE = new HighNoonService();
    
    private final Random random = new Random();
    
    // 游戏状态映射: groupId -> 游戏状态
    private final Map<Long, HighNoonState> games = new ConcurrentHashMap<>();
    
    // 开枪时的台词
    private static final String[] STATEMENTS = {
        "无需退路。( 1 / 6 )",
        "英雄们啊，为这最强大的信念，请站在我们这边。( 2 / 6 )",
        "颤抖吧，在真正的勇敢面前。( 3 / 6 )",
        "哭嚎吧，为你们不堪一击的信念。( 4 / 6 )",
        "现在可没有后悔的余地了。( 5 / 6 )"
    };
    
    /**
     * 开枪结果
     */
    public static class FireResult {
        public final boolean hit;
        public final String message;
        public final boolean gameOver;
        public final int shotCount;
        
        public FireResult(boolean hit, String message, boolean gameOver, int shotCount) {
            this.hit = hit;
            this.message = message;
            this.gameOver = gameOver;
            this.shotCount = shotCount;
        }
        
        public boolean isHit() {
            return hit;
        }
    }
    
    /**
     * 私有构造函数
     */
    private HighNoonService() {}
    
    /**
     * 获取服务单例实例
     * 
     * @return HighNoonService 实例
     */
    public static HighNoonService getInstance() {
        return INSTANCE;
    }
    
    /**
     * 开始新游戏
     * 
     * @param groupId 群号
     * @return 异步结果，包含游戏状态
     */
    public CompletableFuture<Result<HighNoonState>> startGame(long groupId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 如果已有活跃游戏，先结束它
                HighNoonState existingGame = games.get(groupId);
                if (existingGame != null && existingGame.isActive) {
                    endGame(groupId);
                }
                
                // 创建新游戏
                HighNoonState newGame = createGame(groupId);
                games.put(groupId, newGame);
                
                return Result.ok(newGame);
                
            } catch (Exception e) {
                return Result.err("Failed to start game: " + e.getMessage());
            }
        });
    }
    
    /**
     * 创建新游戏状态
     * 
     * @param groupId 群号
     * @return 新创建的游戏状态
     */
    private HighNoonState createGame(long groupId) {
        HighNoonState state = new HighNoonState(groupId);
        state.bulletPos = random.nextInt(6) + 1; // 1-6
        state.shotCount = 0;
        return state;
    }
    
    /**
     * 结束游戏
     * 
     * @param groupId 群号
     * @return True 如果成功结束游戏，False 如果没有活跃游戏
     */
    public boolean endGame(long groupId) {
        HighNoonState game = games.get(groupId);
        if (game != null && game.isActive) {
            game.isActive = false;
            games.remove(groupId);
            return true;
        }
        return false;
    }
    
    /**
     * 获取游戏状态
     * 
     * @param groupId 群号
     * @return 游戏状态，如果没有活跃游戏返回 null
     */
    public HighNoonState getGame(long groupId) {
        HighNoonState game = games.get(groupId);
        if (game != null && game.isActive) {
            return game;
        }
        return null;
    }
    
    /**
     * 检查是否有活跃游戏
     * 
     * @param groupId 群号
     * @return True 如果有活跃游戏
     */
    public boolean hasActiveGame(long groupId) {
        HighNoonState game = games.get(groupId);
        return game != null && game.isActive;
    }
    
    /**
     * 处理开枪
     * 
     * @param groupId 群号
     * @param userId 用户QQ号
     * @param username 用户名
     * @return 异步开枪结果
     */
    public CompletableFuture<Result<FireResult>> fire(long groupId, long userId, String username) {
        return CompletableFuture.supplyAsync(() -> {
            HighNoonState game = getGame(groupId);
            if (game == null || !game.isActive) {
                return Result.err("no_active_game");
            }
            
            // 添加玩家到列表
            if (!game.players.contains(userId)) {
                game.players.add(userId);
            }
            
            game.shotCount++;
            
            // 检查是否中弹
            if (game.shotCount == game.bulletPos) {
                endGame(groupId);
                return Result.ok(new FireResult(
                    true,
                    String.format("来吧,%s,鲜血会染红这神圣的场所", username),
                    true,
                    game.shotCount
                ));
            } else {
                // 未中弹，返回台词
                String statement = game.shotCount <= STATEMENTS.length 
                    ? STATEMENTS[game.shotCount - 1] 
                    : "...";
                return Result.ok(new FireResult(
                    false,
                    statement,
                    false,
                    game.shotCount
                ));
            }
        });
    }
    
    /**
     * 获取当前游戏信息（用于调试）
     * 
     * @param groupId 群号
     * @return 游戏信息字符串
     */
    public String getGameInfo(long groupId) {
        HighNoonState game = getGame(groupId);
        if (game == null || !game.isActive) {
            return "No active game";
        }
        return String.format("Bullet: %d/%d, Players: %d", 
            game.bulletPos, game.shotCount, game.players.size());
    }
}
