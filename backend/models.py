# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 数据模型定义
"""

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Enum, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, ConfigDict
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
    model_id = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    provider = Column(String(50))
    
    # ELO 数据
    elo_rating = Column(Integer, default=1200)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    
    # ELO 历史
    elo_history = Column(JSON, default=list)
    
    # 风格分析
    style_stats = Column(JSON, default=dict)
    
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
    
    has_objective_answer = Column(Boolean, default=False)
    expected_tools = Column(JSON, default=list)
    
    usage_count = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserModel(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 用户信息
    display_name = Column(String(100))
    avatar_url = Column(String(500))
    
    # 统计数据
    matches_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)


class MatchModel(Base):
    """比赛记录表"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(36), unique=True)
    
    # 用户关联
    user_id = Column(Integer, nullable=True)  # 可选，未登录用户为 None
    
    topic = Column(String(500), nullable=False)
    topic_difficulty = Column(Enum(DifficultyLevel))
    rounds_setting = Column(Integer, default=3)
    
    proponent_model_id = Column(String(100), nullable=False)
    opponent_model_id = Column(String(100), nullable=False)
    proponent_personality = Column(Enum(PersonalityType))
    opponent_personality = Column(Enum(PersonalityType))
    
    status = Column(String(20))
    transcript = Column(JSON, default=list)
    judge_result = Column(JSON)
    audience_votes = Column(JSON, default=dict)
    elo_changes = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)


# ========== Pydantic 模型 (API 交互) ==========

class Turn(BaseModel):
    """单次发言"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    round_number: int
    speaker_role: Literal["proponent", "opponent"]
    model_id: str
    content: str
    tool_calls: List[Dict] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JudgeScore(BaseModel):
    """单个裁判的评分"""
    judge_model: str
    scores: Dict[str, Dict[str, float]]
    winner: Literal["proponent", "opponent", "draw"]
    reasoning: str


class MatchResult(BaseModel):
    """比赛结果"""
    winner: Literal["proponent", "opponent", "draw"]
    judge_scores: List[JudgeScore]
    final_scores: Dict[str, float]
    audience_vote_weight: float = 0.2
    audience_winner: Optional[str] = None
    reasoning: str
    mvp_turn_index: int


class MatchSession(BaseModel):
    """完整比赛会话"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    match_id: str
    topic: str
    topic_difficulty: DifficultyLevel
    
    proponent_model_id: str
    opponent_model_id: str
    proponent_personality: PersonalityType
    opponent_personality: PersonalityType
    
    rounds_setting: int = 3
    history: List[Turn] = []
    result: Optional[MatchResult] = None
    status: Literal["PREPARING", "FIGHTING", "JUDGING", "FINISHED", "CANCELLED"] = "PREPARING"
    audience_votes: Dict[str, int] = Field(default_factory=lambda: {"proponent": 0, "opponent": 0})
    user_id: Optional[int] = None  # 用户ID
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CompetitorProfile(BaseModel):
    """选手档案"""
    model_id: str
    display_name: str
    provider: str
    elo_rating: int
    matches_played: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    elo_history: List[Dict]
    style_stats: Dict


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


class MatchRequest(BaseModel):
    """比赛请求"""
    topic: str
    topic_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    proponent_model: str
    opponent_model: str
    proponent_personality: Optional[str] = ""
    opponent_personality: Optional[str] = ""
    rounds: int = 3
    judges: List[str] = Field(default_factory=lambda: ["gpt-4o", "gpt-4o-mini"])
    enabled_tools: List[str] = Field(default_factory=list)  # 默认为空列表，不启用任何工具
    user_id: Optional[int] = None  # 用户ID（可选）


# ========== 用户相关模型 ==========

class UserRegister(BaseModel):
    """用户注册"""
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class UserProfile(BaseModel):
    """用户信息"""
    id: int
    username: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    matches_count: int
    created_at: datetime

