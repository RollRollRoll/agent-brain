---
name: sync-skills
description: 把 Wiki 中分类为 techniques、写明了步骤、所需工具和前置条件的页面生成 Claude Code skill，按领域放进 agent-brain 仓库的 plugin，记录 sync-metadata.json 并提交。用户要求把 Wiki 同步成 skill 时使用。
---

# sync-skills

读取 Wiki Index 中「分类」= techniques 的页面，把可执行的页面生成 SKILL.md，放进 agent-brain 仓库
`plugins/<领域 plugin>/skills/<skill 名>/`（ADR 0009）。同步方向只有 Notion → 仓库（ADR 0002）。
**用户确认之前不写任何文件；推送前单独征得同意。**

本版只做首次同步：已经同步过的 skill 不更新、不删除，在汇报里列出。增量更新、冲突检测和删除见 #10。

调用 `notion-*` 工具的前置条件、写入格式和报错处理见 [Notion 工具使用约定](../../references/notion-tools.md)。
用户说"测试 Wiki"时按 [定位 Wiki](../../references/locate-wiki.md) 用测试根页面。

## 可执行技能的判定标准

页面同时满足下面三条才生成 skill，缺一条就判为不可执行：

1. **有步骤**：正文有「步骤」一节（或同义标题：流程、操作步骤），是至少 2 条的有序列表，每条是一个可以执行的动作。
   只有「要点」「检查项」「特点」这类无序列表的不算
2. **有所需工具**：有「所需工具」一节，或在前置条件里写明了要用的软件、命令或服务
3. **有前置条件**：有「前置条件」一节，列出开始前必须具备的东西

判定只看页面写了什么，不替页面补内容。不可执行的页面在汇报里列出缺了哪一条，用户可以补全页面后再同步。

## sync-metadata.json

放在仓库根目录，格式按 spec §3.4（DEC-003），每个生成的 skill 副本一条记录：

```json
{
  "last_sync": "2026-10-23T08:00:00Z",
  "skills": [
    {
      "notion_page_id": "4017d7a6-48e4-819a-9f05-d338a35a6122",
      "skill_path": "plugins/software-dev/skills/llm-wiki-ingest/SKILL.md",
      "last_sync": "2026-10-23T08:00:00Z"
    }
  ]
}
```

- `notion_page_id`：带连字符的页面 ID。一个页面复制到几个领域，就有几条记录，ID 相同、`skill_path` 不同
- `skill_path`：相对仓库根目录的路径
- `last_sync`：UTC ISO 时间。顶层是本次同步时间，每条记录是这个副本最后一次写入的时间
- 文件不存在时新建；已存在时只追加新记录、更新顶层 `last_sync`，不改已有记录

## 步骤

1. **确认仓库**：skill 以 plugin 安装后运行的是缓存副本，不能往里写（ADR 0009）。检查当前目录：
   - `git remote get-url origin` 指向 `RollRollRoll/agent-brain`，且有 `.claude-plugin/marketplace.json`：用当前目录
   - 不是：问用户本地 agent-brain 仓库的路径，不保存配置
   - `git status --porcelain` 显示 `plugins/`、`.claude-plugin/`、`sync-metadata.json` 下有未提交改动：停下，
     请用户先提交或暂存，避免和生成结果混在一起

2. **定位 Wiki**：按 [定位 Wiki](../../references/locate-wiki.md) 找到根页面，取出 Wiki Index 的 data source ID 和数据库 URL。

3. **列出 techniques 页面**：按 `/wiki-admin:lint-wiki` 第 2 步的方式分页读取 Wiki Index（首选 view 模式，
   每批 100 行，按 `next_cursor` 取完），只保留「分类」= techniques 的页面。
   没有 techniques 页面时告诉用户，结束，不做任何修改。

4. **读取并判定**：对每个页面 `notion-fetch` 读正文，按上面的判定标准分为可执行、不可执行。
   单个页面不存在或无权访问：跳过，在汇报里列出，继续处理其他页面（spec §3.5）。
   对可执行页面：
   - 读 `sync-metadata.json`，页面 ID 已经有记录的标为「已同步过」，本次不处理
   - 按 [领域标签与 plugin 名](references/domain-plugins.md) 得出要放进哪几个 plugin
   - 按 [SKILL.md 模板](references/skill-template.md) 定 skill 名，生成内容（先放在会话里，不写文件）
   - 目标路径已经有文件、但 `sync-metadata.json` 里没有它：不覆盖，标为「路径被占用」，请用户处理

5. **展示清单并等待确认**：列出
   - 拟生成的 skill：页面标题和链接、skill 名、目标路径（每个副本一行）、`description`
   - 要新建的领域 plugin，以及要新增的领域映射（附建议的 plugin 名）
   - 不可执行的页面和缺了哪一条；已同步过的页面；路径被占用的页面；跳过的页面

   问用户：「是否按以上清单生成 skill 并提交？」用户可以删减条目、改 skill 名或 plugin 名。
   **只有用户明确回答「是 / 确认 / 继续」后才写文件。** 用户拒绝时结束，不做任何修改。

6. **写文件**：
   1. 新领域 plugin：建 `plugins/<plugin>/.claude-plugin/plugin.json`，字段照 `plugins/wiki-admin/.claude-plugin/plugin.json`
      （`name`、`description`、`author`、`repository`、`license`、`keywords`），**不写 `version`**（ADR 0009）。
      在 `.claude-plugin/marketplace.json` 的 `plugins` 里加一条：`name`、`source`（`./plugins/<plugin>`）、`description`、`category`
   2. 每个副本写 `plugins/<plugin>/skills/<skill 名>/SKILL.md`
   3. 更新 `sync-metadata.json`
   4. 新增了领域映射时，更新 [领域标签与 plugin 名](references/domain-plugins.md)

7. **校验**：
   - 运行 `claude plugin validate .`（仓库根目录）：marketplace 和每个 plugin 都要通过。
     只有「No version specified」警告可以忽略（ADR 0009 不写 version），其他警告和错误要修好再继续
   - 检查每个 SKILL.md 的 frontmatter 有 `name`、`description`，`name` 和所在目录名一致
   - `sync-metadata.json` 能被 `python3 -m json.tool` 解析，每条记录的 `skill_path` 文件存在

8. **提交**：只 `git add` 本次写入的文件（不要 `git add .`），提交信息
   `feat(skills): 从 Wiki 同步 <n> 个 skill`，正文列出每个 skill 和对应的 Notion 页面。

9. **推送**：问用户「是否推送到 GitHub？」，说明推送后 marketplace 的使用者运行
   `/plugin marketplace update agent-brain` 就能拿到新 skill。用户同意才 `git push`。
   推送失败（远端有新提交）时停下，提示用户先 `git pull --rebase`，再重新推送，不要强推。

## 失败处理

工具报错（`rate_limited`、`usage_limit_reached` 等）按 [Notion 工具使用约定](../../references/notion-tools.md) 处理。

- 读取阶段失败（限流重试后仍失败、额度用完等）：停止，不写任何文件，说明读到了第几个页面和失败原因
- 单个 skill 生成失败或校验不通过：删掉这个 skill 本次新建的文件（只删本次写的），不写它的 metadata 记录，
  在汇报里说明原因，提示用户检查 Notion 页面；其他 skill 照常提交（spec §3.5）
- 提交前失败：不提交，列出已经写入的文件，用户可以用 `git status` 查看、自行决定保留还是丢弃
- 不删除已经提交的内容来"回滚"

## 汇报

- 生成的 skill：skill 名、路径、对应的 Notion 页面
- 新建的领域 plugin，以及安装命令 `/plugin install <plugin>@agent-brain`
- 不可执行的页面（缺了哪一条）、已同步过的页面、路径被占用的页面、跳过的页面
- 提交号；是否已推送
- 遇到限流时，等待了几次、每次多少秒
