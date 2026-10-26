---
name: verify-system
description: 端到端验证 LLM Wiki 系统：在测试 Wiki 里依次运行 wiki-admin 的各个命令，逐项核对 spec §4.3 的 VAL-001 ~ VAL-018，输出验证报告（VAL-019），结束后经用户同意清理测试数据。用户要求验证整个系统、跑端到端测试时使用。
---

# verify-system

在「LLM Wiki 系统（测试）」里真实运行 wiki-admin 的命令，用 `notion-fetch` 回读结果，按 spec §4.3 逐项判定。
本 skill 是 agent-brain 仓库的项目级 skill，只在这个仓库里用，不发布到 marketplace。

**只用测试 Wiki，不碰正式 Wiki「LLM Wiki 系统」。** 验证用的同步写到临时克隆里，不写当前仓库，不推送。
**删除任何东西（旧测试 Wiki、测试数据、临时克隆）都要用户本人同意，不代答。**

调用 `notion-*` 工具的前置条件、写入格式和报错处理见 [Notion 工具使用约定](../../../plugins/wiki-admin/references/notion-tools.md)。
辅助脚本 [`scripts/verify_tools.py`](scripts/verify_tools.py) 只用 Python 标准库，需要 `python3`（3.7 以上）和 `git`。

## 怎么运行被验证的命令

按仓库里的 `plugins/wiki-admin/skills/<命令>/SKILL.md` 一步步执行，不用已安装的 plugin 缓存：验证的是当前仓库的版本。
SKILL.md 里的相对链接按它自己所在的目录解析。每个命令都按「测试 Wiki」运行（定位 Wiki 时用测试根页面标题）。

## 确认怎么回答

各命令运行中会问「是否写入 / 是否修改」。第 2 步把全部写入列给用户，**用户同意一次后**，按下表代答，
每次代答在会话里写一行「代答：<问题> → <回答>（剧本）」。表里没有的问题停下来问用户。

| 命令 | 问题 | 代答 |
|---|---|---|
| init-wiki | 第二次运行的「是否覆盖？」 | 否 |
| ingest | 「是否按以上建议写入？」、新增 multi_select 选项 | 是 |
| lint-wiki | 「是否自动修复以上缺失链接？」 | 否（VAL-005 只看报告） |
| sync-skills | 「是否按以上清单新增和更新 skill？」 | 是 |
| sync-skills | 冲突 | 保留本地 |
| sync-skills | 待删除 | 保留 |
| sync-skills / analyze-failures | 「是否推送到 GitHub？」 | 否 |
| resolve-conflict | 事实性冲突选哪种处理 | 采纳新内容，「是否按此修改？」答是 |
| resolve-conflict | 观点性冲突选哪种处理 | 两者都保留，「是否按此修改？」答否 |
| record-task | 回读发现写错，是否修正 | 否 |
| analyze-failures | 「是否按此修改？」 | 否（VAL-011 只看分类和建议） |

**不代答的**：移入回收站、删除目录、覆盖旧测试 Wiki。这些每次都问用户本人，用户明确回答「是 / 确认 / 继续」才执行。

## 结果文件

在系统临时目录建 `results.json`（不放进仓库），每判定一项追加一条：

```json
{"results": [
  {"id": "VAL-001", "status": "pass", "evidence": "5 个数据库字段与 schema.md 一致；第二次运行提示覆盖且根页面编辑时间未变"},
  {"id": "VAL-016", "status": "pass", "evidence": "入库 3012 字文章", "seconds": 24}
]}
```

- `status`：`pass`、`fail`、`skip`（没运行，`evidence` 写原因，例如「依赖的 VAL-006 失败」）
- `evidence`：判定依据，写回读到的具体值（字段名、记录链接、文件路径、哈希），不要只写「正常」
- 性能项（VAL-016 ~ VAL-018）填 `seconds`，`status` 随便填：`report` 按 spec 门槛重新判定

## 步骤

每一步结束时在会话里写一行进度，例如「VAL-001 通过（3/16 步）」。某一项失败不中止：记为 fail，继续后面的项；
后面的项依赖它而做不了时记为 skip，`evidence` 写依赖哪一项。

1. **准备**：
   - 调用 `notion-get-self` 确认连接，记下 workspace 和用户名
   - 在仓库根目录运行 `python3 .claude/skills/verify-system/scripts/verify_tools.py static --repo .`，
     把输出的 VAL-014、VAL-015 两条原样追加进 `results.json`
   - **记下正式 Wiki 的状态**，第 15 步核对验证期间没被改过。按 [定位 Wiki](../../../plugins/wiki-admin/references/locate-wiki.md)
     第 1–3 步找正式 Wiki「LLM Wiki 系统」；不存在时跳过，在报告里写「没有正式 Wiki」。存在时记下：
     - 根页面的 `page_last_edited_at`
     - Wiki Index：rows 模式按「最后更新时间」降序取 1 条，记下它的最后更新时间（页面被改过会变）
     - Sources、Agent Tasks、Wiki Changelog、Conflicts：每个库一条 SQL
       `SELECT count(*) AS n, max(createdTime) AS latest FROM "<data source URL>"`（一条只查一个库），记下条数和最新创建时间（新增记录会变）

     这 4 个库没有「最后编辑时间」字段，已有记录被改不会被发现，所以第 2 步的「每次写入前核对目标」才是主要防线，这里是兜底。
     这一项一共 5 次查询，占 SQL / rows 额度
   - 问用户测试 Wiki 建在哪个页面下。已有「LLM Wiki 系统（测试）」时，建议用它的父页面（`<ancestor-path>` 里的上一级）

2. **列出写入计划并等待确认**：一次列给用户：
   - 重建测试 Wiki：已有的「LLM Wiki 系统（测试）」会在第 3 步由 init-wiki 问是否覆盖（这一问由用户本人回答）
   - 测试 Wiki 的结构改动：Sources、Wiki Index 的「领域标签」新增选项 `软件开发`（第 4 步）
   - 测试 Wiki 里要建或改的：
     - Sources：3 条样本材料 A、B、C，ingest 会把它们的状态改为「已入库」（第 4–6 步）
     - ingest 生成的 Wiki 页面、对应的「新建」Changelog、B 和 C 的 2 条冲突记录（第 5–6 步）
     - resolve-conflict：改 1 个页面中冲突的那段，B 的冲突记录改为「已解决」，1 条「冲突解决」Changelog（第 7 步）
     - 2 个互相矛盾的 concepts 页面（第 8 步）
     - 1 个同步样本页面和 50 个性能样本页面（第 9–10 步）；改同步样本页面的第 2 步（第 11 步）
     - Agent Tasks 2 条记录（第 12 步）；analyze-failures 回写失败记录的「反馈/问题」（第 13 步）
   - 正式 Wiki：只读，第 1 步和第 15 步各查一次状态
   - 系统临时目录：临时克隆（sync-skills 写 skill、`sync-metadata.json` 并提交；第 11 步手动改 1 个 skill 并提交；**不推送**），
     以及 `results.json`
   - 「确认怎么回答」一节的代答表

   问：「是否按以上计划开始验证？」用户明确同意后才继续。之后每次写入前核对目标 data source 属于第 3 步的测试根页面，
   属于别的根页面就停下。

3. **建测试 Wiki（VAL-001）**：
   1. 按 init-wiki 建「LLM Wiki 系统（测试）」，父页面用第 1 步用户给的页面。问是否覆盖旧测试 Wiki 时转给用户本人
   2. 按 init-wiki 第 8 步回读：5 个数据库的字段、类型、select 选项、relation 目标和 schema.md 一致；
      Sources 有「按状态」board 视图、Wiki Index 有「知识卡片」gallery 视图；3 个分类页面在。记下根页面的 `page_last_edited_at`
   3. 再运行一次 init-wiki：应该问「是否覆盖？」，代答否。再读根页面，`page_last_edited_at` 不变
   4. 全部满足为 pass，`evidence` 写每个数据库的字段数、视图名、第二次运行的提示原文和两次编辑时间

4. **准备样本**：样本在 [`tests/fixtures/verify-demo/samples/`](../../../tests/fixtures/verify-demo/samples/)。
   - `notion-fetch` Sources 和 Wiki Index 的 data source，按 Notion 工具使用约定给两库的「领域标签」加上 `软件开发` 选项
     （新建的测试 Wiki 没有任何选项；必须列出全部已有选项）
   - 在 Sources 建样本 A（`a-python312.md`，约 3000 字）：标题取文件第一行，类型「文章」，状态「待处理」，
     领域标签 `软件开发`，正文是文件全文。B、C 留到第 6 步再建：VAL-016 只计一份材料的耗时

5. **入库（VAL-002、VAL-016）**：
   1. 运行 `python3 -c "import time; print(time.time())"` 记下开始时间，按 ingest 运行
   2. ingest 第 6 步展示建议时再记一次时间，两者之差就是 VAL-016 的 `seconds`（QOS-001：到「建议更新 Wiki」为止，
      不含确认之后的写入）。`evidence` 写材料字数和遇到的 `rate_limited` 等待
   3. 代答「是」，写完后回读：Wiki Index 有新页面，正文包含样本 A 的要点（引用一两句）、「来源材料」是样本 A；
      Wiki Changelog 有对应的「新建」记录；样本 A 状态是「已入库」。满足为 VAL-002 pass
   4. 记下样本 A 生成的、讲 Python 3.12 发布时间和 f-string 的页面，以及它们的 `page_last_edited_at`

6. **冲突（VAL-003、VAL-004）**：在 Sources 建样本 B（`b-release-date.md`）和 C（`c-fstring-opinion.md`），字段同上，再运行 ingest，
   代答「是」。回读 Conflicts：
   - VAL-003：B 产生的冲突记录「冲突类型」= 事实性，「证据链接」非空，正文有「证据」一节
   - VAL-004：C 产生的冲突记录「冲突类型」= 观点性，「证据链接」为空，正文的推荐方案是两种观点都保留
   - 两条记录的「状态」都是「待审核」；第 5 步记下的页面 `page_last_edited_at` 没变（VAL-012 的前半，第 7 步一起判定）

7. **解决冲突（VAL-010、VAL-012）**：
   1. 按 resolve-conflict 处理 B 的事实性冲突，代答「采纳新内容」「是」。回读：页面里的发布日期改成了 B 的说法，
      冲突记录「已解决」，Wiki Changelog 有「冲突解决」记录且详情开头有确认时间。满足为 VAL-010 pass。
      然后读 C 的冲突记录关联的 Wiki 页面，记下它此刻的 `page_last_edited_at`：它可能和 B 的冲突是同一个页面，刚被 7.1 改过
   2. 按 resolve-conflict 处理 C 的观点性冲突，代答「两者都保留」，「是否按此修改？」代答「否」。回读：
      页面 `page_last_edited_at` 和 7.1 结束时记下的一致，冲突记录仍是「待审核」。和第 6 步的检查都满足为 VAL-012 pass

8. **整理检查（VAL-005）**：在 Wiki Index 建两个 concepts 页面（领域标签 `软件开发`），内容取 `d-sqlite-a.md`、`d-sqlite-b.md`，
   两页对 SQLite 并发写入的说法互相矛盾。按 lint-wiki 运行，「是否自动修复」代答「否」。
   报告的「矛盾」里有一条同时列出这两个页面并引用双方原话，为 pass

9. **同步（VAL-006）**：
   1. 在系统临时目录 `git clone <当前仓库> <克隆>`（含本地还没推送的提交），再
      `git -C <克隆> remote set-url origin git@github.com:RollRollRoll/agent-brain.git`：origin 指向 agent-brain，
      能通过 sync-skills 第 1 步的检查；推送一律代答「否」，不会推到 GitHub。以下「克隆」都指它
   2. 运行 `verify_tools.py techniques --count 1 --prefix 同步样本`，按输出在 Wiki Index 建 1 个页面：
      属性填标题、分类、领域标签、简短摘要，正文用 `正文`
   3. 在克隆里按 sync-skills 运行（仓库用克隆的路径），清单代答「是」，推送代答「否」
   4. 回读：生成的 SKILL.md frontmatter 有 `name`、`description`，`name` 和目录名一致；克隆里 `claude plugin validate .`
      只有「No version specified」警告；`sync-metadata.json` 有这个页面 ID 的记录，`content_hash` 等于文件的 `git hash-object`。
      满足为 pass，`evidence` 写文件路径和提交哈希

10. **性能同步（VAL-017）**：
    1. 运行 `verify_tools.py techniques --count 50 --prefix 性能样本`，按输出在 Wiki Index 建 50 个页面，
       每次 `notion-create-pages` 建 25 个
    2. 记下开始时间，在克隆里按 sync-skills 运行，代答同上；sync-skills 第 9 步（提交）完成后记下结束时间，差值就是 `seconds`（QOS-002）
    3. 回读：`sync-metadata.json` 新增 50 条记录，每个文件都存在。不满足时 `evidence` 写缺了哪些，耗时照填

11. **同步冲突（VAL-007、VAL-013）**：
    1. 用 `notion-update-page` 的 `update_content` 改第 9 步建的同步样本页面：「步骤」第 2 条末尾加「，结果保留两位小数」
    2. 在克隆里改生成的 SKILL.md：「## 步骤」最后加一步「3. 把结果写进会话」，然后在克隆里提交这次修改
      （sync-skills 要求工作区干净）。记下这个文件的 `git hash-object` 和克隆的 HEAD
    3. 按 sync-skills 运行。清单里应有「skill <名> 在 Notion 和本地都被修改，需要人工合并」，代答「保留本地」
    4. VAL-007：出现了上面的提示，且这个副本的 action 是 `conflict`，为 pass
    5. VAL-013：文件的 `git hash-object` 和 11.2 记下的一致，`git log <11.2 记下的 HEAD>..HEAD -- <文件>` 没有输出，为 pass

12. **记录任务（VAL-008、VAL-009）**：按 `tests/fixtures/record-task-demo/skills/` 的两个 skill 执行，任务结束时
    按它们「记录结果」一节，按 record-task 记到测试 Wiki：
    - `count-lines`：对 `tests/fixtures/verify-demo/samples/a-python312.md` 统计行数，应成功
    - `render-preview`：对同一个文件渲染预览，第 1 步必然失败（`wikirender` 不存在）
    回读 Agent Tasks：成功记录状态=成功、结果摘要非空（VAL-008）；失败记录状态=失败、失败原因有错误原文和分析（VAL-009）。
    两条的任务名、使用的 Skill、执行时间都要对

13. **失败分析（VAL-011）**：按 analyze-failures 传第 12 步失败记录的链接。「是否按此修改？」代答「否」。
    分类为「工具路径/配置错误」，且修复建议包含「检查路径」（spec §4.3 的期望原文），为 pass。`evidence` 引用建议原文。
    这一步会回写这条记录的「反馈/问题」，不改 skill 文件

14. **加载耗时（VAL-018）**：在系统临时目录运行 3 次，每次：

    ```bash
    T0=$(python3 -c "import time; print(time.time())")
    claude -p "/verify-demo:hello" --plugin-dir <仓库>/tests/fixtures/verify-demo \
      --allowedTools "Bash(python3 -c *)" < /dev/null 2>/dev/null
    ```

    输出里 `Hello <时间戳>` 的时间戳减 `T0` 是这次的耗时，取 3 次的中位数作为 `seconds`（QOS-003）。
    `< /dev/null` 不能省：不重定向时 `claude -p` 会先等 3 秒 stdin。`evidence` 写 3 次的耗时，
    并写明「耗时包含启动 Claude Code 进程的时间，比 spec 定义的从调用到开始执行更长；这样测偏严，
    通过时真实加载时间一定也在门槛内」。报告里这一项照抄这句说明

15. **汇总报告（VAL-019）**：
    1. 按第 1 步的方法再查一次正式 Wiki 的状态（根页面编辑时间、Wiki Index 最新更新时间、4 个库的条数和最新创建时间）。
       任何一项和第 1 步记下的不同时，在报告开头写明「正式 Wiki 在验证期间被改过」，列出变化的项和前后的值，
       VAL-019 判为 fail（`report` 之后手动改）
    2. 运行 `python3 .claude/skills/verify-system/scripts/verify_tools.py report --results <results.json>`。
       脚本按 spec 门槛重新判定 VAL-016 ~ VAL-018，没有结果的项记为 fail，再判定 VAL-019
    3. 按脚本输出在会话里列表：每行一个 VAL 项，写编号、对应的需求、通过 / 失败 / 跳过、依据；
       性能项另写实测耗时和门槛。最后一行写 summary 和 VAL-019 的结论

16. **清理**：
    1. 列出要移入回收站的测试页面：测试根页面「LLM Wiki 系统（测试）」（链接；它下面的数据库、样本、生成的页面会一起移走），
       以及要删除的临时克隆和 `results.json` 的路径。说明 Notion 回收站里的页面可以在 Notion 里恢复，
       MCP 目前不能恢复顶层页面；临时克隆删掉后不能恢复，但里面的提交没有推送，不影响 GitHub
    2. 问：「是否移入回收站并删除以上临时文件？」**用户同意后**才用 `notion-delete-pages` 移走测试根页面、删除临时目录；
       可以只同意其中一部分。用户不同意时保留，汇报里列出这些位置，之后可以手动清理

## 失败处理

工具报错（`rate_limited`、`usage_limit_reached` 等）按 [Notion 工具使用约定](../../../plugins/wiki-admin/references/notion-tools.md) 处理。

- 某个被验证的命令中途失败：这一项记为 fail，`evidence` 写失败的步骤和错误原文；依赖它的项记为 skip，继续其余各项
- `usage_limit_reached`：停下，已有的结果照常跑第 15 步出报告，没跑的项记为 skip（「查询额度用完」）。告诉用户额度重置后
  可以从中断的那一步继续：测试 Wiki 和 `results.json` 都还在
- 发现写入目标不在测试根页面下：立即停下，列出已经写入的内容，不清理，等用户处理

## 汇报

- 验证报告（第 15 步的表格）
- 代答过的问题和回答
- 测试根页面链接、临时克隆路径，以及第 16 步清理了哪些、保留了哪些
