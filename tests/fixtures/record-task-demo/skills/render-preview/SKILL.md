---
name: render-preview
description: 用 wikirender 把 Markdown 文件渲染成 HTML 预览。用户要求渲染 Markdown 预览时使用。
---

# 渲染 Markdown 预览

<!-- #11 验证用的测试 skill，必然失败：wikirender 是一个不存在的命令（模拟工具路径错误）。 -->

把 Markdown 文件渲染成同名的 HTML 预览文件。

## 前置条件

- 已安装 `wikirender` 命令
- 用户给出的 Markdown 文件存在

## 所需工具

- `wikirender`

## 步骤

1. 运行 `wikirender --version`，确认命令可用
2. 运行 `wikirender <文件路径> -o <同名 .html 路径>`
3. 告诉用户生成的 HTML 文件路径

## 失败处理

- 第 1 步报 `command not found`：说明没有安装 `wikirender`，停下，不要换别的工具代替
- 某一步失败时停下，告诉用户是哪一步、失败原因，不要跳过这一步继续

## 记录结果

开始第 1 步前记下开始时间。任务结束后，不论成功还是失败，先把结果告诉用户，再调用 skill
`wiki-admin:record-task`（Claude Code 用 Skill 工具；Codex 读取它的 SKILL.md 照做），参数写明：任务名、使用的 Skill（`record-task-demo:render-preview`）、开始和结束时间、
状态（成功 / 失败）、成功时的结果摘要，或失败时的失败步骤、错误信息原文和你对原因的分析。

- `wiki-admin:record-task` 不可用（没有安装 wiki-admin）或记录失败时，不影响任务结果，
  告诉用户「没能记录到 Agent Tasks」和原因即可，不要为了记录重新执行任务

## 出处

- 没有对应的 Wiki 页面：#11 验证用的测试 skill
