# Implementation-Ready Delivery Spec：LLM Wiki 知识管理与 Agent 技能库系统

```yaml
spec_id: SPEC-LLM-WIKI-001
related_issue: https://github.com/RollRollRoll/agent-brain
source_context:
  - /Users/chenjinfan/WorkSpace/second-brain/GLOSSARY.md
related_adrs:
  - docs/adr/0001-notion-over-obsidian.md
  - docs/adr/0002-skills-in-git-not-notion.md
  - docs/adr/0003-agent-failure-feedback.md
  - docs/adr/0004-conflict-resolution-mechanism.md
  - docs/adr/0006-hosted-notion-mcp.md
  - docs/adr/0007-wiki-pages-in-wiki-index.md
  - docs/adr/0008-locate-wiki-by-notion.md
  - docs/adr/0009-repo-as-plugin-marketplace.md
  - docs/adr/0010-codex-plugin-support.md
last_updated: 2026-10-22
```

---

## 1. Problem, Solution, Outcome and Scope

### 1.1 Problem

用户需要从多领域（视频制作、软件开发等）的原始材料（文章、论文、博客、视频、图片）中提炼和管理知识，但面临以下问题：

1. **知识碎片化**：原始材料散落各处，难以形成系统化的知识结构
2. **信息孤岛**：每次需要知识时都要重新检索原始材料，无法沉淀和复用
3. **知识冲突**：新材料可能与已有认知冲突，缺乏系统化的处理机制
4. **Agent 技能缺失**：希望 Agent 能从知识库学习并执行任务（如视频剪辑），但现有知识库只适合人类阅读，Agent 无法直接使用

如果不解决这些问题，用户的学习效率低下，Agent 无法获得可执行的技能，知识积累无法转化为生产力。

### 1.2 Solution Overview

系统采用 Karpathy LLM Wiki 模式，提供持久化、可演进的知识管理能力：

**核心能力**：
1. **知识提炼与维护**：LLM 从原始材料中提炼结构化知识（concepts/techniques/tools），持续维护 Notion Wiki
2. **智能冲突处理**：自动检测知识冲突，分类处理（事实性、观点性、时效性、场景性、深度性），记录证据和历史
3. **技能库生成**：从 Wiki 的 techniques 中提炼可执行技能，生成符合 Claude Code 规范的 skill 文件，存储到 GitHub 仓库
4. **Agent 执行与反馈**：Agent 使用本地 skill 执行任务，将结果和问题反馈到系统，LLM 根据反馈改进 skill 和 Wiki

**用户体验**：
- 用户添加原始材料到 Notion，运行 `/ingest` 命令，LLM 提炼知识并更新 Wiki
- 用户通过 Notion 的 Gallery/Board/Table 视图浏览和学习知识
- 运行 `/sync-skills` 同步 Wiki 到本地 skill 仓库，Agent 可以直接调用执行任务
- Agent 执行任务的结果自动记录，失败时触发改进流程

### 1.3 User Stories

1. 作为用户，我想要添加一篇关于视频剪辑的文章到系统，以便 LLM 自动提炼知识并更新我的 Wiki
2. 作为用户，我想要浏览 Notion Wiki 中的知识卡片，以便系统化学习某个领域的概念和技术
3. 作为用户，我想要在新材料与已有知识冲突时得到分类和证据，以便做出正确的判断
4. 作为用户，我想要查看某个知识点的演进历史，以便了解它是如何随时间变化的
5. 作为用户，我想要运行一个命令就能将 Wiki 中的技能同步到本地仓库，以便 Agent 可以使用最新技能
6. 作为用户，我想要 Agent 能从技能库学习并执行视频剪辑任务，以便自动化完成工作
7. 作为用户，我想要看到 Agent 执行任务的记录和反馈，以便了解哪些技能有效、哪些需要改进
8. 作为用户，我想要定期检查 Wiki 的健康度（矛盾、过时、缺失链接），以便保持知识库的质量
9. 作为用户，我想要 LLM 自动建立 Wiki 页面之间的双向链接，以便发现知识之间的关联
10. 作为用户，我想要按主题、时间、来源筛选和排序 Wiki 页面，以便快速找到需要的知识
11. 作为用户，我想要追踪原始材料的处理状态（待处理/已入库/已归档），以便管理入库进度
12. 作为开发者，我想要在 GitHub 上管理 skill 的版本，以便追踪变更和回滚错误
13. 作为开发者，我想要为每个 skill 编写测试，以便确保 skill 的可靠性
14. 作为 Agent，我想要优先使用本地 skill 执行任务而不是每次查询 Notion，以便提高执行速度
15. 作为 Agent，我想要在执行失败时记录详细原因，以便 LLM 能够分析并改进 skill

### 1.4 In Scope

**核心功能**：
- Notion Wiki 的初始化、维护和查询（通过 Notion MCP）
- 原始材料的半自动入库（LLM 提炼 → 用户确认 → 写入 Wiki）
- 五类知识冲突的检测、分类、证据核验和历史保留
- Wiki 健康度检查（lint）：矛盾检测、过时内容、缺失链接、孤岛页面
- Notion Wiki → 本地 Git 仓库的单向同步（生成 Claude Code skill）
- Agent 执行任务并反馈到 Notion Agent Tasks 数据库
- Agent 失败的分析和 skill/Wiki 改进机制
- 完整的 Notion 数据库结构（Sources, Wiki Index, Agent Tasks, Wiki Changelog, Conflicts）
- 系统管理命令（`/init-wiki`, `/ingest`, `/sync-skills`, `/lint-wiki`, `/resolve-conflict`, `/verify-system`）

**数据支持**：
- 多领域知识（视频制作、软件开发等，通过标签区分）
- 多种材料类型（文章、视频文稿、图片描述）
- 视频和图片的预处理（视频提取字幕/文字稿，图片转文本描述）

### 1.5 Out of Scope

**明确不做**：
- 实时网页抓取或自动订阅 RSS（原始材料由用户手动筛选）
- 传统 RAG 式的向量检索（LLM 维护结构化 Wiki，不是每次查询都检索原文）
- 多人实时协同编辑（个人知识管理系统）
- 自动发布或对外分享（可见性由用户控制）
- 知识冲突的全自动解决（需要分类、证据和用户确认）
- 双向同步（本地 skill 手动修改后同步回 Notion，当前版本不支持）
- Skill 的 CI/CD 自动测试（手动测试，CI 集成属于后续优化）

### 1.6 Hard Constraints

**技术栈约束**：
- 必须使用 Notion 作为 Wiki 存储（用户不愿安装 Obsidian）
- 必须通过 Notion 官方 MCP server 访问 Notion（https://mcp.notion.com/mcp）
- 必须使用 Claude Code 作为 LLM 和 Agent 运行环境；Codex 也能加载同一套 plugin（ADR 0010）
- Skill 必须符合 Claude Code skill 规范（SKILL.md + frontmatter），并能被 Codex 加载
- Skill 仓库必须是 `git@github.com:RollRollRoll/agent-brain.git`，以 plugin marketplace 形式发布（ADR 0009），同时提供 Claude Code 和 Codex 的清单（ADR 0010）
- 系统命令放在 `plugins/wiki-admin/`，调用时带前缀，如 `/wiki-admin:ingest`

**访问约束**（ADR 0006）：
- 通过托管 MCP 访问，OAuth 登录，以用户本人的 Notion 权限操作
- 所有 Notion 操作由 agent 在 Claude 会话中调用 `notion-*` 工具完成，仓库中不包含 Notion 客户端代码
- MCP 的每次工具调用都计入 Notion API 请求配额

**兼容性约束**：
- 必须遵守 GLOSSARY.md 中定义的术语
- 必须遵守 ADR 0001-0004、0006 中的技术决策

**安全约束**：
- 仓库中不得出现任何 Notion 凭据（OAuth 凭据由 Claude Code 保管）

### 1.7 Change Summary

| Change Type | 内容 | 对现有系统的影响 |
|---|---|---|
| Added | 完整的 LLM Wiki 知识管理系统（Notion + 本地 skill 仓库） | 新系统，无现有系统影响 |
| Added | 五类知识冲突处理机制 | 新功能 |
| Added | Agent 执行与失败反馈机制 | 新功能 |
| Added | 系统管理命令（7 个 skill） | 新功能 |

---

## 2. Behavioral Contract

### 2.1 Functional Requirements

#### REQ-001：初始化 Notion Wiki 结构

系统 MUST 能够在用户的 Notion workspace 中自动创建完整的知识管理结构，包括 5 个数据库和层级页面。

##### SCN-001-A：首次初始化

- GIVEN 用户已安装托管 Notion MCP 并通过 `/mcp` 完成 OAuth 登录
- WHEN 用户运行 `/init-wiki` 命令
- THEN 系统在 Notion 中创建以下结构：
  - 1 个顶层页面"LLM Wiki 系统"
  - 5 个数据库：Sources, Wiki Index, Agent Tasks, Wiki Changelog, Conflicts
  - 3 个 Wiki 分类页面：concepts/, techniques/, tools/
- AND 为每个数据库配置正确的字段和视图（Board/Gallery/Table）
- AND 返回所有创建页面的链接供用户检查

##### SCN-001-B：重复初始化检测

- GIVEN 用户已运行过 `/init-wiki`
- WHEN 用户再次运行 `/init-wiki`
- THEN 系统检测到已存在的结构
- AND 提示用户"Wiki 结构已存在，是否覆盖？"
- AND 等待用户确认后再执行

---

#### REQ-002：半自动入库原始材料

系统 MUST 能够读取用户添加到 Sources 数据库的原始材料，提炼知识，建议更新 Wiki，并在用户确认后写入。

##### SCN-002-A：入库文本材料

- GIVEN 用户在 Sources 数据库添加一条记录（类型=文章，状态=待处理）
- AND 记录包含标题、链接或文本内容、领域标签
- WHEN 用户运行 `/ingest` 命令
- THEN 系统读取所有状态为"待处理"的记录
- AND 提取关键概念、技术、工具
- AND 检测是否与已有 Wiki 页面冲突
- AND 建议创建或更新的 Wiki 页面（显示标题、摘要、分类）
- AND 等待用户确认"是"或"否"
- WHEN 用户确认"是"
- THEN 系统在 Notion Wiki 中创建或更新页面
- AND 建立与相关页面的双向链接
- AND 更新 Sources 记录状态为"已入库"
- AND 记录变更到 Wiki Changelog 数据库

##### SCN-002-B：入库视频材料

- GIVEN 用户添加一条视频材料（类型=视频，包含文字稿或字幕文本）
- WHEN 用户运行 `/ingest`
- THEN 系统按 SCN-002-A 的流程处理文字稿内容

##### SCN-002-C：入库图片材料

- GIVEN 用户添加一条图片材料（类型=图片，包含图片描述文本）
- WHEN 用户运行 `/ingest`
- THEN 系统按 SCN-002-A 的流程处理描述文本

##### SCN-002-D：直接入库指定材料

- GIVEN 用户提供一个 Notion 页面 URL
- WHEN 用户运行 `/ingest <url>`
- THEN 系统直接读取该页面内容并按 SCN-002-A 流程处理
- AND 不检查 Sources 数据库的状态字段

##### SCN-002-E：无待处理材料

- GIVEN Sources 数据库中没有状态为"待处理"的记录
- WHEN 用户运行 `/ingest`
- THEN 系统提示"没有待处理的材料"
- AND 不执行任何操作

---

#### REQ-003：知识冲突检测与分类处理

系统 MUST 在入库过程中自动检测知识冲突，分为五类（事实性、观点性、时效性、场景性、深度性），并根据类型采取不同的处理策略。

##### SCN-003-A：事实性冲突的证据核验

- GIVEN 新材料说"Python 3.12 发布于 2023 年"
- AND 已有 Wiki 页面说"Python 3.12 发布于 2024 年"
- WHEN LLM 检测到冲突
- THEN 系统分类为"事实性冲突"
- AND 使用 `web_search` 或 `WebFetch` 查证官方文档
- AND 记录证据链接（如 python.org 的发布公告）
- AND 评估证据强度（官方文档=高强度）
- AND 创建冲突记录到 Conflicts 数据库：
  - Wiki 页面、冲突类型、新材料、原有内容摘要、新内容摘要
  - 证据链接、证据强度评分、状态=待审核
- AND 给出推荐方案："证据显示新材料正确，建议更新 Wiki"
- AND 等待用户审核确认

##### SCN-003-B：观点性冲突的双方保留

- GIVEN 新材料说"VSCode 是最好的编辑器"
- AND 已有 Wiki 页面说"Vim 是最好的编辑器"
- WHEN LLM 检测到冲突
- THEN 系统分类为"观点性冲突"
- AND 不进行证据查证
- AND 记录双方来源（作者、发布时间、链接）
- AND 创建冲突记录，推荐方案："两种观点都保留，标注来源"
- AND 等待用户审核

##### SCN-003-C：时效性冲突的历史保留

- GIVEN 新材料说"2025 年推荐用 Vite"
- AND 已有 Wiki 页面说"2024 年推荐用 Webpack"
- WHEN LLM 检测到冲突
- THEN 系统分类为"时效性冲突"
- AND 识别时间标记（2024 vs 2025）
- AND 推荐方案："保留旧版本为历史，突出显示新版本"
- AND 等待用户确认后更新 Wiki 并记录到 Changelog

##### SCN-003-D：场景性冲突的补充合并

- GIVEN 新材料说"大项目用 PostgreSQL"
- AND 已有 Wiki 页面说"小项目用 SQLite"
- WHEN LLM 检测到冲突
- THEN 系统分类为"场景性冲突"（实际是补充）
- AND 推荐方案："明确各自适用场景，两者都保留"
- AND 等待用户确认后合并到同一 Wiki 页面

##### SCN-003-E：无法判断的冲突

- GIVEN LLM 无法确定冲突类型或置信度低于 50%
- WHEN 检测到冲突
- THEN 系统分类为"无法判断"
- AND 创建冲突记录，状态=待人工审核
- AND 提示用户手动分类

---

#### REQ-004：Wiki 健康度检查（Lint）

系统 MUST 能够定期检查 Notion Wiki 的健康度，生成报告，并建议修复方案。

##### SCN-004-A：矛盾检测

- GIVEN Wiki 中存在两个页面
- AND 页面 A 说"方法 X 是最佳实践"
- AND 页面 B 说"不推荐使用方法 X"
- WHEN 用户运行 `/lint-wiki`
- THEN 系统扫描所有 Wiki 页面，检测矛盾
- AND 生成报告：
  - 矛盾类型、涉及页面、具体内容、建议处理方式
- AND 将报告写入 Notion 页面或输出到终端

##### SCN-004-B：过时内容检测

- GIVEN 某个 Wiki 页面最后更新时间超过 6 个月
- AND 该页面的领域标签属于快速变化的领域（如前端框架）
- WHEN 运行 `/lint-wiki`
- THEN 系统标记该页面为"可能过时"
- AND 建议用户复核或更新

##### SCN-004-C：缺失链接检测

- GIVEN 页面 A 提到"蒙太奇技术"
- AND Wiki 中存在页面 B 标题为"蒙太奇"
- AND 页面 A 没有链接到页面 B
- WHEN 运行 `/lint-wiki`
- THEN 系统检测到缺失链接
- AND 建议建立双向链接

##### SCN-004-D：孤岛页面检测

- GIVEN 某个 Wiki 页面没有任何入链（没有其他页面链接到它）
- WHEN 运行 `/lint-wiki`
- THEN 系统标记为"孤岛页面"
- AND 建议建立链接或评估是否应该保留

##### SCN-004-E：自动修复简单问题

- GIVEN Lint 发现缺失链接（SCN-004-C）
- AND 链接关系明确（页面 A 提到的术语在 GLOSSARY.md 中有定义，且对应页面 B）
- WHEN 用户在 Lint 报告中确认"自动修复"
- THEN 系统自动建立链接并记录到 Changelog

---

#### REQ-005：同步 Wiki 到 agent-brain plugin marketplace

系统 MUST 能够读取 Wiki Index 中分类为 techniques 的页面，识别可执行技能，生成符合 Claude Code skill 规范的文件，
按领域放进 agent-brain 仓库的 `plugins/<领域>/skills/` 下（新领域同时在 `.claude-plugin/marketplace.json` 加条目），
并提交、推送到 GitHub。用户添加 `agent-brain` marketplace 后即可安装使用（ADR 0009）。

##### SCN-005-A：首次同步

- GIVEN Notion Wiki 的 techniques/ 中有 3 个页面
- AND 其中 2 个页面包含明确的步骤、工具、输入输出（可执行技能）
- AND 本地 Git 仓库 `agent-brain` 已克隆
- WHEN 用户运行 `/sync-skills`
- THEN 系统读取 techniques/ 的所有页面
- AND 识别可执行技能（有步骤、工具、前置条件）
- AND 对比本地 `agent-brain` 仓库，检测新增/修改/删除
- AND 生成符合 Claude Code skill 规范的 SKILL.md 文件
- AND 保存到对应领域 plugin 的目录（如 `plugins/video-production/skills/jump-cut/SKILL.md`）
- AND 更新 `sync-metadata.json`（记录同步时间、Notion 页面 ID、skill 路径）
- AND 提交到 Git 并推送到 GitHub

##### SCN-005-B：增量同步

- GIVEN 上次同步后，Notion Wiki 新增了 1 个 technique 页面
- AND 修改了 1 个已有 technique 页面
- WHEN 运行 `/sync-skills`
- THEN 系统对比 `sync-metadata.json`，检测变更
- AND 生成新 skill 文件
- AND 更新已修改的 skill 文件
- AND 提交变更到 Git

##### SCN-005-C：同步冲突检测

- GIVEN Notion Wiki 的某个 technique 页面已修改
- AND 本地对应的 skill 文件也被手动修改过
- AND 两者的修改时间都晚于上次同步时间
- WHEN 运行 `/sync-skills`
- THEN 系统检测到冲突
- AND 提示用户："skill X 在 Notion 和本地都被修改，需要人工合并"
- AND 不自动覆盖，等待用户处理

##### SCN-005-D：删除已移除的技能

- GIVEN Notion Wiki 的某个 technique 页面被删除或移动到其他分类
- WHEN 运行 `/sync-skills`
- THEN 系统检测到对应的本地 skill 应该删除
- AND 提示用户确认："skill X 对应的 Wiki 页面已不存在，是否删除本地 skill？"
- AND 等待用户确认

---

#### REQ-006：Agent 执行任务并记录反馈

系统 MUST 支持 Agent 使用本地 skill 执行任务，将结果记录到 Notion Agent Tasks 数据库，失败时记录详细原因。

##### SCN-006-A：Agent 成功执行任务

- GIVEN Agent 接收到用户任务："帮我做跳切效果"
- AND 本地 skill 仓库存在 `video-production/jump-cut` skill
- WHEN Agent 调用该 skill 执行任务
- AND 执行成功
- THEN Agent 在 Notion Agent Tasks 数据库创建记录：
  - 任务名、使用的 Skill、执行时间、状态=成功、结果摘要
- AND 返回任务结果给用户

##### SCN-006-B：Agent 执行失败并反馈

- GIVEN Agent 调用 skill 执行任务
- AND 执行失败（如工具路径错误、前置条件不满足）
- WHEN 执行失败
- THEN Agent 在 Notion Agent Tasks 数据库创建记录：
  - 任务名、使用的 Skill、执行时间、状态=失败
  - 失败原因（错误消息、堆栈跟踪、Agent 的分析）
- AND 返回失败信息给用户

##### SCN-006-C：高频失败告警

- GIVEN 同一个 skill 在 1 天内失败 3 次以上
- WHEN 第 3 次失败记录写入 Agent Tasks 数据库
- THEN 系统检测到高频失败
- AND 在 Conflicts 或单独的"待修复 Skills"数据库中创建记录
- AND 提示用户："skill X 高频失败，需要检查和修复"

---

#### REQ-007：冲突解决与历史追溯

系统 MUST 允许用户审核和解决 Conflicts 数据库中的冲突记录，并支持追溯任何 Wiki 页面的变更历史。

##### SCN-007-A：用户审核事实性冲突

- GIVEN Conflicts 数据库中有一条事实性冲突记录（状态=待审核）
- AND LLM 已提供证据链接和推荐方案
- WHEN 用户运行 `/resolve-conflict <conflict-id>`
- THEN 系统显示冲突详情：
  - Wiki 页面、冲突类型、原有内容、新内容、证据链接、推荐方案
- AND 提示用户选择：采纳新内容 / 保留旧内容 / 手动编辑
- WHEN 用户选择"采纳新内容"
- THEN 系统更新 Wiki 页面
- AND 更新 Conflicts 记录状态为"已解决"
- AND 记录变更到 Wiki Changelog：
  - 变更类型=冲突解决、来源材料、详情
- AND Notion 原生 Page History 自动保留旧版本

##### SCN-007-B：查询页面变更历史

- GIVEN 用户想了解某个 Wiki 页面的演进过程
- WHEN 用户查询 Wiki Changelog 数据库（筛选该页面）
- THEN 系统返回该页面的所有变更记录：
  - 变更时间、来源材料、变更类型、详情
- AND 用户可以点击来源材料链接查看原始内容

---

#### REQ-008：Agent 失败分析与改进

系统 MUST 能够分析 Agent Tasks 数据库中的失败记录，识别失败原因，并建议修复 skill 或 Wiki。

##### SCN-008-A：分析失败原因并建议修复

- GIVEN Agent Tasks 数据库中有一条失败记录
- AND 失败原因="工具路径错误：/usr/bin/ffmpeg 不存在"
- WHEN 用户或 LLM 分析该失败
- THEN 系统识别失败类型为"工具路径/配置错误"
- AND 建议修复方案："检查 skill 中的 ffmpeg 路径，改为 which ffmpeg 或环境变量"
- AND 用户确认后，LLM 更新本地 skill 文件
- AND 提交变更到 Git

##### SCN-008-B：知识不足导致的失败

- GIVEN Agent 失败原因="无法理解任务：'故障艺术效果'没有明确步骤"
- WHEN LLM 分析失败
- THEN 系统识别失败类型为"知识不足"
- AND 建议："Notion Wiki 的 techniques/故障艺术效果 页面缺少详细步骤，需要补充"
- AND 用户确认后，LLM 在 Notion Wiki 中标记该页面需要补充

---

### 2.2 Negative Requirements

#### NEG-001：禁止自动覆盖冲突

系统 MUST NOT 在检测到知识冲突时自动覆盖已有 Wiki 内容，必须先分类、记录证据、等待用户确认。

验证：
- 用户或外部系统层面：检查 Conflicts 数据库，所有冲突记录的状态初始为"待审核"
- Wiki Changelog 中的冲突解决记录必须有用户确认的时间戳
- 代码层面：入库逻辑中不存在"直接覆盖"的分支（必须先创建 Conflict 记录）

#### NEG-002：禁止双向同步导致的覆盖

系统 MUST NOT 在 `/sync-skills` 时自动覆盖本地手动修改的 skill 文件。

验证：
- 用户或外部系统层面：运行 `/sync-skills` 时，如果本地 skill 被修改，系统提示冲突而不是覆盖
- 代码层面：同步逻辑中存在"检测本地修改时间"的步骤

#### NEG-003：禁止在仓库中存放 Notion 凭据

系统 MUST NOT 在 Git 仓库中包含 Notion 凭据（token、OAuth 凭据、`.env`）。

验证：
- 用户层面：按 README 完成安装和登录，全程不需要复制或粘贴任何 token
- 仓库层面：`git grep -nE 'ntn_|secret_|NOTION_TOKEN' -- ':!SPEC-LLM-WIKI-SYSTEM.md'` 无结果（排除本 spec，因为它自己写着这个模式）；`.gitignore` 包含 `.env`

#### NEG-004：遇到限流时不得放弃或连续重试

收到 MCP 的 `rate_limited` 时，系统 MUST NOT 立即重试或静默跳过；必须按 `retry_after_seconds` 等待后重试一次，
再次失败就停下来，向用户报告已完成的部分和失败原因。

验证：
- skill 层面：每个调用 `notion-*` 的 SKILL.md 都写有上述限流处理步骤
- 运行层面：批量操作（如 lint 扫描全部页面）中触发限流时，agent 的汇报里有等待和重试记录

---

### 2.3 Quality Requirements

#### QOS-001：入库性能

系统 MUST 在 5 分钟内完成单个文本材料（5000 字以内）的入库（不包括冲突解决时间）。

门槛按 agent 读原文、提炼知识点的实际耗时定：2026-10-27 实测 3000 字文章约 163 秒，原定的 30 秒达不到。

验证：
- 运行 `/ingest` 处理一篇 3000 字文章，记录从开始到建议更新 Wiki 的时间
- 时间 < 5 分钟为通过

#### QOS-002：同步性能

系统 MUST 在 20 分钟内完成 50 个 technique 页面到本地 skill 的同步（假设无冲突）。

门槛按逐页读取正文的实际耗时定：2026-10-27 实测约 916 秒（含一次重跑），原定的 5 分钟达不到。

验证：
- 在测试 Notion workspace 创建 50 个 technique 页面
- 运行 `/sync-skills`，记录完成时间
- 时间 < 20 分钟为通过

#### QOS-003：Agent 执行响应时间

Agent MUST 在 10 秒内加载并开始执行本地 skill（不包括 skill 本身的执行时间）。

验证：
- Agent 调用一个简单的 skill（如打印"Hello"）
- 记录从调用到 skill 开始执行的时间
- 时间 < 10 秒为通过

---

## 3. Technical Design

### 3.1 Existing Context / System Context

#### Greenfield

**系统边界**：
- 本地：Claude Code 运行环境、本地文件系统（skill 仓库）、Git 客户端
- 在线：Notion workspace（通过 MCP 访问）、GitHub 仓库（`agent-brain`）

**外部参与者和外部系统**：
- 用户：添加原始材料、审核冲突、浏览 Wiki、给 Agent 任务
- LLM（Claude）：提炼知识、检测冲突、查证证据、生成 skill、分析失败
- Agent：执行任务、查询 Wiki、记录反馈
- Notion：存储 Wiki 和元数据
- GitHub：存储 skill 仓库

**外部依赖**：
- 托管 Notion MCP（`https://mcp.notion.com/mcp`，ADR 0006）
- GitHub（通过 Git SSH）
- Claude Code skill 规范

**部署和运行边界**：
- 本地运行：用户的 macOS 系统（Darwin 27.0.0）
- 需要网络访问 Notion MCP 和 GitHub

**主要领域上下文及关系**：
- 知识管理上下文：原始材料 → Wiki（concepts/techniques/tools）
- 技能库上下文：Wiki techniques → Skill 文件 → Agent 执行
- 冲突处理上下文：冲突检测 → 分类 → 证据核验 → 解决
- 反馈改进上下文：Agent 执行 → 失败记录 → 分析 → 改进 skill/Wiki

**已确定的技术栈或平台约束**：
- 必须使用 Notion + Notion MCP（ADR 0001）
- 必须使用本地 Git 仓库存储 skill（ADR 0002）
- 必须实现 Agent 失败反馈机制（ADR 0003）
- 必须实现五类冲突处理机制（ADR 0004）

---

### 3.2 Key Technical Decisions

#### DEC-001：Notion 数据库 vs 层级页面

**Selected**

使用 **5 个 Notion 数据库** + **层级页面结构**：
- 数据库：Sources, Wiki Index, Agent Tasks, Wiki Changelog, Conflicts
- 层级页面：Wiki（concepts/, techniques/, tools/）

**Alternatives**

- 方案 A：全部用层级页面，不用数据库
- 方案 B：全部用数据库，Wiki 内容也存在数据库字段中

**Trade-off**

| Dimension | Selected | Alternative A | Alternative B |
|---|---|---|---|
| 可查询性 | 高（数据库字段） | 低（需要全文搜索） | 高 |
| 浏览体验 | 优（Gallery/Board 视图） | 一般（只有列表） | 差（数据库不适合长文本阅读） |
| LLM 维护难度 | 适中（页面用 Markdown，元数据用数据库） | 低（只操作页面） | 高（字段更新复杂） |
| 双向链接 | 原生支持 | 原生支持 | 不支持 |

**Rationale**

- 数据库适合元数据（状态、时间、关联），层级页面适合长文本（Wiki 内容）
- 用户浏览时需要 Gallery/Board 视图（需求 Q12）
- LLM 用 Markdown 读写页面比操作数据库字段更自然

**Supports**

- REQ-001, REQ-002, REQ-004, REQ-007

**ADR**

- ADR 0001

---

#### DEC-002：冲突分类的实现方式

**Selected**

使用 **LLM 基于规则和上下文的分类**，辅以关键词匹配和时间戳分析。

**Alternatives**

- 方案 A：纯规则（关键词匹配）
- 方案 B：训练一个分类模型

**Trade-off**

| Dimension | Selected | Alternative A | Alternative B |
|---|---|---|---|
| 准确性 | 中高（LLM 理解上下文） | 低（关键词不可靠） | 高（但需要训练数据） |
| 实现复杂度 | 低 | 低 | 高 |
| 可解释性 | 高（LLM 给出理由） | 一般 | 低（黑盒） |
| 成本 | 中（LLM token） | 低 | 高（训练+推理） |

**Rationale**

- 冲突类型的判断需要理解语义，纯关键词不可靠
- 训练分类模型的成本高，且训练数据不足
- LLM 可以给出分类理由，便于用户纠正

**Supports**

- REQ-003

**ADR**

- ADR 0004

---

#### DEC-003：Skill 同步的冲突检测策略

**Selected**

使用 **文件修改时间戳 + sync-metadata.json 记录**：
- `sync-metadata.json` 记录每个 skill 的上次同步时间和 Notion 页面 ID
- 同步时对比 Notion 页面的最后修改时间和本地文件的修改时间
- 如果两者都晚于上次同步时间，标记冲突

**Alternatives**

- 方案 A：只检查本地文件修改时间
- 方案 B：使用文件内容哈希对比

**Trade-off**

| Dimension | Selected | Alternative A | Alternative B |
|---|---|---|---|
| 准确性 | 高 | 中（漏检 Notion 修改） | 最高 |
| 性能 | 快 | 快 | 慢（需要读取全部内容计算哈希） |
| 实现复杂度 | 中 | 低 | 高 |

**Rationale**

- 时间戳足够判断冲突，不需要完整内容对比
- 方案 A 无法检测 Notion 侧的修改
- 方案 B 性能开销大，收益有限

**Supports**

- REQ-005, SCN-005-C

**ADR**

- ADR 0002

---

#### DEC-004：Agent 失败分类的决策树

**Selected**

使用 **固定的失败类型列表** + **LLM 分析错误消息**：

失败类型：
1. 工具路径/配置错误
2. 前置条件缺失
3. 输入数据格式问题
4. 知识不足（skill 或 Wiki 不完整）
5. 外部服务不可用
6. Skill 逻辑错误

LLM 读取错误消息和堆栈跟踪，匹配到类型并建议修复方案。

**Alternatives**

- 方案 A：只记录原始错误，不分类
- 方案 B：用异常类型（Exception subclass）自动分类

**Trade-off**

| Dimension | Selected | Alternative A | Alternative B |
|---|---|---|---|
| 可操作性 | 高（明确修复方向） | 低 | 中 |
| 实现复杂度 | 中 | 低 | 高（需要 skill 中定义异常） |
| 灵活性 | 高（LLM 可处理未预见错误） | 高 | 低（只能处理预定义异常） |

**Rationale**

- 固定类型列表覆盖常见失败场景
- LLM 分析错误消息比异常类型更灵活（不需要修改 skill 代码）
- 方案 A 不提供修复指导，用户体验差

**Supports**

- REQ-008

**ADR**

- ADR 0003

---

#### DEC-005：通过托管 Notion MCP 访问，系统命令由 skill 驱动

**Selected**

- 用 `claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp` 安装托管 MCP，`/mcp` 完成 OAuth 登录
- 系统命令写成 SKILL.md 中的操作步骤，由 agent 调用 `notion-*` 工具执行
- 限流由 MCP 服务端处理：等待 ≤ 2 秒时自动重试一次，否则返回 `rate_limited` 和 `retry_after_seconds`，skill 按 NEG-004 处理

**Alternatives**

- 方案 A：Python 直接调用 REST API，integration token 存 `.env`，客户端自己做速率控制（#2、#3 第一版实现）
- 方案 B：MCP 与 REST 混用

**Trade-off**

| Dimension | Selected | Alternative A | Alternative B |
|---|---|---|---|
| 符合约束 | 符合 §1.6 | 不符合 | 部分符合 |
| 凭据管理 | 无（OAuth） | 需要管理 token | 两套 |
| 权限 | 用户本人权限 | 需逐个授权页面 | 两套 |
| 执行确定性 | 较低（agent 按步骤执行） | 高（代码） | 混合 |
| 可测试性 | 真实运行 skill 验证 | mock 单元测试 | 两种都要 |
| 维护成本 | 低（API 版本由服务端处理） | 需跟随 API 升级 | 最高 |

**Rationale**

- 需求访谈 Q6 选定了托管 MCP，§1.6 也写为硬约束
- 需求里没有脱离 Claude 会话运行的场景，代码带来的确定性优势用不上
- 执行确定性的不足靠 skill 中的核对步骤弥补（建完用 `notion-fetch` 回读核对）

**Supports**

- REQ-001 ~ REQ-008, NEG-003, NEG-004

**ADR**

- ADR 0006（取代 ADR 0005）

---

### 3.3 Components and Data Flow

| Component | Change | Responsibility | Depends On | Supports |
|---|---|---|---|---|
| **托管 Notion MCP** | Use | 提供 `notion-*` 工具读写 Notion；OAuth 认证；服务端处理限流 | Notion | 所有 Notion 操作 |
| **Ingest Engine** | Add | 读取原始材料，提炼知识，检测冲突，建议更新 | Notion MCP, Conflict Detector | REQ-002 |
| **Conflict Detector** | Add | 检测知识冲突，分类，查证证据，创建 Conflict 记录 | Notion MCP, web_search | REQ-003 |
| **Wiki Manager** | Add | 维护 Wiki 结构，建立双向链接，记录 Changelog | Notion MCP | REQ-001, REQ-002, REQ-007 |
| **Lint Engine** | Add | 扫描 Wiki，检测矛盾/过时/缺失链接/孤岛页面 | Notion MCP | REQ-004 |
| **Skill Sync Engine** | Add | 扫描 Notion techniques，生成 Claude Code skill 文件，检测冲突，提交 Git | Notion MCP, Git Client | REQ-005 |
| **Agent Task Logger** | Add | 记录 Agent 执行结果到 Notion Agent Tasks 数据库 | Notion MCP | REQ-006 |
| **Failure Analyzer** | Add | 分析失败记录，识别失败类型，建议修复方案 | Notion MCP | REQ-008 |
| **System Commands** | Add | 7 个 Claude Code skill（/init-wiki, /ingest, /sync-skills, /lint-wiki, /resolve-conflict, /test-skill, /verify-system） | 上述所有组件 | 所有 REQ |

**主要数据流**：

**流程 1：入库新材料**
```
用户添加材料到 Sources 数据库
  → 用户运行 /ingest
  → Ingest Engine 读取待处理材料
  → 提炼知识（concepts/techniques/tools）
  → Conflict Detector 检测冲突
  → 如有冲突：分类 → 查证证据 → 创建 Conflict 记录
  → LLM 建议更新 Wiki
  → 用户确认
  → Wiki Manager 更新 Notion Wiki
  → 建立双向链接
  → 记录到 Wiki Changelog
  → 更新 Sources 状态为"已入库"
```

**流程 2：同步技能**
```
用户运行 /sync-skills
  → Skill Sync Engine 读取 Notion techniques/
  → 识别可执行技能
  → 对比 sync-metadata.json
  → 检测新增/修改/删除/冲突
  → 生成 Claude Code skill 文件
  → 保存到本地 agent-brain 仓库
  → 更新 sync-metadata.json
  → Git commit & push
```

**流程 3：Agent 执行与反馈**
```
用户给 Agent 任务
  → Agent 查询本地 skill 仓库
  → 加载并执行 skill
  → 如成功：Agent Task Logger 记录结果
  → 如失败：记录详细错误
  → Failure Analyzer 分析失败类型
  → 建议修复 skill 或 Wiki
  → 用户确认后更新
```

---

### 3.4 Data and Interface Changes

| Item | Type | Change | Contract / Constraint | Supports |
|---|---|---|---|---|
| **Sources Database** | Data | Add | 字段：标题、类型（文章/视频/图片/项目）、链接、状态（待处理/处理中/已入库/已归档）、领域标签、添加时间 | REQ-002 |
| **Wiki Index Database** | Data | Add | 字段：标题、分类（concepts/techniques/tools）、领域标签、简短摘要、最后更新时间、来源材料（关联 Sources） | REQ-001, REQ-002 |
| **Agent Tasks Database** | Data | Add | 字段：任务名、使用的 Skill、执行时间、状态（成功/失败）、结果摘要、失败原因、反馈/问题 | REQ-006, REQ-008 |
| **Wiki Changelog Database** | Data | Add | 字段：Wiki 页面（关联 Wiki Index）、变更时间、来源材料（关联 Sources）、变更类型（新建/更新/冲突解决）、详情 | REQ-007 |
| **Conflicts Database** | Data | Add | 字段：Wiki 页面、冲突类型、新材料、原有内容摘要、新内容摘要、证据链接、证据强度评分、状态（待审核/已解决）、解决方案 | REQ-003, REQ-007 |
| **Wiki 页面** | Data | Add | 即 Wiki Index 条目：正文为页面内容（Markdown），相关页面用页面提及链接；concepts/、techniques/、tools/ 分类页面只放按「分类」筛选的视图（ADR 0007） | REQ-001, REQ-002 |
| **Wiki 定位** | Contract | Add | 不保存本地配置。skill 每次运行时按根页面标题精确搜索（正式「LLM Wiki 系统」，测试「LLM Wiki 系统（测试）」），从根页面内容读出各数据库 URL、data source ID 和分类页面；找到多个时问用户，找不到时提示先运行 `/init-wiki`（ADR 0008） | REQ-001 ~ REQ-008 |
| **sync-metadata.json** | Data | Add | 格式：{ "last_sync": "ISO timestamp", "skills": [{ "notion_page_id": "", "skill_path": "", "last_sync": "" }] } | REQ-005 |
| **Notion MCP 工具** | API | Use | 由 agent 在会话中调用，见下方契约 | 所有 Notion 操作 |
| **Claude Code Skill Format** | API | Use | 输入：SKILL.md 文件（frontmatter + 正文）；输出：skill 可被 Skill() 工具加载 | REQ-005, REQ-006 |
| **Git Push** | API | Use | 输入：commit message；输出：push 成功或失败；错误：认证失败、冲突 | REQ-005 |

**对外接口或跨模块契约**：

**Notion MCP 契约**（工具清单见 https://developers.notion.com/guides/mcp/mcp-supported-tools）：
- 读取：`notion-fetch`（页面、数据库、data source `collection://...`、视图）、`notion-search`
- 页面：`notion-create-pages`（不传 parent 时建私有页面）、`notion-update-page`、`notion-move-pages`
- 删除：`notion-delete-pages`，必须带 `user_confirmed: true`，只能在用户明确同意后调用；顶层页面目前无法通过 MCP 恢复
- 数据库：`notion-create-database`（同时建第一个 data source 和默认视图）、`notion-update-data-source`（更新 select 选项时必须列出全部选项，漏掉的会被删除）
- 视图：`notion-create-view` / `notion-update-view`，配置语法见 MCP 资源 `notion://docs/view-dsl-spec`
- 查询：`notion-query-data-sources`，rows 模式每次最多 100 行
- 限流：每次调用计入 Notion API 配额；返回 `rate_limited` 时带 `retry_after_seconds`
- 权限：以登录用户本人的 Notion 权限操作

**Claude Code Skill 契约**：
- SKILL.md 必须包含 frontmatter（至少有 `name` 和 `description`）
- Skill() 工具加载时验证格式
- 执行失败时抛出异常，包含错误消息

---

### 3.5 Error and Failure Handling

| Failure | Observable Behavior | Recovery / Degradation | Covered Scenario |
|---|---|---|---|
| **MCP 限流（`rate_limited`）** | agent 汇报等待时长 | 按 `retry_after_seconds` 等待后重试一次；再失败则停止并汇报已完成部分 | NEG-004 |
| **MCP 未安装或未登录** | `notion-*` 工具不可用，命令中止 | 提示用户运行 `claude mcp add` 和 `/mcp` 登录，必要时重启会话 | REQ-001 ~ REQ-008 |
| **Notion 页面不存在或无权访问** | 跳过该页面并在汇报中列出 | 继续处理其他页面 | REQ-004, REQ-005 |
| **批量创建中途失败** | 停止，列出已创建内容和失败原因 | 不自动清理；用户修复后重跑，选择覆盖 | REQ-001 |
| **LLM 无法分类冲突** | 冲突记录标记为"无法判断"，提示用户手动分类 | 不阻塞入库流程 | SCN-003-E |
| **Git push 失败（冲突）** | 提示用户"本地仓库有未推送的提交或远程有新提交"，建议先 pull | 用户手动 pull 后重新运行 /sync-skills | REQ-005 |
| **Skill 生成失败（格式错误）** | 跳过该 skill，记录错误日志，提示用户检查 Notion 页面 | 继续处理其他 skill | REQ-005 |
| **Agent 执行 skill 失败** | 记录失败到 Agent Tasks 数据库，返回错误给用户 | Failure Analyzer 分析并建议修复 | REQ-006, REQ-008 |
| **网络不可用** | 命令中止，提示无法连接 Notion MCP 或 GitHub | 用户检查网络后重试 | 所有网络操作 |

---

### 3.6 Observability, Security and Performance

#### Observability

- **日志**：
  - INFO：命令开始/结束、主要步骤（如"读取 5 条待处理材料"）
  - WARN：跳过的页面、检测到的冲突、限流等待
  - ERROR：API 失败、Git 失败、格式错误
- **指标**（可选，后续优化）：
  - 入库材料数量、冲突数量、同步 skill 数量、Agent 任务成功/失败数
- **业务事件**：
  - 记录到 Notion 数据库（Wiki Changelog, Agent Tasks）
- **诊断和审计所需的关键标识**：
  - Notion page_id、database_id
  - Git commit hash
  - Agent task timestamp

#### Security

- **认证**：托管 MCP 的 OAuth 登录，凭据由 Claude Code 保管，仓库中没有凭据（NEG-003）
- **授权**：以登录用户本人的 Notion 权限操作；删除类操作必须先得到用户明确同意
- **敏感数据**：不在仓库、skill 输出或提交信息中记录凭据
- **审计**：Wiki Changelog 和 Agent Tasks 记录所有操作和时间戳

#### Performance

- **延迟预算**：
  - 单个材料入库 < 5 分钟（QOS-001）
  - 50 个 skill 同步 < 20 分钟（QOS-002）
- **吞吐预算**：
  - 受 Notion API 请求配额限制，具体额度由 Notion 按套餐决定
- **容量假设**：
  - Wiki 页面数 < 10000（Notion 单个 workspace 限制）
  - Skill 数量 < 500（假设每个领域 < 100 个技能）
- **性能退化边界**：
  - 待处理材料很多时，入库可能多次触发 `rate_limited`，总耗时随 Notion 套餐的请求额度变化

---

## 4. Verification and Traceability

### 4.1 Testing Principles

- 测试外部可观察行为（Notion 数据库记录、本地 skill 文件、Agent 执行结果），不绑定内部实现
- 优先用集成测试验证完整流程（E2E），单元测试只用于复杂逻辑（如冲突分类算法）
- 涉及 Notion 的行为，在真实 Notion 中运行 skill 验证（DEC-005）：在用户指定的测试页面下执行，不碰正式 Wiki
- 纯逻辑（如冲突分类、skill 生成）可以写成代码并做单元测试，但不直接调用 Notion
- 每个 REQ 的每个场景（SCN）都有对应的验证项（VAL）
- 负向需求（NEG）有独立的负向验证
- 验证结束后，测试数据经用户确认再移入回收站

### 4.2 Test Seams

| Seam | Level | Reason | Prior Art | Covers |
|---|---|---|---|---|
| **Skill 真实运行** | Integration | 在测试页面下运行系统命令 skill，用 `notion-fetch` 回读检查结果；skill 是系统的最外层接口 | `test-skill`（agent-toolkit） | REQ-001 ~ REQ-007 |
| **冲突检测单元测试** | Unit | 验证五类冲突的识别逻辑（规则匹配 + LLM 分类）；这是高组合复杂度的纯逻辑 | 无（新功能） | REQ-003, SCN-003-A ~ SCN-003-E |
| **Skill 生成组件测试** | Component | 验证从 Notion technique 页面生成符合 Claude Code 规范的 SKILL.md 文件 | Claude Code skill 格式验证（参考 `skill-creator` skill） | REQ-005, SCN-005-A |
| **端到端工作流测试** | E2E | 验证完整流程：添加材料 → 入库 → 生成 skill → agent 执行 → 反馈；这是最高可用的 seam | 无（新系统） | 所有 REQ 的主场景 |
| **Skill 执行集成测试** | Integration | 验证生成的 skill 可以被 Claude Code 正确加载和执行 | Claude Code skill 测试（参考 `test-skill` skill） | REQ-006, SCN-006-A |

### 4.3 Verification Plan

| Verification | Requirement / Scenario | Method | Expected Result |
|---|---|---|---|
| **VAL-001** | REQ-001, SCN-001-A, SCN-001-B | 真实运行：在测试页面下运行 `/init-wiki`，用 `notion-fetch` 回读；再运行一次 | 5 个数据库字段、选项、relation 与 schema.md 一致；Board/Gallery 视图存在；3 个分类页面存在；第二次运行提示"是否覆盖？"且未做修改 |
| **VAL-002** | REQ-002, SCN-002-A | 自动测试：添加测试材料到 Sources，运行 `/ingest`，检查 Wiki 页面和 Changelog | Wiki 页面包含提炼的知识；Changelog 有记录 |
| **VAL-003** | REQ-003, SCN-003-A | 单元测试：模拟事实性冲突输入，验证 LLM 分类为"事实性"并查证证据 | 冲突类型=事实性；证据链接非空 |
| **VAL-004** | REQ-003, SCN-003-B | 单元测试：模拟观点性冲突，验证分类为"观点性"且不查证 | 冲突类型=观点性；推荐方案="两者都保留" |
| **VAL-005** | REQ-004, SCN-004-A | 自动测试：在测试 Wiki 创建矛盾页面，运行 `/lint-wiki`，检查报告 | 报告包含矛盾检测结果 |
| **VAL-006** | REQ-005, SCN-005-A | 自动测试：在测试 Notion 创建 technique 页面，运行 `/sync-skills`，检查本地 skill 文件 | skill 文件格式正确；sync-metadata.json 已更新 |
| **VAL-007** | REQ-005, SCN-005-C | 自动测试：同时修改 Notion 和本地 skill，运行 `/sync-skills`，检查冲突提示 | 系统提示冲突，不覆盖 |
| **VAL-008** | REQ-006, SCN-006-A | 集成测试：Agent 调用测试 skill 执行任务，检查 Agent Tasks 记录 | 记录存在，状态=成功 |
| **VAL-009** | REQ-006, SCN-006-B | 集成测试：Agent 调用故意失败的 skill，检查失败记录 | 记录存在，状态=失败，失败原因非空 |
| **VAL-010** | REQ-007, SCN-007-A | 自动测试：创建冲突记录，运行 `/resolve-conflict`，检查 Wiki 更新和 Changelog | Wiki 已更新；Changelog 有冲突解决记录 |
| **VAL-011** | REQ-008, SCN-008-A | 自动测试：创建失败记录（工具路径错误），运行 Failure Analyzer，检查建议 | 失败类型=工具路径错误；建议包含"检查路径" |
| **VAL-012** | NEG-001 | 负向测试：触发冲突但不确认，检查 Wiki 未变化 | Conflicts 数据库有记录，状态=待审核；Wiki 内容未变 |
| **VAL-013** | NEG-002 | 负向测试：手动修改本地 skill 后同步，检查未覆盖 | 系统提示冲突；本地 skill 内容未变 |
| **VAL-014** | NEG-003 | 静态检查：运行 §4.5 的命令 | 无匹配；`.gitignore` 包含 `.env` |
| **VAL-015** | NEG-004 | 检查：每个调用 `notion-*` 的 SKILL.md 都写有限流处理步骤 | 所有相关 skill 都包含按 `retry_after_seconds` 等待、重试一次、失败即停的步骤 |
| **VAL-016** | QOS-001 | 性能测试：入库 3000 字文章，记录时间 | 时间 < 5 分钟 |
| **VAL-017** | QOS-002 | 性能测试：同步 50 个 technique，记录时间 | 时间 < 20 分钟 |
| **VAL-018** | QOS-003 | 性能测试：Agent 加载 skill，记录时间 | 时间 < 10 秒 |
| **VAL-019** | 端到端 | `/verify-system` 脚本：自动运行完整流程并检查所有步骤 | 所有步骤通过 |

### 4.4 Requirement Coverage

| Requirement | Design Location | Verification | Status |
|---|---|---|---|
| REQ-001 | `/init-wiki` skill, `references/schema.md`, DEC-005 | VAL-001 | Covered |
| REQ-002 | §3.3 Ingest Engine, Wiki Manager | VAL-002 | Covered |
| REQ-003 | §3.3 Conflict Detector, §3.4 Conflicts Database, DEC-002 | VAL-003, VAL-004 | Covered |
| REQ-004 | §3.3 Lint Engine | VAL-005 | Covered |
| REQ-005 | §3.3 Skill Sync Engine, §3.4 sync-metadata.json, DEC-003 | VAL-006, VAL-007 | Covered |
| REQ-006 | §3.3 Agent Task Logger | VAL-008, VAL-009 | Covered |
| REQ-007 | §3.3 Wiki Manager, §3.4 Wiki Changelog Database | VAL-010 | Covered |
| REQ-008 | §3.3 Failure Analyzer, DEC-004 | VAL-011 | Covered |
| NEG-001 | §3.3 Conflict Detector 流程 | VAL-012 | Covered |
| NEG-002 | §3.3 Skill Sync Engine, DEC-003 | VAL-013 | Covered |
| NEG-003 | §3.6 Security, DEC-005（OAuth，无本地凭据） | VAL-014 | Covered |
| NEG-004 | §3.5 MCP 限流处理, DEC-005 | VAL-015 | Covered |
| QOS-001 | §3.6 Performance | VAL-016 | Covered |
| QOS-002 | §3.6 Performance | VAL-017 | Covered |
| QOS-003 | §3.6 Performance, Skill 加载机制 | VAL-018 | Covered |

### 4.5 Verification Commands

前置条件（一次性）：

```bash
claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp
# 然后在 Claude Code 中运行 /mcp 完成 OAuth 登录
```

静态检查（VAL-014）：

```bash
git grep --untracked -nE 'ntn_|secret_|NOTION_TOKEN' -- ':!SPEC-LLM-WIKI-SYSTEM.md' \
  ':!.claude/skills/verify-system/scripts/verify_tools.py' ':!tests/verify_system/test_verify_tools.py'
# 期望无输出；--untracked 连还没 git add 的文件一起查，排除的两个文件里写着这些模式本身
grep -x '.env' .gitignore                  # 期望输出 .env
```

VAL-014、VAL-015 也可以用 `python3 .claude/skills/verify-system/scripts/verify_tools.py static --repo .` 一起检查。

纯逻辑和文档约束的单元测试：

```bash
python3 -m unittest discover -s tests -t .
```

Notion 相关的验证项没有 shell 命令，在 Claude Code 会话中运行 `/verify-system`（`.claude/skills/verify-system/SKILL.md`），
它在测试 Wiki 里依次运行各命令，逐项核对 VAL-001 ~ VAL-018 并输出报告（VAL-019）。

### 4.6 Completion Criteria

- ✅ 所有 REQ 的所有 SCN 通过（VAL-001 ~ VAL-011）
- ✅ 所有 NEG 的负向验证通过（VAL-012 ~ VAL-014）
- ✅ 所有 QOS 达到量化门槛（VAL-015 ~ VAL-018）
- ✅ 端到端验证脚本通过（VAL-019）
- ✅ Requirement Coverage 表中所有 REQ/NEG/QOS 状态为 Covered
- ✅ 验证只在测试页面下进行，不污染正式 Wiki；测试数据经用户确认后移入回收站
- ✅ skill 的汇报中能看到每一步的结果、跳过项和失败原因
- ✅ 仓库中没有 Notion 凭据（VAL-014）
- ✅ §5 Open Items 中无阻塞性未决问题

---

## 5. Open Items

**延后处理的优化项**（非阻塞）：

1. **Notion 数据库容量限制**：单个数据库页面数量上限未知，遇到再分库
2. **双向同步**：本地 skill 修改后同步回 Notion Wiki（当前版本不支持）
3. **领域失衡提示**：某些领域材料特别多时的提示或限制机制
4. **自动化程度提升**：
   - 入库从半自动升级到全自动（低风险材料）
   - 冲突解决从人工确认升级到自动解决简单冲突
   - Lint 从只报告升级到自动修复
   - Agent 失败反馈从记录升级到自动修复 skill
5. **Skill 测试套件**：为每个 skill 编写测试文件（当前可选）
6. **CI/CD 集成**：GitHub Actions 自动运行 skill 测试（当前手动测试）
7. **指标和监控**：统计入库数量、冲突数量、Agent 任务成功率（当前只有日志）

**已知技术债**（记录但不阻塞发布）：

- Notion MCP 的 Page History API 不可访问，只能用 Notion UI 查看历史版本
- skill 由 agent 按步骤执行，确定性低于代码；靠 skill 中的回读核对步骤弥补（DEC-005）
- 冲突分类的 LLM prompt 可能需要根据实际使用情况迭代优化

**需要用户确认的配置**（初次使用前）：

- GitHub 仓库 `agent-brain` 的可见性（公开或私有）
- 用于运行 VAL 测试的 Notion 测试页面
