# Notion 工具使用约定

wiki-admin 中调用 `notion-*` 工具的 skill 都按本文处理前置条件、写入格式和工具报错。
各工具的参数格式以工具自身的描述为准。写数据库条目前，先用 `notion-fetch` 读取目标 data source，
按返回的字段名和 SQLite 定义填属性。

## 前置条件

`notion-*` 工具不可用时，停下来，按当前运行环境告诉用户怎么装：

- Claude Code：运行 `claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp`，再用 `/mcp` 登录
- Codex：运行 `codex mcp add notion --url https://mcp.notion.com/mcp`，再运行 `codex mcp login notion`

工具仍不出现就重启会话。

## 写入注意事项（2026-10-22 实测）

- **multi_select 选项必须先存在**：写入不存在的选项会报 `validation_error`。写入前对比 data source 已有选项，
  缺的用 `notion-update-data-source` 加上：`ALTER COLUMN "领域标签" SET MULTI_SELECT('已有选项':颜色, '新选项':颜色)`，
  **必须列出全部已有选项**，漏掉的会被删除。新增选项要先列给用户确认。
- **文件名和域名会被识别成链接**：正文和属性里写 `index.md` 这类"名字.后缀"或 `python.org` 这类域名时，
  Notion 会自动转成 `http://index.md`、`[python.org](http://python.org)` 链接。一律用反引号包起来，例如 `` `index.md` ``（2026-10-27 实测域名也会转）。
- **页面提及**：写 `<mention url="页面 URL" />`。
- **relation 和 multi_select 属性**：值是 JSON 数组字符串，例如 `"[\"https://app.notion.com/p/...\"]"`。
- **批量创建**：同一 data source 下的多个页面可以在一次 `notion-create-pages` 中创建。
- **日期时间只保留到分钟**：写入带秒的时间，回读时秒数会被去掉。核对时不要把这当成写错（2026-10-23 实测）。
- **改页面中的一段**：用 `notion-update-page` 的 `update_content`，`old_str` 取原文且必须在页面中唯一。
  不要用 `replace_content` 整页覆盖。`old_str` 里不要包含 `<mention ... />`：fetch 返回的 mention 标记匹配不到，
  会报 `validation_error: No matches found`（2026-10-23 实测）。要在 mention 列表末尾追加时用 `insert_content`。

## 分页读取 Wiki Index

需要读取全部 Wiki 页面的 skill（lint-wiki、sync-skills）都按下面的方式分页：

- 首选 view 模式（不占 SQL / rows 查询额度）：`notion-fetch` Wiki Index 数据库，取 `Default view` 的 view URL，
  确认它没有筛选条件；然后 `notion-query-data-sources`（`mode: "view"`，`page_size: 100`）查询。
  返回 `has_more: true` 时把 `next_cursor` 作为 `start_cursor` 继续查，直到 `has_more` 为 false。
- 默认视图带筛选、或被删掉时，改用 rows 模式：每次 `limit: 100`，按 `createdTime` 升序；
  不满 100 行说明取完了，满 100 行就用 `created_time` 的 `date_is_on_or_after`（不要用 `date_is_after`：同一批建的页面创建时间相同，
  会漏掉）筛选上一批最后一行的创建时间，继续取，按 URL 去掉已经取过的页面。一批里没有新页面时停下，
  告诉用户 rows 模式无法分页，请恢复默认视图后重试。

汇报里写明共取了几批、几个页面。

## 工具报错

- `rate_limited`：按 `retry_after_seconds` 等待后重试一次；再次失败就停下，按所在 skill 的「写到一半失败」汇报。
- `notion-query-data-sources` 返回 `usage_limit_reached`（非 Business 版的 SQL / rows 查询额度用完）：
  不要重试，立刻停下。已经写入的内容按所在 skill 的「写到一半失败」处理并汇报；告诉用户额度会在 60 分钟内重置，
  重置后重新运行即可。按工具返回的 `client_guidance` 向用户说明一次，带上它给的链接。
- `entitlement_required`（例如一条 SQL 同时查多个 data source）：不要重试。改成每次只查一个 data source；
  做不到就停下，按 `client_guidance` 向用户说明并带上链接。
- 不删除已写入的内容来"回滚"。
