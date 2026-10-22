# ADR 0009: agent-brain 仓库即 plugin marketplace，按领域分 plugin

**状态**：已接受  
**日期**：2026-10-22  
**决策者**：用户

## 背景

ADR 0002 决定把 skill 存进 agent-brain Git 仓库。用户希望在任何项目里都能用这些 skill：
把仓库加为 Claude Code 的 plugin marketplace，按需安装，而不是放进某台机器的 `.claude/skills/`。

## 决策

- 仓库根目录放 `.claude-plugin/marketplace.json`，marketplace 名为 `agent-brain`。
- 系统命令（`/init-wiki`、`/ingest` 等）放在 `plugins/wiki-admin/`。
- `/sync-skills` 从 Wiki 生成的专业 skill **按领域分 plugin**，放在 `plugins/<领域>/`，每个领域一个条目。
- plugin 不写 `version`：relative-path plugin 的版本取安装目录的 commit SHA，push 后 `/plugin marketplace update agent-brain` 即可拿到新内容。

## 候选方案

- **按领域分 plugin（采纳）**：只启用当前用得上的领域，会话上下文里只有这些 skill 的描述。新领域要手动装一次。
- **所有生成的 skill 放一个 plugin**：装一次就全有，但 skill 一多每个会话都背全部描述；以后再拆会让已有安装失效。

## 理由

- 用户的资料多、领域差异大（视频制作、软件开发等），按领域隔离能控制上下文开销。
- plugin 名会成为安装 ID（`<plugin>@agent-brain`），改名会让已有安装失效，所以一开始就按领域定名。

## 后果

- 调用 skill 带 plugin 前缀，如 `/wiki-admin:ingest`。
- plugin 安装后运行的是缓存副本，不能把状态写进 plugin 目录（ADR 0008）。
- `/sync-skills` 要往一份可写的本地 agent-brain 仓库写文件、提交、推送：先检查当前目录的 git remote 是否为 `RollRollRoll/agent-brain`，不是就问用户路径，不保存配置。
- 新增领域 plugin 时，`/sync-skills` 同时在 marketplace.json 加条目，并打印安装命令。

## 相关决策

- ADR 0002：技能库存储在 Git 仓库（本 ADR 细化其存放形式）
- ADR 0008：用 Notion 定位 Wiki
