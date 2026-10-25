---
name: check-markdown-broken-links
description: 在本地 Markdown 目录中找出指向不存在 `.md` 文件的相对链接，列出所在文件、行号和链接目标。用户要检查文档或 Wiki 里的失效链接时使用。
---

# 检查 Markdown 失效链接

<!-- 由 /wiki-admin:sync-skills 从 Notion 页面生成：https://app.notion.com/p/4047d7a648e4810190afee993061bf45，同步时间 2026-10-25T00:50:10Z。
     要改内容请改 Notion 页面再同步；直接改本文件不会回写 Notion，Notion 页面再被修改时同步会提示人工合并。 -->

找出指向不存在文件的相对链接。

## 前置条件

- 要检查的是本地 Markdown 文件目录
- 链接用相对路径写，例如 `[标题](other.md)`

## 所需工具

- `grep`
- 能读写文件的 agent

## 步骤

1. 用 `grep -rnoE '\]\([^)]+\.md\)' <目录>` 找出全部指向 `.md` 的链接。
2. 对每个链接，按链接所在文件的目录拼出目标路径，检查文件是否存在。
3. 列出目标不存在的链接：所在文件、行号、链接目标。

## 失败处理

- 某一步失败时停下，告诉用户是哪一步、失败原因，不要跳过这一步继续

## 出处

- Wiki 页面：检查 Markdown 失效链接（https://app.notion.com/p/4047d7a648e4810190afee993061bf45）
