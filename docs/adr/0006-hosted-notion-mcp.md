# ADR 0006: 通过托管 Notion MCP 访问 Notion，系统命令由 skill 驱动

**状态**：已接受  
**日期**：2026-10-22  
**决策者**：用户  
**取代**：ADR 0005

## 背景

spec §1.6 要求通过 Notion 官方 MCP server（`https://mcp.notion.com/mcp`）访问 Notion。
#2、#3 的第一版实现偏离了这一约束：用 Python 直接调用 REST API，凭 integration token 认证，
token 存在 `.env` 中，并在客户端里自己实现速率控制和 API 版本迁移（ADR 0005）。

## 决策

- 用 `claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp` 安装托管 MCP，
  通过 `/mcp` 完成 OAuth 登录。选 `user` 作用域，是因为 agent 在其他项目里执行任务时也要查询这个知识库。
- `/init-wiki` 等系统命令写成 SKILL.md 中的操作步骤，由 agent 调用 `notion-*` 工具执行，不再有 Notion 客户端代码。
- Notion 结构定义放在 skill 的 references 文件中，作为唯一的定义来源。

## 候选方案

- **A. 托管 MCP + skill 驱动（采纳）**
- **B. 保留 REST + token**：可以脱离 Claude 会话运行，但需求里没有这类场景（不做定时抓取，入库是半自动的）。
- **C. 混合**：两套认证方式并存，维护成本最高。

## 理由

- 符合 spec 约束和需求访谈中的选择。
- OAuth 以用户本人的身份操作：不用管理 token，也没有 internal integration 的页面授权限制。
- 速率限制和 API 版本由 MCP 服务端处理，客户端不必跟着 Notion API 升级。

## 后果

- MCP 工具只能在 Claude 会话中调用。需要脱离会话运行的功能，日后要另做决策。
- 执行确定性低于代码：skill 必须写清每一步、失败处理和核对步骤（建完用 `notion-fetch` 回读核对）。
- 验证方式从 mock 单元测试改为在测试页面下真实运行 skill。
- 纯逻辑（如冲突分类）以后仍可写成代码并做单元测试，但不直接调用 Notion。

## 相关决策

- ADR 0001：使用 Notion 作为 Wiki 存储
- ADR 0005：Notion API 升级到 2026-03-11（已被本 ADR 取代）
