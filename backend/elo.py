# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
ELO Rating System - 动态排位算法"""

from typing import List
from .models import MatchSession, DifficultyLevel, Turn
from .database import get_competitor, update_competitor
from .config import ELO_CONFIG
from .log import logger

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
        return ELO_CONFIG['k_factor_new']
    elif matches_played < 30:
        return ELO_CONFIG['k_factor_mid']
    else:
        return ELO_CONFIG['k_factor_stable']


async def update_elo_ratings(match: MatchSession) -> dict:
    """
    更新 ELO 分数
    
    公式: R' = R + K * D * (S - E)
    
    注意：如果任一方的回答为空或无效，则不更新 ELO
    """
    
    # 0. 验证比赛内容有效性
    if not validate_match_content(match):
        logger.warning(f"⚠️ 比赛 {match.match_id} 内容无效，跳过 ELO 更新")
        return {
            "proponent": {"old_rating": 0, "new_rating": 0, "change": 0, "skipped": True, "reason": "内容无效"},
            "opponent": {"old_rating": 0, "new_rating": 0, "change": 0, "skipped": True, "reason": "内容无效"}
        }
    
    # 1. 获取选手档案
    prop = await get_competitor(match.proponent_model_id)
    opp = await get_competitor(match.opponent_model_id)
    
    if not prop or not opp:
        logger.warning(f"⚠️ 无法获取选手档案，跳过 ELO 更新")
        return {
            "proponent": {"old_rating": 1200, "new_rating": 1200, "change": 0, "skipped": True, "reason": "选手档案缺失"},
            "opponent": {"old_rating": 1200, "new_rating": 1200, "change": 0, "skipped": True, "reason": "选手档案缺失"}
        }
    
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
    
    # 4. 计算 K 因子
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


def validate_match_content(match: MatchSession) -> bool:
    """
    验证比赛内容是否有效
    
    检查项：
    1. 双方是否都有发言
    2. 发言内容是否为空或过短
    3. 是否至少有一个完整回合
    
    Returns:
        bool: 内容有效返回 True，否则返回 False
    """
    if not match.history or len(match.history) == 0:
        logger.warning(f"⚠️ 比赛 {match.match_id} 没有任何发言记录")
        return False
    
    # 检查正方和反方是否都有发言
    prop_turns = [t for t in match.history if t.speaker_role == "proponent"]
    opp_turns = [t for t in match.history if t.speaker_role == "opponent"]
    
    if not prop_turns:
        logger.warning(f"⚠️ 比赛 {match.match_id} 正方没有发言")
        return False
    
    if not opp_turns:
        logger.warning(f"⚠️ 比赛 {match.match_id} 反方没有发言")
        return False
    
    # 检查是否有空内容或过短内容（少于 10 个字符）
    MIN_CONTENT_LENGTH = 10
    
    for turn in prop_turns:
        if not turn.content or len(turn.content.strip()) < MIN_CONTENT_LENGTH:
            logger.warning(f"⚠️ 比赛 {match.match_id} 正方 Round {turn.round_number} 内容为空或过短: '{turn.content[:50] if turn.content else ''}'")
            return False
    
    for turn in opp_turns:
        if not turn.content or len(turn.content.strip()) < MIN_CONTENT_LENGTH:
            logger.warning(f"⚠️ 比赛 {match.match_id} 反方 Round {turn.round_number} 内容为空或过短: '{turn.content[:50] if turn.content else ''}'")
            return False
    
    # 检查是否至少有一个完整回合（正方+反方都在同一回合发言）
    round_numbers = set([t.round_number for t in match.history])
    complete_rounds = []
    
    for round_num in round_numbers:
        round_turns = [t for t in match.history if t.round_number == round_num]
        speakers = set([t.speaker_role for t in round_turns])
        # 完整回合：正反双方都发言了
        if "proponent" in speakers and "opponent" in speakers:
            complete_rounds.append(round_num)
    
    if not complete_rounds:
        logger.warning(f"⚠️ 比赛 {match.match_id} 没有完整回合（正反双方都发言）")
        return False
    
    logger.info(f"✅ 比赛 {match.match_id} 内容有效: {len(prop_turns)} 正方发言, {len(opp_turns)} 反方发言, {len(complete_rounds)} 完整回合")
    return True
