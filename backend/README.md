# LLM Debate Arena - Backend

大模型辩论竞技场后端服务，基于 FastAPI 构建的高性能异步 API 服务。

## 📁 项目结构

```
backend/
├── __init__.py         # 包初始化
├── main.py            # FastAPI 应用入口和路由
├── config.py          # 配置管理（环境变量、API密钥等）
├── models.py          # 数据模型定义（SQLAlchemy ORM + Pydantic）
├── database.py        # 数据库操作和会话管理
├── llm_client.py      # LLM API 客户端封装
├── judge.py           # 裁判评分系统
├── elo.py             # ELO 评分算法
├── tools.py           # 工具集成（搜索、Python解释器等）
├── tournament.py      # 锦标赛赛制实现
├── auth.py            # 用户认证和授权
├── utils.py           # 工具函数
├── log.py             # 日志配置
└── requirements.txt   # Python 依赖
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到项目根目录并重命名为 `.env`，然后配置以下环境变量：

```bash
# LLM API 配置
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_API_URL=https://api.openai.com/v1

# 可用模型列表（逗号分隔）
AVAILABLE_MODELS=gpt-4o,gpt-4o-mini,claude-3.5-sonnet,gpt-5.1

# 数据库配置
DATABASE_URL=sqlite:///./debate_arena.db

# Serper API（用于搜索工具）
SERPER_API_KEY=your_serper_api_key_here
```

### 3. 启动服务

```bash
# 开发模式（支持热重载）
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 或使用项目根目录的启动脚本
./start.sh
```

服务将在 `http://localhost:8000` 启动。

## 📡 API 文档

启动服务后，访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 核心功能模块

### 1. 模型管理 (`models.py`)

定义了完整的数据模型：

- **CompetitorModel**: 参赛选手档案（ELO 评分、对战记录等）
- **DebateTopicModel**: 辩题库
- **MatchModel**: 比赛记录
- **UserModel**: 用户信息

### 2. 辩论引擎 (`llm_client.py`)

- 支持多种 LLM 提供商（OpenAI、Anthropic 等）
- 异步请求处理
- 流式响应支持
- 工具调用（Function Calling）

### 3. 裁判系统 (`judge.py`)

- 多裁判评分机制
- 综合评分算法（论点强度、逻辑严密性、证据支持等）
- 观众投票权重
- MVP 回合评选

### 4. ELO 评分系统 (`elo.py`)

- 动态 K 因子（根据比赛场次调整）
- 支持三种结果：胜/负/平
- 评分历史记录

### 5. 工具集成 (`tools.py`)

- **Python 解释器**: 执行代码片段
- **Web 搜索**: Serper API 集成
- **计算器**: 数学表达式计算
- 工具调用结果格式化

### 6. 锦标赛系统 (`tournament.py`)

- 瑞士制赛制
- 单淘汰赛制
- 循环赛制
- 自动配对和排名

## 🔧 配置说明

### 模型配置

从环境变量 `AVAILABLE_MODELS` 读取可用模型列表：

- 格式：逗号分隔的模型 ID
- 示例：`gpt-4o,gpt-4o-mini,claude-3.5-sonnet,your-custom-model`
- 模型会自动初始化，`display_name` 为模型 ID 的大写形式

### ELO 配置

在 `config.py` 中配置：

```python
ELO_CONFIG = {
    "initial_rating": 1200,
    "k_factor_new": 64,      # 新手期 (< 10 场)
    "k_factor_mid": 32,      # 成长期 (10-30 场)
    "k_factor_stable": 16,   # 成熟期 (> 30 场)
}
```

### 裁判配置

```python
JUDGE_PANEL = [
    "gpt-4o",
    "gpt-4o-mini",
]
```

## 📊 数据库

使用 SQLite 数据库（支持 WAL 模式以提升并发性能）：

- 自动创建表结构
- 自动初始化默认数据（选手、辩题）
- 连接池管理
- 事务重试机制

### 数据库操作

```python
from backend.database import get_all_competitors, save_match

# 获取所有选手
competitors = await get_all_competitors()

# 保存比赛
await save_match(match_session)
```

## 🔐 安全性

- JWT Token 认证
- 密码哈希存储（bcrypt）
- CORS 配置
- API 速率限制（可选）

## 📝 日志

使用 `loguru` 进行日志管理：

- 自动日志轮转
- 按级别过滤
- 彩色输出
- 文件保存

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 测试覆盖率
pytest --cov=backend tests/
```

## 🛠️ 开发建议

1. **代码风格**: 遵循 PEP 8 规范
2. **类型注解**: 使用 Python 类型提示
3. **异步优先**: 所有 I/O 操作使用 async/await
4. **错误处理**: 使用 try-except 并记录日志
5. **文档注释**: 为函数添加 docstring

## 📦 依赖说明

主要依赖：

- **FastAPI**: 现代化的 Web 框架
- **SQLAlchemy**: ORM 框架
- **Pydantic**: 数据验证
- **OpenAI**: LLM API 客户端
- **Loguru**: 日志管理
- **WebSockets**: 实时通信

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
