---
name: export-recent-wiki-log
description: 用 grep 和 tail 从本地 Wiki 的 `log.md` 取出最近 n 条记录的标题行（默认 10 条），按时间倒序输出。用户想看 Wiki 最近做过哪些操作时使用。
---

# 导出最近的 Wiki 日志

<!-- 由 /wiki-admin:sync-skills 从 Notion 页面生成：https://app.notion.com/p/4047d7a648e481998c14d3d39a774076，同步时间 2026-10-25T00:50:10Z。
     要改内容请改 Notion 页面再同步；直接改本文件不会回写 Notion，Notion 页面再被修改时同步会提示人工合并。 -->

用 grep 取 `log.md` 里最近几条记录。

## 前置条件

- Wiki 目录里有 `log.md`，每条记录以 `## [日期]` 开头

## 所需工具

- `grep`
- `tail`

## 步骤

1. 运行 `grep "^## \[" log.md | tail -<n>` 取最近 n 条记录的标题行，n 默认 10。
2. 把结果按时间倒序输出给用户。

## 失败处理

- 某一步失败时停下，告诉用户是哪一步、失败原因，不要跳过这一步继续

## 出处

- Wiki 页面：导出最近的 Wiki 日志（https://app.notion.com/p/4047d7a648e481998c14d3d39a774076）
