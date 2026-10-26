---
name: analyze-failures
description: 分析 Agent Tasks 中的失败记录：归到 6 类失败之一，建议修复本地 skill 或补充 Wiki 页面，用户确认后执行；同一 skill 1 天内失败 3 次以上时在 Conflicts 建告警。用户要求分析失败任务、修复失败的 skill 时使用。
---

# analyze-failures

读取 `wiki-admin:record-task` 记下的失败记录，判断失败类型，给出修复建议（REQ-008，ADR 0003 阶段 2）。
**用户确认之前不修改 skill 文件和 Wiki 页面；每处修改单独确认；推送前单独征得同意。**

用法：

- `/wiki-admin:analyze-failures`：分析所有还没分析过的失败记录（「反馈/问题」为空），并检查高频失败
- `/wiki-admin:analyze-failures <记录链接>`：只分析这一条
- `/wiki-admin:analyze-failures <skill 名>`：只分析这个 skill 的失败记录

调用 `notion-*` 工具的前置条件、写入格式和报错处理见 [Notion 工具使用约定](../../references/notion-tools.md)。
用户说"测试 Wiki"时按 [定位 Wiki](../../references/locate-wiki.md) 用测试根页面。
失败类型的判定条件和修复方向见 [失败分类标准](references/failure-types.md)。

## 步骤

1. **定位 Wiki**：按 [定位 Wiki](../../references/locate-wiki.md) 找到根页面，取出 Agent Tasks、Wiki Index、
   Wiki Changelog、Conflicts 的 data source ID。

2. **读取失败记录**：`notion-query-data-sources` 用 rows 模式查 Agent Tasks，筛选「状态」= 失败，
   按「执行时间」降序，`limit: 100`。给了记录链接时改用 `notion-fetch` 读这一条，确认父级是 Agent Tasks、状态是失败。
   - 无参数：分析「反馈/问题」为空的记录；高频检查用查到的全部失败记录
   - 给了 skill 名：只取「使用的 Skill」等于它的记录，「反馈/问题」不为空的也分析（用户要求重新看）
   - 满 100 条时在汇报里说明只看了最近 100 条失败记录
   - 没有要分析的记录：说明「没有待分析的失败记录」，仍做第 4 步

3. **分类**：对每条要分析的记录，读「失败原因」「结果摘要」，按[失败分类标准](references/failure-types.md)
   归到一类。`record-task` 写的「分析」一段是参考，不是结论：和错误信息对不上时以错误信息为准，并说明为什么改判。
   需要时读本地 skill 文件（第 5 步找到的路径）核对：错误里的路径、命令、参数是否就是 skill 写的。

4. **检查高频失败**（SCN-006-C）：按「使用的 Skill」分组，某个 skill 任意 24 小时内（按执行时间的开始时间）
   有 3 条以上失败记录，就是高频失败。对每个高频失败的 skill：
   1. 查 Conflicts：已有「冲突类型」= 高频失败、「状态」不是「已解决」、「冲突摘要」包含这个 skill 名的记录时不重复建，
      汇报里列出已有告警的链接
   2. `notion-fetch` Conflicts 的 data source，「冲突类型」没有「高频失败」选项时，列出全部已有选项和要加的选项，
      问用户是否添加；同意后用 `notion-update-data-source` 的 `ALTER COLUMN "冲突类型" SET SELECT(...)`
      加上 `'高频失败':red`，**必须列出全部已有选项**。用户不同意就不建告警，只在汇报里提示
   3. 在 Conflicts 建一条记录：「冲突摘要」写 `高频失败：<skill 名> 在 24 小时内失败 <n> 次`，
      「冲突类型」= 高频失败，「状态」= 待审核，其他字段留空。正文列出这几条失败记录（`<mention url="..." />`、执行时间、
      失败步骤），以及第 3 步的分类结果
   4. 告诉用户：「skill <名> 高频失败，需要检查和修复」，附告警链接

   告警由本 skill 建，不由 `record-task` 在写入时检测：记录是附带的，不做额外查询（与 SCN-006-C「写入时检测」的差异）。
   每次运行本 skill 都会检查一遍。

5. **找修复目标**：
   - **本地 skill 文件**：skill 以 plugin 安装后运行的是缓存副本，不能往里改（ADR 0009）。先确认仓库：
     当前目录 `git remote get-url origin` 指向 `RollRollRoll/agent-brain` 且有 `.claude-plugin/marketplace.json` 时用当前目录，
     否则问用户本地 agent-brain 仓库的路径。「使用的 Skill」是 `<plugin>:<skill>`，在仓库里找
     `plugins/<plugin>/skills/<skill>/SKILL.md`；没有就找路径以 `/<plugin>/skills/<skill>/SKILL.md` 结尾的文件（例如测试用的 fixture）。
     找不到或多于一个时问用户
   - **Wiki 页面**：先看仓库根目录 `sync-metadata.json` 里 `skill_path` 是这个文件的记录，取 `notion_page_id`；
     没有记录时按失败原因里提到的主题查 Wiki Index 的「标题」，多于 1 条时让用户选。都找不到时问用户是哪个页面，
     用户也不知道就建议新建页面（用 `/wiki-admin:ingest` 入库相关材料），不在这里建

6. **展示建议并等待确认**：每条记录一段：
   - 记录：任务名、使用的 Skill、执行时间、链接
   - 失败类型和判定依据（引用错误信息原文）
   - 修复建议：改什么、为什么能解决。改 skill 时给出改动前后的那几行；改 Wiki 时给出要加的标记全文
   - 原因不明时写明已经排除的可能，建议用户补充信息或重新运行任务看完整报错，不给修改

   每处修改单独问「是否按此修改？」。**只有用户明确回答「是 / 确认 / 继续」后才执行。**
   用户拒绝或不答的，不修改，跳到第 8 步。

7. **执行修复**：
   - **改 skill**（SCN-008-A）：
     1. `git status --porcelain` 显示这个文件有未提交改动时停下，请用户先处理
     2. 只改建议里的那几行，不顺手改别的
     3. 文件在 `plugins/` 下时运行 `claude plugin validate .`，只有「No version specified」警告可以忽略
     4. 只 `git add` 这个文件，提交信息 `fix(skills): 修复 <skill 名> 的<失败类型>`，正文写失败记录链接、错误信息摘要、改了什么
     5. 问用户「是否推送到 GitHub？」，同意才 `git push`；推送失败时停下，提示先 `git pull --rebase`，不要强推
     6. 这个 skill 在 `sync-metadata.json` 里有记录时提醒用户：`/wiki-admin:sync-skills` 会把它当作本地改过，
        对应的 Notion 页面再被修改时会提示人工合并；建议把同样的修正写回 Notion 页面
   - **标记 Wiki 页面**（SCN-008-B）：
     1. `notion-fetch` 读页面。页首已有引用同一条失败记录的「需要补充」callout 时不重复加
     2. 用 `notion-update-page` 的 `insert_content`（`position: {"type": "start"}`）在页首插入：

        ```
        <callout icon="⚠️" color="yellow_bg">
        需要补充：<缺什么，一两句话>。来源：Agent Tasks 失败记录 <mention url="<记录链接>" />
        </callout>
        ```

        不改正文其他内容。补全页面后删掉这个 callout 即可
     3. 在 Wiki Changelog 建一条记录：变更摘要「标记需要补充：<页面标题>」、Wiki 页面、变更类型「更新」、
        详情写用户确认的时间、标记内容和失败记录链接，例如「2026-10-25 14:20 用户确认；加上需要补充标记：缺少具体步骤」
   - **告警处理完**：这次修复的 skill 有未解决的高频失败告警时，问用户是否把告警标为「已解决」；
     同意后「状态」改为「已解决」，「解决方案」写修复了什么（提交哈希或页面链接）

8. **回写分析结果**：每条分析过的记录，用 `notion-update-page` 的 `update_properties` 更新「反馈/问题」：
   `<日期> 分析：<失败类型>；<已修复：提交哈希 / 已标记页面：链接 / 用户未采纳 / 原因不明>`。
   原来有内容时接在后面（换行），不要覆盖。这一步不改 skill 和 Wiki，无参数运行时据此跳过已分析的记录。

9. **核对**：`notion-fetch` 回读改过的 Wiki 页面、Changelog、告警、Agent Tasks 记录，确认写入内容正确，
   正文没有 `http://<文件名>` 这类误识别的链接；改过的 skill 用 `git show --stat HEAD` 确认只提交了这一个文件。

## 失败处理

工具报错（`rate_limited`、`usage_limit_reached` 等）按 [Notion 工具使用约定](../../references/notion-tools.md) 处理。

- 写到一半失败：停止，列出已经完成的（改了哪些 skill、提交哈希、标记了哪些页面、建了哪些 Changelog 和告警、
  回写了哪些记录）和失败原因。重新运行时，已回写「反馈/问题」的记录不会再被分析；已提交但没回写的，
  先 `git log` 确认修复已在，再只补第 8 步
- 提交或校验失败：不提交，告诉用户改动还在工作区，可以 `git diff` 查看，自行决定保留还是 `git checkout -- <文件>` 丢弃

## 汇报

- 分析了几条记录，每条一行：链接、失败类型、处理结果（已修复 / 已标记 / 未采纳 / 原因不明）
- 修改过的 skill 文件和提交哈希、是否已推送
- 标记过的 Wiki 页面和 Changelog 链接
- 高频失败告警：新建的和已有的，各附链接
