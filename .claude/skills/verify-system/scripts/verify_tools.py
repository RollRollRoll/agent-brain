#!/usr/bin/env python3
"""verify-system 的辅助命令：静态检查、生成性能测试样本、汇总验证报告。"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# spec §4.5 的凭据模式；spec 本身和本脚本、本脚本的测试里写着这些模式，不算泄露
CREDENTIAL_PATTERN = r"ntn_|secret_|NOTION_TOKEN"
CREDENTIAL_EXCLUDES = [
    ":!SPEC-LLM-WIKI-SYSTEM.md",
    ":!.claude/skills/verify-system/",
    ":!tests/verify_system/",
]


def check_credentials(repo):
    """VAL-014：仓库里没有 Notion 凭据。"""
    result = subprocess.run(
        # --untracked：还没 git add 的新文件也查，被 .gitignore 忽略的（如 .env）不查
        ["git", "grep", "--untracked", "-nE", CREDENTIAL_PATTERN, "--", *CREDENTIAL_EXCLUDES],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    # git grep 没有匹配时返回 1
    hits = [line for line in result.stdout.splitlines() if line]
    problems = []
    if hits:
        problems.append("发现疑似凭据：" + "；".join(hits))
    # 和 spec 的 grep -x '.env' .gitignore 一致：要有一整行是 .env
    gitignore = repo / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.is_file() else []
    if ".env" not in (line.strip() for line in lines):
        problems.append(".gitignore 没有 .env 这一行")
    if problems:
        return {"id": "VAL-014", "status": "fail", "evidence": "；".join(problems)}
    return {"id": "VAL-014", "status": "pass", "evidence": "git grep 无匹配；.gitignore 包含 .env"}


def check_rate_limit(repo):
    """VAL-015：每个调用 notion-* 的 SKILL.md 都写了限流处理。

    写法和 tests/skill_docs 的检查一致：提到 rate_limited，并写明按 retry_after_seconds 等待重试，
    或引用 Notion 工具使用约定（notion-tools.md）。
    """
    skills = sorted(repo.glob("plugins/*/skills/*/SKILL.md")) + sorted(
        repo.glob(".claude/skills/*/SKILL.md")
    )
    checked, missing = [], []
    for path in skills:
        text = path.read_text(encoding="utf-8")
        if "notion-" not in text:
            continue
        rel = path.relative_to(repo).as_posix()
        checked.append(rel)
        if "rate_limited" not in text or not (
            "retry_after_seconds" in text or "notion-tools.md" in text
        ):
            missing.append(rel)
    if missing:
        return {"id": "VAL-015", "status": "fail", "evidence": "没有写限流处理：" + "、".join(missing)}
    return {
        "id": "VAL-015",
        "status": "pass",
        "evidence": f"检查了 {len(checked)} 个调用 notion-* 的 SKILL.md，都写了限流处理",
    }


def technique_page(prefix, index):
    """一个满足 sync-skills「可执行」判定的 technique 样本：有步骤、所需工具、前置条件，每步 agent 都能执行。"""
    title = f"{prefix} {index:02d}"
    body = "\n".join(
        [
            "## 前置条件",
            "",
            "- 用户给出的文本文件存在且可读",
            "",
            "## 所需工具",
            "",
            "- `wc`",
            "",
            "## 步骤",
            "",
            "1. 运行 `wc -w < <文件路径>`，取输出的数字",
            f"2. 告诉用户文件路径和词数，并注明结果来自「{title}」",
            "",
            "## 出处",
            "",
            "- verify-system 生成的性能测试样本（VAL-017），验证结束后删除",
        ]
    )
    return {
        "标题": title,
        "分类": "techniques",
        "领域标签": ["软件开发"],
        "简短摘要": f"统计文本文件的词数（VAL-017 性能样本 {index:02d}）。",
        "正文": body,
    }


def cmd_techniques(args):
    pages = [technique_page(args.prefix, i) for i in range(1, args.count + 1)]
    json.dump({"pages": pages}, sys.stdout, ensure_ascii=False, indent=2)
    print()


# spec §2.3 的性能门槛（秒），严格小于才算通过
THRESHOLDS = {
    "VAL-016": ("QOS-001", 30),
    "VAL-017": ("QOS-002", 300),
    "VAL-018": ("QOS-003", 10),
}


def judge_performance(item):
    """按门槛重新判定性能项；填入的 status 不作数。"""
    qos, limit = THRESHOLDS[item["id"]]
    seconds = item.get("seconds")
    item = dict(item)
    if not isinstance(seconds, (int, float)):
        item["status"] = "fail"
        item["evidence"] = f"{item.get('evidence', '')}；没有记录耗时，无法按 {qos} 门槛 < {limit} 秒判定"
        return item
    ok = seconds < limit
    item["status"] = "pass" if ok else "fail"
    item["evidence"] = f"{item.get('evidence', '')}；实测 {seconds} 秒，{qos} 门槛 < {limit} 秒"
    return item


# VAL-019 要求 VAL-001 ~ VAL-018 每一项都有结果
REQUIRED = [f"VAL-{n:03d}" for n in range(1, 19)]


def build_report(items):
    """补齐缺项、判定性能门槛，再按 VAL-001 ~ VAL-018 判定 VAL-019。"""
    by_id = {}
    for item in items:
        by_id[item["id"]] = judge_performance(item) if item["id"] in THRESHOLDS else item
    for val_id in REQUIRED:
        if val_id not in by_id:
            by_id[val_id] = {"id": val_id, "status": "fail", "evidence": "没有结果：这一项没有运行或没有记录"}

    not_passed = [v for v in REQUIRED if by_id[v]["status"] != "pass"]
    if not_passed:
        by_id["VAL-019"] = {
            "id": "VAL-019",
            "status": "fail",
            "evidence": "未通过：" + "、".join(f"{v}（{by_id[v]['status']}）" for v in not_passed),
        }
    else:
        by_id["VAL-019"] = {"id": "VAL-019", "status": "pass", "evidence": "VAL-001 ~ VAL-018 全部通过"}

    results = [by_id[k] for k in sorted(by_id)]
    summary = {s: sum(1 for r in results if r["status"] == s) for s in ("pass", "fail", "skip")}
    return {"results": results, "summary": summary}


def cmd_report(args):
    data = json.loads(Path(args.results).read_text(encoding="utf-8"))
    json.dump(build_report(data["results"]), sys.stdout, ensure_ascii=False, indent=2)
    print()


def cmd_static(args):
    repo = Path(args.repo)
    results = [check_credentials(repo), check_rate_limit(repo)]
    json.dump({"results": results}, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_static = sub.add_parser("static", help="VAL-014 / VAL-015 静态检查")
    p_static.add_argument("--repo", default=".")
    p_static.set_defaults(func=cmd_static)

    p_tech = sub.add_parser("techniques", help="生成 VAL-017 的 technique 样本页")
    p_tech.add_argument("--count", type=int, default=50)
    p_tech.add_argument("--prefix", default="性能样本")
    p_tech.set_defaults(func=cmd_techniques)

    p_report = sub.add_parser("report", help="汇总各 VAL 项结果，判定性能门槛和 VAL-019")
    p_report.add_argument("--results", required=True, help="各 VAL 项结果的 JSON 文件")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
