#!/usr/bin/env python3
"""测试 Notion API 连接

验证 token 有效性并可选读取测试页面。
"""

import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from agent_brain.notion_client import NotionClient, NotionClientError


def extract_page_title(page_data: dict) -> str:
    """从页面数据中提取标题"""
    try:
        properties = page_data.get("properties", {})

        # 尝试多种标题字段名
        for title_key in ["title", "Title", "Name", "名称"]:
            if title_key in properties:
                title_prop = properties[title_key]

                # title 类型
                if title_prop.get("type") == "title":
                    title_items = title_prop.get("title", [])
                    if title_items:
                        return title_items[0].get("plain_text", "无标题")

        return "无标题"
    except Exception:
        return "无法提取标题"


def main():
    """主函数"""
    # 加载环境变量
    load_dotenv()

    token = os.getenv("NOTION_TOKEN")

    if not token:
        print("❌ 错误：未找到 NOTION_TOKEN")
        print()
        print("请在 .env 文件中配置:")
        print("  NOTION_TOKEN=secret_your_token_here")
        print()
        print("获取 token: https://www.notion.so/my-integrations")
        return 1

    print("🔍 测试 Notion API 连接...")
    print()

    try:
        # 创建 client
        client = NotionClient(token=token)

        # 验证连接
        print("1️⃣ 验证连接...")
        client.verify_connection()
        print("   ✅ 连接成功！")
        print()

        # 如果提供了 page_id，尝试读取
        if len(sys.argv) > 1:
            page_id = sys.argv[1].replace("page_id=", "")

            print(f"2️⃣ 读取测试页面: {page_id}")
            page = client.get_page(page_id)

            title = extract_page_title(page)

            print(f"   ✅ 页面读取成功！")
            print(f"   标题: {title}")
            print(f"   ID: {page['id']}")
            print()

        print("=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
        return 0

    except NotionClientError as e:
        print(f"❌ 连接失败: {str(e)}")
        print()
        print("常见问题:")
        print("  - Token 是否有效？")
        print("  - Integration 是否已分享给要访问的页面？")
        print("  - 网络是否正常？")
        return 1
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
