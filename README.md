# Anemone Bot (Java 版)

**Anemone Bot** - 基于 Spring Boot + Shiro 的 QQ 群聊机器人

[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.3.8-brightgreen)](https://spring.io/projects/spring-boot)
[![Java](https://img.shields.io/badge/Java-21-orange)](https://openjdk.org/)
[![Gradle](https://img.shields.io/badge/Gradle-8.5-blue)](https://gradle.org/)

**项目状态**: 积极开发中 (v0.4.0) | 正在从 Python 版本迁移功能

## 简介

Anemone Bot (Java 版) 是原 Python 版机器人的 Java 重构实现，采用 Spring Boot + Shiro 技术栈，保持与 Python 版相同的功能和分层架构设计。

**长期目标**: 功能对齐 Python v2.4.0 后，成为主要维护版本。

## 核心功能

| 功能 | 命令 | 说明 | 状态 |
|------|------|------|------|
| 帮助 | `/help` (别名: `/帮助`) | 显示所有可用命令 | [已完成] |
| 复读 | 自动触发 | 随机复读群消息，有概率倒序 | [已完成] |
| PJSK 谱面 | `/chart` (别名: `/pjsk随机谱面`) | Project Sekai 谱面图片 | [已完成] |
| 数学定义 | `/define` (别名: `/定义`) | 香蕉空间风格数学定义 | [已完成] |
| 数学谜题 | `/mathpuzzle` (别名: `/数学谜`) | 20 Questions 猜数学概念 | [待开发] |
| 午时已到 | `/highnoon` (别名: `/午时已到`) | 俄罗斯轮盘赌禁言游戏 | [待开发] |
| MCMOD 查询 | `/mcmod` | 查询 MCMOD 百科模组信息 | [待开发] |
| 随机回复 | 自动触发 | AI 基于上下文的回复 | [待开发] |
| 状态控制 | `/admin` (别名: `/状态控制`) | 管理员功能 | [待开发] |

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Java | 21 | 编程语言 |
| Spring Boot | 3.3.8 | 应用框架 |
| Shiro | 2.5.2 | OneBot V11 协议框架 |
| Gradle | 8.5 | 构建工具 |
| FastJSON2 | 2.0.53 | JSON 处理 |

## 项目架构

采用与 Python 版相同的 **7 层严格分层架构**：

```
src/main/java/com/anemone/bot/
├── base/                    # 基础层: Result<T>, ServiceBase
├── config/                  # 配置层: BotConfig (application.yaml)
├── protocols/               # 协议层: 服务接口, ServiceLocator
├── service/                 # 服务层: 协议实现
├── handler/                 # 处理器层: PluginHandler, MessageHandler
├── receiver/                # 接收层: BotEventListener
├── plugins/                 # 插件层: HelpHandler, EchoHandler, PJSKHandler...
└── utils/                   # 工具层: TextUtils, ImageUtils, NetworkUtils
```

**依赖规则**: 上层只依赖协议层，不依赖具体实现。服务通过 `ServiceLocator` 注册和获取。

## 快速开始

### 环境要求

- JDK 21+
- Gradle 8.5+ (或使用 Wrapper)
- OneBot 实现 (如 NapCat、go-cqhttp)

### 1. 克隆项目

```bash
git clone <repository-url>
cd Anemone-java
```

### 2. 配置环境

创建 `src/main/resources/application.yaml`：

```yaml
server:
  port: 8091

shiro:
  token: "your_token"
  ws:
    server:
      enable: true
      url: "/ws/shiro"

anemone:
  bot:
    # AI API 配置
    deepseek-api-key: ${DEEPSEEK_API_KEY:}
    deepseek-base-url: https://api.deepseek.com
    deepseek-model: deepseek-chat
    
    # 功能开关
    math-enabled: ${MATH_ENABLED:true}
    echo-enabled: ${ECHO_ENABLED:true}
    
    # AI 参数 - 数学定义
    math-temperature: ${MATH_TEMPERATURE:0.1}
    math-max-tokens: ${MATH_MAX_TOKENS:8192}
    math-top-p: ${MATH_TOP_P:0.1}
    
    # 复读配置
    echo-probability: ${ECHO_PROBABILITY:0.01}
    echo-reverse-probability: ${ECHO_REVERSE_PROBABILITY:0.2}
    
    # 管理员配置
    admin-user-ids: ${ADMIN_USER_IDS:}
```

或通过环境变量配置：

```bash
export DEEPSEEK_API_KEY=your_api_key_here
export ADMIN_USER_IDS=123456789,987654321
```

### 3. 构建项目

```bash
./gradlew build
```

### 4. 运行

```bash
./gradlew bootRun
```

## 配置说明

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| deepseek-api-key | DEEPSEEK_API_KEY | - | DeepSeek API 密钥 |
| admin-user-ids | ADMIN_USER_IDS | - | 管理员 QQ 号，逗号分隔 |
| math-enabled | MATH_ENABLED | true | 数学定义功能开关 |
| math-temperature | MATH_TEMPERATURE | 0.3 | 数学定义 AI 温度参数 |
| math-max-tokens | MATH_MAX_TOKENS | 512 | 数学定义最大 token 数 |
| echo-enabled | ECHO_ENABLED | true | 复读功能开关 |
| echo-probability | ECHO_PROBABILITY | 0.01 | 复读概率 (0-1) |
| echo-reverse-probability | ECHO_REVERSE_PROBABILITY | 0.2 | 倒序复读概率 |

## 开发插件

### 命令插件示例

```java
@Component
public class MyHandler extends PluginHandler {
    
    @Autowired
    public MyHandler(PluginRegistry registry) {
        super("我的插件", "mycommand", Set.of("别名1"), "myfeature", 10, true, false);
    }
    
    @PostConstruct
    public void init() {
        registry.registerCommand(this, "插件描述", "用法说明");
    }
    
    @Override
    public CompletableFuture<Void> handle(Bot bot, AnyMessageEvent event, String args) {
        return reply(bot, event, "Hello, " + args);
    }
}
```

### 消息插件示例

```java
@Component
public class MyMessageHandler extends MessageHandler {
    
    @Autowired
    public MyMessageHandler(PluginRegistry registry) {
        super("消息监听", "myfeature", 1, false);
    }
    
    @PostConstruct
    public void init() {
        registry.registerMessage(this, "消息插件描述");
    }
    
    @Override
    public CompletableFuture<Void> handleMessage(Bot bot, AnyMessageEvent event) {
        String text = event.getRawMessage();
        // 处理消息
        return CompletableFuture.completedFuture(null);
    }
}
```

## 版本对照

参见项目根目录的 [VERSION.md](../VERSION.md)。

| Java 版本 | 目标 | 状态 |
|-----------|------|------|
| v0.1.0 | 基础框架 | [已完成] |
| v0.2.0 | Help + Echo | [已完成] |
| v0.3.0 | PJSK 谱面 | [已完成] |
| v0.4.0 | 数学定义查询 | [已完成] |
| v1.0.0 | 功能对齐发布 | [目标] |

## 与 Python 版的区别

| 特性 | Python 版 | Java 版 |
|------|-----------|---------|
| 框架 | NoneBot2 | Spring Boot + Shiro |
| 语言 | Python 3.9+ | Java 21 |
| 架构 | 7 层分层架构 | 相同架构 |
| 异步 | async/await | CompletableFuture |
| 配置 | .env + Pydantic | application.yaml |
| 依赖注入 | 无 | Spring DI |
| 构建工具 | PDM/pip | Gradle |

## 相关链接

- [Python 版本](https://github.com/LLLichlet/Anemone-bot/tree/master) - 原 Python 实现
- [版本对照](../VERSION.md) - 迁移进度追踪
- [更新日志](CHANGELOG.md) - 版本更新历史

## 许可证

与 Python 版相同。

---

**注意**: Java 版本正在积极开发中，API 可能随时变更。生产环境建议继续使用 Python 版本。
