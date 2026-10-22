# 定位 Wiki

wiki-admin 的 skill 都按本文找到要操作的 Wiki。不保存本地配置，Notion 是唯一的定位来源（ADR 0008）。

## 根页面标题

- 正式 Wiki：`LLM Wiki 系统`
- 测试 Wiki：`LLM Wiki 系统（测试）`

用户说"测试 Wiki"或明确给出标题时用对应标题，否则用正式标题。

## 步骤

1. 用 `notion-search` 搜索根页面标题。只保留标题**完全一致**、类型为 page、且不在回收站里的结果。
2. 按结果数处理：
   - 0 个：停下，告诉用户还没有这个 Wiki，请先运行 `/wiki-admin:init-wiki`。
   - 多于 1 个：列出每个结果的链接和路径，问用户用哪一个，不要自己挑。
   - 1 个：继续。
3. 用 `notion-fetch` 读取根页面。内容里的 `<database url="..." data-source-url="collection://...">名称</database>`
   给出每个数据库的 URL 和 data source ID，`<page url="...">名称</page>` 给出分类页面。
4. 核对 5 个数据库（Sources、Wiki Index、Agent Tasks、Wiki Changelog、Conflicts）和 3 个分类页面
   （concepts/、techniques/、tools/）都在。缺了哪个就停下，告诉用户缺什么，建议运行 `/wiki-admin:init-wiki` 选择覆盖重建。

根页面标题被改动后会找不到。遇到这种情况，提示用户把标题改回上面的值。
