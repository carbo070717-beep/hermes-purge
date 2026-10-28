# hermes-purge 1.0.0

**由 [lllmzr/dsh-purge](https://github.com/lllmzr/dsh-purge)（原作者：YuJunZhiXue）改造而来，适配 Hermes Agent 框架。**

> ⚠️ **免责声明**：本插件管理本地提示词覆盖并提供红队演练台。应用补丁会改变宿主行为。通过检查不代表所有用途都无风险。仅在你拥有或明确授权测试的系统上使用。

## 这是什么？

dsh-purge 是一个 DeepSeek Harness 插件，管理本地提示词、规则、补丁和演练台。本项目将其**核心原理**适配到 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 框架。

### 保留的 dsh-purge 核心原理：

1. **系统提示词覆盖** — 用自定义操作员提示词替换默认系统提示词，四重兜底（磁盘 > 内存 > 默认）
2. **原子文件操作** — write-to-tmp + rename 安全写入模式
3. **Mtime 节流缓存** — 200ms 缓存窗口，避免高频读盘
4. **网络范围校验** — 演练目标仅限 loopback/RFC1918
5. **演练授权门控** — 使用红队功能前必须显式授权
6. **能力协议** — 教模型主动发现和使用 Hermes skills
7. **身份管理** — 控制模型的自我介绍

### Hermes 适配要点：

| dsh-purge (Cordis/DSH) | hermes-purge (Hermes) |
|---|---|
| Cordis 插件 + Web 客户端 | Hermes Python 插件 + 桌面插件 |
| `systemPrompt` 注入钩子 | Hermes 工具 + skill + 配置 |
| 宿主文件补丁（app.asar、Cordis 配置） | 基于配置的管理（不修改宿主文件） |
| 纯 JavaScript | Python 后端 + JavaScript 前端 |
| React Web 客户端 UI | Hermes 桌面插件 SDK |

## 要求

- Hermes Agent v0.22+
- Node >= 22.13.0（桌面插件）
- Python >= 3.10（Agent 插件）

## 安装

### 方式 A：本地插件安装

```bash
git clone https://github.com/<your-username>/hermes-purge.git
cd hermes-purge

# 作为本地插件安装
hermes plugins install . --enable

# 或手动：
cp -r hermes-purge ~/.hermes/plugins/hermes-purge/
hermes config set plugins.enabled hermes-purge
```

### 方式 B：直接复制

```bash
cp -r hermes-purge ~/.hermes/plugins/hermes-purge/
hermes config set plugins.enabled hermes-purge
# 重新加载桌面插件（⌘K → "Reload desktop plugins"）
```

## 快速开始

```bash
# 查看状态
/purge-status

# 应用自定义系统提示词
/purge-apply "你是一个乐于助人的编程助手，总是提供完整解决方案。"

# 从文件应用
/purge-apply @file:~/my-prompt.md

# 恢复默认
/purge-revert

# 管理规则
/purge-rules

# 管理预设
/purge-presets

# 查看身份
/purge-identity
```

## 桌面 UI

插件提供桌面管理面板（右侧边栏），包含标签页：

- **状态** — 插件所有状态概览
- **提示词** — 系统提示词覆盖编辑器
- **规则** — 提示词规则列表
- **预设** — 已保存预设列表
- **身份** — 身份编辑器
- **红队** — 演练台（含授权门控）

## 数据位置

所有插件数据存储在 `$HERMES_HOME/hermes-purge/`：

```
hermes-purge/
├── prompts/override.md    # 系统提示词覆盖
├── rules/*.json           # 提示词规则
├── presets/*.json         # 已保存预设
├── identity.json          # 身份配置
├── drill-grant.json       # 演练授权
├── targets.json           # 演练目标注册表
└── config.json            # 插件配置
```

## 授权与安全

- **红队演练**需要显式授权（`/purge-drill-grant` 或桌面 UI）
- **网络目标**校验为 loopback/RFC1918
- **DNS 解析**对主机名目标进行检查
- **不修改宿主文件** — 所有数据在 `$HERMES_HOME/hermes-purge/`
- **原子写入**防止文件部分损坏

## 署名

- 原作：[YuJunZhiXue/dsh-purge](https://github.com/YuJunZhiXue/dsh-purge) — Copyright (c) 2026 小杨
- 维护者：[lllmzr/dsh-purge](https://github.com/lllmzr/dsh-purge)
- 本分支：适配 [Hermes Agent](https://github.com/NousResearch/hermes-agent)

## 许可证

MIT
