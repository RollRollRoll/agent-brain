# Agent Brain

基于 Notion 的 LLM Wiki：由 LLM 从原始材料中提炼并维护知识库，再把其中的方法整理成 agent 可执行的 skill。

设计见 [SPEC-LLM-WIKI-SYSTEM.md](SPEC-LLM-WIKI-SYSTEM.md)，术语见 [GLOSSARY.md](GLOSSARY.md)，决策记录在 [docs/adr/](docs/adr/)。

## 快速开始

### 1. 安装 Notion MCP

```bash
claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp
```

`--scope user` 让所有项目都能用这个 MCP，agent 在其他项目里执行任务时也能查询知识库。

### 2. 登录

在 Claude Code 中运行 `/mcp`，选择 notion，按提示完成 OAuth 登录。MCP 以你本人的 Notion 权限操作，不需要 token 或 `.env`。

如果登录后 `notion-*` 工具没出现，重启 Claude Code 会话。

### 3. 安装 plugin

本仓库是一个 Claude Code plugin marketplace。在任意目录运行：

```bash
claude plugin marketplace add RollRollRoll/agent-brain
claude plugin install wiki-admin@agent-brain
```

`wiki-admin` 提供维护 Wiki 的命令。从 Wiki 提炼出的专业 skill 按领域放在各自的 plugin 里，
用 `/plugin` 浏览 `agent-brain` marketplace 按需安装。

仓库有新提交后，运行 `/plugin marketplace update agent-brain` 再 `/reload-plugins` 获取更新；
也可以在 `/plugin` 的 Marketplaces 里为 agent-brain 打开自动更新。

### 4. 初始化 Wiki

```
/wiki-admin:init-wiki
```

会创建根页面「LLM Wiki 系统」、5 个数据库（Sources、Wiki Index、Agent Tasks、Wiki Changelog、Conflicts）、
Board / Gallery 视图，以及 concepts/、techniques/、tools/ 三个分类页面。结构定义见
[schema.md](plugins/wiki-admin/skills/init-wiki/references/schema.md)。

想先试用，可以说"建一个测试 Wiki"，它会用标题「LLM Wiki 系统（测试）」另建一套。
其他命令按根页面标题找到 Wiki，所以不要在 Notion 里改这个标题。

### 5. 入库材料

在 Sources 数据库添加材料（状态设为「待处理」），然后运行 `/wiki-admin:ingest`。
它会先列出拟创建的 Wiki 页面，你确认后才写入 Notion。

### 6. 处理冲突

入库时发现的知识冲突记在 Conflicts 数据库。运行 `/wiki-admin:resolve-conflict <冲突链接或关键词>`，
选择采纳新内容、保留旧内容、两者都保留或手动编辑。`/wiki-admin:resolve-conflict history <页面>` 查看页面的变更历史。

### 7. 检查 Wiki

运行 `/wiki-admin:lint-wiki`，在会话中输出矛盾、可能过时、缺失链接、孤岛页面的报告；
明确的缺失链接在你确认后自动补上。

### 8. 记录任务结果

由 `/wiki-admin:sync-skills` 生成的 skill 执行结束后，会调用 `/wiki-admin:record-task` 把结果记到 Agent Tasks：
成功时记结果摘要，失败时记错误信息和 agent 的分析。没有安装 wiki-admin 或记录失败时，任务结果照常返回，
agent 会说明没能记录。

## 项目结构

```
agent-brain/
├── .claude-plugin/
│   └── marketplace.json  # marketplace 目录
├── plugins/
│   ├── wiki-admin/       # 维护 Wiki 的命令
│   └── <领域>/            # 从 Wiki 生成的专业 skill（/sync-skills 生成）
├── docs/
│   ├── adr/              # 架构决策记录
│   └── agents/           # agent-toolkit 配置
├── GLOSSARY.md           # 领域术语
└── SPEC-LLM-WIKI-SYSTEM.md
```

## 开发进度

见 [GitHub Issues](https://github.com/RollRollRoll/agent-brain/issues)。

## 许可证

见 [LICENSE](LICENSE)。

---

参考：
- [Karpathy: LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Obsidian AI 橙皮书](https://github.com/alchaincyf/obsidian-ai-orange-book)
- [Notion MCP 入门](https://developers.notion.com/guides/mcp/get-started-with-mcp)
