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
