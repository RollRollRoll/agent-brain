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

### 3. 初始化 Wiki

在本仓库目录下的 Claude Code 会话中运行：

```
/init-wiki
```

会创建根页面「LLM Wiki 系统」、5 个数据库（Sources、Wiki Index、Agent Tasks、Wiki Changelog、Conflicts）、
Board / Gallery 视图，以及 concepts/、techniques/、tools/ 三个分类页面。结构定义见
[.claude/skills/init-wiki/references/schema.md](.claude/skills/init-wiki/references/schema.md)。

## 项目结构

```
agent-brain/
├── .claude/skills/        # 系统命令（Claude Code skill）
│   └── init-wiki/
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
