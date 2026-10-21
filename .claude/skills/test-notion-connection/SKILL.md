# /test-notion-connection

测试 Notion API 连接并读取一个测试页面。

## 功能

1. 验证 NOTION_TOKEN 配置
2. 测试连接到 Notion API
3. 读取指定的测试页面（验证读取权限）

## 参数

- `page_id`（可选）：要读取的测试页面 ID。如果不提供，只验证连接。

## 使用示例

```bash
# 只验证连接
/test-notion-connection

# 验证连接并读取页面
/test-notion-connection page_id=xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 前置条件

- `.env` 文件中配置了有效的 `NOTION_TOKEN`
- 如果提供 `page_id`，该页面必须已分享给 Integration

## 预期输出

成功时：
```
✅ Notion API 连接成功！
用户 ID: xxxxx

[可选] 页面读取成功
标题: xxxx
ID: xxxx
```

失败时：
```
❌ 连接失败: [错误信息]
```
