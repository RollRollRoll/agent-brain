---
name: sync-skills
description: 把 Wiki 中分类为 techniques、写明了步骤、所需工具和前置条件的页面同步成 agent skill，按领域放进 agent-brain 仓库的 plugin；新增、更新、删除前列清单确认，本地改过的 skill 提示人工合并而不覆盖。用户要求把 Wiki 同步成 skill 时使用。
---

# sync-skills

读取 Wiki Index 中「分类」= techniques 的页面，把可执行的页面生成 SKILL.md，放进 agent-brain 仓库
`plugins/<领域 plugin>/skills/<skill 名>/`（ADR 0009）。同步方向只有 Notion → 仓库（ADR 0002）。
**用户确认之前不写任何文件；删除 skill、用 Notion 版覆盖本地改过的 skill，都要逐个单独征得同意；推送前单独征得同意。**

每次运行都是增量同步：没有记录的页面新建 skill，只在 Notion 改过的更新，本地改过的不覆盖（NEG-002），
对应页面已删除或移出 techniques 的先问再删。判定由 [`scripts/sync_state.py`](scripts/sync_state.py) 完成，
运行需要 `python3`（3.7 以上，只用标准库）和 `git`。

调用 `notion-*` 工具的前置条件、写入格式和报错处理见 [Notion 工具使用约定](../../references/notion-tools.md)。
用户说"测试 Wiki"时按 [定位 Wiki](../../references/locate-wiki.md) 用测试根页面。

## 可执行技能的判定标准

页面同时满足下面四条才生成 skill，缺一条就判为不可执行：

1. **有步骤**：正文有「步骤」一节（或同义标题：流程、操作步骤），是至少 2 条的有序列表，每条是一个可以执行的动作。
   只有「要点」「检查项」「特点」这类无序列表的不算
2. **有所需工具**：有「所需工具」一节，或在前置条件里写明了要用的软件、命令或服务
3. **有前置条件**：有「前置条件」一节，列出开始前必须具备的东西
4. **agent 能执行**：每一步要么 agent 能用命令、文件读写或已有工具完成，要么页面明确写了这一步由用户亲自操作
   （例如「请用户在浏览器里……」）。全部步骤都要人操作图形界面、页面又没这样标注的，判为不可执行：
   生成的 skill 是给 agent 执行的（GLOSSARY「Skill」）

这里和 spec 有一处差异：SCN-005-A 和 ADR 0002 写的是「步骤、工具、输入输出」，SCN-005-A 下一行和 #9 写的是
「步骤、工具、前置条件」。本 skill 按后者判定：techniques 页面按 ingest 第 4 步的要求写前置条件，没有固定的「输入输出」一节。

判定只看页面写了什么，不替页面补内容。不可执行的页面在汇报里列出缺了哪一条，用户可以补全页面后再同步。

## sync-metadata.json

放在仓库根目录，格式按 spec §3.4 的 sync-metadata.json 一行（冲突检测会用到它，见 DEC-003），每个生成的 skill 副本一条记录：

```json
{
  "last_sync": "2026-10-23T08:00:00Z",
  "skills": [
    {
      "notion_page_id": "4017d7a6-48e4-819a-9f05-d338a35a6122",
      "skill_path": "plugins/software-dev/skills/llm-wiki-ingest/SKILL.md",
      "last_sync": "2026-10-23T08:00:00Z",
      "content_hash": "5f7c5209972fdb8db1d665895a432e8f733c79bc"
    }
  ]
}
```

- `notion_page_id`：带连字符的页面 ID。一个页面复制到几个领域，就有几条记录，ID 相同、`skill_path` 不同
- `skill_path`：相对仓库根目录的路径
- `last_sync`：UTC ISO 时间。顶层是最近一次同步时间，每条记录是这个副本最后一次写入的时间
- `content_hash`：写入时文件内容的 `git hash-object` 结果，用来判断本地是否被改过
- **不要手写这个文件**：一律用脚本的 `record`（写入或替换一条记录）和 `remove`（删除一条记录）

判断「改过」的规则（由脚本 `plan` 执行）：

- Notion 改过：页面最后编辑时间晚于这条记录的 `last_sync`
- 本地改过：文件当前的 `git hash-object` 和 `content_hash` 不同；文件被删掉、或记录没有 `content_hash`（#9 写的旧记录）
  也算改过，宁可提示人工合并也不覆盖

这里和 DEC-003 有一处差异：DEC-003 写的是比较本地文件的修改时间（mtime）。git clone、checkout、pull 都会把 mtime
改成当前时间，换机器或切分支后所有 skill 都会被当成「本地改过」，Notion 一改就误报冲突；内容哈希不受这些操作影响。
Notion 一侧仍按 DEC-003 比较最后编辑时间。

## 步骤

1. **确认仓库**：skill 以 plugin 安装后运行的是缓存副本，不能往里写（ADR 0009）。检查当前目录：
   - `git remote get-url origin` 指向 `RollRollRoll/agent-brain`，且有 `.claude-plugin/marketplace.json`：用当前目录
   - 不是：问用户本地 agent-brain 仓库的路径，不保存配置
   - `git status --porcelain` 显示 `plugins/`、`.claude-plugin/`、`.agents/plugins/`、`sync-metadata.json` 下有未提交改动：停下，
     请用户先提交或暂存，避免和生成结果混在一起

2. **定位 Wiki**：按 [定位 Wiki](../../references/locate-wiki.md) 找到根页面，取出 Wiki Index 的 data source ID 和数据库 URL。

3. **列出 techniques 页面**：先记下当前 UTC 时间 `T0`（第 7 步写记录时用）。按
   [Notion 工具使用约定](../../references/notion-tools.md) 的「分页读取 Wiki Index」读取全部页面，只保留「分类」= techniques 的页面。
   没有 techniques 页面、`sync-metadata.json` 也没有记录时告诉用户，结束，不做任何修改。

4. **读取并整理页面状态**：
   - 对每个 techniques 页面 `notion-fetch` 读正文和 `page_last_edited_at`，按上面的判定标准分为可执行、不可执行
   - `sync-metadata.json` 里有记录、但不在 techniques 列表中的页面 ID，逐个 `notion-fetch`：返回的 `<page ...>` 带
     `deleted` 的是已删除（在回收站里）；「分类」不是 techniques 的是已移出；报错找不到或无权访问的是读不到
   - 对可执行页面，定出它的全部副本路径：页面已有记录的，沿用记录里的 skill 名；没有记录的，按
     [SKILL.md 模板](references/skill-template.md) 新定 skill 名。再按 [领域标签与 plugin 名](references/domain-plugins.md)
     得出要放进哪几个 plugin，组成 `plugins/<plugin>/skills/<skill 名>/SKILL.md`

   把结果写成一个临时 JSON 文件（放在系统临时目录，不要放进仓库），每个页面一项：

   ```json
   {"pages": [
     {"notion_page_id": "<带连字符的 ID>", "state": "executable",
      "last_edited": "<page_last_edited_at>", "skill_paths": ["plugins/.../SKILL.md"]},
     {"notion_page_id": "<ID>", "state": "deleted"}
   ]}
   ```

   `state` 取 `executable`（可执行）、`not_executable`（在 techniques 中但不可执行）、`not_techniques`（已移出）、
   `deleted`（已删除）、`inaccessible`（读不到）之一。只有 `executable` 需要 `last_edited` 和 `skill_paths`。

5. **判定动作**：在仓库根目录运行
   `python3 <本 skill 目录>/scripts/sync_state.py plan --pages <临时 JSON> --repo .`，输出每个副本的 `action`。
   `<本 skill 目录>` 是这份 SKILL.md 所在的目录（plugin 缓存里也可以，脚本只读不写自身目录）；`--repo` 指向第 1 步确认的仓库：

   | action | 含义 | 本次怎么处理 |
   |---|---|---|
   | `new` | 没有同步记录，目标路径也没有文件 | 按模板生成 |
   | `path_occupied` | 目标路径已经有文件但没有同步记录，或这个路径属于另一个 Notion 页面 | **不覆盖**，请用户改 skill 名或处理已有文件 |
   | `update` | 只有 Notion 改过 | 按模板重新生成，覆盖本地文件 |
   | `conflict` | Notion 和本地都改过 | **不覆盖**，按第 6 步的冲突处理询问用户 |
   | `local_only` | 只有本地改过 | 保留本地，不处理 |
   | `unchanged` | 两边都没改 | 不处理 |
   | `delete_candidate` | 页面已删除、移出 techniques、不再可执行，或去掉了这个领域标签（`reason`） | 按第 6 步询问是否删除 |
   | `skipped` | 页面读不到 | 不处理，在汇报里列出 |

   生成和重新生成的内容先放在会话里，不写文件。

6. **展示清单并等待确认**：按 action 分组列出
   - 新增（`new`）：页面标题和链接、skill 名、目标路径（每个副本一行）、`description`
   - 更新（`update`）：页面标题和链接、目标路径、改了什么（和现有文件对比，列出增删的步骤或段落）
   - **冲突**（`conflict`）：每条单独写「skill X 在 Notion 和本地都被修改，需要人工合并」，附 Notion 页面链接、
     本地文件路径，以及两边的差异（`git diff --no-index <本地文件> <按 Notion 新生成的临时文件>`，临时文件放在系统临时目录）
   - **待删除**（`delete_candidate`）：每条单独写「skill X 对应的 Wiki 页面已不存在（或已移出 techniques / 不再可执行 /
     去掉了某个领域标签），是否删除本地 skill？」。`local_changed` 为 true 时加一句「本地文件在上次同步后被改过」
   - 要新建的领域 plugin，以及要新增的领域映射（附建议的 plugin 名）
   - 不处理的：只有本地改过的（`local_only`）、没变的（`unchanged`）、不可执行的页面和缺了哪一条、路径被占用的（`path_occupied`）、
     读不到的（`skipped`）

   先问：「是否按以上清单新增和更新 skill？」用户可以删减条目、改 skill 名或 plugin 名。
   再对每个冲突、每个待删除**逐个**询问，选项：

   - 冲突：
     - 「保留本地」（默认）：文件和记录都不改，下次同步仍会提示
     - 「用 Notion 版覆盖本地」：写入新生成的内容
     - 「本地已经合并好」：用户已经把 Notion 的改动手动合进本地文件，以当前文件为准，文件不动，只更新同步记录。
       不更新记录的话，本地哈希和 Notion 编辑时间都还是「改过」，每次同步都会报同一个冲突
   - 待删除：「保留」（默认）/「删除」

   **只有用户明确回答「是 / 确认 / 继续」，或对某一条明确选了覆盖、删除，才动对应的文件。**
   用户没回答、回答不明确的，一律按默认处理：保留本地，不改文件，也不改它的记录。用户全部拒绝时结束，不做任何修改。

7. **写文件**：
   1. 新领域 plugin：Claude Code 和 Codex 的清单都要建（ADR 0010），**都不写 `version`**（ADR 0009）。
      - 建 `plugins/<plugin>/.claude-plugin/plugin.json`，字段照 `plugins/wiki-admin/.claude-plugin/plugin.json`
        （`name`、`description`、`author`、`repository`、`license`、`keywords`）。
        在 `.claude-plugin/marketplace.json` 的 `plugins` 里加一条：`name`、`source`（`./plugins/<plugin>`）、`description`、`category`
      - 建 `plugins/<plugin>/.codex-plugin/plugin.json`，字段照 `plugins/wiki-admin/.codex-plugin/plugin.json`：
        前六个字段和上面相同，`skills` 写 `./skills/`，`interface` 的 `displayName`、`shortDescription`、`longDescription`
        按这个领域写，`defaultPrompt` 删掉。在 `.agents/plugins/marketplace.json` 的 `plugins` 里加一条，
        格式照 wiki-admin 那条，`source.path` 写 `./plugins/<plugin>`
   2. 新增、更新、用户选了覆盖的冲突：写 `plugins/<plugin>/skills/<skill 名>/SKILL.md`，模板注释里的同步时间写 `T0`。
      每写完一个，运行 `python3 <本 skill 目录>/scripts/sync_state.py record --page-id <ID> --skill-path <路径> --synced-at <T0> --repo .`。
      用户选了「本地已经合并好」的冲突：不写文件，只运行同样的 `record`
   3. 用户同意删除的：`git rm` 这个 SKILL.md（删掉后 skill 目录空了就一起删），再运行
      `python3 <本 skill 目录>/scripts/sync_state.py remove --skill-path <路径> --repo .`。plugin 里没有 skill 了也**不要**删 plugin 和 marketplace 条目：
      已经安装的人会因此找不到 plugin，在汇报里提一句，由用户决定
   4. 新增了领域映射时，更新目标仓库里的 `plugins/wiki-admin/skills/sync-skills/references/domain-plugins.md`
      （不是 plugin 缓存里的这份），和生成的 skill 一起提交

   `record` 用 `T0` 而不用写完文件的时间：读页面之后、写文件之前 Notion 又被改了的话，下次同步还能发现。

8. **校验**：
   - 运行 `python3 -m unittest tests.skill_docs.test_skill_docs`（仓库根目录）：检查两套 marketplace 列的 plugin 一致、
     每个 plugin 都有两份清单，要全部通过
   - 有 `claude` 命令时运行 `claude plugin validate .`（仓库根目录）：marketplace 和每个 plugin 都要通过。
     只有「No version specified」警告可以忽略（ADR 0009 不写 version），其他警告和错误要修好再继续。
     没有 `claude` 命令（例如在 Codex 里运行）时跳过，在汇报里说明
   - 检查每个 SKILL.md 的 frontmatter 有 `name`、`description`，`name` 和所在目录名一致
   - `sync-metadata.json` 能被 `python3 -m json.tool` 解析，每条记录的 `skill_path` 文件存在
   - 再运行一次第 5 步的 `plan`（用同一份页面状态 JSON）：本次写入或标记合并的副本应该都是 `unchanged`，删除的副本不再出现，
     保留下来的冲突仍是 `conflict`、保留的待删除仍是 `delete_candidate`。
     某个副本仍是 `update`，说明它的页面最后编辑时间晚于 `T0`（读取期间被改过），在汇报里提示用户再同步一次

9. **提交**：只 `git add` 本次写入和删除的文件（不要 `git add .`），提交信息
   `feat(skills): 从 Wiki 同步 skill（新增 <a>，更新 <b>，删除 <c>）`，正文列出每个 skill、对应的 Notion 页面和动作；
   保留下来的冲突和待删除也列在正文里。没有任何文件变化时不提交。

10. **推送**：问用户「是否推送到 GitHub？」，说明推送后 marketplace 的使用者在 Claude Code 运行
    `/plugin marketplace update agent-brain`、在 Codex 运行 `codex plugin marketplace upgrade agent-brain`，就能拿到新 skill。
    用户同意才 `git push`。
    推送失败（远端有新提交）时停下，提示用户先 `git pull --rebase`，再重新推送，不要强推。

## 失败处理

工具报错（`rate_limited`、`usage_limit_reached` 等）按 [Notion 工具使用约定](../../references/notion-tools.md) 处理。

- 读取阶段失败（限流重试后仍失败、额度用完等）：停止，不写任何文件，说明读到了第几个页面和失败原因
- 单个 skill 生成失败或校验不通过：不写它的 metadata 记录，也不提交它的文件。列出这个 skill 本次新建的文件，
  问用户是否删除，**用户明确同意后才删**；不同意就留在工作区，由用户处理。
  在汇报里写明失败原因，提示用户检查 Notion 页面；其他 skill 照常提交（spec §3.5）
- 写到一半失败（写文件、校验或提交时出错）：不提交，列出已经写入、删除的文件和已经改过的记录，用户可以用 `git status`
  查看、自行决定保留还是丢弃。被更新覆盖的文件可以用 `git checkout -- <路径>` 恢复，但这会丢掉新内容，要用户自己决定
- 不删除已经提交的内容来"回滚"

spec §3.5 要求失败时「记录错误日志」。本 skill 不往仓库写日志文件：失败原因写进汇报，用户在会话里就能看到，
日志文件提交进 marketplace 反而会被安装的人看到。

## 汇报

- 新增、更新、删除的 skill：skill 名、路径、对应的 Notion 页面
- 保留下来的冲突：每条写「skill X 在 Notion 和本地都被修改，需要人工合并」，以及用户选的处理方式
- 保留下来的待删除：skill 名、路径、原因
- 新建的领域 plugin，以及安装命令 `/plugin install <plugin>@agent-brain`；删除后已经没有 skill 的 plugin
- 不处理的：只有本地改过的、没变的、不可执行的页面（缺了哪一条）、路径被占用的、读不到的
- 提交号；是否已推送
- 遇到限流时，等待了几次、每次多少秒
