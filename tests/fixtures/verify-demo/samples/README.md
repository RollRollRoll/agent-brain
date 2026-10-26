# verify-system 样本

`/verify-system`（`.claude/skills/verify-system/SKILL.md`）用这些文件在测试 Wiki 里建材料和页面。
每个文件第一行是标题（去掉 `# `），其余是正文。

| 文件 | 用在 | 设计 |
|---|---|---|
| `a-python312.md` | VAL-002、VAL-016 | 约 3000 字的文章。**故意写错一处**：把 3.12 的发布时间写成「2023 年 9 月」（正式版是 2023-10-02），给 B 制造事实性冲突；并写了「f-string 是最易读的格式化方式」，给 C 制造观点性冲突 |
| `b-release-date.md` | VAL-003、VAL-010 | 说 3.12.0 正式版在 2023 年 10 月 2 日发布，可以用 python.org 的发布页查证，证据支持 B |
| `c-fstring-opinion.md` | VAL-004、VAL-012 | 认为 `str.format` 比 f-string 更易读，纯主观评价，没有客观标准 |
| `d-sqlite-a.md`、`d-sqlite-b.md` | VAL-005 | 两个 concepts 页面，对 SQLite 能否多个连接同时写入说法相反 |

不要把「哪里写错了」写进样本正文：ingest 会读到它。
