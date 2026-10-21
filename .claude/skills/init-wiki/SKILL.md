---
name: init-wiki
description: 在 Notion 中初始化 LLM Wiki 结构（根页面、5 个数据库、3 个分类页面）。用户要求初始化或重建 Wiki 时使用。
---

# init-wiki

在已授权给 Integration 的父页面下创建：

- 根页面「LLM Wiki 系统」
- 5 个数据库：Sources、Wiki Index、Agent Tasks、Wiki Changelog、Conflicts（relation 字段自动关联）
- 3 个分类页面：concepts/、techniques/、tools/

## 前置条件

- `.env` 中有 `NOTION_TOKEN`
- `.env` 中有 `NOTION_PARENT_PAGE_ID`，且该页面已在 Notion 里连接到 Integration
  （internal integration 不能在 workspace 顶层建页面）

## 执行步骤

1. 在项目根目录运行：

   ```bash
   python3 .claude/skills/init-wiki/init-wiki
   ```

2. 按退出码处理：
   - `0`：成功。把输出的页面和数据库链接转给用户。
   - `1`：失败。把错误信息和输出里的修复提示转给用户。
   - `2`：结构已存在。**先问用户是否覆盖**，说明覆盖会把旧结构移入 Notion 回收站。
     只有用户明确回答「是 / 确认 / 继续」后，才运行：

     ```bash
     python3 .claude/skills/init-wiki/init-wiki --overwrite
     ```

     用户没有明确同意时，不要加 `--overwrite`。

3. 视图：脚本会给 Sources 建「按状态」Board 视图，给 Wiki Index 建「知识卡片」Gallery 视图；
   每个数据库另有 Notion 自动创建的默认 Table 视图。输出里如果有视图创建失败，
   告诉用户数据库本身可用，失败的视图可以在 Notion 中手动添加。
