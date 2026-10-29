# 领域文档

说明这套 skill 在探索代码库时如何读取和使用领域文档。

## 探索之前先读这些

- 仓库根的 **`GLOSSARY.md`**
- **`docs/adr/`**：读那些涉及你即将动手的区域的 ADR

这些文件不存在时直接继续，不提示缺失，也不主动建议创建。
`domain-modeling` skill 会在术语或决定确认后按需创建它们。

## 文件结构

单上下文仓库：

```text
/
├── GLOSSARY.md
├── docs/adr/
│   ├── 0001-notion-over-obsidian.md
│   ├── 0002-skills-in-git-not-notion.md
│   ├── 0003-agent-failure-feedback.md
│   ├── 0004-conflict-resolution-mechanism.md
│   ├── 0005-notion-api-2026-03-11.md（已被 0006 取代）
│   ├── 0006-hosted-notion-mcp.md
│   ├── 0007-wiki-pages-in-wiki-index.md
│   ├── 0008-locate-wiki-by-notion.md（已被 0011 取代）
│   ├── 0009-repo-as-plugin-marketplace.md
│   ├── 0010-codex-plugin-support.md
│   └── 0011-register-wiki-root-in-project.md
├── .claude-plugin/marketplace.json
└── plugins/
    ├── wiki-admin/          # 系统命令
    └── <领域>/              # /sync-skills 生成的专业 skill
```

## 使用术语表里的词汇

**当你的产出点到一个领域概念时**（issue 标题、重构提案、假设、测试名），
**用 `GLOSSARY.md` 里定义的那个词**。不要滑向术语表明确要避免的同义词。

## 标出与 ADR 的冲突

**如果你的产出与某条现有 ADR 相抵触，就把它明确摆出来**，而不是悄悄覆盖掉：

> *与 ADR-0007（event-sourced orders）相抵触，但值得重开，因为……*
