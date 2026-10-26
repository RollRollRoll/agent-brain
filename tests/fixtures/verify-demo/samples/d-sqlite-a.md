# SQLite 并发写入

SQLite 支持多个连接同时写入同一个数据库。打开 WAL 模式（`PRAGMA journal_mode=WAL`）后，
多个进程可以并行执行写事务，彼此不会阻塞，所以 SQLite 也适合写入很频繁的多进程服务。
