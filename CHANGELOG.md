# 版本更新日志 (Changelog)

本文档记录 Anemone Bot (Java 版) 的所有版本更新历史。

完整项目信息请参见 [README.md](README.md)。

---

### Version 0.3.0 (开发中)

**新功能**

- 新增 **PJSK 谱面查询插件** (`plugins/pjsk/`)
  - 随机谱面获取：`/chart` 或 `/pjsk随机谱面`
  - 指定编号获取：`/chart 001` - `/chart 639`
  - 歌曲名搜索：支持模糊匹配搜索歌曲名
  - 难度选择：支持 `exp`/`mst`/`apd` 三种难度
  - 图片合并：从 sdvx.in 下载并合并谱面图片
  - 智能匹配：使用 Levenshtein 距离 + 子串匹配算法

**新增工具类**

- `TextUtils`: 文本处理和相似度计算
  - `normalizeText()`: 文本标准化（去标点、空格、转小写）
  - `calculateSimilarity()`: 综合相似度计算（编辑距离 + 子串 bonus）
  - `findBestMatch()`: 最佳匹配查找
  
- `ImageUtils`: 图像处理工具
  - `downloadImageAsync()`: 异步下载图片
  - `mergeImages()`: 多张图片叠加合并
  - `toCQCode()`: 生成 CQ 码图片消息
  - `resizeImage()`: 图片缩放
  
- `NetworkUtils`: 网络请求工具
  - `fetchBytes()`: 异步获取二进制数据
  - `fetchHtml()`: 获取 HTML 文本
  - 支持超时配置和错误处理

**数据文件**

- 新增 `pjsk_songs.json`：包含 001-639 的歌曲 ID 和名称映射

---

### Version 0.2.0 (2026-03-05)

**新功能**

- 新增 **复读插件** (`plugins/echo/`)
  - 随机复读群聊消息，有概率倒序复读
  - 配置项 `echo-enabled`：复读开关（默认开启）
  - 配置项 `echo-probability`：复读概率（默认 1%）
  - 配置项 `echo-reverse-probability`：倒序概率（默认 20%）

**架构改进**

- 统一插件注册机制：通过 `PluginRegistry` 自动收集插件元数据
- 完善帮助系统：从注册表动态生成帮助信息

**Bug 修复**

- 修复 Shiro 3.x 与 Spring Boot 3.4.x 的兼容性问题，降级至 Shiro 2.5.2 + Spring Boot 3.3.8
- 修复 Jackson 依赖缺失导致的启动失败

---

### Version 0.1.0 (2026-03-03)

**项目初始化**

- 基于 Spring Boot 3.3.8 + Shiro 2.5.2 搭建基础框架
- 实现与 Python 版相同的 7 层分层架构

**核心架构**

- `base/`: `Result<T>` 结果封装，`ServiceBase` 单例基类
- `config/`: `BotConfig` 配置管理（application.yaml）
- `protocols/`: 服务协议接口，`ServiceLocator` 服务定位器
- `handler/`: `PluginHandler` 和 `MessageHandler` 基类
- `service/`: `PluginRegistry` 插件注册，`BotServiceImpl` API 实现
- `receiver/`: `BotEventListener` 事件监听

**新功能**

- 新增 **帮助插件** (`plugins/help/`)
  - `/help` 或 `/帮助`：显示所有可用命令
  - `/help <命令名>`：查看指定命令详情
  - 自动从插件注册表获取元数据

**配置支持**

- `deepseek-api-key`: DeepSeek API 密钥
- `admin-user-ids`: 管理员 QQ 号列表
- `math-enabled`: 数学功能开关（预留）
- `echo-enabled`: 复读功能开关

---

**最新版本**: 0.3.0 (开发中)  
**Python 对照版本**: 2.4.0  
查看完整项目信息：[README.md](README.md)
