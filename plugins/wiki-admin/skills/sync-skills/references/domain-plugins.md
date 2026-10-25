# 领域标签与 plugin 名

`/wiki-admin:sync-skills` 按本表把 Wiki 页面的「领域标签」换成 plugin 名（ADR 0009）。
一个页面有几个领域标签，生成的 skill 就复制到几个领域 plugin，每份内容相同。

plugin 名会成为安装 ID（`<plugin>@agent-brain`），**定下后不要改**，改名会让已有安装失效。

| 领域标签 | plugin 名 |
|---|---|
| 知识管理 | knowledge-mgmt |
| 软件开发 | software-dev |
| 视频制作 | video-production |

## 遇到表里没有的标签

不要自己起名。在第 6 步的确认清单里列出这个标签，问用户 plugin 名，并给一个建议值：
英文小写、单词之间用连字符、不超过 32 个字符、不能是 `wiki-admin`。
用户确认后把新的一行加进上表，和生成的 skill 一起提交。

用户不想为这个标签建 plugin 时，这个标签不生成副本；页面的其他标签照常生成。
页面的所有标签都被跳过时，这个页面不生成 skill，在汇报里说明。
