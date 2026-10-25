"""skill 文档约束测试：只读仓库里的 SKILL.md 和模板，检查它们承诺的结构。"""

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


if __name__ == "__main__":
    unittest.main()
