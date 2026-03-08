package com.anemone.bot.plugins.mcmod;

/**
 * 模组信息数据类
 * 
 * 存储 MCMOD 模组的基本信息。
 * 
 * Example:
 * <pre>{@code
 * ModInfo mod = new ModInfo(1, "工业时代2", "Industrial Craft 2", "IC2");
 * }</pre>
 */
public class ModInfo {
    
    private final int id;
    private final String nameCn;
    private final String nameEn;
    private final String abbreviation;
    
    public ModInfo(int id, String nameCn, String nameEn, String abbreviation) {
        this.id = id;
        this.nameCn = nameCn != null ? nameCn : "";
        this.nameEn = nameEn != null ? nameEn : "";
        this.abbreviation = abbreviation != null ? abbreviation : "";
    }
    
    // Getters
    public int getId() { return id; }
    public String getNameCn() { return nameCn; }
    public String getNameEn() { return nameEn; }
    public String getAbbreviation() { return abbreviation; }
    
    /**
     * 获取显示名称（优先中文）
     * 
     * @return 显示名称
     */
    public String getDisplayName() {
        if (!nameCn.isEmpty()) {
            return nameCn;
        }
        if (!nameEn.isEmpty()) {
            return nameEn;
        }
        return "Unknown Mod";
    }
    
    /**
     * 检查名称是否匹配（包括别名）
     * 
     * @param query 查询词
     * @return true 如果匹配
     */
    public boolean matchesName(String query) {
        String queryLower = query.toLowerCase();
        return nameCn.toLowerCase().equals(queryLower) ||
               nameEn.toLowerCase().equals(queryLower) ||
               abbreviation.toLowerCase().equals(queryLower);
    }
}
