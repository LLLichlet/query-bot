package com.anemone.bot.service;

import com.anemone.bot.base.GameState;
import com.anemone.bot.base.Result;
import com.anemone.bot.base.ServiceBase;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * 游戏服务基类 - 统一管理游戏状态
 * 
 * 所有游戏服务应继承此类，自动获得：
 * - 游戏状态管理（按群号隔离）
 * - 多群并发支持（线程安全）
 * - 游戏生命周期管理
 * 
 * @param <T> 游戏状态类型，必须继承 GameState
 * 
 * Example:
 * <pre>{@code
 * public class MyGameService extends GameServiceBase<MyGameState> {
 *     
 *     public static MyGameService getInstance() {
 *         return getInstance(MyGameService.class);
 *     }
 *     
 *     @Override
 *     protected MyGameState createGame(long groupId, Object... kwargs) {
 *         return new MyGameState(groupId);
 *     }
 *     
 *     public void someGameAction(long groupId) {
 *         MyGameState state = getGame(groupId);
 *         if (state != null && state.isActive) {
 *             // 执行游戏逻辑
 *         }
 *     }
 * }
 * }</pre>
 */
public abstract class GameServiceBase<T extends GameState> extends ServiceBase<GameServiceBase<T>> {
    
    // 游戏状态映射: groupId -> 游戏状态
    protected final Map<Long, T> games = new ConcurrentHashMap<>();
    
    /**
     * 创建新游戏状态（子类必须实现）
     * 
     * @param groupId 群号
     * @param kwargs 额外参数（可选）
     * @return 新创建的游戏状态
     */
    protected abstract T createGame(long groupId, Object... kwargs);
    
    /**
     * 开始新游戏
     * 
     * @param groupId 群号
     * @param kwargs 额外参数传递给 createGame
     * @return 异步结果，包含游戏状态
     */
    public CompletableFuture<Result<T>> startGame(long groupId, Object... kwargs) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 如果已有活跃游戏，先结束它
                T existingGame = games.get(groupId);
                if (existingGame != null && existingGame.isActive) {
                    endGame(groupId);
                }
                
                // 创建新游戏
                T newGame = createGame(groupId, kwargs);
                games.put(groupId, newGame);
                
                return Result.ok(newGame);
                
            } catch (Exception e) {
                return Result.err("Failed to start game: " + e.getMessage());
            }
        });
    }
    
    /**
     * 结束游戏
     * 
     * @param groupId 群号
     * @return True 如果成功结束游戏，False 如果没有活跃游戏
     */
    public boolean endGame(long groupId) {
        T game = games.get(groupId);
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
    public T getGame(long groupId) {
        T game = games.get(groupId);
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
        T game = games.get(groupId);
        return game != null && game.isActive;
    }
    
    /**
     * 获取所有活跃游戏数量
     * 
     * @return 活跃游戏数量
     */
    public int getActiveGameCount() {
        return (int) games.values().stream()
                .filter(g -> g.isActive)
                .count();
    }
    
    /**
     * 获取所有活跃游戏的群号列表
     * 
     * @return 群号列表
     */
    public List<Long> getActiveGroupIds() {
        return games.values().stream()
                .filter(g -> g.isActive)
                .map(g -> g.groupId)
                .collect(Collectors.toList());
    }
    
    /**
     * 强制清理所有游戏（用于测试或重置）
     */
    public void clearAllGames() {
        games.clear();
    }
}
