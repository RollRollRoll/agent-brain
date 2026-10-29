# ADR 0007: Wiki 页面即 Wiki Index 条目

**状态**：已接受  
**日期**：2026-10-22  
**决策者**：用户

## 背景

spec 同时写了 Wiki Index 数据库（每个 Wiki 页面一条索引）和 concepts、techniques、tools 层级页面
（每个页面包含 Markdown 内容和双向链接），没有说清知识内容到底存在哪里。#4 入库要往里写，必须先定下来。

## 决策

- 每个 Wiki 页面就是 Wiki Index 中的一条记录：正文是条目页面的内容，分类、领域标签、简短摘要、来源材料是条目属性。
- concepts、techniques、tools 三个分类页面不存放内容，只放一个 Wiki Index 的 Gallery 视图，按「分类」筛选。
- 页面之间用 Notion 页面提及链接；被提及的页面由 Notion 自动显示反向链接。

## 候选方案

- **A. 只存在 Wiki Index（采纳）**
- **B. 层级页面存正文，Wiki Index 存索引**：每个知识点存两份，入库、修改、冲突解决时都要同步两处。
- **C. 只用层级页面**：没有属性可筛选，用户要的 Gallery 知识卡片和按领域、时间筛选都做不了。

## 理由

- 每个知识点只存一份，不存在两处不一致的问题。
- Gallery 卡片、按分类筛选、`/lint-wiki` 扫描、`/sync-skills` 读取 techniques，都直接查同一个 data source。

## 后果

- 分类是属性，不是页面层级：改分类只改属性。Notion 侧边栏里看不到按分类的树形结构，要从分类页面里的视图浏览。
- 后续工单（#8 lint、#9 sync）都从 Wiki Index 读取页面，按「分类」筛选。

## 相关决策

- ADR 0001：使用 Notion 作为 Wiki 存储
- ADR 0004：知识冲突处理机制
