# 版本更新日志 (Changelog)

本文档记录 Anemone Bot (Java 版) 的所有版本更新历史。

完整项目信息请参见 [README.md](README.md)。

---

### Version 1.1.1 (2026-03-10)

**Bug 修复**

- 修复倒序复读中 CQ 码被错误反转的问题
  - 现在倒序复读会清理CQ码，避免破坏消息结构
  
- 修复 LaTeX 渲染相关问题
  - 新增 HTML 实体解码，正确处理 `&amp;`, `&lt;`, `&gt;` 等转义字符
  - 提升渲染清晰度：4x 超采样 + 多步缩放 + 字体大小优化 (20→48)

---

### Version 1.1.0 (2026-03-09)

**新增功能**

- 新增 **LaTeX 公式渲染插件** (`plugins/latex/`)
  - 渲染数学公式：`/latex` 或 `/formula`
  - 使用 JLaTeXMath 库本地渲染，无需 AI
  - 支持分数、积分、矩阵等各种 LaTeX 语法
  - 配置项 `latex-enabled`: 功能开关（默认开启）

**架构改进**

- 重构 HTTP 工具类 (`utils/NetworkUtils`)
  - 统一封装 GET/POST 同步和异步请求
  - 支持自定义超时和请求头
  - 所有网络请求使用标准 `java.net.http.HttpClient`

- 重构图片处理 (`utils/ImageUtils`)
  - 使用 `NetworkUtils` 进行图片下载
  - 新增 `imageToCQCode()` 纯函数，简化图片发送流程
  - 新增 `combineImagesVertically()` 垂直合并图片

- 优化异步处理
  - LaTeX 渲染使用专用线程池，避免阻塞 common pool
  - MCMOD 查询使用专用线程池处理 Selenium 操作
  - PJSK 谱面下载改为并行异步，提升性能

- 优化 MCMOD 查询 (`plugins/mcmod/`)
  - 使用 Selenium 显式等待替代 `Thread.sleep`
  - 减少等待时间，提高响应速度

**Bug 修复**

- 修复插件中重复定义 `logger` 的问题
- 修复未使用字段和 import 的警告

---

### Version 1.0.0 (2026-03-09) 🎉

**正式发布 - 功能对齐 Python v2.4.0**

**新功能**

- 新增 **午时游戏插件** (`plugins/highnoon/`)
  - 俄罗斯轮盘赌禁言游戏：`/highnoon` 或 `/午时已到`
  - 参与游戏：`/fire` 或 `/开枪`
  - 6 发弹仓，随机位置子弹，中弹者禁言 1 分钟
  - 多群隔离：每个群独立游戏状态
  - 支持同一玩家多次参与

- 新增 **数学谜题插件** (`plugins/mathpuzzle/`)
  - 20 Questions 猜数学概念：`/mathpuzzle` 或 `/数学谜`
  - 提问：`/ask` 或 `/问` <问题>
  - 猜测：`/guess` 或 `/猜` <概念名>
  - 揭示答案：`/reveal` 或 `/答案`
  - 726+ 数学概念数据库（来自 Python 版）
  - AI 判定回答，支持是非问题判断

- 新增 **随机回复插件** (`plugins/random/`)
  - 自动触发：被 @ 或特定关键词触发
  - AI 傲娇猫娘风格回复
  - 多轮对话上下文记忆

- 新增 **MCMOD 查询插件** (`plugins/mcmod/`)
  - 查询模组信息：`/mcmod <模组ID或名称>`
  - Selenium 网页截图获取模组详情
  - 自动提取模组名称、简介、下载链接等信息

- 新增 **状态控制插件** (`plugins/status/`)
  - 管理员功能：`/admin` 或 `/状态控制`
  - 获取令牌：`/token` (私聊)
  - 一次性令牌认证，5 分钟有效期
  - 支持功能：状态查看、功能开关、黑名单管理、系统监控

**新增服务**

- `BanService`: 黑名单管理服务
- `TokenService`: 一次性令牌服务
- `ChatService`: 聊天历史管理服务
- `SystemMonitorService`: 系统监控服务
- `GameServiceBase`: 游戏服务基类

**架构改进**

- 完善 7 层分层架构所有服务
- 所有服务通过 `ServiceLocator` 注册和获取
- 完善配置系统，支持所有功能的开关控制

---

### Version 0.4.0 (2026-03-08)

**新功能**

- 新增 **数学定义查询插件** (`plugins/math/`)
  - 香蕉空间风格定义：`/define` 或 `/定义`
  - 多语言支持：自动识别中文、英文、法文、德文、俄文、日文
  - AI 驱动：使用 DeepSeek API 生成形式化数学定义
  - 配置项 `math-enabled`：功能开关（默认开启）
  - 配置项 `math-temperature`：AI 温度参数（默认 0.1）
  - 配置项 `math-max-tokens`：最大生成 token 数（默认 8192）

**新增服务**

- `AIService`: DeepSeek API 封装服务
  - `chat()`: 异步对话接口
  - 自动注册到 `ServiceLocator`

**新增工具类**

- `PromptUtils`: Prompt 文件读取工具
  - `readPrompt()`: 从 resources/prompts 读取提示词
  - 支持多语言 math_def.txt 提示词

---

### Version 0.3.0 (2026-03-06)

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

**最新版本**: 1.1.0 (稳定版)  
**Python 对照版本**: 2.4.0  
**状态**: Java 版本已成为主要维护版本  
查看完整项目信息：[README.md](README.md)
