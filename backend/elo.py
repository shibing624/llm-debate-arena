# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
ELO Rating System - 动态排位算法"""

from .models import MatchSession, DifficultyLevel
from .database import get_competitor, update_competitor
from .config import ELO_CONFIG

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
    """
    
    # 1. 获取选手档案
    prop = await get_competitor(match.proponent_model_id)
    opp = await get_competitor(match.opponent_model_id)
    
    if not prop or not opp:
        return {
            "proponent": {"old_rating": 1200, "new_rating": 1200, "change": 0},
            "opponent": {"old_rating": 1200, "new_rating": 1200, "change": 0}
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
