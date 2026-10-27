"""skill 文档约束测试：只读仓库里的 SKILL.md 和模板，检查它们承诺的结构。"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WIKI_ADMIN = ROOT / "plugins/wiki-admin"


def frontmatter(path):
    """返回 SKILL.md frontmatter 的键值；没有 frontmatter 时返回空字典。"""
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    if not match:
        return {}
    pairs = (line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    return {key.strip(): value.strip() for key, value in pairs}


class RecordTaskSkillTest(unittest.TestCase):
    def test_record_task的frontmatter有name和description(self):
        path = WIKI_ADMIN / "skills/record-task/SKILL.md"
        self.assertTrue(path.is_file(), f"缺少 {path.relative_to(ROOT)}")
        meta = frontmatter(path)
        self.assertEqual(meta.get("name"), "record-task")
        self.assertTrue(meta.get("description"), "description 不能为空")


class AnalyzeFailuresSkillTest(unittest.TestCase):
    SKILL = WIKI_ADMIN / "skills/analyze-failures/SKILL.md"
    TYPES = WIKI_ADMIN / "skills/analyze-failures/references/failure-types.md"
    # ADR 0003 §2 / DEC-004 的 6 类失败
    FAILURE_TYPES = [
        "工具路径/配置错误",
        "前置条件缺失",
        "输入数据格式问题",
        "知识不足",
        "外部服务不可用",
        "Skill 逻辑错误",
    ]

    def test_analyze_failures的frontmatter有name和description(self):
        self.assertTrue(self.SKILL.is_file(), f"缺少 {self.SKILL.relative_to(ROOT)}")
        meta = frontmatter(self.SKILL)
        self.assertEqual(meta.get("name"), "analyze-failures")
        self.assertTrue(meta.get("description"), "description 不能为空")

    def test_分类标准的表格列出6类失败且都有修复目标(self):
        text = self.TYPES.read_text(encoding="utf-8")
        # 取分类表的每一行：第一列是类型，最后一列是修复目标
        rows = {
            cells[0]: cells[-1]
            for cells in (
                [c.strip() for c in line.strip("|").split("|")]
                for line in text.splitlines()
                if line.startswith("| ") and not line.startswith("| 类型")
            )
        }
        self.assertEqual(sorted(rows), sorted(self.FAILURE_TYPES))
        for name, target in rows.items():
            with self.subTest(type=name):
                self.assertIn(target, ("本地 skill", "Wiki 页面"))
        self.assertEqual(rows["知识不足"], "Wiki 页面")

    def test_告警类型在schema和skill里一致(self):
        schema = (WIKI_ADMIN / "skills/init-wiki/references/schema.md").read_text(encoding="utf-8")
        line = next(l for l in schema.splitlines() if l.startswith("| 冲突类型 |"))
        self.assertIn("高频失败", line)
        self.assertIn("'高频失败'", self.SKILL.read_text(encoding="utf-8"))

    def test_修改前要用户确认(self):
        text = self.SKILL.read_text(encoding="utf-8")
        self.assertIn("用户确认之前不修改 skill 文件和 Wiki 页面", text)
        self.assertIn("是否按此修改？", text)
        self.assertIn("是否推送到 GitHub？", text)


class VerifySystemSkillTest(unittest.TestCase):
    """#13：/verify-system 的 SKILL.md 承诺的结构。"""

    SKILL = ROOT / ".claude/skills/verify-system/SKILL.md"

    def text(self):
        self.assertTrue(self.SKILL.is_file(), f"缺少 {self.SKILL.relative_to(ROOT)}")
        return self.SKILL.read_text(encoding="utf-8")

    def test_verify_system的frontmatter有name和description(self):
        self.text()
        meta = frontmatter(self.SKILL)
        self.assertEqual(meta.get("name"), "verify-system")
        self.assertTrue(meta.get("description"), "description 不能为空")

    def test_逐项列出VAL_001到VAL_018(self):
        text = self.text()
        for n in range(1, 19):
            with self.subTest(val=f"VAL-{n:03d}"):
                self.assertIn(f"VAL-{n:03d}", text)

    def test_只用测试Wiki不碰正式Wiki(self):
        text = self.text()
        self.assertIn("LLM Wiki 系统（测试）", text)
        self.assertIn("不碰正式 Wiki", text)

    def test_删除测试数据前先列清单并等用户同意(self):
        text = self.text()
        self.assertIn("移入回收站", text)
        self.assertIn("用户同意后", text)

    def test_用辅助脚本做静态检查和汇总报告(self):
        text = self.text()
        for command in ("verify_tools.py static", "verify_tools.py techniques", "verify_tools.py report"):
            with self.subTest(command=command):
                self.assertIn(command, text)


class SkillTemplateTest(unittest.TestCase):
    def template_body(self):
        """取 skill-template.md 里「文件内容」一节的 markdown 代码块，即生成的 SKILL.md 原样。"""
        text = (WIKI_ADMIN / "skills/sync-skills/references/skill-template.md").read_text(
            encoding="utf-8"
        )
        match = re.search(r"## 文件内容\n+```markdown\n(.*?)\n```\n", text, re.S)
        self.assertIsNotNone(match, "模板里找不到「文件内容」代码块")
        return match.group(1)

    def test_生成的skill在失败处理之后调用record_task(self):
        body = self.template_body()
        sections = re.findall(r"^## (.+)$", body, re.M)
        self.assertIn("记录结果", sections)
        # 记录结果要在失败处理之后：失败也要记
        self.assertGreater(sections.index("记录结果"), sections.index("失败处理"))
        record = body.split("## 记录结果", 1)[1].split("\n## ", 1)[0]
        self.assertIn("wiki-admin:record-task", record)

    def test_验证用skill的记录结果与模板一致(self):
        template = self.template_body().split("## 记录结果", 1)[1].split("\n## ", 1)[0]
        fixtures = sorted(ROOT.glob("tests/fixtures/record-task-demo/skills/*/SKILL.md"))
        self.assertTrue(fixtures, "没有找到 record-task-demo 的 skill")
        for path in fixtures:
            expected = template.replace("<plugin 名>:<skill 名>", f"record-task-demo:{path.parent.name}")
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=path.parent.name):
                self.assertIn("## 记录结果", text)
                self.assertEqual(text.split("## 记录结果", 1)[1].split("\n## ", 1)[0], expected)


class RateLimitHandlingTest(unittest.TestCase):
    """VAL-015：每个调用 notion-* 的 SKILL.md 都写有限流处理。"""

    def test_每个调用notion工具的skill都写了限流处理(self):
        skills = sorted(ROOT.glob("plugins/*/skills/*/SKILL.md"))
        notion_skills = [p for p in skills if "notion-" in p.read_text(encoding="utf-8")]
        self.assertTrue(notion_skills, "没有找到调用 notion-* 的 skill")
        for path in notion_skills:
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=str(path.relative_to(ROOT))):
                self.assertIn("rate_limited", text)
                # 等待并重试一次的写法：自己写明，或引用 Notion 工具使用约定
                self.assertTrue(
                    "retry_after_seconds" in text or "notion-tools.md" in text,
                    "没有写按 retry_after_seconds 等待重试，也没有引用 notion-tools.md",
                )


class MarketplaceManifestTest(unittest.TestCase):
    """ADR 0010：Claude Code 和 Codex 两套 marketplace 列出同一批 plugin，每个 plugin 都有两份清单。"""

    CLAUDE_MARKETPLACE = ROOT / ".claude-plugin/marketplace.json"
    CODEX_MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"

    def load(self, path):
        self.assertTrue(path.is_file(), f"缺少 {path.relative_to(ROOT)}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_两套marketplace名称相同(self):
        self.assertEqual(self.load(self.CLAUDE_MARKETPLACE)["name"], "agent-brain")
        self.assertEqual(self.load(self.CODEX_MARKETPLACE)["name"], "agent-brain")

    def test_两套marketplace列出同一批plugin且路径一致(self):
        claude = {p["name"]: p["source"] for p in self.load(self.CLAUDE_MARKETPLACE)["plugins"]}
        codex = {p["name"]: p["source"] for p in self.load(self.CODEX_MARKETPLACE)["plugins"]}
        self.assertEqual(sorted(claude), sorted(codex))
        for name, source in codex.items():
            with self.subTest(plugin=name):
                self.assertEqual(source.get("source"), "local")
                self.assertEqual(source.get("path"), claude[name])

    def test_每个plugin都有两份清单且字段一致(self):
        plugins = sorted(p.parent for p in ROOT.glob("plugins/*/skills"))
        self.assertTrue(plugins, "plugins/ 下没有 plugin")
        for plugin in plugins:
            with self.subTest(plugin=plugin.name):
                claude = self.load(plugin / ".claude-plugin/plugin.json")
                codex = self.load(plugin / ".codex-plugin/plugin.json")
                self.assertEqual(claude["name"], plugin.name)
                for key in ("name", "description", "author", "repository", "license"):
                    self.assertEqual(codex.get(key), claude.get(key), f"{key} 不一致")
                self.assertEqual(codex.get("skills"), "./skills/")
                # ADR 0009：不写 version，版本跟着 commit 走
                self.assertNotIn("version", claude)
                self.assertNotIn("version", codex)


if __name__ == "__main__":
    unittest.main()
