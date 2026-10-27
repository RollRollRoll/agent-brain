"""verify_tools.py 的 CLI 测试：在临时 git 仓库里运行真实命令，只看命令的输入输出。"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".claude/skills/verify-system/scripts/verify_tools.py"
)


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class StaticTest(unittest.TestCase):
    """VAL-014 / VAL-015 的静态检查。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.write(".gitignore", ".env\n")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", rel], cwd=self.repo, check=True)

    def static(self):
        result = run_cli("static", "--repo", str(self.repo))
        self.assertEqual(result.returncode, 0, result.stderr)
        return {r["id"]: r for r in json.loads(result.stdout)["results"]}

    def test_仓库里有notion凭据时VAL_014失败并指出位置(self):
        self.write("config.py", 'TOKEN = "ntn_abc123"\n')
        val = self.static()["VAL-014"]
        self.assertEqual(val["status"], "fail")
        self.assertIn("config.py:1", val["evidence"])

    def test_还没git_add的文件里有凭据也算失败(self):
        (self.repo / "draft.py").write_text('KEY = "secret_xyz"\n', encoding="utf-8")
        val = self.static()["VAL-014"]
        self.assertEqual(val["status"], "fail")
        self.assertIn("draft.py:1", val["evidence"])

    def test_只排除写着模式本身的两个文件同目录其他文件照查(self):
        self.write(".claude/skills/verify-system/notes.md", "token: ntn_leaked\n")
        self.write("tests/verify_system/fixture.txt", "secret_leaked\n")
        val = self.static()["VAL-014"]
        self.assertEqual(val["status"], "fail")
        self.assertIn(".claude/skills/verify-system/notes.md:1", val["evidence"])
        self.assertIn("tests/verify_system/fixture.txt:1", val["evidence"])

    def test_gitignore没有忽略env时VAL_014失败(self):
        self.write(".gitignore", ".env.local\n")
        val = self.static()["VAL-014"]
        self.assertEqual(val["status"], "fail")
        self.assertIn(".env", val["evidence"])

    def test_没有凭据且忽略了env时VAL_014通过(self):
        self.write("README.md", "用 OAuth 登录，不需要 token\n")
        self.assertEqual(self.static()["VAL-014"]["status"], "pass")

    def test_调用notion工具却没写限流处理的skill让VAL_015失败(self):
        self.write(
            "plugins/demo/skills/good/SKILL.md",
            "用 `notion-fetch` 读取。工具报错（`rate_limited` 等）按 notion-tools.md 处理。\n",
        )
        self.write("plugins/demo/skills/bad/SKILL.md", "用 `notion-search` 搜索根页面。\n")
        self.write("plugins/demo/skills/offline/SKILL.md", "只读本地文件。\n")
        val = self.static()["VAL-015"]
        self.assertEqual(val["status"], "fail")
        self.assertIn("plugins/demo/skills/bad/SKILL.md", val["evidence"])
        self.assertNotIn("good", val["evidence"])

    def test_项目级skill也算进VAL_015(self):
        self.write(
            ".claude/skills/verify/SKILL.md",
            "用 `notion-fetch` 回读。遇到 `rate_limited` 按 `retry_after_seconds` 等待后重试一次。\n",
        )
        val = self.static()["VAL-015"]
        self.assertEqual(val["status"], "pass")
        self.assertIn("1 个", val["evidence"])


def sections(markdown):
    """把正文按二级标题切开，返回 {标题: 内容}。"""
    result, current = {}, None
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        elif current is not None and line.strip():
            result[current].append(line.strip())
    return result


class TechniquesTest(unittest.TestCase):
    """VAL-017 的样本：50 个 technique 页面。"""

    def techniques(self, *args):
        result = run_cli("techniques", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["pages"]

    def test_按数量生成标题不重复的样本(self):
        pages = self.techniques("--count", "50", "--prefix", "性能样本")
        self.assertEqual(len(pages), 50)
        titles = [p["标题"] for p in pages]
        self.assertEqual(len(set(titles)), 50)
        self.assertTrue(all(t.startswith("性能样本") for t in titles))

    def test_每个样本都满足sync_skills的可执行判定(self):
        # 判定标准见 plugins/wiki-admin/skills/sync-skills/SKILL.md「可执行技能的判定标准」
        for page in self.techniques("--count", "3", "--prefix", "性能样本"):
            with self.subTest(title=page["标题"]):
                self.assertEqual(page["分类"], "techniques")
                self.assertTrue(page["简短摘要"])
                body = sections(page["正文"])
                steps = [l for l in body.get("步骤", []) if l[:1].isdigit() and ". " in l]
                self.assertGreaterEqual(len(steps), 2, "步骤至少 2 条有序列表")
                self.assertTrue(body.get("所需工具"), "缺少所需工具")
                self.assertTrue(body.get("前置条件"), "缺少前置条件")


class ReportTest(unittest.TestCase):
    """汇总各 VAL 项，判定性能门槛和 VAL-019。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def report(self, results):
        path = self.dir / "results.json"
        path.write_text(json.dumps({"results": results}, ensure_ascii=False), encoding="utf-8")
        result = run_cli("report", "--results", str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def by_id(self, report):
        return {r["id"]: r for r in report["results"]}

    def test_性能项按spec门槛判定而不是按填入的状态(self):
        # 门槛：QOS-001 入库 < 5 分钟，QOS-002 同步 < 20 分钟，QOS-003 加载 < 10 秒
        report = self.by_id(
            self.report(
                [
                    {"id": "VAL-016", "status": "pass", "evidence": "入库 3000 字", "seconds": 301},
                    {"id": "VAL-017", "status": "fail", "evidence": "同步 50 个", "seconds": 1199},
                    {"id": "VAL-018", "status": "pass", "evidence": "加载 hello", "seconds": 10},
                ]
            )
        )
        self.assertEqual(report["VAL-016"]["status"], "fail")
        self.assertEqual(report["VAL-017"]["status"], "pass")
        self.assertEqual(report["VAL-018"]["status"], "fail", "门槛是小于 10 秒，等于不算通过")
        self.assertIn("301", report["VAL-016"]["evidence"])
        self.assertIn("300", report["VAL-016"]["evidence"])

    def all_pass(self):
        """VAL-001 ~ VAL-018 全部通过，性能项耗时都在门槛内。"""
        seconds = {"VAL-016": 12, "VAL-017": 200, "VAL-018": 3}
        return [
            {"id": f"VAL-{n:03d}", "status": "pass", "evidence": "回读一致",
             **({"seconds": seconds[f"VAL-{n:03d}"]} if f"VAL-{n:03d}" in seconds else {})}
            for n in range(1, 19)
        ]

    def test_全部通过时VAL_019通过(self):
        report = self.report(self.all_pass())
        val = self.by_id(report)["VAL-019"]
        self.assertEqual(val["status"], "pass")
        self.assertEqual(report["summary"], {"pass": 19, "fail": 0, "skip": 0})

    def test_缺项按失败记且VAL_019失败(self):
        results = [r for r in self.all_pass() if r["id"] != "VAL-005"]
        report = self.by_id(self.report(results))
        self.assertEqual(report["VAL-005"]["status"], "fail")
        self.assertIn("没有结果", report["VAL-005"]["evidence"])
        self.assertEqual(report["VAL-019"]["status"], "fail")
        self.assertIn("VAL-005", report["VAL-019"]["evidence"])

    def test_有跳过项时VAL_019不算通过(self):
        results = self.all_pass()
        results[6] = {"id": "VAL-007", "status": "skip", "evidence": "用户中止"}
        report = self.report(results)
        val = self.by_id(report)["VAL-019"]
        self.assertEqual(val["status"], "fail")
        self.assertIn("VAL-007", val["evidence"])
        self.assertEqual(report["summary"]["skip"], 1)

    def test_报告按编号排序(self):
        results = list(reversed(self.all_pass()))
        ids = [r["id"] for r in self.report(results)["results"]]
        self.assertEqual(ids, [f"VAL-{n:03d}" for n in range(1, 20)])


if __name__ == "__main__":
    unittest.main()
