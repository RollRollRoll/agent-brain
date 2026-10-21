"""WikiStructure 测试"""

from unittest.mock import Mock

import pytest

from agent_brain.wiki_structure import (
    DATABASE_SCHEMAS,
    ROOT_TITLE,
    VIEW_SPECS,
    WikiStructure,
    WikiStructureExistsError,
    build_properties,
    build_view_configuration,
)
from agent_brain.notion_client import NotionClientError


def _page(page_id, title, in_trash=False):
    """构造 Notion search 返回的页面对象"""
    return {
        "id": page_id,
        "url": f"https://notion.so/{page_id}",
        "in_trash": in_trash,
        "properties": {"title": {"type": "title", "title": [{"plain_text": title}]}},
    }


def _data_source(ds_id):
    """按 schema 构造 Retrieve data source 的响应，属性 ID 为 "id-<属性名>" """
    db_name = ds_id[len("ds-"):]
    return {
        "object": "data_source",
        "id": ds_id,
        "properties": {
            name: {"id": f"id-{name}", "name": name, "type": spec["type"]}
            for name, spec in DATABASE_SCHEMAS[db_name]["properties"].items()
        },
    }


@pytest.fixture
def client():
    mock = Mock()
    mock.search_pages.return_value = []
    mock.create_page_simple.side_effect = lambda title, parent_id, content=None: {
        "id": f"page-{title}", "url": f"https://notion.so/{title}", "title": title
    }
    mock.create_database.side_effect = lambda parent_id, title, properties: {
        "id": f"db-{title}", "data_source_id": f"ds-{title}",
        "url": f"https://notion.so/db-{title}", "title": title
    }
    mock.get_data_source.side_effect = _data_source
    mock.create_view.return_value = {"object": "view", "id": "view-1"}
    return mock


class TestSchema:
    def test_包含五个数据库(self):
        assert list(DATABASE_SCHEMAS) == [
            "Sources", "Wiki Index", "Agent Tasks", "Wiki Changelog", "Conflicts"
        ]

    def test_每个数据库恰好一个title字段(self):
        for name, schema in DATABASE_SCHEMAS.items():
            titles = [p for p in schema["properties"].values() if p["type"] == "title"]
            assert len(titles) == 1, name

    def test_被关联的数据库排在前面(self):
        seen = []
        for name, schema in DATABASE_SCHEMAS.items():
            for prop in schema["properties"].values():
                if prop["type"] == "relation":
                    assert prop["relation_target"] in seen, name
            seen.append(name)

    def test_sources字段符合spec(self):
        props = build_properties("Sources", {})
        assert props["标题"] == {"title": {}}
        assert [o["name"] for o in props["状态"]["select"]["options"]] == [
            "待处理", "处理中", "已入库", "已归档"
        ]
        assert props["领域标签"] == {"multi_select": {}}
        assert props["添加时间"] == {"created_time": {}}

    def test_视图引用的属性都在schema里(self):
        for spec in VIEW_SPECS:
            props = DATABASE_SCHEMAS[spec["database"]]["properties"]
            for name in [spec.get("group_by")] + spec.get("show", []):
                if name:
                    assert name in props, (spec["database"], name)

    def test_board按select属性ID分组(self):
        config = build_view_configuration(VIEW_SPECS[0], {"状态": "abc"})
        assert config["type"] == "board"
        assert config["group_by"]["type"] == "select"
        assert config["group_by"]["property_id"] == "abc"

    def test_视图属性不存在时报错(self):
        with pytest.raises(ValueError, match="没有属性"):
            build_view_configuration(VIEW_SPECS[0], {})

    def test_relation填入真实数据库ID(self):
        props = build_properties("Conflicts", {"Sources": "s-1", "Wiki Index": "w-1"})
        assert props["新材料"]["relation"]["data_source_id"] == "s-1"
        assert props["Wiki 页面"]["relation"]["data_source_id"] == "w-1"
        assert props["Wiki 页面"]["relation"]["type"] == "single_property"

    def test_relation目标未创建时报错(self):
        with pytest.raises(ValueError, match="尚未创建"):
            build_properties("Wiki Index", {})

    def test_未知数据库报错(self):
        with pytest.raises(ValueError, match="未知"):
            build_properties("Nope", {})


class TestWikiStructure:
    def test_父页面为空时报错(self, client):
        with pytest.raises(ValueError, match="parent_page_id"):
            WikiStructure(client, "")

    def test_首次初始化创建完整结构(self, client):
        result = WikiStructure(client, "parent-1").init()

        # 根页面建在授权父页面下
        root_call = client.create_page_simple.call_args_list[0]
        assert root_call.kwargs["title"] == ROOT_TITLE
        assert root_call.kwargs["parent_id"] == "parent-1"

        assert list(result["databases"]) == list(DATABASE_SCHEMAS)
        assert [c["title"] for c in result["categories"]] == [
            "concepts/", "techniques/", "tools/"
        ]
        # 数据库和分类页面都挂在根页面下
        for call in client.create_database.call_args_list:
            assert call.kwargs["parent_id"] == f"page-{ROOT_TITLE}"
        assert result["trashed"] is None
        client.trash_page.assert_not_called()

    def test_relation关联到前面创建的数据库(self, client):
        WikiStructure(client, "parent-1").init()
        calls = {c.kwargs["title"]: c.kwargs["properties"] for c in client.create_database.call_args_list}
        assert calls["Wiki Changelog"]["来源材料"]["relation"]["data_source_id"] == "ds-Sources"
        assert calls["Wiki Changelog"]["Wiki 页面"]["relation"]["data_source_id"] == "ds-Wiki Index"

    def test_已存在时不覆盖并报告(self, client):
        client.search_pages.return_value = [_page("old-1", ROOT_TITLE)]

        with pytest.raises(WikiStructureExistsError) as exc:
            WikiStructure(client, "parent-1").init()

        assert exc.value.root_page["id"] == "old-1"
        client.create_page_simple.assert_not_called()
        client.create_database.assert_not_called()
        client.trash_page.assert_not_called()

    def test_确认覆盖时先移入回收站再重建(self, client):
        client.search_pages.return_value = [_page("old-1", ROOT_TITLE)]

        result = WikiStructure(client, "parent-1").init(overwrite=True)

        client.trash_page.assert_called_once_with("old-1")
        assert result["trashed"]["id"] == "old-1"
        assert client.create_database.call_count == 5

    def test_搜索结果标题不完全匹配时视为不存在(self, client):
        client.search_pages.return_value = [_page("x", "LLM Wiki 系统（旧版笔记）")]
        assert WikiStructure(client, "parent-1").find_existing() is None

    def test_回收站里的页面视为不存在(self, client):
        client.search_pages.return_value = [_page("x", ROOT_TITLE, in_trash=True)]
        assert WikiStructure(client, "parent-1").find_existing() is None

    def test_创建board和gallery视图(self, client):
        result = WikiStructure(client, "parent-1").init()

        calls = {c.kwargs["name"]: c.kwargs for c in client.create_view.call_args_list}
        board = calls["按状态"]
        assert board["database_id"] == "db-Sources"
        assert board["data_source_id"] == "ds-Sources"
        assert board["view_type"] == "board"
        assert board["configuration"]["group_by"]["property_id"] == "id-状态"

        gallery = calls["知识卡片"]
        assert gallery["database_id"] == "db-Wiki Index"
        assert gallery["view_type"] == "gallery"
        assert [p["property_id"] for p in gallery["configuration"]["properties"]] == [
            "id-分类", "id-领域标签", "id-简短摘要"
        ]

        assert [v["name"] for v in result["views"]["created"]] == ["按状态", "知识卡片"]
        assert result["views"]["failed"] == []

    def test_视图失败不影响其余结构(self, client):
        client.create_view.side_effect = [NotionClientError("Notion API 错误 [400]: bad"), {"id": "v"}]

        result = WikiStructure(client, "parent-1").init()

        assert len(result["databases"]) == 5
        assert len(result["categories"]) == 3
        assert [v["name"] for v in result["views"]["created"]] == ["知识卡片"]
        assert result["views"]["failed"][0]["name"] == "按状态"
        assert "400" in result["views"]["failed"][0]["error"]
