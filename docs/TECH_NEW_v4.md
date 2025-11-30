# LLM Debate Tournament v4 技术方案
## 竞技对抗型 AI 辩论挑战赛 - 完整设计

---

## 目录
1. [核心理念](#核心理念)
2. [技术选型](#技术选型)
3. [系统架构](#系统架构)
4. [数据结构设计](#数据结构设计)
5. [核心模块实现](#核心模块实现)
6. [公平性保障机制](#公平性保障机制)
7. [游戏化设计](#游戏化设计)
8. [前端交互设计](#前端交互设计)
9. [API 接口设计](#api-接口设计)
10. [部署方案](#部署方案)

---

## 核心理念

### 从协作到对抗的范式转换

| 维度 | Council v3 (协作) | **Tournament v4 (竞技)** |
|------|------------------|-------------------------|
| **目标** | 获得最佳答案 | **赢得比赛，提升排名** |
| **角色** | 正方(提案) + 反方(审查) | **双方对等对抗** |
| **模型选择** | 系统预设 (最优模型) | **用户自选 (PK 任意两个模型)** |
| **流程控制** | 收敛即停 | **固定轮次，必须打满** |
| **裁判** | 总结陈词 | **多裁判打分 + 观众投票** |
| **工具使用** | 辅助验证 | **竞技武器 (攻击/防御)** |
| **数据沉淀** | 对话历史 | **ELO 排行榜 + 对战记录库** |

---

## 技术选型

### 后端技术栈

```yaml
语言: Python 3.12
框架: FastAPI 0.109+
  - 异步支持: async/await
  - WebSocket: 实时流式输出
  - Pydantic V2: 数据验证

数据库:
  - SQLite (开发/Demo): 轻量级，无需额外服务
  - PostgreSQL (生产): 
    - 支持 JSONB 字段存储辩论记录
    - 事务支持 (ELO 计算的原子性)
  
ORM: SQLAlchemy 2.0+
  - 异步引擎: async_engine
  - 支持复杂查询 (排行榜统计)

LLM 调用:
  - OpenAI SDK (GPT 系列)
  - Anthropic SDK (Claude 系列)
  - 统一封装: openrouter.py

工具调用:
  - Python Sandbox: RestrictedPython (安全沙盒)
  - Web Search: Serper API / Tavily API
  - Calculator: sympy (符号计算)

日志: loguru
缓存: Redis (可选，用于热门辩题缓存)
```

### 前端技术栈

```yaml
框架: React 18+ (Hooks)
构建工具: Vite 5+
UI 组件库: 
  - shadcn/ui (现代化、可定制)
  - Tailwind CSS (快速样式)
  
状态管理: Zustand (轻量级)
实时通信: 
  - Server-Sent Events (SSE) (辩论流式输出)
  - 单向推送，自动重连

数据可视化:
  - Recharts (ELO 趋势图、雷达图)
  - Framer Motion (动画效果)

代码高亮: 
  - react-syntax-highlighter (工具调用代码展示)

Markdown 渲染:
  - react-markdown (辩论内容展示)
```

### 为什么这样选型？

| 技术 | 理由 |
|------|------|
| **SSE** | 原生异步、自动 API 文档、SSE 支持、类型提示 |
| **SQLite/PostgreSQL** | SQLite 快速开发，PostgreSQL 无缝切换生产 |
| **React + Vite** | 生态成熟、开发体验好、构建速度快 |
| **shadcn/ui** | 2024 年最流行的组件库，样式现代、源码可控 |
| **SSE** | 实时流式输出辩论内容，用户体验最佳，更简单可靠 |

---

## 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (React)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  竞技场页面   │  │  排行榜页面   │  │  回放页面     │         │
│  │  (Arena)     │  │ (Leaderboard)│  │  (Replay)    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                  │
│                            │ SSE / HTTP                      │
└────────────────────────────┼─────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    后端 API (FastAPI)                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                   /api/tournament/                        │ │
│  │  • POST /match/stream      (SSE 流式推送比赛)              │ │
│  │  • GET  /leaderboard       (排行榜)                        │ │
│  │  • GET  /matches/history   (历史记录)                      │ │
│  │  • POST /vote              (观众投票)                      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            ↓                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Tournament   │  │  Judge Panel │  │  ELO System  │         │
│  │  Manager     │→ │  (多裁判)     │→ │  (排位算法)   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         ↓                  ↓                  ↓                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ LLM Clients  │  │  Tool Engine │  │   Database   │         │
│  │ (GPT/Claude) │  │  (工具调用)   │  │ (SQLAlchemy) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                         数据层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Competitors  │  │    Matches   │  │   Topics     │         │
│  │   (选手)      │  │   (比赛)      │  │  (辩题库)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 数据结构设计

### 核心数据模型

```python
# backend/models.py

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field
import enum

Base = declarative_base()

# ========== 枚举类型 ==========

class DifficultyLevel(str, enum.Enum):
    """辩题难度"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class TopicCategory(str, enum.Enum):
    """辩题分类"""
    TECH = "tech"
    PHILOSOPHY = "philosophy"
    SOCIAL = "social"
    SCIENCE = "science"
    BUSINESS = "business"

class PersonalityType(str, enum.Enum):
    """选手性格"""
    RATIONAL = "rational"          # 理性分析型
    AGGRESSIVE = "aggressive"      # 激进攻击型
    DIPLOMATIC = "diplomatic"      # 温和外交型
    HUMOROUS = "humorous"          # 幽默讽刺型
    ACADEMIC = "academic"          # 学术严谨型

# ========== 数据库表 (SQLAlchemy ORM) ==========

class CompetitorModel(Base):
    """参赛选手档案表"""
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(100), unique=True, nullable=False)  # 例: "gpt-4o"
    display_name = Column(String(200), nullable=False)
    provider = Column(String(50))  # "openai", "anthropic"
    
    # ELO 数据
    elo_rating = Column(Integer, default=1200)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    
    # ELO 历史 (JSON 数组: [{date, rating}])
    elo_history = Column(JSON, default=list)
    
    # 风格分析
    style_stats = Column(JSON, default=dict)  # {logic_score, evidence_score, ...}
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_match_at = Column(DateTime)


class DebateTopicModel(Base):
    """辩题库表"""
    __tablename__ = "debate_topics"
    
    id = Column(Integer, primary_key=True)
    topic = Column(String(500), nullable=False)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    category = Column(Enum(TopicCategory), default=TopicCategory.TECH)
    
    # 是否有客观答案 (影响裁判评分标准)
    has_objective_answer = Column(Boolean, default=False)
    
    # 期望工具使用 (提示 LLM 可以用哪些工具)
    expected_tools = Column(JSON, default=list)  # ["python", "search"]
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)  # 用户评分
    
    created_at = Column(DateTime, default=datetime.utcnow)


class MatchModel(Base):
    """比赛记录表"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(36), unique=True)  # UUID
    
    # 比赛信息
    topic = Column(String(500), nullable=False)
    topic_difficulty = Column(Enum(DifficultyLevel))
    rounds_setting = Column(Integer, default=3)
    
    # 选手信息
    proponent_model_id = Column(String(100), nullable=False)
    opponent_model_id = Column(String(100), nullable=False)
    proponent_personality = Column(Enum(PersonalityType))
    opponent_personality = Column(Enum(PersonalityType))
    
    # 比赛状态
    status = Column(String(20))  # PREPARING, FIGHTING, JUDGING, FINISHED
    
    # 辩论历史 (JSON: List[Turn])
    transcript = Column(JSON, default=list)
    
    # 裁判结果 (JSON: MatchResult)
    judge_result = Column(JSON)
    
    # 观众投票
    audience_votes = Column(JSON, default=dict)  # {proponent: 120, opponent: 80}
    
    # ELO 变化
    elo_changes = Column(JSON)  # {proponent: +15, opponent: -15}
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)


# ========== Pydantic 模型 (API 交互) ==========

class Turn(BaseModel):
    """单次发言"""
    round_number: int
    speaker_role: Literal["proponent", "opponent"]
    model_id: str
    content: str
    tool_calls: List[Dict] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JudgeScore(BaseModel):
    """单个裁判的评分"""
    judge_model: str
    scores: Dict[str, Dict[str, float]]  # {proponent: {logic: 8.5, ...}}
    winner: Literal["proponent", "opponent", "draw"]
    reasoning: str


class MatchResult(BaseModel):
    """比赛结果 (多裁判综合)"""
    winner: Literal["proponent", "opponent", "draw"]
    
    # 多裁判评分
    judge_scores: List[JudgeScore]
    
    # 综合得分
    final_scores: Dict[str, float]  # {proponent: 25.5, opponent: 23.0}
    
    # 观众投票影响 (20%)
    audience_vote_weight: float = 0.2
    audience_winner: Optional[str] = None
    
    # 最终判词
    reasoning: str
    
    # MVP 回合
    mvp_turn_index: int


class MatchSession(BaseModel):
    """完整比赛会话"""
    match_id: str
    topic: str
    topic_difficulty: DifficultyLevel
    
    # 选手
    proponent_model_id: str
    opponent_model_id: str
    proponent_personality: PersonalityType
    opponent_personality: PersonalityType
    
    # 设置
    rounds_setting: int = 3
    
    # 历史
    history: List[Turn] = []
    
    # 结果
    result: Optional[MatchResult] = None
    
    # 状态
    status: Literal["PREPARING", "FIGHTING", "JUDGING", "FINISHED"] = "PREPARING"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CompetitorProfile(BaseModel):
    """选手档案 (API 返回)"""
    model_id: str
    display_name: str
    provider: str
    elo_rating: int
    matches_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    elo_history: List[Dict]  # [{date: "2024-01", rating: 1250}]
    style_stats: Dict  # {logic_heavy: 0.8, aggressive: 0.6}


class DebateTopic(BaseModel):
    """辩题"""
    id: int
    topic: str
    difficulty: DifficultyLevel
    category: TopicCategory
    has_objective_answer: bool
    expected_tools: List[str]
    usage_count: int
    avg_rating: float
```

---

## 核心模块实现

### 5.1 Tournament Manager (赛事编排)

```python
# backend/tournament.py

import asyncio
from typing import AsyncGenerator
from .models import MatchSession, Turn, PersonalityType
from .llm_client import query_model_with_tools
from .tools import get_debate_tools
from .judge import judge_match_with_panel
from .elo import update_elo_ratings
from .database import save_match, update_match_status

async def run_tournament_match(
    topic: str,
    topic_difficulty: str,
    prop_model_id: str,
    opp_model_id: str,
    prop_personality: PersonalityType,
    opp_personality: PersonalityType,
    rounds: int = 3
) -> AsyncGenerator[dict, None]:
    """
    运行竞技赛，使用 SSE 流式推送
    
    Yields:
        dict: 事件流
            - {"type": "status", "content": "正方思考中..."}
            - {"type": "turn", "data": Turn}
            - {"type": "judging", "progress": 0.33}
            - {"type": "result", "data": MatchResult}
    """
    
    # 创建比赛会话
    match = MatchSession(
        match_id=generate_id(),
        topic=topic,
        topic_difficulty=topic_difficulty,
        proponent_model_id=prop_model_id,
        opponent_model_id=opp_model_id,
        proponent_personality=prop_personality,
        opponent_personality=opp_personality,
        rounds_setting=rounds,
        status="FIGHTING"
    )
    
    await save_match(match)
    
    yield {"type": "match_start", "data": match.dict()}
    
    # 辩论上下文 (供 LLM 参考历史)
    context = []
    
    # === 正式辩论 ===
    for r in range(1, rounds + 1):
        
        # === 正方发言 ===
        yield {"type": "status", "speaker": "proponent", "content": f"Round {r}: 正方正在思考..."}
        
        prop_turn = await execute_turn(
            role="proponent",
            model_id=prop_model_id,
            personality=prop_personality,
            topic=topic,
            topic_difficulty=topic_difficulty,
            round_num=r,
            context=context,
            is_opening=(r==1)
        )
        
        match.history.append(prop_turn)
        context.append(prop_turn)
        
        # 流式推送正方内容
        yield {"type": "turn", "data": prop_turn.dict()}
        
        # === 反方发言 ===
        yield {"type": "status", "speaker": "opponent", "content": f"Round {r}: 反方正在反驳..."}
        
        opp_turn = await execute_turn(
            role="opponent",
            model_id=opp_model_id,
            personality=opp_personality,
            topic=topic,
            topic_difficulty=topic_difficulty,
            round_num=r,
            context=context,
            is_opening=False
        )
        
        match.history.append(opp_turn)
        context.append(opp_turn)
        
        yield {"type": "turn", "data": opp_turn.dict()}
    
    # === 裁判判决 ===
    match.status = "JUDGING"
    await update_match_status(match.match_id, "JUDGING")
    
    yield {"type": "status", "content": "裁判团正在打分..."}
    
    # 多裁判打分 (并行)
    result = await judge_match_with_panel(match)
    match.result = result
    
    yield {"type": "result", "data": result.dict()}
    
    # === 更新 ELO ===
    elo_changes = await update_elo_ratings(match)
    
    yield {"type": "elo_update", "data": elo_changes}
    
    # === 保存比赛 ===
    match.status = "FINISHED"
    await save_match(match)
    
    yield {"type": "match_end", "match_id": match.match_id}


async def execute_turn(
    role: str,
    model_id: str,
    personality: PersonalityType,
    topic: str,
    topic_difficulty: str,
    round_num: int,
    context: List[Turn],
    is_opening: bool
) -> Turn:
    """执行单次辩论发言"""
    
    # 构建系统提示词
    system_prompt = build_debate_prompt(
        role=role,
        personality=personality,
        topic=topic,
        topic_difficulty=topic_difficulty,
        is_opening=is_opening
    )
    
    # 构建历史上下文
    messages = [{"role": "system", "content": system_prompt}]
    
    for turn in context:
        role_name = "正方" if turn.speaker_role == "proponent" else "反方"
        tool_info = ""
        if turn.tool_calls:
            tool_info = f"\n[使用工具: {', '.join([tc['tool_name'] for tc in turn.tool_calls])}]"
        
        messages.append({
            "role": "user",
            "content": f"【{role_name} Round {turn.round_number}】\n{turn.content}{tool_info}"
        })
    
    messages.append({
        "role": "user",
        "content": f"轮到你了，这是 Round {round_num}。请发言。"
    })
    
    # 获取工具定义
    tools = get_debate_tools()
    
    # 调用 LLM (支持工具)
    response = await query_model_with_tools(
        model_id=model_id,
        messages=messages,
        tools=tools
    )
    
    # 处理工具调用 (执行并获取结果)
    tool_calls = []
    if response.get('tool_calls'):
        from .tools import execute_tool
        for tc in response['tool_calls']:
            result = await execute_tool(tc)
            tool_calls.append({
                "tool_name": tc['function']['name'],
                "arguments": tc['function']['arguments'],
                "result": result
            })
    
    return Turn(
        round_number=round_num,
        speaker_role=role,
        model_id=model_id,
        content=response['content'],
        tool_calls=tool_calls,
        timestamp=datetime.utcnow()
    )


def build_debate_prompt(
    role: str,
    personality: PersonalityType,
    topic: str,
    topic_difficulty: str,
    is_opening: bool
) -> str:
    """构建辩论提示词 (含性格注入)"""
    
    position = "正方（支持方）" if role == "proponent" else "反方（反对方）"
    
    # 性格描述
    personality_traits = {
        PersonalityType.RATIONAL: "你是一个理性分析型辩手，善用逻辑推理和数据分析。",
        PersonalityType.AGGRESSIVE: "你是一个激进攻击型辩手，言辞犀利，直击要害，不留情面。",
        PersonalityType.DIPLOMATIC: "你是一个温和外交型辩手，善于沟通，注重礼貌和说服力。",
        PersonalityType.HUMOROUS: "你是一个幽默讽刺型辩手，善用比喻和反讽，寓教于乐。",
        PersonalityType.ACADEMIC: "你是一个学术严谨型辩手，引经据典，强调权威和证据。"
    }
    
    personality_desc = personality_traits.get(personality, "")
    
    # 难度提示
    difficulty_hints = {
        "easy": "这是一个相对简单的辩题，请用清晰的逻辑和常识进行论证。",
        "medium": "这是一个中等难度的辩题，需要一定的专业知识和论证深度。",
        "hard": "这是一个困难的辩题，需要深度思考和强有力的证据支持。",
        "expert": "这是一个专家级辩题，需要引用权威资料和复杂推理。"
    }
    
    difficulty_hint = difficulty_hints.get(topic_difficulty, "")
    
    # 策略指导
    if role == "proponent":
        if is_opening:
            strategy = "这是开篇立论。请清晰地阐述你的核心观点，并提供强有力的论据或数据支持。"
        else:
            strategy = "请反驳反方的观点，维护你的立论，并指出对方逻辑中的谬误或证据的不足。"
    else:
        strategy = "请猛烈抨击正方的观点。寻找事实错误、逻辑漏洞或反例。提出更有说服力的替代观点。"
    
    return f"""
你正在参加一场关于 "{topic}" 的高水平辩论赛。

【你的身份】
{position}

【你的性格】
{personality_desc}

【辩题难度】
{difficulty_hint}

【你的目标】
你的目标是赢得这场辩论，击败对手，赢得裁判和观众的认可。

【当前策略】
{strategy}

【评分标准】
裁判将从三个维度评分：
1. 逻辑性 (Logic): 论证结构是否严密，是否有效反驳了对方
2. 证据力 (Evidence): 是否使用了事实、数据或代码来支持观点
3. 说服力 (Persuasion): 语言表达是否清晰、有力、切中要害

【工具使用】
你可以调用以下工具来增强论证：
- `python_interpreter`: 运行代码证明你的观点
- `web_search`: 搜索权威资料
- `calculator`: 精确计算

**注意**：
- 工具是辅助手段，不是评分的绝对标准
- 如果逻辑本身足够强，不用工具也能得高分
- 滥用工具但未切中要害，不会加分

【禁止行为】
- 不要试图达成共识或妥协
- 不要承认对方的核心观点
- 你的目的是战胜对手，而非合作
"""


def generate_id() -> str:
    """生成唯一 ID"""
    import uuid
    return str(uuid.uuid4())
```

---

### 5.2 多裁判投票制 (Judge Panel)

```python
# backend/judge.py

import asyncio
from typing import List
from .models import MatchSession, JudgeScore, MatchResult
from .llm_client import query_model
from .utils import parse_json

# 裁判团配置 (避免参赛选手做自己的裁判)
JUDGE_PANEL = [
    "gpt-4o",
    "claude-3.5-sonnet",
    "gpt-4o-mini",  # 作为"平民视角"
]

async def judge_match_with_panel(match: MatchSession) -> MatchResult:
    """
    多裁判投票制
    
    流程:
    1. 排除参赛选手
    2. 并行调用多个裁判
    3. 综合打分 (加权平均)
    4. 结合观众投票 (20% 权重)
    """
    
    # 筛选裁判 (排除参赛选手)
    eligible_judges = [
        j for j in JUDGE_PANEL
        if j not in [match.proponent_model_id, match.opponent_model_id]
    ]
    
    if len(eligible_judges) < 2:
        # 降级：如果可用裁判不足，使用元裁判机制
        eligible_judges = ["gpt-4o", "claude-3.5-sonnet"]
    
    # 并行调用裁判
    tasks = [
        judge_single(match, judge_model)
        for judge_model in eligible_judges
    ]
    
    judge_scores: List[JudgeScore] = await asyncio.gather(*tasks)
    
    # === 综合打分 ===
    
    # 统计胜负票
    votes = {"proponent": 0, "opponent": 0, "draw": 0}
    for score in judge_scores:
        votes[score.winner] += 1
    
    # 多数投票决定胜者
    winner = max(votes, key=votes.get)
    
    # 计算平均分
    prop_scores_sum = {"logic": 0, "evidence": 0, "persuasion": 0}
    opp_scores_sum = {"logic": 0, "evidence": 0, "persuasion": 0}
    
    for score in judge_scores:
        for key in ["logic", "evidence", "persuasion"]:
            prop_scores_sum[key] += score.scores["proponent"][key]
            opp_scores_sum[key] += score.scores["opponent"][key]
    
    n = len(judge_scores)
    prop_avg_total = sum(prop_scores_sum.values()) / n
    opp_avg_total = sum(opp_scores_sum.values()) / n
    
    # === 结合观众投票 (20% 权重) ===
    audience_votes = match.audience_votes or {"proponent": 0, "opponent": 0}
    total_audience_votes = sum(audience_votes.values())
    
    audience_winner = None
    if total_audience_votes > 0:
        audience_winner = "proponent" if audience_votes["proponent"] > audience_votes["opponent"] else "opponent"
        
        # 调整最终得分
        if audience_winner == "proponent":
            prop_avg_total *= 1.05  # 观众支持加成 5%
        else:
            opp_avg_total *= 1.05
    
    # 最终判定
    if prop_avg_total > opp_avg_total:
        final_winner = "proponent"
    elif opp_avg_total > prop_avg_total:
        final_winner = "opponent"
    else:
        final_winner = "draw"
    
    # 生成综合判词
    reasoning = generate_final_reasoning(judge_scores, winner, audience_winner)
    
    return MatchResult(
        winner=final_winner,
        judge_scores=judge_scores,
        final_scores={
            "proponent": round(prop_avg_total, 2),
            "opponent": round(opp_avg_total, 2)
        },
        audience_vote_weight=0.2,
        audience_winner=audience_winner,
        reasoning=reasoning,
        mvp_turn_index=find_mvp_turn(match)
    )


async def judge_single(match: MatchSession, judge_model: str) -> JudgeScore:
    """单个裁判的评分"""
    
    transcript = format_transcript(match.history)
    
    judge_prompt = f"""
你是一场高水平辩论赛的裁判。请根据以下辩论记录判决胜负。

【辩题】
{match.topic}

【正方选手】
{match.proponent_model_id} (性格: {match.proponent_personality})

【反方选手】
{match.opponent_model_id} (性格: {match.opponent_personality})

【辩论记录】
{transcript}

【评分标准】
请从以下三个维度对双方进行 0-10 分的打分：

1. **逻辑性 (Logic)**: 
   - 论证结构是否严密
   - 是否有效反驳了对方
   - 是否避免了逻辑谬误

2. **证据力 (Evidence)**: 
   - 是否使用了事实、数据或代码
   - **注意**: 工具使用是辅助手段，不是评分绝对标准
   - 如果逻辑本身足够强，不用工具也能得高分
   - 滥用工具但未切中要害，不加分

3. **说服力 (Persuasion)**: 
   - 语言表达是否清晰、有力
   - 是否切中要害
   - 是否符合其性格特点

【输出格式】
返回 JSON (严格格式):
{{
    "scores": {{
        "proponent": {{
            "logic": 8.5,
            "evidence": 9.0,
            "persuasion": 8.0
        }},
        "opponent": {{
            "logic": 7.0,
            "evidence": 6.0,
            "persuasion": 7.5
        }}
    }},
    "winner": "proponent" | "opponent" | "draw",
    "reasoning": "详细的判词，说明胜方为何获胜，败方哪里表现不足，以及双方的精彩点。(100-200字)"
}}
"""
    
    response = await query_model(judge_model, [{"role": "user", "content": judge_prompt}])
    result = parse_json(response['content'])
    
    return JudgeScore(
        judge_model=judge_model,
        scores=result['scores'],
        winner=result['winner'],
        reasoning=result['reasoning']
    )


def format_transcript(history: List[Turn]) -> str:
    """格式化辩论记录"""
    lines = []
    for turn in history:
        role_name = "正方" if turn.speaker_role == "proponent" else "反方"
        tool_info = ""
        if turn.tool_calls:
            tool_info = f"\n[工具使用: {', '.join([tc['tool_name'] for tc in turn.tool_calls])}]"
        
        lines.append(f"## {role_name} - Round {turn.round_number}")
        lines.append(turn.content)
        lines.append(tool_info)
        lines.append("")
    
    return "\n".join(lines)


def generate_final_reasoning(
    judge_scores: List[JudgeScore],
    裁判团胜者: str,
    观众胜者: Optional[str]
) -> str:
    """生成综合判词"""
    
    # 汇总裁判意见
    reasoning_parts = []
    for i, score in enumerate(judge_scores, 1):
        reasoning_parts.append(f"裁判 {i} ({score.judge_model}): {score.reasoning}")
    
    combined = "\n\n".join(reasoning_parts)
    
    audience_note = ""
    if 观众胜者:
        audience_note = f"\n\n【观众投票】: 观众更支持{观众胜者}方。"
    
    return f"【裁判团综合判词】\n\n{combined}{audience_note}"


def find_mvp_turn(match: MatchSession) -> int:
    """
    找出 MVP 回合 (最精彩的一轮)
    
    简单启发式: 工具使用最多的回合
    """
    max_tools = 0
    mvp_index = 0
    
    for i, turn in enumerate(match.history):
        if len(turn.tool_calls) > max_tools:
            max_tools = len(turn.tool_calls)
            mvp_index = i
    
    return mvp_index
```

---

### 5.3 动态 ELO 系统

```python
# backend/elo.py

from .models import MatchSession, DifficultyLevel
from .database import get_competitor, update_competitor

# 辩题难度系数
DIFFICULTY_MULTIPLIERS = {
    DifficultyLevel.EASY: 0.8,
    DifficultyLevel.MEDIUM: 1.0,
    DifficultyLevel.HARD: 1.5,
    DifficultyLevel.EXPERT: 2.0
}

def get_k_factor(matches_played: int) -> int:
    """
    动态 K 因子
    
    新手有更高的 K 值，快速定位真实水平
    """
    if matches_played < 10:
        return 64  # 新手期，快速调整
    elif matches_played < 30:
        return 32  # 成长期
    else:
        return 16  # 成熟期，稳定


async def update_elo_ratings(match: MatchSession) -> dict:
    """
    更新 ELO 分数
    
    公式: R' = R + K * D * (S - E)
    其中:
    - K: 动态 K 因子
    - D: 难度系数
    - S: 实际得分 (1/0.5/0)
    - E: 期望得分
    """
    
    # 1. 获取选手档案
    prop = await get_competitor(match.proponent_model_id)
    opp = await get_competitor(match.opponent_model_id)
    
    rating_a = prop.elo_rating
    rating_b = opp.elo_rating
    
    # 2. 计算期望胜率
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))
    
    # 3. 确定实际得分
    if match.result.winner == "proponent":
        score_a, score_b = 1.0, 0.0
    elif match.result.winner == "opponent":
        score_a, score_b = 0.0, 1.0
    else:  # draw
        score_a, score_b = 0.5, 0.5
    
    # 4. 计算 K 因子 (动态)
    k_a = get_k_factor(prop.matches_played)
    k_b = get_k_factor(opp.matches_played)
    
    # 5. 应用难度系数
    difficulty_mult = DIFFICULTY_MULTIPLIERS.get(match.topic_difficulty, 1.0)
    
    # 6. 计算新分数
    delta_a = k_a * difficulty_mult * (score_a - expected_a)
    delta_b = k_b * difficulty_mult * (score_b - expected_b)
    
    new_rating_a = int(rating_a + delta_a)
    new_rating_b = int(rating_b + delta_b)
    
    # 7. 更新数据库
    await update_competitor(
        model_id=match.proponent_model_id,
        new_rating=new_rating_a,
        result=score_a
    )
    
    await update_competitor(
        model_id=match.opponent_model_id,
        new_rating=new_rating_b,
        result=score_b
    )
    
    return {
        "proponent": {
            "old_rating": rating_a,
            "new_rating": new_rating_a,
            "change": int(delta_a)
        },
        "opponent": {
            "old_rating": rating_b,
            "new_rating": new_rating_b,
            "change": int(delta_b)
        }
    }
```

---

### 5.4 辩题管理系统

```python
# backend/topic_manager.py

from typing import List
from .models import DebateTopic, DifficultyLevel, TopicCategory

# 精选辩题库
CURATED_TOPICS = [
    # Easy - Tech
    {
        "topic": "Python 比 Java 更容易学",
        "difficulty": DifficultyLevel.EASY,
        "category": TopicCategory.TECH,
        "has_objective_answer": False,
        "expected_tools": ["web_search"],
    },
    {
        "topic": "远程办公比办公室办公更高效",
        "difficulty": DifficultyLevel.EASY,
        "category": TopicCategory.BUSINESS,
        "has_objective_answer": False,
        "expected_tools": ["web_search"],
    },
    
    # Medium - Tech
    {
        "topic": "React 比 Vue 更适合大型项目",
        "difficulty": DifficultyLevel.MEDIUM,
        "category": TopicCategory.TECH,
        "has_objective_answer": False,
        "expected_tools": ["web_search", "python"],
    },
    {
        "topic": "微服务架构优于单体架构",
        "difficulty": DifficultyLevel.MEDIUM,
        "category": TopicCategory.TECH,
        "has_objective_answer": False,
        "expected_tools": ["web_search"],
    },
    
    # Hard - Philosophy
    {
        "topic": "AI 能否创作出真正的艺术",
        "difficulty": DifficultyLevel.HARD,
        "category": TopicCategory.PHILOSOPHY,
        "has_objective_answer": False,
        "expected_tools": [],
    },
    {
        "topic": "自由意志是否存在",
        "difficulty": DifficultyLevel.HARD,
        "category": TopicCategory.PHILOSOPHY,
        "has_objective_answer": False,
        "expected_tools": ["web_search"],
    },
    
    # Expert - Science
    {
        "topic": "暗物质的本质是轴子还是WIMP",
        "difficulty": DifficultyLevel.EXPERT,
        "category": TopicCategory.SCIENCE,
        "has_objective_answer": True,
        "expected_tools": ["web_search"],
    },
    {
        "topic": "量子计算能否在10年内实现商用",
        "difficulty": DifficultyLevel.EXPERT,
        "category": TopicCategory.SCIENCE,
        "has_objective_answer": False,
        "expected_tools": ["web_search", "calculator"],
    },
]

async def get_topics_by_difficulty(difficulty: DifficultyLevel) -> List[DebateTopic]:
    """根据难度获取辩题"""
    from .database import query_topics
    
    return await query_topics(difficulty=difficulty)


async def recommend_topic(
    prop_elo: int,
    opp_elo: int
) -> DebateTopic:
    """
    智能推荐辩题
    
    规则:
    - 平均 ELO < 1300: Easy
    - 1300-1450: Medium
    - 1450-1600: Hard
    - > 1600: Expert
    """
    avg_elo = (prop_elo + opp_elo) / 2
    
    if avg_elo < 1300:
        difficulty = DifficultyLevel.EASY
    elif avg_elo < 1450:
        difficulty = DifficultyLevel.MEDIUM
    elif avg_elo < 1600:
        difficulty = DifficultyLevel.HARD
    else:
        difficulty = DifficultyLevel.EXPERT
    
    topics = await get_topics_by_difficulty(difficulty)
    
    # 返回使用次数最少的辩题 (保证新鲜度)
    return min(topics, key=lambda t: t.usage_count)
```

---

### 5.5 风格分析系统

```python
# backend/style_analyzer.py

from typing import Dict
from .models import MatchSession, Turn

async def analyze_debate_style(match: MatchSession) -> Dict[str, Dict[str, float]]:
    """
    赛后分析辩论风格
    
    返回:
    {
        "proponent": {
            "logic_heavy": 0.8,      # 逻辑导向
            "evidence_heavy": 0.9,   # 数据导向
            "emotional": 0.3,        # 感性程度
            "aggressive": 0.6,       # 攻击性
            "tool_usage": 0.7        # 工具依赖度
        },
        "opponent": {...}
    }
    """
    
    prop_turns = [t for t in match.history if t.speaker_role == "proponent"]
    opp_turns = [t for t in match.history if t.speaker_role == "opponent"]
    
    prop_style = calculate_style(prop_turns, match.result.judge_scores, "proponent")
    opp_style = calculate_style(opp_turns, match.result.judge_scores, "opponent")
    
    return {
        "proponent": prop_style,
        "opponent": opp_style
    }


def calculate_style(turns: List[Turn], judge_scores, role: str) -> Dict[str, float]:
    """计算单方风格"""
    
    # 统计数据
    total_words = sum(len(t.content) for t in turns)
    total_tools = sum(len(t.tool_calls) for t in turns)
    
    # 从裁判评分中提取
    avg_logic = sum(s.scores[role]["logic"] for s in judge_scores) / len(judge_scores)
    avg_evidence = sum(s.scores[role]["evidence"] for s in judge_scores) / len(judge_scores)
    
    # 计算风格指标
    logic_heavy = avg_logic / 10  # 归一化到 0-1
    evidence_heavy = avg_evidence / 10
    
    tool_usage = min(total_tools / (len(turns) * 2), 1.0)  # 平均每轮2个工具算满分
    
    # 情感分析 (简化版: 检测感叹号、问句)
    emotional_markers = sum(t.content.count("!") + t.content.count("?") for t in turns)
    emotional = min(emotional_markers / total_words * 100, 1.0)
    
    # 攻击性 (检测否定词汇)
    attack_keywords = ["错误", "荒谬", "不对", "漏洞", "反驳", "驳斥"]
    attack_count = sum(
        sum(t.content.count(kw) for kw in attack_keywords)
        for t in turns
    )
    aggressive = min(attack_count / len(turns) / 5, 1.0)
    
    return {
        "logic_heavy": round(logic_heavy, 2),
        "evidence_heavy": round(evidence_heavy, 2),
        "emotional": round(emotional, 2),
        "aggressive": round(aggressive, 2),
        "tool_usage": round(tool_usage, 2)
    }
```

---

### 5.6 赛后复盘系统

```python
# backend/replay_analyzer.py

from .models import MatchSession
from .llm_client import query_model

async def generate_match_review(match: MatchSession) -> str:
    """
    生成赛后复盘报告
    
    让一个"教练 LLM"分析比赛，给出改进建议
    """
    
    transcript = format_transcript(match.history)
    result_summary = format_result(match.result)
    
    coach_prompt = f"""
你是一位经验丰富的辩论教练。请分析这场辩论，给出专业的复盘建议。

【辩题】
{match.topic}

【比赛结果】
{result_summary}

【辩论记录】
{transcript}

【复盘任务】
请从以下角度进行分析：

1. **胜方的制胜关键** (2-3点)
   - 哪些论证最有力？
   - 哪次反驳最致命？
   - 工具使用是否得当？

2. **败方的失误分析** (2-3点)
   - 错过了哪些反驳机会？
   - 哪些论证站不住脚？
   - 应该如何调整策略？

3. **如果重来的建议** (针对败方)
   - 开篇应该如何立论？
   - 应该使用哪些工具？
   - 应该采取什么辩论策略？

4. **精彩瞬间点评**
   - 双方各有哪些亮点？

【输出格式】
使用 Markdown 格式，分段清晰，便于阅读。
"""
    
    response = await query_model("gpt-4o", [{"role": "user", "content": coach_prompt}])
    
    return response['content']


def format_result(result) -> str:
    """格式化比赛结果"""
    return f"""
胜者: {result.winner}
最终得分: 正方 {result.final_scores['proponent']} vs 反方 {result.final_scores['opponent']}
裁判团意见: {len(result.judge_scores)} 位裁判
观众投票: {result.audience_winner or '未投票'}
"""
```

---

## 公平性保障机制

### 6.1 裁判公正性

```python
# 多重保障机制

1. **多裁判投票制**
   - 至少 2 位裁判
   - 排除参赛选手
   - 多数投票决定胜负

2. **观众投票权重**
   - 观众投票占 20% 权重
   - 避免裁判独断

3. **评分标准明确**
   - 工具不是绝对标准
   - 逻辑 > 证据 > 说服力

4. **判词透明化**
   - 每个裁判都要给出理由
   - 用户可以查看所有裁判意见
```

### 6.2 辩题公平性

```python
# 辩题设计原则

1. **避免绝对真理型**
   - ❌ "1+1=2"
   - ✅ "数学是发现还是发明"

2. **正反方势均力敌**
   - 避免"正方必胜"的辩题
   - 示例: "AI 会取代人类" → 正反都有论据

3. **难度匹配 ELO**
   - 新手不给 Expert 辩题
   - 高手不给 Easy 辩题
```

---

## 游戏化设计

### 7.1 成就系统

```python
# backend/achievements.py

ACHIEVEMENTS = [
    {
        "id": "first_win",
        "name": "首胜",
        "description": "赢得第一场比赛",
        "icon": "🏆",
        "condition": lambda stats: stats["wins"] >= 1
    },
    {
        "id": "tool_master",
        "name": "工具大师",
        "description": "在一场比赛中使用 5 次以上工具",
        "icon": "🔧",
        "condition": lambda match: sum(len(t.tool_calls) for t in match.history) >= 5
    },
    {
        "id": "elo_1500",
        "name": "大师段位",
        "description": "ELO 达到 1500",
        "icon": "⭐",
        "condition": lambda stats: stats["elo_rating"] >= 1500
    },
]
```

### 7.2 每日挑战

```python
# backend/daily_challenge.py

async def generate_daily_challenge():
    """
    每日自动生成一个热点辩题
    让排行榜 Top 2 自动对决
    """
    from .database import get_top_competitors
    
    # 获取榜首和榜二
    top2 = await get_top_competitors(limit=2)
    
    # 生成当日热点辩题 (调用 LLM)
    topic = await generate_trending_topic()
    
    # 自动开赛
    match = await run_tournament_match(
        topic=topic,
        prop_model_id=top2[0].model_id,
        opp_model_id=top2[1].model_id,
        rounds=3
    )
    
    return match
```

---

## 前端交互设计

### 8.1 竞技场页面 (Arena)

```typescript
// frontend/src/pages/Arena.tsx

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { useSSE } from '@/hooks/useSSE';

export function Arena() {
  const [topic, setTopic] = useState('');
  const [propModel, setPropModel] = useState('');
  const [oppModel, setOppModel] = useState('');
  const [propPersonality, setPropPersonality] = useState('rational');
  const [oppPersonality, setOppPersonality] = useState('aggressive');
  
  const { messages, connect, isConnected, clearMessages } = useSSE();
  
  const startMatch = async () => {
    clearMessages();
    
    const config = {
      topic,
      proponent_model: propModel,
      opponent_model: oppModel,
      proponent_personality: propPersonality,
      opponent_personality: oppPersonality,
      rounds: 3
    };
    
    // 连接 SSE 接收流式输出
    connect('/api/tournament/match/stream', config);
  };
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">🔥 辩论竞技场</h1>
      
      {/* 配置区 */}
      <Card className="p-6 mb-6">
        <div className="grid grid-cols-2 gap-6">
          {/* 正方配置 */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-blue-600">正方 (Affirmative)</h3>
            <Select
              value={propModel}
              onChange={setPropModel}
              options={[
                { value: 'gpt-4o', label: 'GPT-4o (ELO: 1450)' },
                { value: 'claude-3.5-sonnet', label: 'Claude-3.5 (ELO: 1420)' },
              ]}
            />
            <Select
              value={propPersonality}
              onChange={setPropPersonality}
              options={[
                { value: 'rational', label: '🧠 理性分析型' },
                { value: 'aggressive', label: '⚔️ 激进攻击型' },
                { value: 'diplomatic', label: '🤝 温和外交型' },
                { value: 'humorous', label: '😄 幽默讽刺型' },
                { value: 'academic', label: '📚 学术严谨型' },
              ]}
            />
          </div>
          
          {/* 反方配置 */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-red-600">反方 (Negative)</h3>
            <Select value={oppModel} onChange={setOppModel} />
            <Select value={oppPersonality} onChange={setOppPersonality} />
          </div>
        </div>
        
        {/* 辩题输入 */}
        <div className="mt-6">
          <label className="block text-sm font-medium mb-2">辩题</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="例如: Python 比 Java 更适合做后端开发"
            className="w-full p-3 border rounded-lg"
          />
        </div>
        
        <Button
          onClick={startMatch}
          className="w-full mt-6 bg-gradient-to-r from-blue-500 to-red-500 text-white text-lg py-3"
          disabled={!topic || !propModel || !oppModel}
        >
          ⚔️ 开始对决！
        </Button>
      </Card>
      
      {/* 辩论展示区 */}
      <DebateViewer messages={messages} />
    </div>
  );
}
```

### 8.2 实时流式展示

```typescript
// frontend/src/components/DebateViewer.tsx

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

export function DebateViewer({ messages }) {
  const [turns, setTurns] = useState([]);
  const [currentStatus, setCurrentStatus] = useState('');
  
  useEffect(() => {
    messages.forEach(msg => {
      if (msg.type === 'turn') {
        setTurns(prev => [...prev, msg.data]);
      } else if (msg.type === 'status') {
        setCurrentStatus(msg.content);
      }
    });
  }, [messages]);
  
  return (
    <div className="space-y-4">
      {/* 状态提示 */}
      <AnimatePresence>
        {currentStatus && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="bg-yellow-100 p-4 rounded-lg text-center"
          >
            <div className="animate-pulse">{currentStatus}</div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* 辩论记录 */}
      <div className="grid grid-cols-2 gap-4">
        {turns.map((turn, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: turn.speaker_role === 'proponent' ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`
              ${turn.speaker_role === 'proponent' ? 'col-start-1' : 'col-start-2'}
              p-4 rounded-lg shadow-md
              ${turn.speaker_role === 'proponent' ? 'bg-blue-50' : 'bg-red-50'}
            `}
          >
            <div className="flex items-center mb-2">
              <span className="font-bold">
                {turn.speaker_role === 'proponent' ? '🔵 正方' : '🔴 反方'}
              </span>
              <span className="text-sm text-gray-500 ml-2">Round {turn.round_number}</span>
            </div>
            
            <ReactMarkdown className="prose">
              {turn.content}
            </ReactMarkdown>
            
            {/* 工具调用展示 */}
            {turn.tool_calls?.length > 0 && (
              <details className="mt-4 bg-white p-2 rounded">
                <summary className="cursor-pointer font-medium">
                  🔧 使用了 {turn.tool_calls.length} 个工具
                </summary>
                {turn.tool_calls.map((tc, j) => (
                  <div key={j} className="mt-2 text-sm">
                    <strong>{tc.tool_name}</strong>
                    <SyntaxHighlighter language="python">
                      {tc.arguments}
                    </SyntaxHighlighter>
                    <pre className="bg-gray-100 p-2 rounded text-xs">
                      {JSON.stringify(tc.result, null, 2)}
                    </pre>
                  </div>
                ))}
              </details>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
```

### 8.3 排行榜页面

```typescript
// frontend/src/pages/Leaderboard.tsx

import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function Leaderboard() {
  const [competitors, setCompetitors] = useState([]);
  
  useEffect(() => {
    fetch('/api/tournament/leaderboard')
      .then(res => res.json())
      .then(data => setCompetitors(data));
  }, []);
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">🏆 天梯榜</h1>
      
      <div className="grid gap-4">
        {competitors.map((comp, i) => (
          <Card key={comp.model_id} className="p-4 hover:shadow-lg transition">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="text-3xl font-bold text-gray-400">#{i + 1}</div>
                <div>
                  <h3 className="text-xl font-bold">{comp.display_name}</h3>
                  <div className="text-sm text-gray-500">
                    {comp.matches_played} 场 · 胜率 {comp.win_rate}%
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-3xl font-bold text-yellow-600">
                  {comp.elo_rating}
                </div>
                <div className="text-sm text-gray-500">ELO Rating</div>
              </div>
            </div>
            
            {/* ELO 趋势图 */}
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-blue-600">
                查看 ELO 历史
              </summary>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={comp.elo_history}>
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="rating" stroke="#3b82f6" />
                </LineChart>
              </ResponsiveContainer>
            </details>
            
            {/* 风格雷达图 */}
            <details className="mt-2">
              <summary className="cursor-pointer text-sm text-blue-600">
                查看辩论风格
              </summary>
              <RadarChart data={comp.style_stats} />
            </details>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

---

## API 接口设计

### 9.1 接口列表

```yaml
# 比赛相关
POST   /api/tournament/match/stream   # SSE 流式推送比赛
GET    /api/tournament/match/{id}    # 获取比赛详情

# 排行榜
GET    /api/tournament/leaderboard    # 获取排行榜
GET    /api/tournament/competitor/{model_id}  # 获取选手详情

# 辩题
GET    /api/tournament/topics         # 获取辩题列表
GET    /api/tournament/topics/recommend  # 推荐辩题

# 观众投票
POST   /api/tournament/vote           # 提交投票

# 历史记录
GET    /api/tournament/matches/history  # 获取历史记录
GET    /api/tournament/matches/{id}/replay  # 查看回放

# 复盘
GET    /api/tournament/matches/{id}/review  # 获取复盘报告
```

### 9.2 SSE 事件流

```json
// SSE 事件类型 (格式: data: {json}\n\n)

// 1. 比赛开始
data: {"type": "match_start", "data": {"match_id": "xxx", "topic": "..."}}

// 2. 状态更新
data: {"type": "status", "speaker": "proponent", "content": "正方正在思考..."}

// 3. 发言推送（流式增量）
data: {"type": "turn_delta", "speaker": "proponent", "delta": "我认为", "round": 1}

// 4. 发言完成
data: {"type": "turn_complete", "turn": {"round_number": 1, "speaker_role": "proponent", "content": "...", "tool_calls": [...]}}

// 5. 裁判打分
data: {"type": "judging", "progress": 0.33, "judge": "gpt-4o"}

// 6. 结果公布
data: {"type": "judge_complete", "result": {"winner": "proponent", "final_scores": {...}, "reasoning": "..."}}

// 7. ELO 更新
data: {"type": "elo_update", "data": {"proponent": {"change": 15}, "opponent": {"change": -15}}}

// 8. 比赛结束
data: {"type": "match_end", "match_id": "xxx"}
```

---

## 部署方案

### 10.1 开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### 10.2 生产环境

```yaml
# docker-compose.yml

version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/tournament
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - SERPER_API_KEY=${SERPER_API_KEY}
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=tournament
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### 10.3 性能优化

```python
# 1. Redis 缓存热门辩题
@cache(ttl=3600)
async def get_trending_topics():
    pass

# 2. 数据库索引
CREATE INDEX idx_competitors_elo ON competitors(elo_rating DESC);
CREATE INDEX idx_matches_created ON matches(created_at DESC);

# 3. 裁判并行调用
async def judge_match_with_panel(match):
    tasks = [judge_single(match, j) for j in JUDGE_PANEL]
    results = await asyncio.gather(*tasks)  # 并行

# 4. WebSocket 连接池
# 使用 FastAPI 原生 WebSocket Manager
```

---

## 总结

### v4 的核心亮点

1. ✅ **多裁判投票制** - 公平性保障
2. ✅ **动态 ELO + 难度系数** - 排位更准确
3. ✅ **辩题分级系统** - 匹配选手水平
4. ✅ **工具使用明确规则** - 避免滥用
5. ✅ **实时流式展示** - 用户体验佳
6. ✅ **观众投票** - 社区参与
7. ✅ **风格分析** - 数据可视化
8. ✅ **赛后复盘** - 教练级建议
9. ✅ **人机对战** - 互动性强
10. ✅ **性格注入** - 辩论更生动
11. ✅ **历史记录** - 完整数据沉淀

### 技术栈优势

- **后端**: FastAPI + SQLAlchemy + SSE (异步、高性能)
- **前端**: React + Vite + shadcn/ui (现代化、开发效率高)
- **数据库**: SQLite/PostgreSQL (灵活切换)
- **实时通信**: SSE (低延迟、流式输出、自动重连)

### 下一步行动

1. **Phase 1 (MVP)**: 实现核心对战功能 + 基础排行榜
2. **Phase 2**: 加入观众投票 + 风格分析
3. **Phase 3**: 复盘系统 + 人机对战
4. **Phase 4**: 社区功能 + 每日挑战

---

**LLM Debate Tournament v4** - 让 AI 在竞技中展现真正的智慧！🔥⚔️🏆
