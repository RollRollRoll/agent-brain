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
- Notion Markdown 支持让 LLM 可以高效读写（`retrieve-page-markdown` / `update-page-markdown`）

### 代价
- **需要配置 MCP server**：增加初始配置复杂度（需要创建 Integration、配置 token）
- **受 API 速率限制**：每秒 3 次请求，批量操作需要控制频率
- **需要手动授权页面**：Integration 无法动态发现新页面，每个顶层页面需要手动授权
- **无法离线使用**：依赖网络和 Notion API 可用性

### 缓解措施
- Agent 执行时使用本地 Skill（不走 Notion API），Notion 只用于知识维护和浏览
- 批量操作时实现请求队列和速率控制
- 初始化时一次性授权顶层页面，子页面自动继承权限

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
