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

### 9. 分析失败任务

运行 `/wiki-admin:analyze-failures`，分析 Agent Tasks 里还没分析过的失败记录：判断失败类型，建议修改本地 skill
或在 Wiki 页面上标记需要补充，你确认后才会修改。同一个 skill 24 小时内失败 3 次以上时，会在 Conflicts 建一条
「高频失败」告警。也可以传记录链接或 skill 名，只分析一条或一个 skill。

## 命令一览

| 命令 | 做什么 | 会改 Notion 吗 |
|---|---|---|
| `/wiki-admin:init-wiki` | 建 Wiki 结构，或建测试 Wiki | 会；已存在时先问是否覆盖 |
| `/wiki-admin:ingest` | 把 Sources 里待处理的材料提炼成 Wiki 页面 | 你确认后才写 |
| `/wiki-admin:resolve-conflict <冲突>` | 处理一条冲突；`history <页面>` 查变更历史 | 你选了处理方式并确认后才改 |
| `/wiki-admin:lint-wiki` | 检查矛盾、过时、缺失链接、孤岛页面 | 只有你确认的缺失链接会补上 |
| `/wiki-admin:sync-skills` | 把 techniques 页面同步成 skill，提交到本仓库 | 不改 Notion；写文件和推送前都会问 |
| `/wiki-admin:record-task` | 记录一次任务结果（生成的 skill 会自动调用） | 写一条 Agent Tasks |
| `/wiki-admin:analyze-failures` | 分析失败记录，建议修 skill 或补 Wiki | 每处修改都要你确认 |

所有命令都可以加一句「测试 Wiki」，改为操作「LLM Wiki 系统（测试）」。

## 验证整个系统

在本仓库目录里打开 Claude Code，运行 `/verify-system`（项目级 skill，不随 plugin 发布）。它会：

1. 在你指定的页面下重建「LLM Wiki 系统（测试）」，不碰正式 Wiki
2. 用 [`tests/fixtures/verify-demo/samples/`](tests/fixtures/verify-demo/samples/) 的样本依次运行上面的命令，
   用回读结果逐项判定 spec §4.3 的 VAL-001 ~ VAL-018，并实测入库、同步 50 个 skill、加载 skill 的耗时
3. 输出每一项的通过 / 失败和依据（VAL-019）
4. 最后列出要移入回收站的测试页面和临时目录，你同意后才删除

开始前它会列出全部写入计划，你同意一次后，各命令中途的确认按固定剧本代答；覆盖和删除仍然每次问你。
同步写到系统临时目录的一份克隆里，不会推送。

只想跑不需要 Notion 的检查：

```bash
python3 -m unittest discover -s tests -t .
python3 .claude/skills/verify-system/scripts/verify_tools.py static --repo .
```

## 常见问题

**`notion-*` 工具不出现**：确认 `claude mcp list` 里有 notion，运行 `/mcp` 重新登录，然后重启会话。

**提示「还没有这个 Wiki」**：先运行 `/wiki-admin:init-wiki`。如果 Wiki 已经建过，检查根页面标题是否被改过，
命令靠「LLM Wiki 系统」这个标题找到它；改回原标题即可。

**提示找到多个 Wiki**：工作区里有不止一个同名根页面。按提示选一个，或把多余的移入回收站。

**遇到 `rate_limited`**：命令会按 Notion 返回的等待时间重试一次，还失败就停下并列出已完成的部分，稍后重新运行即可。

**遇到 `usage_limit_reached`**：非 Business 套餐的 SQL / rows 查询额度用完了，60 分钟内会重置，重置后重新运行。

**sync-skills 提示「需要人工合并」**：这个 skill 在 Notion 和本地都改过。对比两边的差异，把要保留的改动合进本地文件，
再运行一次，选「本地已经合并好」。

**安装后看不到新 skill**：运行 `/plugin marketplace update agent-brain`，再 `/reload-plugins`。
新领域的 plugin 要先用 `/plugin` 安装一次。

**记录任务时提示「没能记录到 Agent Tasks」**：任务本身不受影响。按提示给出的内容，稍后用 `/wiki-admin:record-task` 补记。

## 项目结构

```
agent-brain/
├── .claude-plugin/
│   └── marketplace.json  # marketplace 目录
├── .claude/skills/
│   └── verify-system/    # 端到端验证（项目级，不发布）
├── plugins/
│   ├── wiki-admin/       # 维护 Wiki 的命令
│   └── <领域>/            # 从 Wiki 生成的专业 skill（/sync-skills 生成）
├── docs/
│   ├── adr/              # 架构决策记录
│   └── agents/           # agent-toolkit 配置
├── tests/                # 单元测试和验证样本
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
