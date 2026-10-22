# ADR 0001: 使用 Notion 而非 Obsidian 作为 Wiki 存储

**状态**：已接受  
**日期**：2026-10-21  
**决策者**：用户

## 背景

Karpathy 的 LLM Wiki 模式和橙皮书推荐的实现都基于本地 Markdown 文件（Obsidian），原因是：
- LLM/Agent 可以直接通过文件系统读写
- 零配置成本
- 完全离线可用

但用户选择使用 Notion 作为 Wiki 存储。

## 决策

使用 Notion 作为知识库的主要存储，通过 Notion 官方 MCP server 让 Claude Code 访问。

## 理由

用户给出的原因：
1. **不想安装额外软件**：不希望安装 Obsidian
2. **Notion 的展示能力更好**：
   - 数据库视图（Table/Board/Gallery）更适合组织和浏览
   - 知识卡片（Gallery 视图）比纯文件列表更直观
3. **已有 Notion 使用习惯**：用户更熟悉 Notion 的操作方式

## 后果

### 优势
- 用户浏览体验更好（数据库视图、卡片展示）
- 可以利用 Notion 的协作功能（如果将来需要）
- 托管 Notion MCP 以 Markdown 读写页面内容，LLM 可以直接处理

### 代价
- **需要安装并登录 MCP**：一次性运行 `claude mcp add` 和 `/mcp` OAuth 登录（ADR 0006）
- **受 Notion API 请求限制**：MCP 的每次工具调用都计入配额，批量操作可能遇到 `rate_limited`
- **只能在 Claude 会话中访问**：MCP 工具无法被脚本直接调用
- **无法离线使用**：依赖网络和 Notion 服务可用性

### 缓解措施
- Agent 执行时使用本地 Skill（不走 Notion），Notion 只用于知识维护和浏览
- 收到 `rate_limited` 时按 `retry_after_seconds` 等待后重试

## 替代方案

### 方案 A：使用 Obsidian（未采纳）
- 优点：零配置，LLM 直接读写，无速率限制
- 缺点：需要安装软件，用户不想用

### 方案 B：Notion 导出 + 本地 Markdown 混合（未采纳）
- 定期将 Notion 导出为 Markdown，Agent 读本地副本
- 优点：Agent 访问快，不受 API 限制
- 缺点：实时性差，同步复杂，失去了 Notion 作为单一数据源的优势

## 相关决策

- ADR 0002：技能库存储在本地 Git 仓库而非 Notion
- ADR 0003：Agent 失败反馈机制
