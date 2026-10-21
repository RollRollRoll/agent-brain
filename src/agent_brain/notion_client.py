"""Notion API Client

封装 Notion API 调用，提供速率控制和错误处理。
"""

import os
import requests
from typing import Optional, Dict, Any, List
from .rate_limiter import TokenBucketRateLimiter


class NotionClientError(Exception):
    """Notion Client 错误"""
    pass


class NotionClient:
    """Notion API Client

    功能：
    - Token 验证和管理
    - API 请求封装
    - 速率控制（Token Bucket）
    - 错误处理和重试

    使用示例：
        client = NotionClient(token=os.getenv("NOTION_TOKEN"))
        client.verify_connection()
        page = client.get_page("page-id-123")
    """

    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(
        self,
        token: Optional[str] = None,
        rate_limit: int = 3,
        api_version: str = API_VERSION
    ):
        """初始化 Notion Client

        Args:
            token: Notion Integration Token
            rate_limit: 每秒请求数限制（默认 3）
            api_version: Notion API 版本

        Raises:
            ValueError: token 为空
        """
        if not token:
            raise ValueError(
                "NOTION_TOKEN 不能为空。"
                "请在 .env 文件中设置或通过参数传入。"
            )

        self.token = token
        self.api_version = api_version

        # 创建速率控制器
        self.rate_limiter = TokenBucketRateLimiter(
            rate=rate_limit,
            capacity=rate_limit
        )

        # 请求头
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.api_version,
            "Content-Type": "application/json"
        }

    @staticmethod
    def _clean_id(notion_id: str) -> str:
        """清理 Notion ID（移除连字符）

        Args:
            notion_id: 原始 Notion ID

        Returns:
            清理后的 ID（无连字符）
        """
        return notion_id.replace("-", "")

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发起 API 请求（内部方法）

        自动应用速率控制和错误处理。

        Args:
            method: HTTP 方法（GET, POST, PATCH, DELETE）
            endpoint: API 端点（如 "/pages/xxx"）
            **kwargs: 传递给 requests 的其他参数

        Returns:
            API 响应的 JSON 数据

        Raises:
            NotionClientError: API 请求失败
        """
        # 速率控制
        self.rate_limiter.acquire()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )

            # 检查响应状态
            if response.status_code >= 400:
                try:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("message", "Unknown error")
                except (ValueError, requests.exceptions.JSONDecodeError):
                    error_msg = response.text[:200] if response.text else "Unknown error"
                raise NotionClientError(
                    f"Notion API 错误 [{response.status_code}]: {error_msg}"
                )

            # 处理无内容响应（204 No Content）
            if response.status_code == 204 or not response.content:
                return {}

            # 解析 JSON 响应
            try:
                return response.json()
            except (ValueError, requests.exceptions.JSONDecodeError) as e:
                raise NotionClientError(f"无法解析响应 JSON: {str(e)}") from e

        except requests.exceptions.RequestException as e:
            raise NotionClientError(f"网络请求失败: {str(e)}") from e
        except Exception as e:
            if isinstance(e, NotionClientError):
                raise
            raise NotionClientError(f"请求处理失败: {str(e)}") from e

    def verify_connection(self) -> bool:
        """验证连接和 token 有效性

        通过调用 /users/me 端点验证 token。

        Returns:
            连接成功返回 True

        Raises:
            NotionClientError: 连接失败或 token 无效
        """
        try:
            result = self._request("GET", "/users/me")
            print(f"[Notion] 连接成功！用户: {result.get('id', 'unknown')}")
            return True
        except NotionClientError as e:
            print(f"[Notion] 连接失败: {str(e)}")
            raise

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """读取页面

        Args:
            page_id: 页面 ID（32 位 UUID，可以带或不带连字符）

        Returns:
            页面对象

        Raises:
            NotionClientError: 页面不存在或无权访问
        """
        clean_id = self._clean_id(page_id)
        return self._request("GET", f"/pages/{clean_id}")

    def get_database(self, database_id: str) -> Dict[str, Any]:
        """读取数据库

        Args:
            database_id: 数据库 ID

        Returns:
            数据库对象

        Raises:
            NotionClientError: 数据库不存在或无权访问
        """
        clean_id = self._clean_id(database_id)
        return self._request("GET", f"/databases/{clean_id}")

    def query_database(
        self,
        database_id: str,
        filter_obj: Optional[Dict[str, Any]] = None,
        sorts: Optional[list] = None,
        start_cursor: Optional[str] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """查询数据库

        Args:
            database_id: 数据库 ID
            filter_obj: 过滤条件
            sorts: 排序规则
            start_cursor: 分页游标
            page_size: 每页数量（默认 100）

        Returns:
            查询结果（包含 results 和分页信息）

        Raises:
            NotionClientError: 查询失败
        """
        clean_id = self._clean_id(database_id)

        payload = {"page_size": page_size}
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts
        if start_cursor:
            payload["start_cursor"] = start_cursor

        return self._request("POST", f"/databases/{clean_id}/query", json=payload)

    def create_page(
        self,
        parent: Dict[str, str],
        properties: Dict[str, Any],
        children: Optional[list] = None
    ) -> Dict[str, Any]:
        """创建页面

        Args:
            parent: 父级（database_id 或 page_id）
            properties: 页面属性
            children: 页面内容块（可选）

        Returns:
            创建的页面对象

        Raises:
            NotionClientError: 创建失败
        """
        payload = {
            "parent": parent,
            "properties": properties
        }
        if children:
            payload["children"] = children

        return self._request("POST", "/pages", json=payload)

    def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新页面属性

        Args:
            page_id: 页面 ID
            properties: 要更新的属性

        Returns:
            更新后的页面对象

        Raises:
            NotionClientError: 更新失败
        """
        clean_id = self._clean_id(page_id)

        payload = {"properties": properties}
        return self._request("PATCH", f"/pages/{clean_id}", json=payload)

    def archive_page(self, page_id: str) -> Dict[str, Any]:
        """归档页面（移入回收站，可在 Notion 中恢复）

        归档父页面会连带归档它下面的子页面和数据库。

        Raises:
            NotionClientError: 归档失败
        """
        clean_id = self._clean_id(page_id)
        return self._request("PATCH", f"/pages/{clean_id}", json={"archived": True})

    def search_pages(self, query: str) -> List[Dict[str, Any]]:
        """搜索页面

        Args:
            query: 搜索关键词

        Returns:
            匹配的页面列表

        Raises:
            NotionClientError: 搜索失败
        """
        payload = {
            "query": query,
            "filter": {"property": "object", "value": "page"}
        }
        response = self._request("POST", "/search", json=payload)
        return response.get("results", [])

    def create_database(
        self,
        parent_id: str,
        title: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建数据库（便捷方法）

        Args:
            parent_id: 父页面 ID
            title: 数据库标题
            properties: 数据库属性定义

        Returns:
            创建的数据库对象（包含 id, url, title）

        Raises:
            NotionClientError: 创建失败
        """
        payload = {
            "parent": {"type": "page_id", "page_id": self._clean_id(parent_id)},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties
        }
        result = self._request("POST", "/databases", json=payload)

        # 提取标题
        title_text = ""
        if result.get("title") and len(result["title"]) > 0:
            title_text = result["title"][0].get("plain_text", "")

        return {
            "id": result["id"],
            "url": result.get("url", ""),
            "title": title_text
        }

    def create_page_simple(
        self,
        title: str,
        parent_id: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建页面（便捷方法）

        Internal integration 不能在 workspace 顶层建页面，必须指定父页面。

        Args:
            title: 页面标题
            parent_id: 父页面 ID
            content: 纯文本内容，按行拆成段落（可选）

        Returns:
            创建的页面对象（包含 id, url, title）

        Raises:
            ValueError: parent_id 为空
            NotionClientError: 创建失败
        """
        if not parent_id:
            raise ValueError("parent_id 不能为空：internal integration 必须指定父页面")
        parent = {"type": "page_id", "page_id": self._clean_id(parent_id)}

        # 构建标题属性（Notion API 格式）
        properties = {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }

        # 构建内容块
        children = None
        if content:
            # 简单处理：将内容分段，每段作为一个 paragraph block
            lines = content.strip().split("\n")
            children = []
            for line in lines:
                stripped_line = line.strip()
                if stripped_line:
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": stripped_line}}]
                        }
                    })

        result = self.create_page(parent, properties, children)

        # 提取标题
        title_text = ""
        if result.get("properties", {}).get("title"):
            title_prop = result["properties"]["title"]
            if title_prop.get("title") and len(title_prop["title"]) > 0:
                title_text = title_prop["title"][0].get("plain_text", "")

        return {
            "id": result["id"],
            "url": result.get("url", ""),
            "title": title_text or title
        }

