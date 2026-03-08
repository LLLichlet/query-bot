package com.anemone.bot.base;

/**
 * 游戏状态基类
 * 
 * 所有游戏状态应继承此类，包含基本的游戏信息：
 * - 群号 (groupId)
 * - 游戏是否活跃 (isActive)
 * 
 * Example:
 * <pre>{@code
 * public class MyGameState extends GameState {
 *     public int score = 0;
 *     public String currentPlayer = "";
 * }
 * }</pre>
 */
public abstract class GameState {
    
    public final long groupId;
    public volatile boolean isActive;
    
    public GameState(long groupId) {
        this.groupId = groupId;
        this.isActive = true;
    }
}
