"""Notion MCP Client 测试"""

import time
import pytest
from unittest.mock import Mock, patch
from agent_brain.notion_client import NotionClient, NotionClientError


class TestNotionClient:
    """Notion Client 测试"""

    def test_初始化时验证token存在(self):
        """初始化时应该检查 token 是否存在"""
        with pytest.raises(ValueError, match="NOTION_TOKEN"):
            NotionClient(token=None)

        with pytest.raises(ValueError, match="NOTION_TOKEN"):
            NotionClient(token="")

    def test_初始化时创建速率控制器(self):
        """初始化时应该创建速率控制器"""
        client = NotionClient(token="secret_test", rate_limit=5)
        assert client.rate_limiter is not None
        assert client.rate_limiter.rate == 5

    @patch('requests.request')
    def test_验证连接成功(self, mock_request):
        """验证连接应该调用 Notion API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "user", "id": "test-user"}
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")
        result = client.verify_connection()

        assert result is True
        mock_request.assert_called_once()
        # 检查请求头
        call_args = mock_request.call_args
        assert call_args[1]['headers']['Authorization'] == "Bearer secret_test"
        assert call_args[1]['headers']['Notion-Version'] == "2022-06-28"

    @patch('requests.request')
    def test_验证连接失败时抛出异常(self, mock_request):
        """API 返回错误时应该抛出 NotionClientError"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.content = b'{"message": "Unauthorized"}'
        mock_response.json.return_value = {"message": "Unauthorized"}
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_invalid")

        with pytest.raises(NotionClientError, match="401"):
            client.verify_connection()

    @patch('requests.request')
    def test_读取页面成功(self, mock_request):
        """读取页面应该返回页面内容"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "page",
            "id": "page-123",
            "properties": {
                "title": {
                    "title": [{"plain_text": "测试页面"}]
                }
            }
        }
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")
        page = client.get_page("page-123")

        assert page["id"] == "page-123"
        assert page["object"] == "page"

    @patch('requests.request')
    def test_读取不存在的页面抛出异常(self, mock_request):
        """读取不存在的页面应该抛出 NotionClientError"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = b'{"message": "Page not found"}'
        mock_response.json.return_value = {"message": "Page not found"}
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")

        with pytest.raises(NotionClientError, match="404"):
            client.get_page("invalid-id")

    @patch('requests.request')
    def test_速率限制自动生效(self, mock_request):
        """批量请求时速率控制器应该自动限速"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"object": "page", "id": "test"}
        mock_request.return_value = mock_response

        # 创建一个速率很低的 client
        client = NotionClient(token="secret_test", rate_limit=2)

        start = time.time()

        # 连续发起 5 次请求
        for i in range(5):
            client.get_page(f"page-{i}")

        elapsed = time.time() - start

        # 前 2 次立即通过，后 3 次需要等待
        # 应该至少需要 1 秒（3 个请求 / 2 每秒 = 1.5 秒）
        assert elapsed >= 1.0

    @patch('requests.request')
    def test_网络错误时抛出异常(self, mock_request):
        """网络错误时应该抛出 NotionClientError"""
        import requests
        mock_request.side_effect = requests.exceptions.RequestException("Network error")

        client = NotionClient(token="secret_test")

        with pytest.raises(NotionClientError, match="网络请求失败"):
            client.get_page("page-123")

    @patch('requests.request')
    def test_搜索页面成功(self, mock_request):
        """搜索页面应该返回匹配结果"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"object": "page", "id": "page-1"},
                {"object": "page", "id": "page-2"}
            ]
        }
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")
        results = client.search_pages("测试关键词")

        assert len(results) == 2
        assert results[0]["id"] == "page-1"
        # 验证请求参数
        call_args = mock_request.call_args
        assert call_args[1]['json']['query'] == "测试关键词"

    @patch('requests.request')
    def test_创建数据库成功(self, mock_request):
        """创建数据库应该返回数据库对象"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "database",
            "id": "db-123",
            "url": "https://notion.so/db-123",
            "title": [{"type": "text", "text": {"content": "测试数据库"}, "plain_text": "测试数据库"}]
        }
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")
        db = client.create_database(
            parent_id="page-123",
            title="测试数据库",
            properties={"Name": {"title": {}}}
        )

        assert db["id"] == "db-123"
        assert db["title"] == "测试数据库"
        assert db["url"] == "https://notion.so/db-123"

    @patch('requests.request')
    def test_创建数据库时标题为空(self, mock_request):
        """创建数据库时 API 返回空标题应该正常处理"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "database",
            "id": "db-123",
            "url": "https://notion.so/db-123",
            "title": []  # 空标题数组
        }
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")
        db = client.create_database(
            parent_id="page-123",
            title="测试",
            properties={"Name": {"title": {}}}
        )

        assert db["title"] == ""  # 应该返回空字符串而不是崩溃

    @patch('requests.request')
    def test_简化创建页面成功(self, mock_request):
        """create_page_simple 应该简化页面创建"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "object": "page",
            "id": "page-456",
            "url": "https://notion.so/page-456",
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": "新页面"}, "plain_text": "新页面"}]
                }
            }
        }
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")
        page = client.create_page_simple(
            title="新页面",
            parent_id="parent-123",
            content="这是测试内容"
        )

        assert page["id"] == "page-456"
        assert page["title"] == "新页面"
        assert page["url"] == "https://notion.so/page-456"

    def test_简化创建页面必须指定父页面(self):
        """internal integration 不能在 workspace 顶层建页面"""
        client = NotionClient(token="secret_test")
        with pytest.raises(ValueError, match="parent_id"):
            client.create_page_simple(title="x", parent_id="")

    @patch('requests.request')
    def test_简化创建页面使用正确的请求格式(self, mock_request):
        """父级是 page_id，标题放在 properties.title.title 里"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "p-1", "url": "u", "properties": {}}
        mock_request.return_value = mock_response

        NotionClient(token="secret_test").create_page_simple(title="标题", parent_id="abc-def")

        payload = mock_request.call_args[1]['json']
        assert payload["parent"] == {"type": "page_id", "page_id": "abcdef"}
        assert payload["properties"]["title"]["title"][0]["text"]["content"] == "标题"

    @patch('requests.request')
    def test_归档页面(self, mock_request):
        """archive_page 应该 PATCH archived=true"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "p-1", "archived": True}
        mock_request.return_value = mock_response

        NotionClient(token="secret_test").archive_page("p-1")

        call_args = mock_request.call_args[1]
        assert call_args['method'] == "PATCH"
        assert call_args['url'].endswith("/pages/p1")
        assert call_args['json'] == {"archived": True}

    @patch('requests.request')
    def test_JSON解析错误时抛出NotionClientError(self, mock_request):
        """响应不是有效 JSON 时应该抛出 NotionClientError"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"<html>Server Error</html>"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")

        with pytest.raises(NotionClientError, match="无法解析响应 JSON"):
            client.get_page("page-123")

    @patch('requests.request')
    def test_204响应正常处理(self, mock_request):
        """204 No Content 响应应该返回空字典"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.content = b""
        mock_request.return_value = mock_response

        client = NotionClient(token="secret_test")
        result = client._request("DELETE", "/blocks/block-123")

        assert result == {}

