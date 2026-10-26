---
name: hello
description: 打印 Hello 和开始执行的时间戳，用来测量加载 skill 的耗时。verify-system 的 VAL-018 调用。
---

# Hello

<!-- #13 验证用的测试 skill（VAL-018 / QOS-003）：第 1 步的时间戳减去调用前的时间，就是加载并开始执行的耗时。 -->

## 步骤

1. 运行 `python3 -c "import time; print(time.time())"`，记下输出
2. 只输出一行：`Hello <第 1 步的输出>`，不要输出别的内容
