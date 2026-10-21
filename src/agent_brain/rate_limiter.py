"""Token Bucket 速率控制器

实现令牌桶算法来限制 API 请求速率。
"""

import time
import threading
from typing import Optional


class TokenBucketRateLimiter:
    """Token Bucket 速率控制器

    使用令牌桶算法控制请求速率：
    - 令牌以固定速率生成（rate 个/秒）
    - 每次请求消耗 1 个令牌
    - 令牌数量上限为 capacity
    - 无可用令牌时阻塞等待

    线程安全。
    """

    def __init__(self, rate: float, capacity: int):
        """初始化速率控制器

        Args:
            rate: 每秒生成的令牌数
            capacity: 令牌桶容量（上限）
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)  # 初始时令牌桶已满
        self.last_update = time.time()
        self.lock = threading.Lock()

    def _refill(self):
        """补充令牌（内部方法，需持有锁）"""
        now = time.time()
        elapsed = now - self.last_update

        # 按速率补充令牌
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_update = now

    def acquire(self, tokens: int = 1) -> bool:
        """获取令牌（阻塞直到成功）

        Args:
            tokens: 需要获取的令牌数量

        Returns:
            True（总是成功，会阻塞等待）
        """
        with self.lock:
            while True:
                self._refill()

                if self.tokens >= tokens:
                    # 有足够令牌，立即消耗
                    self.tokens -= tokens
                    return True
                else:
                    # 令牌不足，计算需要等待的时间
                    needed = tokens - self.tokens
                    wait_time = needed / self.rate

                    print(f"[速率限制] 等待 {wait_time:.2f} 秒...")

                    # 释放锁并等待
                    self.lock.release()
                    time.sleep(wait_time)
                    self.lock.acquire()

    def try_acquire(self, tokens: int = 1) -> bool:
        """尝试获取令牌（非阻塞）

        Args:
            tokens: 需要获取的令牌数量

        Returns:
            成功返回 True，失败返回 False
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False
