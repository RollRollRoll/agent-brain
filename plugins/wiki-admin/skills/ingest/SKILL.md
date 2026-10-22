---
name: ingest
description: 把 Sources 中待处理的原始材料提炼成 Wiki 页面，用户确认后再写入 Notion。用户要求入库材料时使用。
---

# ingest

把 Sources 里状态为「待处理」的材料提炼成 Wiki 页面（即 Wiki Index 条目，ADR 0007）。
**用户确认之前不修改 Notion。** 本版不检测冲突（见 #5），已有页面一律不改。

各工具的参数格式以工具自身的描述为准。写数据库条目前，先用 `notion-fetch` 读取目标 data source，
按返回的字段名和 SQLite 定义填属性。

## 前置条件

`notion-*` 工具不可用时，停下来告诉用户：运行
`claude mcp add --transport http --scope user notion https://mcp.notion.com/mcp`，再用 `/mcp` 登录；
工具仍不出现就重启会话。

## 步骤

1. **定位 Wiki**：按 [定位 Wiki](../../references/locate-wiki.md) 找到根页面，取出 Sources、Wiki Index、
   Wiki Changelog 的 data source ID。

2. **找待处理材料**：用 `notion-query-data-sources` 查询 Sources，筛选「状态」= 待处理。
   没有结果时告诉用户「没有待处理的材料」，结束，不做任何修改。

3. **读取内容**：对每条材料用 `notion-fetch` 读取页面正文（文章正文、视频文字稿、图片描述）。
   正文为空但有「链接」时，用 WebFetch 读取链接内容。两者都没有可用内容时跳过这条，在汇报中说明原因。

4. **提炼知识点**：每个知识点准备：
   - 标题：简短的名词短语
   - 分类：concepts（概念、原理）、techniques（方法、流程）、tools（软件、框架、库）之一
   - 领域标签：沿用材料的领域标签，必要时补充
   - 简短摘要：一两句话
   - 正文：要点、原理或步骤、出处。techniques 要写清步骤、所需工具和前置条件，`/sync-skills` 会读取它们

5. **查重**：查询 Wiki Index，找标题相同或明显是同一主题的已有页面。
   - 已有页面：不修改，在建议里标为「已有页面，未修改」，并列为相关页面
   - 已有页面的「来源材料」已包含这条材料：说明之前写入过，跳过这个知识点

6. **展示建议并等待确认**：按材料分组列出拟新建的页面（标题、分类、领域标签、摘要），以及涉及但不修改的已有页面。
   问用户：「是否按以上建议写入？」用户可以删减或修改条目。
   **只有用户明确回答「是 / 确认 / 继续」后才写入。** 用户拒绝时结束，不做任何修改。

7. **写入**：逐条材料处理：
   1. 用 `notion-create-pages` 在 Wiki Index 中新建页面（parent 用 Wiki Index 的 data source ID），
      属性填标题、分类、领域标签、简短摘要，「来源材料」填这条材料的页面 URL。
   2. 正文末尾加「相关页面」一节，用 `<mention-page url="...">标题</mention-page>` 提及相关页面。
      同一批新建的页面互相提及时，先把页面都建好，再用 `notion-update-page` 追加这一节。
   3. 在 Wiki Changelog 中为每个新页面建一条记录：变更摘要「新建：<标题>」、Wiki 页面、来源材料、
      变更类型「新建」、详情（一句话说明提炼自哪条材料）。
   4. 这条材料的页面和 Changelog 都写完后，用 `notion-update-page` 把它在 Sources 中的「状态」改为「已入库」。

8. **核对**：用 `notion-fetch` 回读新建的页面，确认属性和来源材料关联正确。

## 失败处理

- 工具返回 `rate_limited`：按 `retry_after_seconds` 等待后重试一次；再次失败就停下并汇报。
- 写到一半失败：停止，列出已写入的页面和 Changelog，以及失败原因。这条材料的状态保持「待处理」；
  重新运行时，第 5 步会跳过已经写入的知识点。
- 不删除已写入的内容来"回滚"。

## 汇报

结束时列出：

- 处理了哪些材料，跳过了哪些（附原因）
- 新建的 Wiki 页面链接（按分类分组）
- 涉及但未修改的已有页面
- 写入的 Changelog 条数
- 状态改为「已入库」的材料
