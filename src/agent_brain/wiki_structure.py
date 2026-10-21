"""
Notion Wiki 结构管理

负责初始化、检测和验证 Notion Wiki 的数据库和页面结构
"""
from typing import Any, Dict, List, Optional


ROOT_TITLE = "LLM Wiki 系统"
WIKI_CATEGORIES = ["concepts/", "techniques/", "tools/"]

# 数据库 Schema 定义
# relation 字段用 relation_target 写被关联数据库的名字，创建时再换成真实 ID；
# 字典顺序就是创建顺序，被关联的数据库必须排在前面。
DATABASE_SCHEMAS = {
    "Sources": {
        "properties": {
            "标题": {"type": "title"},
            "类型": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "文章"},
                        {"name": "视频"},
                        {"name": "图片"},
                        {"name": "项目"}
                    ]
                }
            },
            "链接": {"type": "url"},
            "状态": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "待处理"},
                        {"name": "处理中"},
                        {"name": "已入库"},
                        {"name": "已归档"}
                    ]
                }
            },
            "领域标签": {"type": "multi_select"},
            "添加时间": {"type": "created_time"}
        }
    },

    "Wiki Index": {
        "properties": {
            "标题": {"type": "title"},
            "分类": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "concepts"},
                        {"name": "techniques"},
                        {"name": "tools"}
                    ]
                }
            },
            "领域标签": {"type": "multi_select"},
            "简短摘要": {"type": "rich_text"},
            "最后更新时间": {"type": "last_edited_time"},
            "来源材料": {"type": "relation", "relation_target": "Sources"}
        }
    },

    "Agent Tasks": {
        "properties": {
            "任务名": {"type": "title"},
            "使用的 Skill": {"type": "rich_text"},
            "执行时间": {"type": "date"},
            "状态": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "成功"},
                        {"name": "失败"}
                    ]
                }
            },
            "结果摘要": {"type": "rich_text"},
            "失败原因": {"type": "rich_text"},
            "反馈/问题": {"type": "rich_text"}
        }
    },

    "Wiki Changelog": {
        "properties": {
            # Notion 要求每个数据库有且只有一个 title 字段
            "变更摘要": {"type": "title"},
            "Wiki 页面": {"type": "relation", "relation_target": "Wiki Index"},
            "变更时间": {"type": "created_time"},
            "来源材料": {"type": "relation", "relation_target": "Sources"},
            "变更类型": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "新建"},
                        {"name": "更新"},
                        {"name": "冲突解决"}
                    ]
                }
            },
            "详情": {"type": "rich_text"}
        }
    },

    "Conflicts": {
        "properties": {
            "冲突摘要": {"type": "title"},
            "Wiki 页面": {"type": "relation", "relation_target": "Wiki Index"},
            "冲突类型": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "事实性"},
                        {"name": "观点性"},
                        {"name": "时效性"},
                        {"name": "场景性"},
                        {"name": "深度性"},
                        {"name": "无法判断"}
                    ]
                }
            },
            "新材料": {"type": "relation", "relation_target": "Sources"},
            "原有内容摘要": {"type": "rich_text"},
            "新内容摘要": {"type": "rich_text"},
            "证据链接": {"type": "url"},
            "证据强度评分": {"type": "number", "number": {"format": "number"}},
            "状态": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "待审核"},
                        {"name": "待人工审核"},
                        {"name": "已解决"}
                    ]
                }
            },
            "解决方案": {"type": "rich_text"}
        }
    }
}


def build_properties(db_name: str, db_ids: Dict[str, str]) -> Dict[str, Any]:
    """把 schema 转成 Notion API 的属性定义

    Notion 的属性定义形如 {"类型名": {配置}}，relation 需要真实的 database_id。

    Args:
        db_name: 数据库名称
        db_ids: 已创建数据库的 名称 → ID 映射

    Raises:
        ValueError: 数据库名未知，或被关联的数据库还没创建
    """
    if db_name not in DATABASE_SCHEMAS:
        raise ValueError(f"未知的数据库名称: {db_name}")

    properties = {}
    for prop_name, spec in DATABASE_SCHEMAS[db_name]["properties"].items():
        prop_type = spec["type"]
        if prop_type == "relation":
            target = spec["relation_target"]
            if target not in db_ids:
                raise ValueError(f"{db_name}.{prop_name} 关联的数据库 {target} 尚未创建")
            properties[prop_name] = {
                "relation": {
                    "database_id": db_ids[target],
                    "type": "single_property",
                    "single_property": {}
                }
            }
        else:
            properties[prop_name] = {prop_type: spec.get(prop_type, {})}
    return properties


def _page_title(page: Dict[str, Any]) -> str:
    """从 Notion 页面对象中取出标题纯文本"""
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(item.get("plain_text", "") for item in prop.get("title", []))
    return ""


class WikiStructureExistsError(Exception):
    """授权页面下已存在 Wiki 结构"""

    def __init__(self, root_page: Dict[str, Any]):
        self.root_page = root_page
        super().__init__(f"Wiki 结构已存在: {root_page.get('url', root_page.get('id'))}")


class WikiStructure:
    """Notion Wiki 结构管理器

    Internal integration 不能在 workspace 顶层建页面，
    所以整个结构都建在用户手动授权的那个父页面下。
    """

    def __init__(self, notion_client, parent_page_id: str):
        """
        Args:
            notion_client: NotionClient 实例
            parent_page_id: 已授权给 Integration 的父页面 ID
        """
        if not parent_page_id:
            raise ValueError("parent_page_id 不能为空，请提供已授权给 Integration 的页面 ID")
        self.client = notion_client
        self.parent_page_id = parent_page_id

    def find_existing(self) -> Optional[Dict[str, Any]]:
        """查找已存在的 "LLM Wiki 系统" 页面

        搜索是模糊匹配，所以还要核对标题完全一致、且未归档。

        Returns:
            找到时返回 {"id", "url", "title"}，否则返回 None
        """
        for page in self.client.search_pages(ROOT_TITLE):
            if page.get("archived") or page.get("in_trash"):
                continue
            if _page_title(page) == ROOT_TITLE:
                return {"id": page["id"], "url": page.get("url", ""), "title": ROOT_TITLE}
        return None

    def create_root_page(self) -> Dict[str, Any]:
        """在授权页面下创建 "LLM Wiki 系统" 页面"""
        return self.client.create_page_simple(
            title=ROOT_TITLE,
            parent_id=self.parent_page_id,
            content="这是 Agent Brain 知识库的根页面，由 /init-wiki 创建。"
        )

    def create_database(self, parent_id: str, db_name: str, db_ids: Dict[str, str]) -> Dict[str, Any]:
        """在指定页面下创建数据库

        Args:
            parent_id: 父页面 ID
            db_name: 数据库名称（DATABASE_SCHEMAS 的 key）
            db_ids: 已创建数据库的 名称 → ID 映射，用于填充 relation
        """
        return self.client.create_database(
            parent_id=parent_id,
            title=db_name,
            properties=build_properties(db_name, db_ids)
        )

    def create_wiki_categories(self, parent_id: str) -> List[Dict[str, Any]]:
        """创建 concepts/、techniques/、tools/ 三个分类页面"""
        return [
            self.client.create_page_simple(
                title=category,
                parent_id=parent_id,
                content=f"{category} 类别的 Wiki 页面放在这里。"
            )
            for category in WIKI_CATEGORIES
        ]

    def init(self, overwrite: bool = False) -> Dict[str, Any]:
        """初始化完整的 Wiki 结构

        Args:
            overwrite: 已存在结构时，是否归档旧结构后重建

        Returns:
            {"root_page", "databases", "categories", "archived"}

        Raises:
            WikiStructureExistsError: 已存在结构且 overwrite=False
        """
        archived = None
        existing = self.find_existing()
        if existing:
            if not overwrite:
                raise WikiStructureExistsError(existing)
            # 归档根页面会连带归档子页面和数据库，可在 Notion 回收站恢复
            self.client.archive_page(existing["id"])
            archived = existing

        root_page = self.create_root_page()

        databases: Dict[str, Dict[str, Any]] = {}
        db_ids: Dict[str, str] = {}
        for db_name in DATABASE_SCHEMAS:
            db = self.create_database(root_page["id"], db_name, db_ids)
            databases[db_name] = db
            db_ids[db_name] = db["id"]

        categories = self.create_wiki_categories(root_page["id"])

        return {
            "root_page": root_page,
            "databases": databases,
            "categories": categories,
            "archived": archived
        }
