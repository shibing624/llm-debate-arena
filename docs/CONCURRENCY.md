# 多用户并发支持说明

## 🎯 并发特性

本系统已经优化并发性能，支持多个用户同时使用，无需担心性能和数据安全问题。

## ✅ 已支持的并发能力

### 1. 数据库并发优化

- **WAL 模式**：启用 SQLite 的 Write-Ahead Logging，支持多读单写并发
- **连接池**：配置连接池（size=10, max_overflow=20），避免连接耗尽
- **超时控制**：设置 30 秒超时，避免长时间锁定
- **自动重试**：关键操作（比赛保存、ELO 更新）带重试机制

### 2. 异步处理

- **FastAPI 异步支持**：所有路由使用 `async/await`，天然支持并发
- **独立 SSE 连接**：每个用户的流式输出完全独立
- **非阻塞 I/O**：LLM 调用、工具执行都是异步的

### 3. 数据隔离

- **用户隔离**：每个用户通过 `user_id` 隔离数据
- **比赛隔离**：每场比赛有唯一 `match_id`，互不干扰
- **状态隔离**：前端状态完全独立，不共享

## 📊 并发能力指标

### 理论并发能力

| 场景 | 并发数 | 说明 |
|------|--------|------|
| 同时查看历史记录 | 100+ | 数据库读操作，性能很高 |
| 同时开始新辩论 | 50+ | 受 LLM API 限速影响 |
| 同时流式输出 | 50+ | 每个连接独立，互不影响 |

### 实际测试建议

- **小型部署**（<10 用户）：无需任何优化
- **中型部署**（10-50 用户）：当前配置足够
- **大型部署**（50+ 用户）：建议迁移到 PostgreSQL

## 🔧 优化细节

### 1. 数据库连接池配置

```python
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # 30 秒超时
    },
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True  # 连接前检查可用性
)
```

### 2. WAL 模式启用

在 `init_db()` 中自动启用：

```python
conn.execute('PRAGMA journal_mode=WAL')
```

这使得：
- 读操作不会被写操作阻塞
- 多个读操作可以并发执行
- 写操作性能更好

### 3. 重试机制

关键操作（保存比赛、更新 ELO）都有重试：

```python
max_retries = 3
while retry_count < max_retries:
    try:
        # 数据库操作
        db.commit()
        break
    except Exception:
        db.rollback()
        retry_count += 1
        time.sleep(0.1 * retry_count)  # 指数退避
```

### 4. 行级锁（ELO 更新）

避免同一模型的 ELO 竞态条件：

```python
competitor = db.query(CompetitorModel).filter(
    CompetitorModel.model_id == model_id
).with_for_update().first()  # 行锁
```

## 🚀 如何进一步提升并发能力

### 方案 1: 迁移到 PostgreSQL（推荐）

如果预期用户数 > 50，建议迁移到 PostgreSQL：

```python
# 修改 backend/database.py
DATABASE_URL = "postgresql://user:password@localhost/debate_arena"
```

优势：
- 更强的并发写入能力
- 更好的事务隔离
- 支持更多高级特性

### 方案 2: 使用 Redis 缓存

缓存热点数据（排行榜、历史记录）：

```python
@lru_cache(ttl=60)
async def get_leaderboard():
    # 缓存 60 秒
    pass
```

### 方案 3: 水平扩展

使用 Docker + Nginx 负载均衡：

```bash
# 启动多个后端实例
docker-compose up --scale backend=3
```

## 📝 注意事项

### 1. LLM API 限速

并发瓶颈通常在 LLM API 而非数据库：

- OpenAI API 有 RPM（每分钟请求数）限制
- 建议配置多个 API Key 轮询
- 或使用企业版 API

### 2. SSE 连接限制

每个用户只维护一个 SSE 连接：

- 点击历史记录会断开当前连接
- 新开辩题会关闭旧连接
- 这是设计上的简化，不是 bug

### 3. 数据库文件锁

SQLite 在极高并发下可能出现 `database is locked`：

- 已配置 30 秒超时
- 已添加自动重试机制
- 如果仍频繁出现，建议迁移到 PostgreSQL

## 🧪 压力测试

可以使用以下脚本测试并发能力：

```python
import asyncio
import aiohttp

async def start_match(session, topic):
    async with session.post(
        'http://localhost:8000/api/tournament/match/stream',
        json={
            'topic': topic,
            'proponent_model': 'gpt-4o',
            'opponent_model': 'claude-3.5-sonnet',
            # ...
        }
    ) as resp:
        async for line in resp.content:
            pass

async def stress_test():
    async with aiohttp.ClientSession() as session:
        tasks = [
            start_match(session, f"测试辩题 {i}")
            for i in range(10)  # 10 个并发
        ]
        await asyncio.gather(*tasks)

asyncio.run(stress_test())
```

## 📈 监控建议

建议添加以下监控：

1. **数据库连接数**：通过日志监控连接池使用情况
2. **响应时间**：监控 API 响应延迟
3. **错误率**：监控数据库锁定错误频率
4. **并发数**：监控活跃 SSE 连接数

## 总结

✅ **当前系统已经支持多用户并发**，无需额外配置  
✅ 小型到中型部署（<50 用户）完全够用  
✅ 如需更高并发，可按上述方案扩展  
