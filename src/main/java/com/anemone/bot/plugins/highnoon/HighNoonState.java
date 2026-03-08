package com.anemone.bot.plugins.highnoon;

import com.anemone.bot.base.GameState;

import java.util.ArrayList;
import java.util.List;

/**
 * 午时已到游戏状态
 * 
 * 存储单个群聊中午时已到游戏的当前状态。
 * 
 * Attributes:
 * - bulletPos: 子弹位置 (1-6)
 * - shotCount: 已射击次数
 * - players: 参与玩家列表
 * 
 * Example:
 * <pre>{@code
 * HighNoonState state = new HighNoonState(123456L);
 * state.shotCount++;  // 增加射击次数
 * }</pre>
 */
public class HighNoonState extends GameState {
    
    // 子弹位置 (1-6)
    public int bulletPos;
    
    // 已射击次数
    public int shotCount;
    
    // 参与玩家列表
    public final List<Long> players;
    
    /**
     * 创建午时已到游戏状态
     * 
     * @param groupId 群号
     */
    public HighNoonState(long groupId) {
        super(groupId);
        this.bulletPos = 0;
        this.shotCount = 0;
        this.players = new ArrayList<>();
    }
    
    /**
     * 检查是否中弹
     * 
     * @return true 如果当前射击位置就是子弹位置
     */
    public boolean isHit() {
        return shotCount == bulletPos;
    }
    
    /**
     * 获取剩余安全次数
     * 
     * @return 剩余安全射击次数
     */
    public int getRemainingSafeShots() {
        return bulletPos - shotCount - 1;
    }
    
    /**
     * 检查游戏是否结束（5次安全射击后必中）
     * 
     * @return true 如果已达到最大射击次数
     */
    public boolean isGameOver() {
        return shotCount >= 6;
    }
}
