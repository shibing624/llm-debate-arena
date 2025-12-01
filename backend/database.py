# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 数据库操作
"""

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from datetime import datetime
import json
import os

from .config import DATABASE_URL, AVAILABLE_MODELS
from .log import logger
from .models import (
    Base, CompetitorModel, DebateTopicModel, MatchModel,
    DifficultyLevel, TopicCategory, PersonalityType,
    MatchSession, CompetitorProfile, DebateTopic
)

# SQLite 数据库（启用 WAL 模式以支持更好的并发）
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # 增加超时时间，避免 database locked
    },
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True  # 连接前检查可用性
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
    
    # 启用 WAL 模式以支持更好的并发
    try:
        import sqlite3
        # 从 DATABASE_URL 中提取数据库文件路径
        # DATABASE_URL 格式: sqlite:///./debate_arena.db
        db_path = DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.close()
    except Exception as e:
        logger.error(f"启用 WAL 模式失败: {e}")
    
    # 初始化默认数据
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(CompetitorModel).count() == 0:
            _init_default_competitors(db)
        if db.query(DebateTopicModel).count() == 0:
            _init_default_topics(db)
        db.commit()
    finally:
        db.close()


def _init_default_competitors(db: Session):
    """从环境变量初始化选手"""
    # 从环境变量读取可用模型列表
    model_ids = [m.strip() for m in AVAILABLE_MODELS.split(",") if m.strip()]
    
    competitors = []
    for model_id in model_ids:
        competitors.append(
            CompetitorModel(
                model_id=model_id,
                display_name=model_id.upper(),  # 直接使用 model_id 的大写形式
                provider="",  # provider 置空
                elo_rating=1200
            )
        )
    
    if competitors:
        db.add_all(competitors)


def _init_default_topics(db: Session):
    """初始化默认辩题"""
    topics = [
        DebateTopicModel(
            topic="Python 比 Java 更容易学",
            difficulty=DifficultyLevel.EASY,
            category=TopicCategory.TECH,
            has_objective_answer=False,
            expected_tools=["web_search"]
        ),
        DebateTopicModel(
            topic="远程办公比办公室办公更高效",
            difficulty=DifficultyLevel.EASY,
            category=TopicCategory.BUSINESS,
            has_objective_answer=False,
            expected_tools=["web_search"]
        ),
        DebateTopicModel(
            topic="React 比 Vue 更适合大型项目",
            difficulty=DifficultyLevel.MEDIUM,
            category=TopicCategory.TECH,
            has_objective_answer=False,
            expected_tools=["web_search", "python_interpreter"]
        ),
        DebateTopicModel(
            topic="微服务架构优于单体架构",
            difficulty=DifficultyLevel.MEDIUM,
            category=TopicCategory.TECH,
            has_objective_answer=False,
            expected_tools=["web_search"]
        ),
        DebateTopicModel(
            topic="AI 能否创作出真正的艺术",
            difficulty=DifficultyLevel.HARD,
            category=TopicCategory.PHILOSOPHY,
            has_objective_answer=False,
            expected_tools=[]
        ),
        DebateTopicModel(
            topic="自由意志是否存在",
            difficulty=DifficultyLevel.HARD,
            category=TopicCategory.PHILOSOPHY,
            has_objective_answer=False,
            expected_tools=["web_search"]
        ),
    ]
    db.add_all(topics)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== 选手相关 ==========

async def get_competitor(model_id: str) -> Optional[CompetitorModel]:
    """获取选手信息"""
    db = SessionLocal()
    try:
        return db.query(CompetitorModel).filter(CompetitorModel.model_id == model_id).first()
    finally:
        db.close()


async def get_all_competitors() -> List[CompetitorProfile]:
    """获取所有选手"""
    db = SessionLocal()
    try:
        competitors = db.query(CompetitorModel).order_by(desc(CompetitorModel.elo_rating)).all()
        return [_competitor_to_profile(c) for c in competitors]
    finally:
        db.close()


async def update_competitor(model_id: str, new_rating: int, result: float):
    """更新选手数据（带重试机制，避免并发冲突）"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        db = SessionLocal()
        try:
            competitor = db.query(CompetitorModel).filter(
                CompetitorModel.model_id == model_id
            ).with_for_update().first()  # 使用行锁
            
            if competitor:
                competitor.elo_rating = new_rating
                competitor.matches_played += 1
                
                if result == 1.0:
                    competitor.wins += 1
                elif result == 0.0:
                    competitor.losses += 1
                else:
                    competitor.draws += 1
                
                # 更新 ELO 历史
                if not competitor.elo_history:
                    competitor.elo_history = []
                competitor.elo_history.append({
                    "date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "rating": new_rating
                })
                
                competitor.last_match_at = datetime.utcnow()
                db.commit()
                break  # 成功，退出循环
        except Exception as e:
            db.rollback()
            retry_count += 1
            if retry_count >= max_retries:
                raise e
            # 简单的退避策略
            import time
            time.sleep(0.1 * retry_count)
        finally:
            db.close()


def _competitor_to_profile(c: CompetitorModel) -> CompetitorProfile:
    """转换为 Profile 对象"""
    win_rate = (c.wins / c.matches_played * 100) if c.matches_played > 0 else 0
    return CompetitorProfile(
        model_id=c.model_id,
        display_name=c.display_name,
        provider=c.provider,
        elo_rating=c.elo_rating,
        matches_played=c.matches_played,
        wins=c.wins,
        losses=c.losses,
        draws=c.draws,
        win_rate=round(win_rate, 1),
        elo_history=c.elo_history or [],
        style_stats=c.style_stats or {}
    )


# ========== 辩题相关 ==========

async def get_topics_by_difficulty(difficulty: DifficultyLevel) -> List[DebateTopic]:
    """根据难度获取辩题"""
    db = SessionLocal()
    try:
        topics = db.query(DebateTopicModel).filter(
            DebateTopicModel.difficulty == difficulty
        ).all()
        return [_topic_to_pydantic(t) for t in topics]
    finally:
        db.close()


async def get_all_topics() -> List[DebateTopic]:
    """获取所有辩题"""
    db = SessionLocal()
    try:
        topics = db.query(DebateTopicModel).all()
        return [_topic_to_pydantic(t) for t in topics]
    finally:
        db.close()


def _topic_to_pydantic(t: DebateTopicModel) -> DebateTopic:
    """转换为 Pydantic 对象"""
    return DebateTopic(
        id=t.id,
        topic=t.topic,
        difficulty=t.difficulty,
        category=t.category,
        has_objective_answer=t.has_objective_answer,
        expected_tools=t.expected_tools or [],
        usage_count=t.usage_count,
        avg_rating=t.avg_rating
    )


# ========== 比赛相关 ==========

async def save_match(match: MatchSession):
    """保存或更新比赛（带重试机制）"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        db = SessionLocal()
        try:
            # 检查是否已存在
            existing = db.query(MatchModel).filter(MatchModel.match_id == match.match_id).first()
            
            # 序列化 Turn 对象，处理 datetime
            transcript_json = []
            for t in match.history:
                turn_dict = t.model_dump(mode='json')
                # 确保 timestamp 是 ISO 格式字符串
                if 'timestamp' in turn_dict and isinstance(turn_dict['timestamp'], datetime):
                    turn_dict['timestamp'] = turn_dict['timestamp'].isoformat()
                transcript_json.append(turn_dict)
            
            # 序列化 result
            judge_result_json = None
            if match.result:
                judge_result_json = match.result.model_dump(mode='json')
            
            # 确保 created_at 是 datetime 对象
            created_at_value = match.created_at
            if isinstance(created_at_value, str):
                from datetime import datetime as dt
                created_at_value = dt.fromisoformat(created_at_value)
            
            if existing:
                # 更新现有记录
                existing.topic = match.topic
                existing.topic_difficulty = match.topic_difficulty
                existing.rounds_setting = match.rounds_setting
                existing.proponent_model_id = match.proponent_model_id
                existing.opponent_model_id = match.opponent_model_id
                existing.proponent_personality = match.proponent_personality
                existing.opponent_personality = match.opponent_personality
                existing.status = match.status
                existing.transcript = transcript_json
                existing.judge_result = judge_result_json
                existing.audience_votes = match.audience_votes
                existing.user_id = match.user_id  # 更新用户ID
                if match.status == "FINISHED":
                    existing.finished_at = datetime.utcnow()
            else:
                # 创建新记录
                match_model = MatchModel(
                    match_id=match.match_id,
                    topic=match.topic,
                    topic_difficulty=match.topic_difficulty,
                    rounds_setting=match.rounds_setting,
                    proponent_model_id=match.proponent_model_id,
                    opponent_model_id=match.opponent_model_id,
                    proponent_personality=match.proponent_personality,
                    opponent_personality=match.opponent_personality,
                    status=match.status,
                    transcript=transcript_json,
                    judge_result=judge_result_json,
                    audience_votes=match.audience_votes,
                    user_id=match.user_id,  # 保存用户ID
                    created_at=created_at_value
                )
                db.add(match_model)
            
            db.commit()
            break  # 成功，退出循环
        except Exception as e:
            db.rollback()
            retry_count += 1
            if retry_count >= max_retries:
                raise e
            import time
            time.sleep(0.1 * retry_count)
        finally:
            db.close()


async def update_match_status(match_id: str, status: str, elo_changes: dict = None):
    """更新比赛状态和 ELO 变化"""
    db = SessionLocal()
    try:
        match = db.query(MatchModel).filter(MatchModel.match_id == match_id).first()
        if match:
            match.status = status
            if status == "FINISHED":
                match.finished_at = datetime.utcnow()
            if elo_changes:
                match.elo_changes = elo_changes
            db.commit()
    finally:
        db.close()


async def get_match(match_id: str) -> Optional[MatchModel]:
    """获取比赛详情"""
    db = SessionLocal()
    try:
        return db.query(MatchModel).filter(MatchModel.match_id == match_id).first()
    finally:
        db.close()


async def get_match_history(limit: int = 20, model_id: str = None, user_id: int = None) -> List[MatchModel]:
    """获取历史比赛（支持按模型和用户筛选）"""
    db = SessionLocal()
    try:
        query = db.query(MatchModel)
        
        # 按模型筛选（包含正方或反方）
        if model_id:
            query = query.filter(
                (MatchModel.proponent_model_id == model_id) | 
                (MatchModel.opponent_model_id == model_id)
            )
        
        # 按用户筛选
        if user_id:
            query = query.filter(MatchModel.user_id == user_id)
        
        return query.order_by(desc(MatchModel.created_at)).limit(limit).all()
    finally:
        db.close()
