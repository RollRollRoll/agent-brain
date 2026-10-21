"""WikiStructure 测试"""

from unittest.mock import Mock

import pytest

from agent_brain.wiki_structure import (
    DATABASE_SCHEMAS,
    ROOT_TITLE,
    WikiStructure,
    WikiStructureExistsError,
    build_properties,
)


def _page(page_id, title, archived=False):
    """构造 Notion search 返回的页面对象"""
    return {
        "id": page_id,
        "url": f"https://notion.so/{page_id}",
        "archived": archived,
        "properties": {"title": {"type": "title", "title": [{"plain_text": title}]}},
    }


@pytest.fixture
def client():
    mock = Mock()
    mock.search_pages.return_value = []
    mock.create_page_simple.side_effect = lambda title, parent_id, content=None: {
        "id": f"page-{title}", "url": f"https://notion.so/{title}", "title": title
    }
    mock.create_database.side_effect = lambda parent_id, title, properties: {
        "id": f"db-{title}", "url": f"https://notion.so/db-{title}", "title": title
    }
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

    def test_relation填入真实数据库ID(self):
        props = build_properties("Conflicts", {"Sources": "s-1", "Wiki Index": "w-1"})
        assert props["新材料"]["relation"]["database_id"] == "s-1"
        assert props["Wiki 页面"]["relation"]["database_id"] == "w-1"
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
        assert result["archived"] is None
        client.archive_page.assert_not_called()

    def test_relation关联到前面创建的数据库(self, client):
        WikiStructure(client, "parent-1").init()
        calls = {c.kwargs["title"]: c.kwargs["properties"] for c in client.create_database.call_args_list}
        assert calls["Wiki Changelog"]["来源材料"]["relation"]["database_id"] == "db-Sources"
        assert calls["Wiki Changelog"]["Wiki 页面"]["relation"]["database_id"] == "db-Wiki Index"

    def test_已存在时不覆盖并报告(self, client):
        client.search_pages.return_value = [_page("old-1", ROOT_TITLE)]

        with pytest.raises(WikiStructureExistsError) as exc:
            WikiStructure(client, "parent-1").init()

        assert exc.value.root_page["id"] == "old-1"
        client.create_page_simple.assert_not_called()
        client.create_database.assert_not_called()
        client.archive_page.assert_not_called()

    def test_确认覆盖时先归档再重建(self, client):
        client.search_pages.return_value = [_page("old-1", ROOT_TITLE)]

        result = WikiStructure(client, "parent-1").init(overwrite=True)

        client.archive_page.assert_called_once_with("old-1")
        assert result["archived"]["id"] == "old-1"
        assert client.create_database.call_count == 5

    def test_搜索结果标题不完全匹配时视为不存在(self, client):
        client.search_pages.return_value = [_page("x", "LLM Wiki 系统（旧版笔记）")]
        assert WikiStructure(client, "parent-1").find_existing() is None

    def test_已归档的页面视为不存在(self, client):
        client.search_pages.return_value = [_page("x", ROOT_TITLE, archived=True)]
        assert WikiStructure(client, "parent-1").find_existing() is None
