# Notion 工具使用约定

wiki-admin 中调用 `notion-*` 工具的 skill 都按本文处理前置条件、写入格式和工具报错。
各工具的参数格式以工具自身的描述为准。写数据库条目前，先用 `notion-fetch` 读取目标 data source，
按返回的字段名和 SQLite 定义填属性。

## 前置条件

`notion-*` 工具不可用时，停下来告诉用户：运行
`claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp`，再用 `/mcp` 登录；
工具仍不出现就重启会话。

## 写入注意事项（2026-10-22 实测）

- **multi_select 选项必须先存在**：写入不存在的选项会报 `validation_error`。写入前对比 data source 已有选项，
  缺的用 `notion-update-data-source` 加上：`ALTER COLUMN "领域标签" SET MULTI_SELECT('已有选项':颜色, '新选项':颜色)`，
  **必须列出全部已有选项**，漏掉的会被删除。新增选项要先列给用户确认。
- **文件名会被识别成链接**：正文和属性里写 `index.md` 这类"名字.后缀"时，Notion 会自动转成 `http://index.md` 链接。
  一律用反引号包起来，例如 `` `index.md` ``。
- **页面提及**：写 `<mention url="页面 URL" />`。
- **relation 和 multi_select 属性**：值是 JSON 数组字符串，例如 `"[\"https://app.notion.com/p/...\"]"`。
- **批量创建**：同一 data source 下的多个页面可以在一次 `notion-create-pages` 中创建。
- **改页面中的一段**：用 `notion-update-page` 的 `update_content`，`old_str` 取原文且必须在页面中唯一。
  不要用 `replace_content` 整页覆盖。

## 工具报错

- `rate_limited`：按 `retry_after_seconds` 等待后重试一次；再次失败就停下，按所在 skill 的「写到一半失败」汇报。
- `notion-query-data-sources` 返回 `usage_limit_reached`（非 Business 版的 SQL / rows 查询额度用完）：
  不要重试，立刻停下。已经写入的内容按所在 skill 的「写到一半失败」处理并汇报；告诉用户额度会在 60 分钟内重置，
  重置后重新运行即可。按工具返回的 `client_guidance` 向用户说明一次，带上它给的链接。
- `entitlement_required`（例如一条 SQL 同时查多个 data source）：不要重试。改成每次只查一个 data source；
  做不到就停下，按 `client_guidance` 向用户说明并带上链接。
- 不删除已写入的内容来"回滚"。
