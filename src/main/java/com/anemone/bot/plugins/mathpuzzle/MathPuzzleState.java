package com.anemone.bot.plugins.mathpuzzle;

import com.anemone.bot.base.GameState;

/**
 * 数学谜题游戏状态
 * 
 * 存储单个群聊中数学谜题游戏的当前状态。
 * 
 * Attributes:
 * - concept: 当前游戏的概念对象
 * - questionCount: 玩家提问次数计数
 * - guessCount: 玩家猜测次数计数
 * 
 * Example:
 * <pre>{@code
 * MathConcept concept = new MathConcept("test", "答案", ...);
 * MathPuzzleState state = new MathPuzzleState(123456L, concept);
 * state.questionCount++;  // 增加提问次数
 * }</pre>
 */
public class MathPuzzleState extends GameState {
    
    // 当前游戏的概念对象
    private MathConcept concept;
    
    // 玩家提问次数计数
    public int questionCount;
    
    // 玩家猜测次数计数
    public int guessCount;
    
    /**
     * 创建数学谜题游戏状态
     * 
     * @param groupId 群号
     * @param concept 数学概念
     */
    public MathPuzzleState(long groupId, MathConcept concept) {
        super(groupId);
        this.concept = concept;
        this.questionCount = 0;
        this.guessCount = 0;
    }
    
    /**
     * 获取当前概念
     * 
     * @return 数学概念
     */
    public MathConcept getConcept() {
        return concept;
    }
    
    /**
     * 设置当前概念
     * 
     * @param concept 数学概念
     */
    public void setConcept(MathConcept concept) {
        this.concept = concept;
    }
    
    /**
     * 获取游戏统计信息
     * 
     * @return 统计字符串
     */
    public String getStats() {
        return String.format("Questions: %d, Guesses: %d", questionCount, guessCount);
    }
}
