# ADR 0010: 同一仓库同时发布 Claude Code 和 Codex 的 plugin

**状态**：已接受  
**日期**：2026-10-27  
**决策者**：用户

## 背景

ADR 0009 把 agent-brain 仓库做成 Claude Code 的 plugin marketplace。用户也用 Codex CLI，
希望在 Codex 里同样能用 wiki-admin 的命令和从 Wiki 生成的领域 skill。

Codex 的 plugin 格式和 Claude Code 很接近：skill 同样是 `SKILL.md` + frontmatter，
只是清单文件不同。用户的 agent-toolkit 仓库已经这样同时发布两边。

## 决策

- 仓库根目录加 `.agents/plugins/marketplace.json`，marketplace 名同样是 `agent-brain`，
  每个 plugin 用 `{"source": "local", "path": "./plugins/<plugin>"}` 指向和 Claude Code 相同的目录。
- 每个 plugin 目录同时放 `.claude-plugin/plugin.json` 和 `.codex-plugin/plugin.json`，
  Codex 清单写 `"skills": "./skills/"`，加 `interface` 给 Codex 的 plugin 界面用。两份清单都不写 `version`（沿用 ADR 0009）。
- 两边共用 `plugins/<plugin>/skills/` 下的同一份 SKILL.md，不为 Codex 另写一套。
- SKILL.md 里只有 Claude Code 才有的命令（`claude mcp add`、`claude plugin validate`、Skill 工具）改成按运行环境分别说明，
  或在没有 `claude` 命令时跳过。
- `/sync-skills` 新建领域 plugin 时，两套清单和两个 marketplace 条目一起写。
- 测试检查两个 marketplace 列出的 plugin 和路径一致、每个 plugin 都有两份清单且基础字段相同。

## 候选方案

- **共用 skill，只加 Codex 清单（采纳）**：改动小，Wiki 同步一次两边都能用。
- **为 Codex 单独生成一份 skill**：可以按 Codex 的习惯写，但两份内容要同步，`sync-metadata.json` 也要记两套路径。
- **另开一个 Codex 仓库**：互不影响，但 Wiki → skill 要推两个仓库，失败分析也要找两个地方。

## 理由

- 两边的 SKILL.md 格式兼容，wiki-admin 的步骤只依赖 `notion-*` 工具、git 和 python3，两边都有。
- 用临时 `CODEX_HOME` 实测（codex-cli 0.164.0）：本地路径加 marketplace、`codex plugin add wiki-admin@agent-brain` 都成功，
  缓存目录是 `plugins/cache/agent-brain/wiki-admin/local`；源文件改了之后再 `add` 一次会刷新缓存。

## 后果

- Codex 里调用命令用 `$wiki-admin:ingest` 的形式，或者直接用自然语言。
- Notion MCP 在 Codex 里另外配置：`codex mcp add notion --url https://mcp.notion.com/mcp`，再 `codex mcp login notion`。
- Codex 没有 `claude plugin validate` 的对应命令，清单的一致性靠 `tests/skill_docs` 检查。
- 生成的 skill 调用 `wiki-admin:record-task` 时，Claude Code 用 Skill 工具，Codex 读取它的 SKILL.md 照做。
- `.claude/skills/verify-system` 是 Claude Code 的项目级 skill，本次不改，只在 Claude Code 里跑。

## 相关决策

- ADR 0006：通过托管 Notion MCP 访问 Notion
- ADR 0009：agent-brain 仓库即 plugin marketplace（本 ADR 扩展到 Codex）
