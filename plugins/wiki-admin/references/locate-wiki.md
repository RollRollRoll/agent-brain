# 定位 Wiki

wiki-admin 的 skill 都按本文找到要操作的 Wiki。根页面登记在本地文件里，由 `/wiki-admin:init-wiki` 写入（ADR 0011）。

## 正式 Wiki 和测试 Wiki

用户说"测试 Wiki"时操作测试 Wiki，否则操作正式 Wiki。两个 Wiki 在登记文件里各有一条记录，键分别是 `production` 和 `test`。

## 登记文件

有两个位置，格式相同：

- **项目登记文件**：项目根目录下的 `.agent-brain/wiki.json`，只对这个项目有效。项目根目录是当前工作目录所在 git 仓库的根
  （`git rev-parse --show-toplevel`）；不在 git 仓库里时就是当前工作目录
- **用户登记文件**：`~/.agent-brain/wiki.json`，所有没有项目登记的项目都用它

找某个 Wiki（正式或测试）时，先看项目登记文件里有没有这个 Wiki 的记录，有就用它；没有再看用户登记文件。
两个 Wiki 分开找：项目登记文件里只有测试 Wiki 时，正式 Wiki 仍然从用户登记文件取。

```json
{
  "wikis": {
    "production": {
      "root_page_url": "https://app.notion.com/p/...",
      "root_page_title": "我的知识库",
      "root_page_created": false,
      "registered_at": "2026-10-29T10:00:00+08:00"
    },
    "test": {
      "root_page_url": "https://app.notion.com/p/...",
      "root_page_title": "LLM Wiki 系统（测试）",
      "root_page_created": true,
      "registered_at": "2026-10-29T10:05:00+08:00"
    }
  }
}
```

- `root_page_url`：根页面 URL，定位只认它
- `root_page_title`：登记时的标题，只用于给用户看；用户在 Notion 里改了标题不影响定位
- `root_page_created`：根页面是 init-wiki 新建的为 `true`，用的是用户已有页面为 `false`。覆盖重建时按它决定移走什么
- `registered_at`：登记时间，带时区的 ISO 时间

只有 init-wiki 写这个文件，其他 skill 只读。

## 步骤

1. 按上一节的顺序找这个 Wiki 的记录，记下用的是哪个文件。文件不存在或没有这个 Wiki 的记录时看下一个；
   文件不是合法 JSON 时停下，告诉用户哪个文件坏了，不要跳到下一个文件，以免用错 Wiki。
   两个文件都没有记录时，停下，告诉用户「还没有登记<正式 / 测试> Wiki（查过：<两个文件的路径>）」，
   请先运行 `/wiki-admin:init-wiki`：Notion 里已经有 Wiki 时选「用已有页面」并给出根页面链接，它会只登记、不改 Notion。
   不要按标题去 Notion 里搜。
2. 用 `notion-fetch` 读取 `root_page_url`。打不开或在回收站里时，停下，告诉用户登记的根页面已失效（附链接和登记文件路径），
   请在 Notion 里恢复，或重新运行 `/wiki-admin:init-wiki`。不要改用另一个文件的记录。
3. 根页面内容里的 `<database url="..." data-source-url="collection://...">名称</database>`
   给出每个数据库的 URL 和 data source ID，`<page url="...">名称</page>` 给出分类页面。
4. 核对 5 个数据库（Sources、Wiki Index、Agent Tasks、Wiki Changelog、Conflicts）和 3 个分类页面
   （concepts/、techniques/、tools/）都在。缺了哪个就停下，告诉用户缺什么，建议运行 `/wiki-admin:init-wiki` 选择覆盖重建。

登记文件不同步：换机器后要重新运行一次 init-wiki 登记。
