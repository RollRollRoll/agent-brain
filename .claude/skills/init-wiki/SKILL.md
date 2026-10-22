---
name: init-wiki
description: 在 Notion 中初始化 LLM Wiki 结构（根页面、5 个数据库、视图、3 个分类页面）。用户要求初始化或重建 Wiki 时使用。
---

# init-wiki

通过 Notion MCP（`notion-*` 工具）创建 [references/schema.md](references/schema.md) 定义的结构。

各工具的参数格式以工具自身的描述为准；视图配置语法读 MCP 资源 `notion://docs/view-dsl-spec`。
不要凭记忆拼参数。

## 前置条件

`notion-*` 工具不可用时，停下来告诉用户：

1. 运行 `claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp`
2. 在 Claude Code 中运行 `/mcp`，按提示完成 OAuth 登录
3. 如果工具仍不出现，重启会话

## 步骤

1. **确认连接**：调用 `notion-get-self`，记下 workspace 名称和用户名。

2. **确定位置**：用户指定了父页面时，根页面建在它下面；没指定时，不传 parent，建成用户的私有页面。

3. **检查是否已存在**：用 `notion-search` 搜索 `LLM Wiki 系统`。只有标题完全一致、且不在回收站里的页面才算已存在。
   - 已存在时，**停下来问用户**：「Wiki 结构已存在（附链接），是否覆盖？覆盖会把旧结构移入 Notion 回收站，
     可以在 Notion 里恢复，但 MCP 目前不能恢复顶层页面。」
   - 用户明确回答「是 / 确认 / 继续」后，才用 `notion-delete-pages` 移走旧根页面，`user_confirmed` 设为 `true`。
   - 用户没有明确同意时，结束，不做任何修改。

4. **建根页面**：用 `notion-create-pages` 创建 `LLM Wiki 系统`，内容写一句「Agent Brain 知识库根页面，由 /init-wiki 创建。」

5. **建数据库**：在根页面下用 `notion-create-database`，按 schema.md 的顺序逐个创建。
   `schema` 参数用 SQL DDL，例如（2026-10-22 实测可用）：

   ```sql
   CREATE TABLE ("标题" TITLE, "状态" SELECT('待处理':gray, '已入库':green),
                 "领域标签" MULTI_SELECT(), "简短摘要" RICH_TEXT, "链接" URL,
                 "证据强度评分" NUMBER, "执行时间" DATE,
                 "添加时间" CREATED_TIME, "最后更新时间" LAST_EDITED_TIME,
                 "来源材料" RELATION('<被关联库的 data source ID>'))
   ```

   - 响应里的 `<data-source url="collection://...">` 就是 data source ID，记下它和 database URL。
     响应里没有时，用 `notion-fetch` 读取该数据库获取。
   - `RELATION('<id>')` 是单向关联，填被关联库的 data source ID（不带 `collection://` 前缀）。
   - select 字段的选项必须全部写上；颜色可选 default、gray、brown、orange、yellow、green、blue、purple、pink、red。
   - Sources、Wiki Index 建完后，剩下 3 个库互不依赖，可以并行创建。

6. **建视图**：按 schema.md 的视图表，用 `notion-create-view` 补建视图，`database_id` 和 `data_source_id` 都要传。
   `configure` 用视图 DSL：
   - Board：`GROUP BY "状态" SHOW EMPTY`。select 属性不要加 `BY OPTION` / `BY GROUP`，那两个只用于 status 属性。
   - Gallery：`SHOW "分类", "领域标签", "简短摘要"`（Notion 会自动把标题加进卡片）。

   单个视图失败时记下错误，继续往下，不回滚已建好的结构。

7. **建分类页面**：在根页面下用 `notion-create-pages` 一次创建 `concepts/`、`techniques/`、`tools/`。

8. **核对**：用 `notion-fetch` 读一遍每个数据库，确认字段名、类型、select 选项、relation 目标都和 schema.md 一致。
   发现不一致就用 `notion-update-data-source` 修正。注意：更新 select 选项时必须列出全部选项，漏掉的选项会被删除。

## 失败处理

- 工具返回 `rate_limited`：按 `retry_after_seconds` 等待后重试一次；再次失败就停下并汇报。
- 数据库建到一半失败：停止，列出已创建内容的链接和失败原因。不要自动清理；告诉用户修复后可以重新运行，
  到第 3 步时选择覆盖即可。
- 视图失败：结构其余部分照常完成，在汇报中说明哪个视图没建成，用户可以在 Notion 中手动添加。

## 汇报

结束时给用户列出：

- 根页面链接
- 5 个数据库的链接
- 已建成的视图（以及失败的视图和原因）
- 3 个分类页面的链接
- 如果覆盖过旧结构，旧根页面的链接
