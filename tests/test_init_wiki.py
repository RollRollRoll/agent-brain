"""/init-wiki 命令测试：在命令入口这一层验证可观察输出和退出码"""

import io
from unittest.mock import Mock

from agent_brain.init_wiki import EXIT_ERROR, EXIT_EXISTS, EXIT_OK, run
from agent_brain.notion_client import NotionClientError
from agent_brain.wiki_structure import DATABASE_SCHEMAS, ROOT_TITLE

ENV = {"NOTION_TOKEN": "secret_test", "NOTION_PARENT_PAGE_ID": "parent-1"}


def _data_source(ds_id):
    db_name = ds_id[len("ds-"):]
    return {"id": ds_id, "properties": {
        name: {"id": f"id-{name}", "name": name}
        for name in DATABASE_SCHEMAS[db_name]["properties"]
    }}


def _client(existing=False):
    client = Mock()
    client.verify_connection.return_value = True
    client.search_pages.return_value = [{
        "id": "old-1",
        "url": "https://notion.so/old-1",
        "properties": {"title": {"type": "title", "title": [{"plain_text": ROOT_TITLE}]}},
    }] if existing else []
    client.create_page_simple.side_effect = lambda title, parent_id, content=None: {
        "id": f"page-{title}", "url": f"https://notion.so/{title}", "title": title
    }
    client.create_database.side_effect = lambda parent_id, title, properties: {
        "id": f"db-{title}", "data_source_id": f"ds-{title}",
        "url": f"https://notion.so/db-{title}", "title": title
    }
    client.get_data_source.side_effect = _data_source
    client.create_view.return_value = {"object": "view", "id": "v-1"}
    return client


def _run(argv, env=ENV, client=None):
    out = io.StringIO()
    client = client or _client()
    code = run(argv, env, client_factory=lambda token: client, out=out)
    return code, out.getvalue(), client


def test_首次初始化成功并输出所有链接():
    code, output, _ = _run([])
    assert code == EXIT_OK
    assert "https://notion.so/LLM Wiki 系统" in output
    for name in ["Sources", "Wiki Index", "Agent Tasks", "Wiki Changelog", "Conflicts"]:
        assert f"https://notion.so/db-{name}" in output
    for cat in ["concepts/", "techniques/", "tools/"]:
        assert cat in output
    assert "Sources / 按状态（board）" in output
    assert "Wiki Index / 知识卡片（gallery）" in output
    assert "手动添加" not in output


def test_视图失败时仍成功并提示手动添加():
    client = _client()
    client.create_view.side_effect = NotionClientError("Notion API 错误 [400]: bad")
    code, output, _ = _run([], client=client)
    assert code == EXIT_OK
    assert "按状态 创建失败" in output
    assert "手动添加" in output


def test_已存在时提示是否覆盖且不做任何修改():
    code, output, client = _run([], client=_client(existing=True))
    assert code == EXIT_EXISTS
    assert "Wiki 结构已存在，是否覆盖？" in output
    assert "https://notion.so/old-1" in output
    client.create_page_simple.assert_not_called()
    client.trash_page.assert_not_called()


def test_带overwrite时旧结构移入回收站并重建():
    code, output, client = _run(["--overwrite"], client=_client(existing=True))
    assert code == EXIT_OK
    client.trash_page.assert_called_once_with("old-1")
    assert "旧结构已移入回收站" in output


def test_缺少token时报错():
    code, output, _ = _run([], env={"NOTION_PARENT_PAGE_ID": "parent-1"})
    assert code == EXIT_ERROR
    assert "NOTION_TOKEN" in output


def test_缺少父页面时报错():
    code, output, _ = _run([], env={"NOTION_TOKEN": "secret_test"})
    assert code == EXIT_ERROR
    assert "NOTION_PARENT_PAGE_ID" in output


def test_parent参数优先于环境变量():
    _, _, client = _run(["--parent", "parent-cli"])
    assert client.create_page_simple.call_args_list[0].kwargs["parent_id"] == "parent-cli"


def test_连接失败时报错():
    client = _client()
    client.verify_connection.side_effect = NotionClientError("Notion API 错误 [401]: invalid")
    code, output, _ = _run([], client=client)
    assert code == EXIT_ERROR
    assert "401" in output
    client.create_page_simple.assert_not_called()


def test_输出不包含token():
    _, output, _ = _run([])
    assert "secret_test" not in output
