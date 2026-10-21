---
project: LLM Wiki 系统
domain: 知识管理与 Agent 技能库
---

# 术语表

## 核心概念

### 原始材料（Sources）
用户手动筛选和添加的高质量信息来源，包括：
- 文章、论文、博客
- 视频转录文稿
- 图片描述
- 项目案例

**特征**：不可变，作为知识提炼的输入。

### Wiki
由 LLM 持续维护的结构化知识库，从原始材料中提炼而来。按三个维度组织：
- **Concepts**（概念）：领域基础概念和理论
- **Techniques**（技术/方法）：具体的实施方法和流程
- **Tools**（工具）：软件工具、框架、库

**特征**：可变，LLM 负责维护一致性和时效性。

### Skill
从 Wiki 的 Techniques 中提炼出的可执行技能，格式符合 Claude Code skill 规范。

**关键区别**：
- **Wiki Technique**：面向人类学习，包含背景、原理、案例（存储在 Notion）
- **Skill**：面向 Agent 执行，包含步骤、前置条件、失败处理（存储在本地 Git 仓库）

### 知识入库（Ingest）
将原始材料转化为 Wiki 页面的过程。LLM 执行以下操作：
1. 提取关键概念、技术、工具
2. 在 Wiki 中创建或更新页面
3. 建立双向链接
4. 识别冲突并记录

**触发方式**：半自动（用户添加材料后手动触发，LLM 处理后等待确认）

### 知识冲突（Conflict）
新材料与已有 Wiki 内容不一致时产生的记录。分为五类：
1. **事实性冲突**：可验证的事实不一致
2. **观点性冲突**：主观偏好或评价不同
3. **时效性冲突**：新信息覆盖旧信息
4. **场景性冲突**：不同场景下的不同建议（实际是补充）
5. **深度性冲突**：简化版 vs 完整版（实际是层次差异）

### 证据核验（Evidence Verification）
处理冲突的机制，根据冲突类型采取不同策略：
- 事实性：LLM 主动查证可信来源，记录证据链接
- 观点性/场景性：记录双方来源和上下文，两者都保留
- 包含证据强度评分（官方文档 > 知名博客 > 个人博客）

### 历史保留（History Preservation）
两层机制：
1. Notion 原生 Page History（防误改，但 API 不可访问）
2. Wiki Changelog 数据库（追溯知识演进，支持查询和统计）

### 知识整理（Lint）
定期检查 Wiki 健康度的过程，检查项包括：
- 矛盾检测：不同页面的说法冲突
- 过时内容：长期未更新的页面
- 缺失链接：应建立但未建立的页面关联
- 孤岛页面：无其他页面链接的页面

**频率**：每周或手动触发

### 同步（Sync）
将 Notion Wiki 的 Techniques 转化为本地 Skill 的过程。

**方向**：单向（Notion → 本地 Git 仓库）

**触发方式**：手动（运行 `/sync-skills` 命令）

**冲突处理**：如果本地 skill 和 Notion technique 都被修改，标记冲突需要人工合并。

## 参与者

### 用户
- **主要职责**：筛选和添加原始材料，浏览学习 Wiki 内容
- **次要职责**：解决知识冲突，审核 LLM 的入库结果
- **不负责**：维护 Wiki 结构，编写 Skill

### LLM
- **主要职责**：维护 Wiki（ingest/lint），生成和更新 Skill
- **辅助职责**：分类冲突，查证事实性冲突，提供专业知识支持用户决策
- **不负责**：筛选原始材料（质量把控由用户负责）

### Agent
- **主要职责**：执行用户任务，优先使用本地 Skill
- **辅助职责**：查询 Notion Wiki（辅助用户讨论方案）
- **反馈职责**：将执行结果和问题记录到 Agent Tasks 数据库
- **不负责**：直接修改 Wiki 或 Skill（反馈由 LLM 整合）

## 领域分类

系统支持多领域知识，当前包括但不限于：
- 视频制作（拍摄、剪辑、特效）
- 软件开发（编程、调试、架构）
- 其他领域按需添加

**组织方式**：统一分类（concepts/techniques/tools 跨领域共享），通过标签（tags）区分领域。

## 工具生态

### Notion
- **职责**：存储 Wiki 和元数据（原始材料清单、冲突记录、变更日志、任务记录）
- **访问方式**：Notion 官方 MCP server（通过 Claude Code）
- **格式**：支持 Markdown 读写（`retrieve-page-markdown` / `update-page-markdown`）

### Git / GitHub
- **职责**：版本控制 Skill 仓库（`git@github.com:RollRollRoll/agent-brain.git`）
- **内容**：Claude Code skill 文件、系统管理 skill（如 `/init-wiki`、`/ingest`）
- **可见性**：待定（公开或私有）

### Claude Code
- **职责**：运行 LLM 和 Agent，连接 Notion（通过 MCP）和本地文件系统
- **配置**：`~/.claude/settings.json` 中配置 Notion MCP server

## 相关链接

- Karpathy LLM Wiki 模式：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Obsidian AI 橙皮书：https://github.com/alchaincyf/obsidian-ai-orange-book
- Notion MCP 文档：https://developers.notion.com/docs/mcp
- Skill 仓库：git@github.com:RollRollRoll/agent-brain.git
