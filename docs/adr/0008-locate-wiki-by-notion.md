# ADR 0008: 用 Notion 定位 Wiki，不保存本地配置

**状态**：已接受  
**日期**：2026-10-22  
**决策者**：用户

## 背景

skill 运行时要知道 Wiki 在哪：根页面、5 个数据库的 data source ID、分类页面。
最初打算让 `/init-wiki` 写一个本地 `wiki-config.json`，但 skill 以 plugin 形式安装，换机器、重装 plugin 后配置就没了，
而所有环境连的都是同一个 Notion。

## 决策

- 不保存本地配置。skill 每次运行时按根页面标题精确搜索，再读根页面内容取得数据库和分类页面（规则见 `plugins/wiki-admin/references/locate-wiki.md`）。
- 正式 Wiki 标题 `LLM Wiki 系统`，测试 Wiki 标题 `LLM Wiki 系统（测试）`。
- 搜到多个同名根页面时问用户；搜不到时提示先运行 `/init-wiki`。

## 候选方案

- **A. 每次从 Notion 定位（采纳）**
- **B. 本地 `wiki-config.json`**：换环境失效。
- **C. 配置提交到 agent-brain 仓库**：每次初始化都要提交推送，切换测试和正式环境要改文件。
- **D. 存进 Notion Memory**：未验证可用性和套餐限制。

## 后果

- 每次运行多一次搜索和一次读取。
- 根页面标题成为契约：用户在 Notion 里改了标题，skill 就找不到 Wiki，会提示改回。

## 相关决策

- ADR 0006：通过托管 Notion MCP 访问
- ADR 0009：仓库即 plugin marketplace
