# ADR 0002: 技能库存储在本地 Git 仓库而非 Notion

**状态**：已接受（存放形式由 ADR 0009 细化：仓库即 plugin marketplace，按领域分 plugin）  
**日期**：2026-10-21  
**决策者**：用户 + 技术推荐

## 背景

系统需要存储两类内容：
1. **知识（Wiki）**：陈述性知识，面向人类学习（"什么是蒙太奇"、"常见转场效果"）
2. **技能（Skills）**：过程性知识，面向 Agent 执行（"如何用 Premiere 做跳切"、"故障艺术效果的 5 步流程"）

讨论中提出三种方案：
- A：技能存在 Notion，Agent 实时读取
- B：技能存在本地 Git 仓库，Notion 只存知识
- C：混合（Notion 存技能描述，本地存 skill 实现）

## 决策

技能库存储在单独的 Git 仓库（`git@github.com:RollRollRoll/agent-brain.git`），与 Notion Wiki 分离。

## 理由

### 技术原因
1. **Claude Code skill 有专门格式**：
   - 需要符合 `SKILL.md` + frontmatter 规范
   - 直接存 Notion 无法被 `Skill()` 工具识别
2. **Agent 执行需要速度**：
   - 本地文件由 Claude Code 直接加载，不需要网络往返
   - 不占用 Notion API 请求配额
3. **版本控制和测试**：
   - Git 提供完整的版本历史和回滚能力
   - 可以为每个 skill 编写测试
   - 可以集成 CI 自动验证

### 架构原因
4. **职责分离**：
   - **Notion Wiki**：存储"是什么"、"为什么"（人浏览学习）
   - **本地 Skill**：存储"怎么做"（Agent 执行）
   - 两者格式和用途不同，强行统一会增加复杂度
5. **可复用性**：
   - Git 仓库可以跨项目使用
   - 可以分享给其他用户
   - 可以作为独立的技能库发布

## 后果

### 优势
- Agent 执行快速（本地文件，无网络延迟）
- 技能有完整的版本控制和测试
- 可以独立分享和复用
- 符合 Claude Code skill 规范，直接可用

### 代价
- **需要同步机制**：Notion Wiki → 本地 Skill 需要手动或自动同步
- **内容分散在两处**：知识在 Notion，技能在本地（但用途不同，属于合理分离）
- **同步冲突处理**：如果两边都修改了，需要人工合并

### 缓解措施
- 实现 `/sync-skills` 命令，简化同步流程
- 记录同步元数据（`sync-metadata.json`），追踪哪些 skill 对应哪些 Wiki 页面
- 同步冲突时明确标记，提示人工合并

## 同步机制

**方向**：单向（Notion Wiki → 本地 Git 仓库）

**触发方式**：手动（运行 `/sync-skills` 命令）

**逻辑**：
1. LLM 读取 Notion Wiki 的 `techniques` 分类
2. 识别可执行技能（有明确步骤、工具、输入输出）
3. 对比本地 skill 仓库，找出新增/修改/删除的技能
4. 生成/更新符合 Claude Code skill 格式的文件
5. 提交到 Git 仓库

**冲突处理**：如果 Notion 和本地都修改了同一个技能，标记冲突需要人工合并。

## 替代方案

### 方案 A：技能存在 Notion（未采纳）
- 优点：所有内容统一，人和 Agent 看同一份
- 缺点：
  - Agent 每次执行都调用 API（慢，受限）
  - 格式不符合 Claude Code skill 规范
  - 无法利用 Git 版本控制和测试

### 方案 C：混合存储（未采纳）
- Notion 存技能描述（人类可读），本地存 skill 实现（Agent 可执行）
- 优点：人和 Agent 各有适合的格式
- 缺点：维护复杂度高，内容冗余

## 相关决策

- ADR 0001：使用 Notion 而非 Obsidian 作为 Wiki 存储
- ADR 0003：Agent 失败反馈机制（skill 执行失败时需要反馈到系统）
