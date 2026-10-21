"""/init-wiki 命令

在已授权的父页面下创建 LLM Wiki 结构。

Claude Code 里运行脚本时没有交互式 stdin，所以“是否覆盖？”这个确认交给 agent：
脚本发现已有结构就以退出码 2 结束，agent 问过用户、得到明确同意后再带 --overwrite 重跑。
"""

import argparse
import os
import sys
from typing import Callable, List, Optional, TextIO

from .notion_client import NotionClient, NotionClientError
from .wiki_structure import WikiStructure, WikiStructureExistsError

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_EXISTS = 2


def run(
    argv: List[str],
    env: dict,
    client_factory: Callable[[str], NotionClient] = NotionClient,
    out: TextIO = sys.stdout,
) -> int:
    """执行 /init-wiki，返回退出码

    Args:
        argv: 命令行参数（不含程序名）
        env: 环境变量（读取 NOTION_TOKEN、NOTION_PARENT_PAGE_ID）
        client_factory: 用 token 创建 NotionClient，测试时可替换
        out: 输出流
    """
    parser = argparse.ArgumentParser(prog="init-wiki", description="初始化 Notion Wiki 结构")
    parser.add_argument("--parent", help="已授权页面的 ID，默认读 NOTION_PARENT_PAGE_ID")
    parser.add_argument("--overwrite", action="store_true",
                        help="已存在结构时，归档旧结构后重建（需用户明确确认）")
    args = parser.parse_args(argv)

    token = env.get("NOTION_TOKEN")
    if not token:
        print("❌ 未设置 NOTION_TOKEN，请在 .env 中配置", file=out)
        return EXIT_ERROR

    parent_id: Optional[str] = args.parent or env.get("NOTION_PARENT_PAGE_ID")
    if not parent_id:
        print("❌ 未指定父页面。请在 .env 中设置 NOTION_PARENT_PAGE_ID，"
              "或用 --parent 传入已授权给 Integration 的页面 ID", file=out)
        return EXIT_ERROR

    try:
        client = client_factory(token)
        client.verify_connection()
        result = WikiStructure(client, parent_id).init(overwrite=args.overwrite)
    except WikiStructureExistsError as e:
        print("⚠️  Wiki 结构已存在，是否覆盖？", file=out)
        print(f"   现有页面: {e.root_page.get('url') or e.root_page['id']}", file=out)
        print("   覆盖会把旧结构移入 Notion 回收站（可恢复）。"
              "确认后用 --overwrite 重新运行。", file=out)
        return EXIT_EXISTS
    except (NotionClientError, ValueError) as e:
        print(f"❌ 初始化失败: {e}", file=out)
        return EXIT_ERROR

    if result["archived"]:
        print(f"🗑️  已归档旧结构: {result['archived'].get('url') or result['archived']['id']}", file=out)
    root = result["root_page"]
    print(f"✅ 初始化完成\n\n📄 {root['title']}: {root['url']}\n\n🗄️  数据库:", file=out)
    for name, db in result["databases"].items():
        print(f"   - {name}: {db['url']}", file=out)
    print("\n📁 分类页面:", file=out)
    for cat in result["categories"]:
        print(f"   - {cat['title']}: {cat['url']}", file=out)
    print("\n💡 Board / Gallery 视图需要在 Notion 中手动添加（API 不支持创建视图）", file=out)
    return EXIT_OK


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    sys.exit(run(sys.argv[1:], dict(os.environ)))


if __name__ == "__main__":
    main()
