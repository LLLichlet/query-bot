package com.anemone.bot.plugins.mathpuzzle;

import java.util.List;
import java.util.Map;

/**
 * 数学概念数据类
 * 
 * 存储一个数学概念的信息，包括标准答案、别名、分类等。
 * 
 * Example:
 * <pre>{@code
 * MathConcept concept = new MathConcept(
 *     "fermat_last_theorem",
 *     "费马大定理",
 *     List.of("费马最后定理"),
 *     "数论",
 *     List.of("数论", "证明", "358年"),
 *     "当整数n>2时，方程a^n+b^n=c^n没有正整数解"
 * );
 * }</pre>
 */
public class MathConcept {
    
    private final String id;
    private final String answer;
    private final List<String> aliases;
    private final String category;
    private final List<String> tags;
    private final String description;
    
    public MathConcept(String id, String answer, List<String> aliases, 
                       String category, List<String> tags, String description) {
        this.id = id;
        this.answer = answer;
        this.aliases = aliases != null ? aliases : List.of();
        this.category = category != null ? category : "";
        this.tags = tags != null ? tags : List.of();
        this.description = description != null ? description : "";
    }
    
    /**
     * 从 Map 创建 MathConcept 对象
     * 
     * @param data 包含概念数据的 Map
     * @return MathConcept 实例
     */
    @SuppressWarnings("unchecked")
    public static MathConcept fromMap(Map<String, Object> data) {
        String id = (String) data.get("id");
        String answer = (String) data.get("answer");
        List<String> aliases = (List<String>) data.get("aliases");
        String category = (String) data.get("category");
        List<String> tags = (List<String>) data.get("tags");
        String description = (String) data.get("description");
        
        return new MathConcept(id, answer, aliases, category, tags, description);
    }
    
    // Getters
    public String getId() { return id; }
    public String getAnswer() { return answer; }
    public List<String> getAliases() { return aliases; }
    public String getCategory() { return category; }
    public List<String> getTags() { return tags; }
    public String getDescription() { return description; }
    
    /**
     * 获取所有可能的答案（包括别名）
     * 
     * @return 答案列表
     */
    public List<String> getAllAnswers() {
        java.util.List<String> all = new java.util.ArrayList<>();
        all.add(answer);
        all.addAll(aliases);
        return all;
    }
}
