"""sync_state.py 的 CLI 测试：在临时 git 仓库里运行真实命令，只看命令的输入输出。"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "plugins/wiki-admin/skills/sync-skills/scripts/sync_state.py"
)

PAGE = "4017d7a6-48e4-819a-9f05-d338a35a6122"
PATH_KM = "plugins/knowledge-mgmt/skills/llm-wiki-ingest/SKILL.md"
PATH_SD = "plugins/software-dev/skills/llm-wiki-ingest/SKILL.md"


class SyncStateTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--repo", str(self.repo)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def plan(self, pages):
        pages_file = self.repo / "pages.json"
        pages_file.write_text(json.dumps({"pages": pages}), encoding="utf-8")
        out = json.loads(self.run_cli("plan", "--pages", str(pages_file)))
        return {item["skill_path"]: item for item in out["items"]}

    def test_没有同步记录的可执行页面是新增(self):
        items = self.plan(
            [
                {
                    "notion_page_id": PAGE,
                    "state": "executable",
                    "last_edited": "2026-10-24T08:00:00.000Z",
                    "skill_paths": [PATH_KM],
                }
            ]
        )
        self.assertEqual(items[PATH_KM]["action"], "new")
        self.assertEqual(items[PATH_KM]["notion_page_id"], PAGE)

    def write_skill(self, skill_path, text):
        path = self.repo / skill_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def record(self, skill_path, synced_at="2026-10-24T08:00:00Z", page=PAGE):
        self.run_cli(
            "record",
            "--page-id", page,
            "--skill-path", skill_path,
            "--synced-at", synced_at,
        )

    def executable(self, last_edited, skill_paths=(PATH_KM,), page=PAGE):
        return {
            "notion_page_id": page,
            "state": "executable",
            "last_edited": last_edited,
            "skill_paths": list(skill_paths),
        }

    def test_只改了Notion页面时更新本地skill(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM, synced_at="2026-10-24T08:00:00Z")

        items = self.plan([self.executable("2026-10-24T09:30:00.000Z")])

        self.assertEqual(items[PATH_KM]["action"], "update")

    def test_Notion和本地都改过时报冲突(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM, synced_at="2026-10-24T08:00:00Z")
        self.write_skill(PATH_KM, "生成的内容\n用户手动加的一行\n")

        items = self.plan([self.executable("2026-10-24T09:30:00.000Z")])

        self.assertEqual(items[PATH_KM]["action"], "conflict")

    def test_只改了本地文件时保留本地(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM, synced_at="2026-10-24T08:00:00Z")
        self.write_skill(PATH_KM, "生成的内容\n用户手动加的一行\n")

        items = self.plan([self.executable("2026-10-24T07:00:00.000Z")])

        self.assertEqual(items[PATH_KM]["action"], "local_only")

    def test_两边都没改时不处理(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM, synced_at="2026-10-24T08:00:00Z")

        items = self.plan([self.executable("2026-10-24T07:00:00.000Z")])

        self.assertEqual(items[PATH_KM]["action"], "unchanged")

    def test_旧记录没有content_hash时按本地已改处理(self):
        # #9 写的记录没有 content_hash，无法确认本地是否改过，宁可报冲突也不覆盖
        self.write_skill(PATH_KM, "生成的内容\n")
        metadata = {
            "last_sync": "2026-10-24T08:00:00Z",
            "skills": [
                {
                    "notion_page_id": PAGE,
                    "skill_path": PATH_KM,
                    "last_sync": "2026-10-24T08:00:00Z",
                }
            ],
        }
        (self.repo / "sync-metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        items = self.plan([self.executable("2026-10-24T09:30:00.000Z")])

        self.assertEqual(items[PATH_KM]["action"], "conflict")

    def test_页面被删除时列为待删除(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM)

        items = self.plan([{"notion_page_id": PAGE, "state": "deleted"}])

        self.assertEqual(items[PATH_KM]["action"], "delete_candidate")
        self.assertEqual(items[PATH_KM]["reason"], "deleted")
        self.assertFalse(items[PATH_KM]["local_changed"])

    def test_页面无权访问时跳过而不是删除(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM)

        items = self.plan([{"notion_page_id": PAGE, "state": "inaccessible"}])

        self.assertEqual(items[PATH_KM]["action"], "skipped")

    def test_本地文件被删掉后Notion又改了时报冲突(self):
        # 用户手动删掉 skill 也是一种本地修改，不能直接重新生成
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM, synced_at="2026-10-24T08:00:00Z")
        (self.repo / PATH_KM).unlink()

        items = self.plan([self.executable("2026-10-24T09:30:00.000Z")])

        self.assertEqual(items[PATH_KM]["action"], "conflict")

    def test_页面新增领域标签时只给新领域生成副本(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.record(PATH_KM, synced_at="2026-10-24T08:00:00Z")

        items = self.plan(
            [self.executable("2026-10-24T09:30:00.000Z", skill_paths=(PATH_KM, PATH_SD))]
        )

        self.assertEqual(items[PATH_SD]["action"], "new")
        self.assertEqual(items[PATH_KM]["action"], "update")

    def test_页面去掉领域标签时把那个副本列为待删除(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.write_skill(PATH_SD, "生成的内容\n")
        self.record(PATH_KM)
        self.record(PATH_SD)

        items = self.plan(
            [self.executable("2026-10-24T07:00:00.000Z", skill_paths=(PATH_KM,))]
        )

        self.assertEqual(items[PATH_KM]["action"], "unchanged")
        self.assertEqual(items[PATH_SD]["action"], "delete_candidate")
        self.assertEqual(items[PATH_SD]["reason"], "domain_removed")

    def metadata(self):
        return json.loads((self.repo / "sync-metadata.json").read_text(encoding="utf-8"))

    def test_record重复写入同一路径时替换旧记录(self):
        self.write_skill(PATH_KM, "第一版\n")
        self.record(PATH_KM, synced_at="2026-10-24T08:00:00Z")
        self.write_skill(PATH_KM, "第二版\n")
        self.record(PATH_KM, synced_at="2026-10-24T10:00:00Z")

        meta = self.metadata()

        self.assertEqual(meta["last_sync"], "2026-10-24T10:00:00Z")
        self.assertEqual(len(meta["skills"]), 1)
        entry = meta["skills"][0]
        self.assertEqual(entry["last_sync"], "2026-10-24T10:00:00Z")
        # 「第二版\n」的 git blob 哈希，由 `printf '第二版\n' | git hash-object --stdin` 事先算出
        self.assertEqual(entry["content_hash"], "5f7c5209972fdb8db1d665895a432e8f733c79bc")

    def test_remove只删除指定路径的记录(self):
        self.write_skill(PATH_KM, "生成的内容\n")
        self.write_skill(PATH_SD, "生成的内容\n")
        self.record(PATH_KM)
        self.record(PATH_SD)

        self.run_cli("remove", "--skill-path", PATH_SD)

        paths = [r["skill_path"] for r in self.metadata()["skills"]]
        self.assertEqual(paths, [PATH_KM])


if __name__ == "__main__":
    unittest.main()
