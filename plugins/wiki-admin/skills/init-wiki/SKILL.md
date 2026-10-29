---
name: init-wiki
description: 在 Notion 中初始化 LLM Wiki 结构（根页面、5 个数据库、视图、3 个分类页面），根页面可以用已有页面或新建，并登记到用户目录或当前项目的 .agent-brain/wiki.json；也可建测试 Wiki。用户要求初始化、重建 Wiki 或登记已有 Wiki 时使用。
---

# init-wiki

通过 Notion MCP（`notion-*` 工具）创建 [references/schema.md](references/schema.md) 定义的结构。

各工具的参数格式以工具自身的描述为准；视图配置语法读 MCP 资源 `notion://docs/view-dsl-spec`。
不要凭记忆拼参数。

## 前置条件

见 [Notion 工具使用约定](../../references/notion-tools.md) 的「前置条件」。

## 步骤

1. **确认连接**：调用 `notion-get-self`，记下 workspace 名称和用户名。

2. **确定是哪个 Wiki**：用户说要建测试 Wiki 时是测试 Wiki，否则是正式 Wiki。
   读 [定位 Wiki](../../references/locate-wiki.md) 中的两个登记文件：项目登记文件 `.agent-brain/wiki.json`
   和用户登记文件 `~/.agent-brain/wiki.json`。

3. **检查是否已登记**：按定位 Wiki 的顺序找这个 Wiki 的记录（先项目、后用户）。找到时 `notion-fetch` 记录里的根页面。
   - 根页面打不开或在回收站里：告诉用户这条记录已失效（附登记文件路径），按没有记录继续，第 6 步写新记录时替换它。
   - 根页面还在：**停下来问用户**：「当前项目已经能找到<正式 / 测试> Wiki（附链接，登记在<文件路径>）。要怎么做？
     1. 覆盖重建这个 Wiki
     2. 保留它，另选根页面登记一个新的 Wiki（旧 Wiki 在 Notion 里不动）
     3. 取消」
   - 选 1：说明覆盖会移走什么：`root_page_created` 为 `true` 时把整个根页面移入回收站；为 `false` 时根页面是用户原有的页面，
     只把它下面和 Wiki 结构同名的数据库和分类页面（有几个移几个）移入回收站，页面本身和其他内容保留。
     回收站里的内容可以在 Notion 里恢复，但 MCP 目前不能恢复顶层页面。
     用户明确回答「是 / 确认 / 继续」后，才用 `notion-delete-pages` 移走上面说的内容，`user_confirmed` 设为 `true`。
     第 6 步写回同一个登记文件，不再问登记位置
   - 选 2：继续往下，不移走任何东西
   - 选 3，或者用户没有明确选择时：结束，不做任何修改。

4. **选根页面和登记位置**：用户在请求里已经说了的，照用户说的做；没说的**一次问完**：
   「1. Wiki 根页面用哪个？
      - 用已有页面：给出页面链接，Wiki 结构建在它下面，页面标题和原有内容不变
      - 新建页面：可以给父页面链接（不给就建成你的私有页面）和标题（默认 `<默认标题>`）
   2. 登记到哪里？
      - 用户目录 `~/.agent-brain/wiki.json`：所有项目都用这个 Wiki，除非项目自己另外登记了（推荐）
      - 只登记当前项目 `<项目根目录>/.agent-brain/wiki.json`：只有这个项目用它，优先于用户目录的登记」

   默认标题：正式 Wiki 是 `LLM Wiki 系统`，测试 Wiki 是 `LLM Wiki 系统（测试）`。
   第 3 步选了覆盖时，登记位置不用问，用原来的登记文件。

5. **准备根页面**：
   - **用已有页面**：`notion-fetch` 用户给的链接。不是页面（例如是数据库）、打不开或在回收站里时，告诉用户原因，
     请用户换一个。这个页面已登记为另一个 Wiki（正式 / 测试）的根页面时，停下告诉用户，不要两个 Wiki 共用一个根页面。
     再看页面内容里有没有和 Wiki 结构同名的 `<database>`（Sources、Wiki Index、Agent Tasks、Wiki Changelog、Conflicts）
     和 `<page>`（concepts/、techniques/、tools/）：
     - 8 个都有：这是一个已建好的 Wiki。问用户：「这个页面下已经有 Wiki 结构，是直接登记到本地（不改 Notion），
       还是覆盖重建？」选登记：做第 6 步，然后跳到第 10 步核对，再汇报。选覆盖：按第 3 步的确认方式，
       只把这 8 个移入回收站，继续往下
     - 只有一部分：列出已有的几个，问是否把它们移入回收站后重建；用户不同意就结束，不做任何修改
     - 都没有：继续往下

     不要改这个页面的标题和原有内容。
   - **新建页面**：用 `notion-create-pages` 创建根页面，标题用用户给的或默认标题，
     内容写一句「Agent Brain 知识库根页面，由 /init-wiki 创建。」用户给了父页面时建在它下面；没给时不传 parent，建成私有页面。

6. **登记到本地**：按定位 Wiki 的格式，把这个 Wiki 的记录写进第 4 步定下的登记文件：`root_page_url` 填根页面 URL，
   `root_page_title` 填它的标题，`root_page_created` 新建页面填 `true`、用已有页面填 `false`，
   `registered_at` 填当前时间。文件或 `.agent-brain/` 目录不存在就创建；文件里另一个 Wiki 的记录原样保留，
   另一个登记文件不动。
   这一步在建数据库之前做：后面失败时，重新运行能在第 3 步认出这个 Wiki 并覆盖。
   登记到用户目录时，如果当前项目的登记文件里也有这个 Wiki 的记录，提醒用户：当前项目仍然会用项目里登记的那个。

7. **建数据库**：在根页面下用 `notion-create-database`，按 schema.md 的顺序逐个创建。
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

8. **建视图**：按 schema.md 的视图表，用 `notion-create-view` 补建视图，`database_id` 和 `data_source_id` 都要传。
   `configure` 用视图 DSL：
   - Board：`GROUP BY "状态" SHOW EMPTY`。select 属性不要加 `BY OPTION` / `BY GROUP`，那两个只用于 status 属性。
   - Gallery：`SHOW "分类", "领域标签", "简短摘要"`（Notion 会自动把标题加进卡片）。

   单个视图失败时记下错误，继续往下，不回滚已建好的结构。

9. **建分类页面**：在根页面下用 `notion-create-pages` 一次创建 `concepts/`、`techniques/`、`tools/`。
   然后按 schema.md 的分类页面视图表，在每个分类页面里用 `notion-create-view` 建 Wiki Index 的 Gallery 视图：
   传 `parent_page_id`（分类页面）和 Wiki Index 的 `data_source_id`，不传 `database_id`；
   `show_data_source_title` 设为 `false`；`configure` 例如 `FILTER "分类" = "concepts"; SHOW "领域标签", "简短摘要"`。

10. **核对**：用 `notion-fetch` 读一遍每个数据库，确认字段名、类型、select 选项、relation 目标都和 schema.md 一致。
    发现不一致就用 `notion-update-data-source` 修正。注意：更新 select 选项时必须列出全部选项，漏掉的选项会被删除。

## 失败处理

- 工具报错（`rate_limited` 等）按 [Notion 工具使用约定](../../references/notion-tools.md) 处理。
- 根页面准备好、登记之后，数据库建到一半失败：停止，列出已创建内容的链接和失败原因。不要自动清理；
  告诉用户修复后可以重新运行，到第 3 步时选择覆盖即可。
- 登记文件写不进去（例如目录没有写权限）：停止，不要接着建数据库。告诉用户原因；根页面是新建的就附上链接，
  用户解决后重新运行，在第 4 步选「用已有页面」并给这个链接即可。
- 视图失败：结构其余部分照常完成，在汇报中说明哪个视图没建成，用户可以在 Notion 中手动添加。

## 汇报

结束时给用户列出：

- 根页面链接，以及是新建的还是用的已有页面
- 登记文件的路径；登记到用户目录、但当前项目另有登记时，说明当前项目仍用项目里的那条
- 5 个数据库的链接
- 已建成的视图（以及失败的视图和原因）
- 3 个分类页面的链接
- 如果覆盖过旧结构，移入回收站的内容的链接
