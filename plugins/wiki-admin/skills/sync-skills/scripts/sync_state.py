#!/usr/bin/env python3
"""sync-skills 的同步状态判定：对比 Notion 页面状态和 sync-metadata.json，决定每个 skill 副本怎么处理。"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

METADATA = "sync-metadata.json"


def load_metadata(repo):
    path = repo / METADATA
    if not path.exists():
        return {"last_sync": None, "skills": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_metadata(repo, metadata):
    text = json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
    (repo / METADATA).write_text(text, encoding="utf-8")


def parse_time(value):
    # Notion 返回 2026-10-24T09:30:00.000Z，Python 3.9 的 fromisoformat 不认 Z
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def content_hash(repo, skill_path):
    """文件内容的 git blob 哈希；文件不存在时返回 None。"""
    if not (repo / skill_path).is_file():
        return None
    result = subprocess.run(
        ["git", "hash-object", skill_path],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def local_changed(repo, rec):
    """本地文件和上次同步写入的内容不同。

    旧记录没有 content_hash、或文件已被删掉时无法确认，按已改处理，避免覆盖。
    两者都缺时不能当成「相等」。
    """
    expected = rec.get("content_hash")
    current = content_hash(repo, rec["skill_path"])
    if expected is None or current is None:
        return True
    return current != expected


def plan(repo, pages):
    records = {r["skill_path"]: r for r in load_metadata(repo)["skills"]}
    pages_by_id = {p["notion_page_id"]: p for p in pages}
    items = []
    claimed = set()  # (skill_path, 页面 ID)：这次被所属页面认领的记录
    assigned = {}  # skill_path -> 页面 ID：这次已经分给某个页面的路径
    for page in pages:
        if page["state"] != "executable":
            continue
        page_id = page["notion_page_id"]
        for skill_path in page["skill_paths"]:
            item = {"skill_path": skill_path, "notion_page_id": page_id}
            rec = records.get(skill_path)
            owner = rec["notion_page_id"] if rec else assigned.get(skill_path, page_id)
            if owner != page_id:
                # 路径已经属于另一个页面（有记录，或本次先分给了别的页面），不能拿来覆盖
                item["action"] = "path_occupied"
                items.append(item)
                continue
            assigned[skill_path] = page_id
            claimed.add((skill_path, page_id))
            if rec is None:
                # 没有记录但文件已存在：多半是用户自己写的 skill，不覆盖
                item["action"] = "path_occupied" if (repo / skill_path).exists() else "new"
                items.append(item)
                continue
            notion_dirty = parse_time(page["last_edited"]) > parse_time(rec["last_sync"])
            local_dirty = local_changed(repo, rec)
            if notion_dirty and local_dirty:
                item["action"] = "conflict"
            elif notion_dirty:
                item["action"] = "update"
            elif local_dirty:
                item["action"] = "local_only"
            else:
                item["action"] = "unchanged"
            items.append(item)

    # 有记录、但这次没有被任何可执行页面认领的副本：对应页面已删除、不再可执行，或去掉了这个领域标签
    for skill_path, rec in records.items():
        if (skill_path, rec["notion_page_id"]) in claimed:
            continue
        page = pages_by_id.get(rec["notion_page_id"])
        item = {"skill_path": skill_path, "notion_page_id": rec["notion_page_id"]}
        if page and page["state"] == "inaccessible":
            # 读不到页面不代表页面没了，不能据此删除（spec §3.5：跳过并在汇报中列出）
            item["action"] = "skipped"
        else:
            item["action"] = "delete_candidate"
            if page is None:
                item["reason"] = "not_listed"
            elif page["state"] == "executable":
                # 页面还在、仍可执行，只是不再认领这个副本：去掉了对应的领域标签
                item["reason"] = "domain_removed"
            else:
                item["reason"] = page["state"]
            item["local_changed"] = local_changed(repo, rec)
        items.append(item)
    return {"items": items}


def record(repo, page_id, skill_path, synced_at):
    """写入或替换一条同步记录，content_hash 取文件当前内容。"""
    digest = content_hash(repo, skill_path)
    if digest is None:
        # 没有文件就记一条 content_hash 为空的记录，下次会被当成「本地已改」，所以直接报错
        sys.exit(f"错误：{skill_path} 不存在，先写文件再 record")
    metadata = load_metadata(repo)
    entry = {
        "notion_page_id": page_id,
        "skill_path": skill_path,
        "last_sync": synced_at,
        "content_hash": digest,
    }
    others = [r for r in metadata["skills"] if r["skill_path"] != skill_path]
    metadata["skills"] = others + [entry]
    metadata["last_sync"] = synced_at
    save_metadata(repo, metadata)


def remove(repo, skill_path):
    """删除一条同步记录。只改 sync-metadata.json，不删文件：删文件要用户同意后由 skill 另做。"""
    metadata = load_metadata(repo)
    metadata["skills"] = [r for r in metadata["skills"] if r["skill_path"] != skill_path]
    save_metadata(repo, metadata)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_plan = sub.add_parser("plan", help="输出每个 skill 副本的处理动作")
    p_plan.add_argument("--pages", required=True, help="Notion 页面状态 JSON 文件")
    p_plan.add_argument("--repo", default=".", help="agent-brain 仓库根目录")
    p_record = sub.add_parser("record", help="写入一个 skill 副本的同步记录")
    p_record.add_argument("--page-id", required=True, help="带连字符的 Notion 页面 ID")
    p_record.add_argument("--skill-path", required=True, help="相对仓库根目录的 SKILL.md 路径")
    p_record.add_argument("--synced-at", required=True, help="UTC ISO 时间")
    p_record.add_argument("--repo", default=".", help="agent-brain 仓库根目录")
    p_remove = sub.add_parser("remove", help="删除一个 skill 副本的同步记录")
    p_remove.add_argument("--skill-path", required=True, help="相对仓库根目录的 SKILL.md 路径")
    p_remove.add_argument("--repo", default=".", help="agent-brain 仓库根目录")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    if args.command == "plan":
        pages = json.loads(Path(args.pages).read_text(encoding="utf-8"))["pages"]
        json.dump(plan(repo, pages), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif args.command == "record":
        record(repo, args.page_id, args.skill_path, args.synced_at)
    elif args.command == "remove":
        remove(repo, args.skill_path)


if __name__ == "__main__":
    main()
