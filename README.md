# Agent Brain

基于 Notion 的 LLM 知识管理系统，让 AI 持续维护你的 Wiki 和技能库。

## 🎯 核心特性

- **自动化知识入库**：将文章、论文、课程笔记提炼成结构化 Wiki
- **知识冲突检测**：自动发现新旧知识矛盾，辅助证据查证
- **Wiki 健康度监控**：检测矛盾、过时内容、孤岛页面
- **Skill 自动同步**：将 Notion 技能文档同步为 Claude Code skills
- **Agent 反馈闭环**：记录 Agent 执行结果，持续改进知识库

## 🚀 快速开始

### 1. 配置 Notion Integration

访问 [Notion Integrations](https://www.notion.so/my-integrations) 创建 Integration：

1. 点击 "New integration"
2. 选择 workspace
3. 设置名称（如 "Agent Brain"）
4. 复制 "Internal Integration Token"

### 2. 配置环境变量

```bash
# 如果还没有 .env 文件，复制模板
# 注意：如果已有 .env 文件，请手动编辑而不是覆盖
[ ! -f .env ] && cp .env.example .env

# 编辑 .env 文件，填入你的 token
# NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 安装依赖

```bash
# 生产环境
pip install -r requirements.txt

# 开发环境（包含测试工具）
pip install -r requirements-dev.txt
```

### 4. 测试连接

```bash
# 验证 token 和连接
./scripts/test-notion-connection

# 或者通过 Claude Code skill
/test-notion-connection
```

看到 "✅ 所有测试通过！" 即表示配置成功。

## 📖 项目结构

```
agent-brain/
├── src/agent_brain/          # 核心代码
│   ├── notion_client.py      # Notion API 封装
│   ├── rate_limiter.py       # 速率控制器
│   ├── wiki_manager.py       # Wiki 管理（待实现）
│   ├── ingest_engine.py      # 入库引擎（待实现）
│   └── conflict_detector.py  # 冲突检测（待实现）
│
├── tests/                    # 测试文件
│   ├── test_notion_client.py
│   └── test_rate_limiter.py
│
├── scripts/                  # 可执行脚本
│   └── test-notion-connection
│
├── .claude/skills/           # Claude Code skills
│   └── test-notion-connection/
│
├── docs/                     # 文档
│   └── adr/                 # 架构决策记录
│
├── SPEC-LLM-WIKI-SYSTEM.md  # 详细需求规格
│
├── .env                      # 环境变量（不提交）
├── .env.example              # 环境变量模板
├── requirements.txt          # 生产依赖
└── requirements-dev.txt      # 开发依赖
```

## 🧪 运行测试

```bash
# 运行所有测试
python3 -m pytest

# 运行特定测试文件
python3 -m pytest tests/test_notion_client.py -v

# 运行并显示覆盖率
python3 -m pytest --cov=src/agent_brain
```

## 📚 下一步

当前已完成 **Issue #2**（项目基础设施与 Notion MCP 连接）。

接下来的工单：

- **Issue #3**：初始化 Notion Wiki 结构（待实现）
- **Issue #4**：入库单个文本材料（待实现）
- **Issue #5**：知识冲突检测（待实现）

查看完整计划：[GitHub Issues](https://github.com/RollRollRoll/agent-brain/issues)

## 🤝 贡献

本项目使用 TDD（测试驱动开发）方式开发。每个新功能应该：

1. 先编写测试（`tests/test_*.py`）
2. 实现功能代码（`src/agent_brain/*.py`）
3. 确保所有测试通过
4. 运行代码审查（`/code-review`）

## 📄 许可证

MIT License

---

**灵感来源**：
- [Karpathy: LLM OS](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Obsidian AI 橙皮书](https://github.com/alchaincyf/obsidian-ai-orange-book)
