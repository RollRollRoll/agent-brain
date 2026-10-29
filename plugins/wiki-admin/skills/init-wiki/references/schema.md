# LLM Wiki 结构定义

`/init-wiki` 按本文创建结构。字段的业务含义见 spec §3.4，这里给出建库所需的完整取值。

## 根页面与分类页面

- 根页面：用户已有的页面，或新建页面（默认标题 `LLM Wiki 系统`，测试 Wiki 为 `LLM Wiki 系统（测试）`），
  登记在当前项目的 `.agent-brain/wiki.json`（见 [定位 Wiki](../../../references/locate-wiki.md)）
- 分类页面（建在根页面下）：`concepts/`、`techniques/`、`tools/`
- Wiki 页面本身就是 Wiki Index 的条目（ADR 0007）。分类页面不存放内容，
  只放一个 Wiki Index 的 Gallery 视图，按「分类」筛选出对应条目

## 数据库

按下表顺序创建。后面的库会关联前面的库，关联时用被关联库的 data source ID（`collection://...`）。
每个库恰好一个 title 字段。

### 1. Sources

| 字段 | 类型 | 取值 |
|---|---|---|
| 标题 | title | |
| 类型 | select | 文章、视频、图片、项目 |
| 链接 | url | |
| 状态 | select | 待处理、处理中、已入库、已归档 |
| 领域标签 | multi_select | 无预设选项 |
| 添加时间 | created_time | |

### 2. Wiki Index

| 字段 | 类型 | 取值 |
|---|---|---|
| 标题 | title | |
| 分类 | select | concepts、techniques、tools |
| 领域标签 | multi_select | 无预设选项 |
| 简短摘要 | rich_text | |
| 最后更新时间 | last_edited_time | |
| 来源材料 | relation（单向） | → Sources |

### 3. Agent Tasks

| 字段 | 类型 | 取值 |
|---|---|---|
| 任务名 | title | |
| 使用的 Skill | rich_text | |
| 执行时间 | date | |
| 状态 | select | 成功、失败 |
| 结果摘要 | rich_text | |
| 失败原因 | rich_text | |
| 反馈/问题 | rich_text | |

### 4. Wiki Changelog

| 字段 | 类型 | 取值 |
|---|---|---|
| 变更摘要 | title | |
| Wiki 页面 | relation（单向） | → Wiki Index |
| 变更时间 | created_time | |
| 来源材料 | relation（单向） | → Sources |
| 变更类型 | select | 新建、更新、冲突解决 |
| 详情 | rich_text | |

### 5. Conflicts

| 字段 | 类型 | 取值 |
|---|---|---|
| 冲突摘要 | title | |
| Wiki 页面 | relation（单向） | → Wiki Index |
| 冲突类型 | select | 事实性、观点性、时效性、场景性、深度性、无法判断、高频失败 |
| 新材料 | relation（单向） | → Sources |
| 原有内容摘要 | rich_text | |
| 新内容摘要 | rich_text | |
| 证据链接 | url | |
| 证据强度评分 | number | |
| 状态 | select | 待审核、待人工审核、已解决 |
| 解决方案 | rich_text | |

「高频失败」不是知识冲突，是 `/wiki-admin:analyze-failures` 建的高频失败告警（SCN-006-C）：
同一 skill 24 小时内失败 3 次以上时记一条，只填冲突摘要、冲突类型、状态。

## 视图

每个库建好后 Notion 会自动带一个默认 Table 视图。另外补建：

| 数据库 | 视图名 | 类型 | 配置 |
|---|---|---|---|
| Sources | 按状态 | board | 按「状态」分组 |
| Wiki Index | 知识卡片 | gallery | 卡片显示「分类」「领域标签」「简短摘要」 |

分类页面里的视图（Wiki Index 的 linked view，不显示数据源标题）：

| 分类页面 | 视图名 | 类型 | 配置 |
|---|---|---|---|
| concepts/ | concepts | gallery | 筛选「分类」= concepts；卡片显示「领域标签」「简短摘要」 |
| techniques/ | techniques | gallery | 筛选「分类」= techniques；卡片显示「领域标签」「简短摘要」 |
| tools/ | tools | gallery | 筛选「分类」= tools；卡片显示「领域标签」「简短摘要」 |
