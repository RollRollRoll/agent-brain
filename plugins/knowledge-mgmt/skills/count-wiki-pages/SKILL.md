---
name: count-wiki-pages
description: 用 find 和 wc 统计本地 Markdown Wiki 的页面数（不含 `index.md`、`log.md`）。用户想知道 Wiki 有多少页面时使用。
---

# 统计 Wiki 页面数

<!-- 由 /wiki-admin:sync-skills 从 Notion 页面生成：https://app.notion.com/p/4047d7a648e48102a4c5ceead11a1f8d，同步时间 2026-10-25T01:00:11Z。
     要改内容请改 Notion 页面再同步；直接改本文件不会回写 Notion，Notion 页面再被修改时同步会提示人工合并。 -->

用 find 和 wc 统计本地 Wiki 的页面数。

## 前置条件

- Wiki 是本地 Markdown 目录

## 所需工具

- `find`
- `wc`

## 步骤

1. 运行 `find <目录> -name '*.md' ! -name index.md ! -name log.md | wc -l` 统计页面数。
2. 把结果告诉用户。

## 失败处理

- 某一步失败时停下，告诉用户是哪一步、失败原因，不要跳过这一步继续

## 出处

- Wiki 页面：统计 Wiki 页面数（https://app.notion.com/p/4047d7a648e48102a4c5ceead11a1f8d）
