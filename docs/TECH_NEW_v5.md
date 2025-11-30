# LLM Debate Arena v5 技术方案
## 竞技对抗型 AI 辩论挑战赛 - 实现文档

**版本**: v5.0  
**更新日期**: 2025-11-30  
**状态**: ✅ 已实现

---

## 目录

1. [核心理念](#核心理念)
2. [技术选型](#技术选型)
3. [系统架构](#系统架构)
4. [核心功能实现](#核心功能实现)
5. [数据库设计](#数据库设计)
6. [API 接口](#api-接口)
7. [前端设计](#前端设计)
8. [v5 新特性](#v5-新特性)
9. [部署方案](#部署方案)

---

## 核心理念

### 从协作到竞技的转变

LLM Debate Arena v5 是一个完全竞技对抗型的 AI 辩论平台，核心理念：

| 维度 | 传统对话 | **Debate Arena v5** |
|------|---------|-------------------|
| **目标** | 获得答案 | **赢得比赛** |
| **角色** | 单一模型 | **双方对等竞技** |
| **评判** | 用户主观 | **多裁判 + ELO排位** |
| **数据** | 对话历史 | **完整比赛记录 + 排行榜** |
| **体验** | 问答式 | **观赛 + 实时流式** |

---

## 技术选型

### 后端技术栈

```yaml
语言: Python 3.10+
框架: FastAPI
  - 异步支持: async/await
  - SSE: Server-Sent Events
  - Pydantic V2: 数据验证

数据库:
  - SQLite (生产可用)
  - SQLAlchemy ORM
  
LLM 调用:
  - OpenRouter API (统一接口)
  - 支持 GPT/Claude/混元等

认证:
  - JWT Token (永久有效)
  - bcrypt 密码哈希

工具:
  - Python解释器 (exec沙盒)
  - 网络搜索 (Serper API)
  - 计算器 (sympy)

日志: loguru
```

### 前端技术栈

```yaml
框架: React 18 (Hooks)
构建: Vite 5
语言: TypeScript
样式: Tailwind CSS
动画: Framer Motion
路由: React Router v6
实时: SSE (useSSE Hook)
渲染: React Markdown
```

### 为什么选择 SSE？

| 特性 | WebSocket | **SSE** |
|------|-----------|---------|
| 双向通信 | ✅ | ❌ (单向推送) |
| 自动重连 | 需手动实现 | ✅ **原生支持** |
| 协议 | ws:// | ✅ **HTTP/HTTPS** |
| 防火墙 | 易被拦截 | ✅ **友好** |
| 实现复杂度 | 中 | ✅ **低** |
| 适用场景 | 聊天室 | ✅ **流式推送** |

**结论**: 辩论场景只需服务端推送，SSE 是最佳选择。

---

## 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 竞技场   │  │ 天梯榜   │  │ 注册     │  │ 登录     │   │
│  │ Arena    │  │ Leaderboard│ │ Register │  │ (Modal)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                     │ SSE / HTTP REST                       │
└─────────────────────┼───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  后端 API (FastAPI)                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            /api/tournament/                          │  │
│  │  • POST /match/stream    (SSE流式比赛)               │  │
│  │  • GET  /leaderboard     (天梯榜)                    │  │
│  │  • GET  /matches/history (历史，支持筛选)            │  │
│  │  • GET  /match/{id}      (比赛详情)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            /api/auth/                                │  │
│  │  • POST /register        (注册)                      │  │
│  │  • POST /login           (登录，支持邮箱)            │  │
│  │  • GET  /me              (获取用户信息)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                      ↓                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Tournament│  │  Judge   │  │   ELO    │  │   Auth   │  │
│  │ Manager  │→ │  Panel   │→ │  System  │  │   JWT    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │              │             │          │
│       ↓             ↓              ↓             ↓          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐ │
│  │   LLM    │  │  Tools   │  │      Database            │ │
│  │  Client  │  │  Engine  │  │  (SQLAlchemy + SQLite)   │ │
│  └──────────┘  └──────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    数据层 (SQLite)                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────┐│
│  │ competitors│  │  matches   │  │   topics   │  │ users ││
│  │  (模型)     │  │  (比赛)     │  │  (辩题)     │  │(用户)││
│  └────────────┘  └────────────┘  └────────────┘  └───────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 核心功能实现

### 1. SSE 流式比赛

**核心文件**: `backend/tournament.py`

```python
async def run_tournament_match(
    topic: str,
    prop_model_id: str,
    opp_model_id: str,
    rounds: int = 3,
    judges: List[str] = [],
    same_model_battle: bool = False
) -> AsyncGenerator[dict, None]:
    """
    运行比赛，流式推送事件
    
    Yields:
        - {"type": "match_start", ...}
        - {"type": "status", "content": "正方思考中..."}
        - {"type": "turn_complete", "turn": {...}}
        - {"type": "judge_complete", "result": {...}}
        - {"type": "elo_update", ...}
        - {"type": "match_end", ...}
    """
```

**SSE 事件流程**:

1. `match_start` - 比赛开始
2. 每轮发言:
   - `status` - 思考中提示
   - `turn_complete` - 发言完成（包含工具调用）
3. `judge_complete` - 裁判打分完成
4. `elo_update` - ELO 更新（同模型对战跳过）
5. `match_end` - 比赛结束

**前端SSE连接**: `frontend/src/hooks/useSSE.ts`

```typescript
// 使用 AbortController 支持手动中止
const abortController = new AbortController()

fetch(url, {
  method: 'POST',
  body: JSON.stringify(config),
  signal: abortController.signal  // ✅ 支持中止
})

// 中止方法
const disconnect = () => {
  abortController.abort()  // ✅ 前后端同步中止
}
```

### 2. 多裁判投票制

**核心文件**: `backend/judge.py`

```python
async def judge_match_with_panel(match: MatchSession) -> MatchResult:
    """
    多裁判投票
    
    1. 筛选裁判（排除参赛选手）
    2. 并行调用多个裁判
    3. 综合打分（逻辑/证据/说服力）
    """
    
    # 排除参赛选手
    eligible_judges = [
        j for j in JUDGE_PANEL
        if j not in [match.proponent_model_id, match.opponent_model_id]
    ]
    
    # 并行打分
    judge_scores = await asyncio.gather(*[
        judge_single(match, j) for j in eligible_judges
    ])
    
    # 计算胜者
    votes = {"proponent": 0, "opponent": 0, "draw": 0}
    for score in judge_scores:
        votes[score.winner] += 1
    
    winner = max(votes, key=votes.get)
    
    return MatchResult(winner=winner, judge_scores=judge_scores, ...)
```

### 3. 动态 ELO 系统

**核心文件**: `backend/elo.py`

```python
async def update_elo_ratings(match: MatchSession) -> dict:
    """
    ELO 公式: R' = R + K × D × (S - E)
    
    其中:
    - K: 动态K因子 (新手64, 成长32, 成熟16)
    - D: 难度系数 (Easy 0.8, Medium 1.0, Hard 1.5, Expert 2.0)
    - S: 实际得分 (1/0.5/0)
    - E: 期望得分
    """
    
    # 计算期望胜率
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    # 计算新分数
    delta = k_factor * difficulty_mult * (score - expected)
    new_rating = old_rating + delta
    
    return {"change": int(delta), "new_rating": new_rating}
```

**特殊处理**: 同模型对战不计入ELO，但正常记录。

### 4. 用户认证系统

**核心文件**: `backend/auth.py`

```python
# JWT Token (永久有效)
def create_access_token(data: dict) -> str:
    payload = data.copy()
    # 不设置过期时间 = 永久有效
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# 密码哈希
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

**登录流程**:

1. 前端: 邮箱 + 密码 → `/api/auth/login`
2. 后端: 支持邮箱或用户名查询
3. 验证密码 → 生成JWT → 返回token和用户信息
4. 前端: 存储到 localStorage

### 5. 历史记录筛选

**核心文件**: `backend/database.py`

```python
async def get_match_history(
    limit: int = 20,
    model_id: str = None,
    user_id: int = None
) -> List[MatchModel]:
    """
    获取历史记录
    
    支持筛选:
    - model_id: 该模型参与的所有比赛
    - user_id: 该用户发起的比赛
    """
    query = db.query(MatchModel)
    
    if model_id:
        query = query.filter(
            (MatchModel.proponent_model_id == model_id) |
            (MatchModel.opponent_model_id == model_id)
        )
    
    if user_id:
        query = query.filter(MatchModel.user_id == user_id)
    
    return query.order_by(desc(MatchModel.created_at)).limit(limit).all()
```

---

## 数据库设计

### 核心表结构

#### 1. competitors (模型档案)

```sql
CREATE TABLE competitors (
    id INTEGER PRIMARY KEY,
    model_id VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    provider VARCHAR(50),
    elo_rating INTEGER DEFAULT 1200,
    matches_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    elo_history JSON,
    created_at DATETIME
);
```

#### 2. matches (比赛记录)

```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY,
    match_id VARCHAR(36) UNIQUE,
    topic VARCHAR(500) NOT NULL,
    topic_difficulty VARCHAR(20),
    proponent_model_id VARCHAR(100),
    opponent_model_id VARCHAR(100),
    status VARCHAR(20),
    transcript JSON,              -- 辩论记录
    judge_result JSON,            -- 裁判结果
    elo_changes JSON,
    user_id INTEGER,              -- 发起人
    created_at DATETIME,
    finished_at DATETIME
);
```

#### 3. users (用户表)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    matches_count INTEGER DEFAULT 0,
    created_at DATETIME,
    last_login DATETIME
);
```

#### 4. debate_topics (辩题库)

```sql
CREATE TABLE debate_topics (
    id INTEGER PRIMARY KEY,
    topic VARCHAR(500) NOT NULL,
    difficulty VARCHAR(20),
    category VARCHAR(50),
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME
);
```

---

## API 接口

### 比赛相关

```yaml
# SSE 流式比赛
POST /api/tournament/match/stream
Body:
  {
    "topic": "辩题",
    "proponent_model": "gpt-4o",
    "opponent_model": "claude-3.5-sonnet",
    "rounds": 3,
    "judges": ["gpt-4o", "gpt-4o-mini"],
    "enabled_tools": []  # 可选工具列表
  }
Response: SSE Stream

# 获取比赛详情
GET /api/tournament/match/{match_id}

# 获取历史记录
GET /api/tournament/matches/history?limit=20&model_id=gpt-4o&user_id=1
```

### 排行榜

```yaml
# 获取天梯榜
GET /api/tournament/leaderboard
Response:
  [
    {
      "model_id": "gpt-4o",
      "display_name": "GPT-4o",
      "elo_rating": 1450,
      "matches_played": 25,
      "wins": 15,
      "losses": 8,
      "draws": 2,
      "win_rate": 60.0
    }
  ]
```

### 用户认证

```yaml
# 注册
POST /api/auth/register
Body:
  {
    "username": "user@example.com",  # 自动从邮箱提取
    "email": "user@example.com",
    "password": "password123"
  }

# 登录（支持邮箱或用户名）
POST /api/auth/login
Body:
  {
    "username": "user@example.com",  # 邮箱或用户名
    "password": "password123"
  }
Response:
  {
    "token": "jwt_token_here",
    "user": {
      "id": 1,
      "username": "user",
      "email": "user@example.com"
    }
  }
```

---

## 前端设计

### 页面结构

#### 1. Arena (竞技场 - 主页)

**组件**: `frontend/src/pages/Arena.tsx`

**核心功能**:
- 侧边栏: 历史记录（可折叠，登录后可见）
- 配置区: 模型选择、性格、裁判、工具、辩题
- 展示区: 实时辩论内容（DebateViewer）
- 用户登录: 头像（首字母）、登出、登录弹窗

**状态管理**:
```typescript
const [topic, setTopic] = useState('')
const [propModel, setPropModel] = useState('gpt-4o')
const [judges, setJudges] = useState(['gpt-4o', 'gpt-4o-mini'])
const [enabledTools, setEnabledTools] = useState([])  // ✅ 默认空
const [user, setUser] = useState(null)
const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
```

**SSE 连接**:
```typescript
const { messages, connect, disconnect, clearMessages } = useSSE()

const startMatch = () => {
  connect('/api/tournament/match/stream', config)
}

const stopMatch = () => {
  disconnect()  // ✅ 前端中止
}
```

#### 2. Leaderboard (天梯榜)

**组件**: `frontend/src/pages/Leaderboard.tsx`

**核心功能**:
- 点击卡片展开对战记录
- 显示胜/负/平统计
- 标记同模型对战
- 返回主页按钮

**交互优化**:
```typescript
// 整个卡片可点击
<div onClick={() => toggleHistory(model_id)}>
  
// 历史记录区域阻止冒泡
<div onClick={(e) => e.stopPropagation()}>
  {/* 记录列表 */}
</div>
```

#### 3. Register (注册)

**组件**: `frontend/src/pages/Register.tsx`

**简化设计**:
- 仅邮箱 + 密码
- 自动从邮箱提取用户名
- 注册成功自动登录

### 组件设计

#### DebateViewer (辩论展示)

**组件**: `frontend/src/components/DebateViewer.tsx`

**特性**:
- 轻量化状态提示（删除卡片样式，使用 `<p>` 标签）
- 左右对齐（正方左，反方右）
- 工具调用折叠展示
- 裁判结果卡片

```typescript
// ✅ v5 轻量化提示
{currentStatus && (
  <motion.p className="text-xs text-gray-500 text-center py-2">
    {currentStatus}
  </motion.p>
)}
```

#### Toast (消息提示)

**组件**: `frontend/src/components/Toast.tsx`

**用法**:
```typescript
const { toast } = useToast()

toast.success('操作成功')
toast.error('操作失败')
toast.warning('警告信息')
toast.info('提示信息')
```

---

## v5 新特性

### 1. 用户系统 ✅

- **注册**: 邮箱 + 密码（自动提取用户名）
- **登录**: 支持邮箱或用户名
- **认证**: JWT Token（永久有效）
- **头像**: 显示首字母
- **历史**: 登录后可见个人记录

### 2. 侧边栏折叠 ✅

- 点击小三角图标切换
- 按钮位置跟随侧边栏
- 流畅动画过渡

### 3. 天梯榜优化 ✅

- 点击整个卡片展开记录
- 删除"查看历史对战"按钮
- 显示对手、胜负、日期
- 标记同模型对战

### 4. 同模型对战 ✅

- 允许同模型对战
- 标记 `same_model_battle`
- **不计入ELO排位**

### 5. 历史记录筛选 ✅

- 按模型筛选
- 按用户筛选
- API支持多条件组合

### 6. 交互优化 ✅

- 删除多余loading提示
- 工具选择默认不选中
- 主页宽度85%自适应
- 辩论进度轻量化

### 7. SSE 中止支持 ✅

- 前端使用 `AbortController`
- 点击中止按钮立即停止
- 前后端同步中止

---

## 部署方案

### 开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m backend.main

# 前端
cd frontend
npm install
npm run dev
```

### 生产环境

#### 使用 start.sh（推荐）

```bash
chmod +x start.sh
./start.sh
```

#### Docker 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./debate_arena.db:/app/debate_arena.db
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### 环境变量

```env
# .env
OPENROUTER_API_KEY=your_api_key
OPENROUTER_API_URL=http://hunyuanapi.woa.com/openapi/v1
DEFAULT_MODEL=hunyuan-turbos-latest
SERPER_API_KEY=your_serper_key
DATABASE_URL=sqlite:///./debate_arena.db
SECRET_KEY=your_jwt_secret_key
```

---

## 性能优化

### 1. 后端优化

```python
# 1. 异步数据库操作
async def get_match_history(...):
    pass

# 2. 裁判并行打分
judge_scores = await asyncio.gather(*tasks)

# 3. SSE 流式推送（减少内存占用）
async for event in run_tournament_match(...):
    yield event
```

### 2. 前端优化

```typescript
// 1. 组件懒加载
const Leaderboard = lazy(() => import('./pages/Leaderboard'))

// 2. 避免不必要的re-render
const memoizedComponent = useMemo(() => ...)

// 3. SSE自动重连
// fetch + AbortController 天然支持
```

### 3. 数据库索引

```sql
CREATE INDEX idx_competitors_elo ON competitors(elo_rating DESC);
CREATE INDEX idx_matches_created ON matches(created_at DESC);
CREATE INDEX idx_matches_user ON matches(user_id);
```

---

## 总结

### v5 核心亮点

1. ✅ **用户系统** - 注册登录、个人记录
2. ✅ **SSE流式** - 实时推送、支持中止
3. ✅ **多裁判制** - 公平评分
4. ✅ **ELO排位** - 动态算法、难度系数
5. ✅ **同模型对战** - 支持但不计ELO
6. ✅ **历史筛选** - 按模型/用户查询
7. ✅ **响应式设计** - 大屏自适应
8. ✅ **交互优化** - 轻量化、可折叠

### 技术优势

- **后端**: FastAPI + SQLAlchemy + SSE（高性能、易维护）
- **前端**: React + TypeScript + Tailwind（现代化、类型安全）
- **通信**: SSE（自动重连、简单可靠）
- **认证**: JWT（无状态、可扩展）

### 下一步计划

- [ ] 风格分析雷达图
- [ ] ELO历史趋势图
- [ ] 赛后复盘报告
- [ ] 观众投票功能
- [ ] 每日挑战赛
- [ ] 数据分析看板

---

**LLM Debate Arena v5** - 让 AI 在竞技中展现真正的智慧！🔥⚔️🏆
