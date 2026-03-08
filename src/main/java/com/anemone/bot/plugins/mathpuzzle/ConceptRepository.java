package com.anemone.bot.plugins.mathpuzzle;

import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * 数学概念题库
 * 
 * 负责从文件系统加载数学概念数据，并提供查询接口。
 * 支持延迟初始化和自动回退到内置默认概念。
 * 
 * Example:
 * <pre>{@code
 * ConceptRepository repo = new ConceptRepository();
 * repo.initialize();
 * MathConcept concept = repo.getRandomConcept();
 * }</pre>
 */
@Component
public class ConceptRepository {
    
    private static final Logger logger = LoggerFactory.getLogger(ConceptRepository.class);
    
    // 内置默认概念列表，当外部文件不可用时使用
    private static final List<Map<String, Object>> DEFAULT_CONCEPTS = List.of(
        Map.of(
            "id", "fermat_last_theorem",
            "answer", "费马大定理",
            "aliases", List.of("费马最后定理"),
            "category", "数论",
            "tags", List.of("数论", "证明", "358年"),
            "description", "当整数n>2时，方程a^n+b^n=c^n没有正整数解"
        ),
        Map.of(
            "id", "pythagorean_theorem",
            "answer", "勾股定理",
            "aliases", List.of("毕达哥拉斯定理", "商高定理"),
            "category", "几何",
            "tags", List.of("几何", "三角形", "直角"),
            "description", "直角三角形的两条直角边的平方和等于斜边的平方"
        ),
        Map.of(
            "id", "euler_formula",
            "answer", "欧拉公式",
            "aliases", List.of(),
            "category", "分析",
            "tags", List.of("复数", "指数", "三角函数"),
            "description", "e^(iπ) + 1 = 0，被誉为最美的数学公式"
        )
    );
    
    // 概念存储: id -> MathConcept
    private final Map<String, MathConcept> concepts = new HashMap<>();
    
    // 是否已初始化
    private volatile boolean initialized = false;
    
    /**
     * 初始化题库
     */
    @PostConstruct
    public void initialize() {
        if (initialized) {
            return;
        }
        
        // 尝试从 resources 加载
        boolean loaded = loadFromClasspath();
        
        if (!loaded) {
            // 使用默认概念
            loadDefaults();
        }
        
        initialized = true;
        logger.info("ConceptRepository initialized with {} concepts", concepts.size());
    }
    
    /**
     * 从 classpath 加载概念数据
     * 
     * @return true 如果加载成功
     */
    private boolean loadFromClasspath() {
        try {
            ClassPathResource resource = new ClassPathResource("math_concepts.json");
            if (!resource.exists()) {
                logger.warn("math_concepts.json not found in classpath, using defaults");
                return false;
            }
            
            try (InputStream is = resource.getInputStream()) {
                String content = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                JSONObject json = JSONUtil.parseObj(content);
                JSONArray conceptsArray = json.getJSONArray("concepts");
                
                if (conceptsArray != null) {
                    for (int i = 0; i < conceptsArray.size(); i++) {
                        JSONObject obj = conceptsArray.getJSONObject(i);
                        MathConcept concept = jsonToConcept(obj);
                        if (concept != null) {
                            concepts.put(concept.getId(), concept);
                        }
                    }
                }
                
                logger.info("Loaded {} concepts from math_concepts.json", concepts.size());
                return !concepts.isEmpty();
            }
        } catch (Exception e) {
            logger.error("Failed to load math_concepts.json", e);
            return false;
        }
    }
    
    /**
     * 将 JSON 对象转换为 MathConcept
     * 
     * @param obj JSON 对象
     * @return MathConcept 或 null
     */
    private MathConcept jsonToConcept(JSONObject obj) {
        try {
            String id = obj.getStr("id");
            String answer = obj.getStr("answer");
            
            if (id == null || answer == null) {
                return null;
            }
            
            List<String> aliases = new ArrayList<>();
            JSONArray aliasesArray = obj.getJSONArray("aliases");
            if (aliasesArray != null) {
                for (int i = 0; i < aliasesArray.size(); i++) {
                    aliases.add(aliasesArray.getStr(i));
                }
            }
            
            List<String> tags = new ArrayList<>();
            JSONArray tagsArray = obj.getJSONArray("tags");
            if (tagsArray != null) {
                for (int i = 0; i < tagsArray.size(); i++) {
                    tags.add(tagsArray.getStr(i));
                }
            }
            
            return new MathConcept(
                id,
                answer,
                aliases,
                obj.getStr("category", ""),
                tags,
                obj.getStr("description", "")
            );
        } catch (Exception e) {
            logger.warn("Failed to parse concept: {}", obj, e);
            return null;
        }
    }
    
    /**
     * 加载内置默认概念
     */
    private void loadDefaults() {
        for (Map<String, Object> data : DEFAULT_CONCEPTS) {
            MathConcept concept = MathConcept.fromMap(data);
            concepts.put(concept.getId(), concept);
        }
        logger.info("Loaded {} default concepts", concepts.size());
    }
    
    /**
     * 随机获取一个数学概念
     * 
     * @return MathConcept 对象，题库为空时返回 null
     */
    public MathConcept getRandomConcept() {
        ensureInitialized();
        if (concepts.isEmpty()) {
            return null;
        }
        List<MathConcept> list = new ArrayList<>(concepts.values());
        return list.get(new Random().nextInt(list.size()));
    }
    
    /**
     * 获取概念总数
     * 
     * @return 概念总数
     */
    public int getConceptCount() {
        ensureInitialized();
        return concepts.size();
    }
    
    /**
     * 根据 ID 获取概念
     * 
     * @param id 概念 ID
     * @return MathConcept 或 null
     */
    public MathConcept getConceptById(String id) {
        ensureInitialized();
        return concepts.get(id);
    }
    
    /**
     * 确保已初始化
     */
    private void ensureInitialized() {
        if (!initialized) {
            initialize();
        }
    }
}
