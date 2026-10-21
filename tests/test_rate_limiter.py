"""Token Bucket 速率控制器测试"""

import time
import pytest
from agent_brain.rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter:
    """Token Bucket 速率控制器测试"""

    def test_初始化时令牌桶已满(self):
        """初始化时令牌桶应该是满的"""
        limiter = TokenBucketRateLimiter(rate=3, capacity=3)
        # 应该能立即消耗 3 个令牌
        assert limiter.acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire() is True

    def test_令牌耗尽后需要等待(self):
        """令牌耗尽后，下次获取需要等待"""
        limiter = TokenBucketRateLimiter(rate=3, capacity=3)

        # 耗尽令牌
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()

        # 第 4 次获取应该等待
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start

        # 应该等待约 1/3 秒（rate=3 每秒）
        assert 0.3 <= elapsed <= 0.4

    def test_令牌按速率补充(self):
        """令牌应该按指定速率补充"""
        limiter = TokenBucketRateLimiter(rate=2, capacity=2)

        # 耗尽令牌
        limiter.acquire()
        limiter.acquire()

        # 等待 1 秒，应该补充 2 个令牌
        time.sleep(1.0)

        # 应该能立即获取 2 个令牌
        start = time.time()
        limiter.acquire()
        limiter.acquire()
        elapsed = time.time() - start

        # 应该几乎不需要等待
        assert elapsed < 0.1

    def test_批量请求自动限速(self, capsys):
        """批量请求时自动限速，并输出日志"""
        limiter = TokenBucketRateLimiter(rate=5, capacity=5)

        # 连续发起 8 次请求
        start = time.time()
        for i in range(8):
            limiter.acquire()
        elapsed = time.time() - start

        # 前 5 次立即通过，后 3 次需要等待
        # 后 3 次总共需要等待约 3/5 = 0.6 秒
        assert 0.5 <= elapsed <= 0.8

        # 检查日志输出
        captured = capsys.readouterr()
        assert "速率限制" in captured.out or "等待" in captured.out

    def test_容量限制令牌积累上限(self):
        """令牌数量不应超过容量上限"""
        limiter = TokenBucketRateLimiter(rate=10, capacity=3)

        # 等待足够长时间，令牌应该只补充到容量上限
        time.sleep(1.0)

        # 应该只能立即获取 3 个令牌
        start = time.time()
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.1

        # 第 4 次需要等待
        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start
        assert elapsed >= 0.08  # 1/10 秒左右
