# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Judge Panel - 多裁判投票制
"""

import asyncio
from typing import List, Optional, AsyncGenerator

from .log import logger
from .models import MatchSession, JudgeScore, MatchResult, Turn
from .llm_client import query_model
from .utils import parse_json
from .config import JUDGE_PANEL


async def judge_match_with_panel_stream(match: MatchSession, judges: List[str] = None) -> AsyncGenerator[dict, None]:
    """
    多裁判投票制 (流式)
    
    Yields:
        {"type": "judge_start", "judges": [...]}
        {"type": "judge_progress", "judge": "gpt-4o", "progress": 0.33}
        {"type": "judge_score", "judge_score": JudgeScore}
        {"type": "judge_complete", "result": MatchResult}
    """
    
    logger.info("👨‍⚖️ 开始裁判评分")
    
    # 使用传入的裁判团，或使用配置的默认裁判团
    if judges is None:
        from .config import JUDGE_PANEL
        judges = JUDGE_PANEL
    
    # 筛选裁判 (排除参赛选手)
    eligible_judges = [
        j for j in judges
        if j not in [match.proponent_model_id, match.opponent_model_id]
    ]
    
    if len(eligible_judges) < 2:
        # 降级：使用默认裁判
        eligible_judges = ["gpt-4o", "gpt-4o-mini"]
        logger.warning(f"⚠️ 可用裁判不足，使用默认裁判: {eligible_judges}")
    
    logger.info(f"📋 裁判团: {eligible_judges}")
    yield {"type": "judge_start", "judges": eligible_judges}
    
    # 并行调用裁判 (带进度推送)
    judge_scores: List[JudgeScore] = []
    total_judges = len(eligible_judges)
    
    tasks = []
    for i, judge_model in enumerate(eligible_judges):
        tasks.append(judge_single_with_progress(match, judge_model, i, total_judges))
    
    # 收集裁判评分
    for coro in asyncio.as_completed(tasks):
        score, judge_model, index = await coro
        judge_scores.append(score)
        
        logger.info(f"✅ 裁判 {index + 1}/{total_judges} ({judge_model}) 完成评分，胜者: {score.winner}")
        
        yield {
            "type": "judge_progress",
            "judge": judge_model,
            "progress": len(judge_scores) / total_judges,
            "current": len(judge_scores),
            "total": total_judges
        }
        
        yield {
            "type": "judge_score",
            "judge_score": score.model_dump(mode='json')
        }
    
    # === 综合打分 ===
    logger.info("📊 开始综合打分")
    
    # 统计胜负票
    votes = {"proponent": 0, "opponent": 0, "draw": 0}
    for score in judge_scores:
        votes[score.winner] += 1
    
    logger.info(f"   投票结果: 正方 {votes['proponent']}, 反方 {votes['opponent']}, 平局 {votes['draw']}")
    
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
    
    logger.info(f"   平均分: 正方 {prop_avg_total:.2f}, 反方 {opp_avg_total:.2f}")
    
    # === 结合观众投票 (20% 权重) ===
    audience_votes = match.audience_votes or {"proponent": 0, "opponent": 0}
    total_audience_votes = sum(audience_votes.values())
    
    audience_winner = None
    if total_audience_votes > 0:
        audience_winner = "proponent" if audience_votes["proponent"] > audience_votes["opponent"] else "opponent"
        logger.info(f"   观众投票: {audience_winner} 方胜出")
        
        # 调整最终得分
        if audience_winner == "proponent":
            prop_avg_total *= 1.05
        else:
            opp_avg_total *= 1.05
    
    # 最终判定
    if prop_avg_total > opp_avg_total:
        final_winner = "proponent"
    elif opp_avg_total > prop_avg_total:
        final_winner = "opponent"
    else:
        final_winner = "draw"
    
    logger.info(f"⚖️ 最终判决: {final_winner} 胜出")
    
    # 生成综合判词
    reasoning = generate_final_reasoning(judge_scores, winner, audience_winner)
    
    result = MatchResult(
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
    
    yield {
        "type": "judge_complete",
        "result": result.model_dump(mode='json')
    }


async def judge_single_with_progress(
    match: MatchSession, 
    judge_model: str, 
    index: int, 
    total: int
) -> tuple:
    """单个裁判的评分 (带进度)"""
    logger.info(f"👨‍⚖️ 裁判 {index + 1}/{total} ({judge_model}) 开始评分")
    score = await judge_single(match, judge_model)
    return score, judge_model, index


async def judge_single(match: MatchSession, judge_model: str) -> JudgeScore:
    """单个裁判的评分"""
    
    transcript = format_transcript(match.history)
    
    judge_prompt = f"""
你是一场高水平辩论赛的裁判。请根据以下辩论记录判决胜负。

【辩题】
{match.topic}

【正方选手】
{match.proponent_model_id} (性格: {match.proponent_personality.value})

【反方选手】
{match.opponent_model_id} (性格: {match.opponent_personality.value})

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
    "winner": "proponent",
    "reasoning": "详细的判词，说明胜方为何获胜，败方哪里表现不足，以及双方的精彩点。(100-200字)"
}}
"""
    
    try:
        logger.debug(f"   发送评分请求到 {judge_model}")
        response = await query_model(judge_model, [{"role": "user", "content": judge_prompt}])
        result = parse_json(response['content'])
        
        # 验证必要字段
        if not result or 'scores' not in result:
            raise ValueError("Invalid judge response")
        
        logger.debug(f"   {judge_model} 评分结果: {result.get('winner', 'unknown')}")
        
        return JudgeScore(
            judge_model=judge_model,
            scores=result['scores'],
            winner=result.get('winner', 'draw'),
            reasoning=result.get('reasoning', '')
        )
    except Exception as e:
        logger.error(f"❌ 裁判 {judge_model} 评分失败: {e}", exc_info=True)
        # 返回默认评分
        return JudgeScore(
            judge_model=judge_model,
            scores={
                "proponent": {"logic": 5.0, "evidence": 5.0, "persuasion": 5.0},
                "opponent": {"logic": 5.0, "evidence": 5.0, "persuasion": 5.0}
            },
            winner="draw",
            reasoning="评分出错，默认平局"
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
    """
    max_tools = 0
    mvp_index = 0
    
    for i, turn in enumerate(match.history):
        if len(turn.tool_calls) > max_tools:
            max_tools = len(turn.tool_calls)
            mvp_index = i
    
    return mvp_index
