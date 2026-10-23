---
name: llm-wiki-ingest
description: 把一份新材料合并进本地 Markdown 文件形式的 LLM Wiki：读材料、和用户确认重点、写摘要页、更新 `index.md`、修订相关页面、追加 `log.md`。用户要把资料入库到 Obsidian 或 Markdown Wiki 时使用；Notion Wiki 用 /wiki-admin:ingest。
---

# LLM Wiki 入库

<!-- 由 /wiki-admin:sync-skills 从 Notion 页面生成：https://app.notion.com/p/4017d7a648e4819a9f05d338a35a6122，同步时间 2026-10-23T07:23:21Z。
     要改内容请改 Notion 页面再同步；直接改本文件，下次同步时会提示冲突。 -->

把一份新材料合并进 Wiki：读材料、讨论要点、写摘要页、更新索引、修订相关页面、追加日志；一次只处理一份。

## 前置条件

- 材料已放进原始材料目录（只读）
- 有 schema 文件说明页面约定

## 所需工具

- 能读写文件的 LLM agent（如 Claude Code）
- 可选：Obsidian，实时查看改动

## 步骤

1. 读取新材料。
2. 和用户讨论主要收获，确认重点。
3. 为这份材料写一个摘要页。
4. 更新索引（`index.md`），加入新页面。
5. 修订受影响的实体页和概念页，标出与已有说法冲突的地方。
6. 在日志（`log.md`）追加一条入库记录。

## 注意

- 一份材料通常会动到 10 到 15 个页面。
- 一次只入库一份、全程参与，能把握重点；也可以批量入库，减少人的参与。

## 出处

- Wiki 页面：LLM Wiki 入库（https://app.notion.com/p/4017d7a648e4819a9f05d338a35a6122）
- [Karpathy: LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
