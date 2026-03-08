package com.anemone.bot.plugins.mathpuzzle;

import com.anemone.bot.base.Result;
import com.anemone.bot.config.BotConfig;
import com.anemone.bot.protocols.AIServiceProtocol;
import com.anemone.bot.protocols.ServiceLocator;
import com.anemone.bot.utils.TextUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 数学谜题游戏服务
 * 
 * 实现 20 Questions 风格的数学概念猜测游戏逻辑，
 * 包括开始游戏、提问、猜测、结束游戏等功能。
 * 
 * Example:
 * <pre>{@code
 * MathPuzzleService service = MathPuzzleService.getInstance();
 * service.startGame(123456L);
 * 
 * // 提问
 * Result<String> result = service.askQuestion(123456L, "这是一个数论概念吗？").join();
 * System.out.println(result.getValue());  // "是" 或 "否" 或 "不确定"
 * 
 * // 猜测
 * Result<Map<String, Object>> guess = service.makeGuess(123456L, "费马大定理").join();
 * }</pre>
 */
@Component
public class MathPuzzleService {
    
    private static final Logger logger = LoggerFactory.getLogger(MathPuzzleService.class);
    
    private static final MathPuzzleService INSTANCE = new MathPuzzleService();
    
    // 游戏状态映射: groupId -> 游戏状态
    private final Map<Long, MathPuzzleState> games = new ConcurrentHashMap<>();
    
    private ConceptRepository repository;
    private BotConfig config;
    
    /**
     * 私有构造函数
     */
    private MathPuzzleService() {}
    
    /**
     * 获取服务单例实例
     * 
     * @return MathPuzzleService 实例
     */
    public static MathPuzzleService getInstance() {
        return INSTANCE;
    }
    
    /**
     * 设置依赖（由 Spring 注入）
     * 
     * @param repository 题库仓库
     * @param config 配置
     */
    public void setDependencies(ConceptRepository repository, BotConfig config) {
        this.repository = repository;
        this.config = config;
    }
    
    /**
     * 开始新游戏
     * 
     * @param groupId 群号
     * @return 异步结果，包含游戏状态
     */
    public CompletableFuture<Result<MathPuzzleState>> startGame(long groupId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 如果已有活跃游戏，先结束它
                MathPuzzleState existingGame = games.get(groupId);
                if (existingGame != null && existingGame.isActive) {
                    endGame(groupId);
                }
                
                // 获取随机概念
                if (repository == null) {
                    return Result.err("Repository not initialized");
                }
                
                MathConcept concept = repository.getRandomConcept();
                if (concept == null) {
                    return Result.err("题库为空，无法开始游戏");
                }
                
                // 创建新游戏
                MathPuzzleState newGame = new MathPuzzleState(groupId, concept);
                games.put(groupId, newGame);
                
                return Result.ok(newGame);
                
            } catch (Exception e) {
                logger.error("Failed to start game", e);
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
        MathPuzzleState game = games.get(groupId);
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
    public MathPuzzleState getGame(long groupId) {
        MathPuzzleState game = games.get(groupId);
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
        MathPuzzleState game = games.get(groupId);
        return game != null && game.isActive;
    }
    
    /**
     * 处理玩家提问并返回答复
     * 
     * @param groupId 群号
     * @param questionText 玩家的问题文本
     * @return 异步结果，"是"/"否"/"不确定"
     */
    public CompletableFuture<Result<String>> askQuestion(long groupId, String questionText) {
        return CompletableFuture.supplyAsync(() -> {
            MathPuzzleState game = getGame(groupId);
            if (game == null || !game.isActive) {
                return Result.err("没有进行中的游戏");
            }
            
            MathConcept concept = game.getConcept();
            if (concept == null) {
                return Result.err("游戏状态异常");
            }
            
            // 获取 AI 服务
            AIServiceProtocol ai = ServiceLocator.get(AIServiceProtocol.class);
            if (ai == null || !ai.isAvailable()) {
                return Result.err("AI 服务不可用");
            }
            
            // 构建系统提示词
            String systemPrompt = buildJudgePrompt(concept, questionText);
            
            // 调用 AI 判定
            try {
                Result<String> aiResult = ai.chat(
                    systemPrompt,
                    questionText,
                    config != null ? config.getMathSoupTemperature() : 0.1,
                    10,
                    0.1
                ).join();
                
                if (aiResult.isFailure()) {
                    return Result.err("AI 服务暂时不可用，请稍后再试");
                }
                
                // 解析 AI 回答
                String answer = aiResult.getValue().trim().toLowerCase();
                String finalAnswer;
                
                if (answer.contains("是") || answer.contains("yes")) {
                    finalAnswer = "是";
                } else if (answer.contains("否") || answer.contains("no")) {
                    finalAnswer = "否";
                } else {
                    finalAnswer = "不确定";
                }
                
                // 更新游戏状态（"不确定"不消耗次数）
                if (!"不确定".equals(finalAnswer)) {
                    game.questionCount++;
                }
                
                return Result.ok(finalAnswer);
                
            } catch (Exception e) {
                logger.error("AI query failed", e);
                return Result.err("AI 服务暂时不可用，请稍后再试");
            }
        });
    }
    
    /**
     * 构建判定提示词
     * 
     * @param concept 数学概念
     * @param question 问题
     * @return 系统提示词
     */
    private String buildJudgePrompt(MathConcept concept, String question) {
        // 从文件读取提示词模板
        String template = com.anemone.bot.utils.PromptUtils.readPrompt("math_soup_judge");
        
        if (template == null) {
            // 如果文件不存在，使用默认提示词
            template = """
                你是一个数学谜题游戏的裁判。玩家正在猜测一个数学概念（定理、公式、数学家或数学对象），你需要根据概念信息回答玩家的是非问题。
                
                ## 规则
                1. 你只能回答以下三种之一：
                   - **"是"**：玩家的猜测与概念一致
                   - **"否"**：玩家的猜测与概念不符
                   - **"不确定"**：问题与概念无直接关联，或无法明确判断
                2. 回答必须严格基于概念名称和分类，不要添加额外信息。
                3. 如果玩家问"这是XXX吗"，只有与答案或别名匹配时才回答"是"。
                
                ## 当前概念信息
                - **答案**：{answer}
                - **别名**：{aliases}
                - **分类**：{category}
                
                ## 当前问题
                玩家问：{question}
                
                请只回答"是"、"否"或"不确定"，不要解释。""";
        }
        
        String aliasesText = concept.getAliases().isEmpty() ? "无" : String.join(", ", concept.getAliases());
        
        return template
            .replace("{answer}", concept.getAnswer())
            .replace("{aliases}", aliasesText)
            .replace("{category}", concept.getCategory())
            .replace("{question}", question);
    }
    
    /**
     * 处理玩家猜测答案
     * 
     * @param groupId 群号
     * @param guessText 玩家的猜测文本
     * @return 异步结果，包含猜测结果
     */
    public CompletableFuture<Result<Map<String, Object>>> makeGuess(long groupId, String guessText) {
        return CompletableFuture.supplyAsync(() -> {
            MathPuzzleState game = getGame(groupId);
            if (game == null || !game.isActive) {
                return Result.err("没有进行中的游戏");
            }
            
            MathConcept concept = game.getConcept();
            if (concept == null) {
                return Result.err("游戏状态异常");
            }
            
            game.guessCount++;
            
            // 标准化猜测文本和答案
            String guessNormalized = TextUtils.normalizeText(guessText);
            String answerNormalized = TextUtils.normalizeText(concept.getAnswer());
            
            boolean isCorrect = guessNormalized.equals(answerNormalized);
            
            // 检查别名匹配
            if (!isCorrect) {
                for (String alias : concept.getAliases()) {
                    if (guessNormalized.equals(TextUtils.normalizeText(alias))) {
                        isCorrect = true;
                        break;
                    }
                }
            }
            
            // 计算最大相似度（用于提示）
            double maxSimilarity = TextUtils.calculateSimilarity(guessText, concept.getAnswer());
            for (String alias : concept.getAliases()) {
                double sim = TextUtils.calculateSimilarity(guessText, alias);
                maxSimilarity = Math.max(maxSimilarity, sim);
            }
            
            Map<String, Object> result = new java.util.HashMap<>();
            result.put("correct", isCorrect);
            result.put("answer", isCorrect ? concept.getAnswer() : null);
            result.put("description", isCorrect ? concept.getDescription() : null);
            result.put("category", isCorrect ? concept.getCategory() : null);
            result.put("similarity", maxSimilarity);
            
            if (isCorrect) {
                endGame(groupId);
            }
            
            return Result.ok(result);
        });
    }
    
    /**
     * 获取游戏信息
     * 
     * @param groupId 群号
     * @return 游戏信息字典，无游戏时返回 null
     */
    public Map<String, Object> getGameInfo(long groupId) {
        MathPuzzleState game = getGame(groupId);
        if (game == null) {
            return null;
        }
        
        Map<String, Object> info = new java.util.HashMap<>();
        info.put("questionCount", game.questionCount);
        info.put("guessCount", game.guessCount);
        info.put("conceptAnswer", game.getConcept() != null ? game.getConcept().getAnswer() : null);
        return info;
    }
}
