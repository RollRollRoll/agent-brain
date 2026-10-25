---
name: generate-wiki-index
description: 读取本地 Markdown Wiki 中全部页面 frontmatter 的 title 和 summary，按标题排序重新生成 `index.md`。用户要刷新或重建 Wiki 索引文件时使用。
---

# 生成 Wiki 索引文件

<!-- 由 /wiki-admin:sync-skills 从 Notion 页面生成：https://app.notion.com/p/4047d7a648e48175b38ce8d17b026898，同步时间 2026-10-25T01:00:11Z。
     要改内容请改 Notion 页面再同步；直接改本文件不会回写 Notion，Notion 页面再被修改时同步会提示人工合并。 -->

读取全部页面的标题和摘要，重新生成 `index.md`。

## 前置条件

- Wiki 是本地 Markdown 目录，每个页面一个 `.md` 文件
- 每个页面的 frontmatter 有 `title` 和 `summary` 字段

## 所需工具

- 能读写文件的 agent（如 Claude Code）

## 步骤

1. 列出 Wiki 目录下除 `index.md`、`log.md` 之外的全部 `.md` 文件。
2. 读取每个文件 frontmatter 里的 `title` 和 `summary`。
3. 按 `title` 排序，每个页面写一行 `- [title](文件名) — summary`，覆盖写入 `index.md`。
4. 统计写入的页面数，告诉用户索引里有几个页面。

## 失败处理

- 某一步失败时停下，告诉用户是哪一步、失败原因，不要跳过这一步继续

## 出处

- Wiki 页面：生成 Wiki 索引文件（https://app.notion.com/p/4047d7a648e48175b38ce8d17b026898）
