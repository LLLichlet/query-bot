package com.anemone.bot.utils;

import java.util.*;

/**
 * 文本处理工具类
 * 
 * 提供文本标准化、相似度计算等纯函数工具。
 * 对应 Python 版本的 plugins/utils/text.py
 */
public class TextUtils {
    
    // ========== 常量 ==========
    
    /** 需要移除的标点符号和特殊字符 */
    public static final String NORMALIZABLE_CHARS = " ·•-ˈ·•\u00b7\u2022\u2219";
    
    /** 完全匹配的相似度值 */
    public static final double EXACT_MATCH = 100.0;
    
    /** 子串匹配的基础分 */
    public static final double SUBSTRING_BASE = 70.0;
    
    /** 子串匹配的额外分数比例系数 */
    public static final double SUBSTRING_BONUS_FACTOR = 25.0;
    
    /** 短字符串阈值 */
    public static final int SHORT_STRING_THRESHOLD = 4;
    
    /** 短字符串的相似度比例阈值 */
    public static final double SHORT_STRING_RATIO_THRESHOLD = 0.8;
    
    /** 短字符串相似度惩罚系数 */
    public static final double SHORT_STRING_PENALTY_FACTOR = 80.0;
    
    // ========== 文本标准化 ==========
    
    /**
     * 标准化文本，用于比较
     * 
     * 移除空格、特殊标点，转为小写。
     * 
     * @param text 原始文本
     * @return 标准化后的文本
     */
    public static String normalizeText(String text) {
        if (text == null || text.isEmpty()) {
            return "";
        }
        
        String result = text.toLowerCase();
        for (char c : NORMALIZABLE_CHARS.toCharArray()) {
            result = result.replace(String.valueOf(c), "");
        }
        return result;
    }
    
    /**
     * 批量标准化文本
     * 
     * @param texts 文本列表
     * @return 标准化后的文本列表
     */
    public static List<String> normalizeTexts(List<String> texts) {
        List<String> result = new ArrayList<>();
        for (String text : texts) {
            result.add(normalizeText(text));
        }
        return result;
    }
    
    // ========== 相似度计算 ==========
    
    /**
     * 计算两个字符串的相似度（0-100%）
     * 
     * 使用改进的算法：
     * 1. 完全匹配返回 100.0
     * 2. 子串匹配返回 70-95 分（根据长度比例）
     * 3. 其他情况使用 Levenshtein 距离计算
     * 4. 短字符串（<=4字符）相似度低于 0.8 时应用惩罚
     * 
     * @param s1 第一个字符串
     * @param s2 第二个字符串
     * @return 相似度分数（0.0 - 100.0）
     */
    public static double calculateSimilarity(String s1, String s2) {
        String s1Clean = normalizeText(s1);
        String s2Clean = normalizeText(s2);
        
        if (s1Clean.isEmpty() || s2Clean.isEmpty()) {
            return 0.0;
        }
        
        // 完全匹配
        if (s1Clean.equals(s2Clean)) {
            return EXACT_MATCH;
        }
        
        // 子串匹配
        if (s1Clean.contains(s2Clean) || s2Clean.contains(s1Clean)) {
            int shorter = Math.min(s1Clean.length(), s2Clean.length());
            int longer = Math.max(s1Clean.length(), s2Clean.length());
            return SUBSTRING_BASE + SUBSTRING_BONUS_FACTOR * ((double) shorter / longer);
        }
        
        // 使用 Levenshtein 距离计算相似度
        double ratio = levenshteinRatio(s1Clean, s2Clean);
        
        // 短字符串特殊处理
        if (s1Clean.length() <= SHORT_STRING_THRESHOLD || s2Clean.length() <= SHORT_STRING_THRESHOLD) {
            if (ratio < SHORT_STRING_RATIO_THRESHOLD) {
                return ratio * SHORT_STRING_PENALTY_FACTOR;
            }
        }
        
        return ratio * 100;
    }
    
    /**
     * 在候选列表中找到最佳匹配
     * 
     * @param text 要匹配的文本
     * @param candidates 候选文本列表
     * @return 匹配结果 [最佳匹配候选, 相似度分数]
     */
    public static MatchResult findBestMatch(String text, List<String> candidates) {
        if (candidates == null || candidates.isEmpty()) {
            return new MatchResult("", 0.0);
        }
        
        String bestCandidate = candidates.get(0);
        double bestScore = calculateSimilarity(text, candidates.get(0));
        
        for (int i = 1; i < candidates.size(); i++) {
            double score = calculateSimilarity(text, candidates.get(i));
            if (score > bestScore) {
                bestScore = score;
                bestCandidate = candidates.get(i);
            }
        }
        
        return new MatchResult(bestCandidate, bestScore);
    }
    
    /**
     * 判断文本是否匹配目标
     * 
     * @param text 输入文本
     * @param target 目标文本
     * @param threshold 相似度阈值（默认90%）
     * @return 是否匹配
     */
    public static boolean isTextMatch(String text, String target, double threshold) {
        return calculateSimilarity(text, target) >= threshold;
    }
    
    /**
     * 判断文本是否匹配目标（默认阈值90%）
     */
    public static boolean isTextMatch(String text, String target) {
        return isTextMatch(text, target, 90.0);
    }
    
    // ========== Levenshtein 距离 ==========
    
    /**
     * 计算 Levenshtein 距离
     */
    public static int levenshteinDistance(String s1, String s2) {
        int[][] dp = new int[s1.length() + 1][s2.length() + 1];
        
        for (int i = 0; i <= s1.length(); i++) dp[i][0] = i;
        for (int j = 0; j <= s2.length(); j++) dp[0][j] = j;
        
        for (int i = 1; i <= s1.length(); i++) {
            for (int j = 1; j <= s2.length(); j++) {
                int cost = (s1.charAt(i - 1) == s2.charAt(j - 1)) ? 0 : 1;
                dp[i][j] = Math.min(Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1), dp[i - 1][j - 1] + cost);
            }
        }
        
        return dp[s1.length()][s2.length()];
    }
    
    /**
     * 计算 Levenshtein 相似度比例（0.0 - 1.0）
     */
    public static double levenshteinRatio(String s1, String s2) {
        int maxLen = Math.max(s1.length(), s2.length());
        if (maxLen == 0) return 1.0;
        
        int distance = levenshteinDistance(s1, s2);
        return 1.0 - (double) distance / maxLen;
    }
    
    // ========== 匹配结果类 ==========
    
    public static class MatchResult {
        public final String candidate;
        public final double score;
        
        public MatchResult(String candidate, double score) {
            this.candidate = candidate;
            this.score = score;
        }
        
        @Override
        public String toString() {
            return String.format("MatchResult{candidate='%s', score=%.2f}", candidate, score);
        }
    }
}
