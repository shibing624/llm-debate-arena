# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: Tournament Manager - 辩论赛事编排
"""

import asyncio
from typing import AsyncGenerator, List, Optional
from datetime import datetime
import json

from .log import logger
from .models import MatchSession, Turn, PersonalityType, DifficultyLevel
from .llm_client import query_model_stream
from .tools import get_debate_tools, execute_tool
from .judge import judge_match_with_panel_stream
from .elo import update_elo_ratings
from .database import save_match, update_match_status
from .utils import generate_id

# 全局字典：跟踪正在进行的比赛，用于中止功能
# key: match_id, value: {"should_stop": bool}
_active_matches = {}


async def run_tournament_match(
    topic: str,
    topic_difficulty: DifficultyLevel,
    prop_model_id: str,
    opp_model_id: str,
    prop_personality: Optional[str],
    opp_personality: Optional[str],
    rounds: int = 3,
    judges: List[str] = None,
    enabled_tools: List[str] = None,
    same_model_battle: bool = False,
    user_id: Optional[int] = None
) -> AsyncGenerator[dict, None]:
    """
    运行竞技赛，使用 WebSocket 流式推送
    
    Yields:
        dict: 事件流
    """
    
    # 设置默认值
    if judges is None:
        judges = ["gpt-4o", "gpt-4o-mini"]
    if enabled_tools is None:
        enabled_tools = []  # 默认为空，不启用任何工具
    
    # 处理性格：空字符串或None转换为默认rational
    from .models import PersonalityType
    prop_personality_enum = PersonalityType.RATIONAL
    opp_personality_enum = PersonalityType.RATIONAL
    
    if prop_personality and prop_personality in [e.value for e in PersonalityType]:
        prop_personality_enum = PersonalityType(prop_personality)
    if opp_personality and opp_personality in [e.value for e in PersonalityType]:
        opp_personality_enum = PersonalityType(opp_personality)
    
    logger.info(f"🎮 开始新比赛: {topic}")
    logger.info(f"   正方: {prop_model_id} ({prop_personality_enum})")
    logger.info(f"   反方: {opp_model_id} ({opp_personality_enum})")
    logger.info(f"   轮次: {rounds}, 难度: {topic_difficulty}")
    logger.info(f"   裁判团: {judges}")
    logger.info(f"   可用工具: {enabled_tools}")
    
    # 创建比赛会话
    match = MatchSession(
        match_id=generate_id(),
        topic=topic,
        topic_difficulty=topic_difficulty,
        proponent_model_id=prop_model_id,
        opponent_model_id=opp_model_id,
        proponent_personality=prop_personality_enum,
        opponent_personality=opp_personality_enum,
        rounds_setting=rounds,
        status="FIGHTING",
        user_id=user_id  # 传递用户ID
    )
    
    # ⚠️ 重要：立即注册到活跃列表（在第一个 yield 之前）
    # 这样可以确保用户能够立即中止比赛
    _active_matches[match.match_id] = {"should_stop": False}
    logger.info(f"✅ 比赛已注册到活跃列表: {match.match_id}")
    
    # 立即 yield 初始事件，让前端获取 match_id（触发生成器执行）
    yield {"type": "match_init", "match_id": match.match_id}
    
    await save_match(match)
    logger.info(f"✅ 比赛会话已创建: {match.match_id}")
    
    yield {"type": "match_start", "data": match.model_dump(mode='json')}
    
    # 辩论上下文
    context = []
    
    # === 正式辩论 ===
    for r in range(1, rounds + 1):
        # 🛑 检查是否需要中止
        if _active_matches.get(match.match_id, {}).get("should_stop", False):
            logger.warning(f"⚠️ 比赛被中止: {match.match_id}")
            match.status = "CANCELLED"
            await save_match(match)
            yield {"type": "match_cancelled", "match_id": match.match_id, "message": "比赛已被用户中止"}
            # 清理活跃比赛记录
            _active_matches.pop(match.match_id, None)
            return
        
        logger.info(f"📍 开始 Round {r}")
        
        # === 正方发言 (流式) ===
        yield {"type": "status", "speaker": "proponent", "content": f"Round {r}: 正方正在思考..."}
        
        try:
            async for event in execute_turn_stream(
                role="proponent",
                model_id=prop_model_id,
                personality=prop_personality_enum,
                topic=topic,
                topic_difficulty=topic_difficulty,
                round_num=r,
                context=context,
                is_opening=(r==1),
                enabled_tools=enabled_tools,  # 传递工具列表
                match_id=match.match_id  # 传递match_id用于检查中止
            ):
                # 🛑 在流式输出中也检查中止
                if _active_matches.get(match.match_id, {}).get("should_stop", False):
                    logger.warning(f"⚠️ 正方发言中被中止: {match.match_id}")
                    match.status = "CANCELLED"
                    await save_match(match)
                    yield {"type": "match_cancelled", "match_id": match.match_id, "message": "比赛已被用户中止"}
                    _active_matches.pop(match.match_id, None)
                    return
                
                if event["type"] == "turn_complete":
                    # turn_complete 事件中的 turn 是 dict，需要转换回 Turn 对象
                    turn_dict = event["turn"]
                    prop_turn = Turn(**turn_dict)
                    match.history.append(prop_turn)
                    context.append(prop_turn)
                    logger.info(f"✅ 正方 Round {r} 完成，内容长度: {len(prop_turn.content)}")
                    yield event
                else:
                    # 流式推送内容增量
                    yield event
        except Exception as e:
            logger.error(f"❌ 正方发言失败: {e}", exc_info=True)
            yield {"type": "error", "content": f"正方发言出错: {str(e)}"}
        
        # 🛑 在轮次间也检查中止
        if _active_matches.get(match.match_id, {}).get("should_stop", False):
            logger.warning(f"⚠️ 比赛在轮次间被中止: {match.match_id}")
            match.status = "CANCELLED"
            await save_match(match)
            yield {"type": "match_cancelled", "match_id": match.match_id, "message": "比赛已被用户中止"}
            _active_matches.pop(match.match_id, None)
            return
        
        # === 反方发言 (流式) ===
        yield {"type": "status", "speaker": "opponent", "content": f"Round {r}: 反方正在反驳..."}
        
        try:
            async for event in execute_turn_stream(
                role="opponent",
                model_id=opp_model_id,
                personality=opp_personality_enum,
                topic=topic,
                topic_difficulty=topic_difficulty,
                round_num=r,
                context=context,
                is_opening=False,
                enabled_tools=enabled_tools,  # 传递工具列表
                match_id=match.match_id  # 传递match_id用于检查中止
            ):
                # 🛑 在流式输出中也检查中止
                if _active_matches.get(match.match_id, {}).get("should_stop", False):
                    logger.warning(f"⚠️ 反方发言中被中止: {match.match_id}")
                    match.status = "CANCELLED"
                    await save_match(match)
                    yield {"type": "match_cancelled", "match_id": match.match_id, "message": "比赛已被用户中止"}
                    _active_matches.pop(match.match_id, None)
                    return
                
                if event["type"] == "turn_complete":
                    # turn_complete 事件中的 turn 是 dict，需要转换回 Turn 对象
                    turn_dict = event["turn"]
                    opp_turn = Turn(**turn_dict)
                    match.history.append(opp_turn)
                    context.append(opp_turn)
                    logger.info(f"✅ 反方 Round {r} 完成，内容长度: {len(opp_turn.content)}")
                    yield event
                else:
                    yield event
        except Exception as e:
            logger.error(f"❌ 反方发言失败: {e}", exc_info=True)
            yield {"type": "error", "content": f"反方发言出错: {str(e)}"}
    
    # === 裁判判决 ===
    logger.info("👨‍⚖️ 开始裁判判决")
    match.status = "JUDGING"
    await update_match_status(match.match_id, "JUDGING")
    
    yield {"type": "status", "content": "裁判团正在打分..."}
    
    try:
        async for event in judge_match_with_panel_stream(match, judges):
            if event["type"] == "judge_complete":
                # result 是 dict，需要转换回 MatchResult 对象
                result_dict = event["result"]
                from .models import MatchResult
                match.result = MatchResult(**result_dict)
                logger.info(f"⚖️ 裁判判决完成，胜者: {match.result.winner}")
            yield event
    except Exception as e:
        logger.error(f"❌ 裁判打分失败: {e}", exc_info=True)
        yield {"type": "error", "content": f"裁判打分出错: {str(e)}"}
    
    # === 更新 ELO ===
    elo_changes = None
    if not same_model_battle:
        logger.info("📊 准备更新 ELO 排名")
        try:
            # 确保 result 存在才更新 ELO
            if match.result is not None:
                elo_changes = await update_elo_ratings(match)
                
                # 检查是否跳过了 ELO 更新
                if elo_changes.get('proponent', {}).get('skipped'):
                    skip_reason = elo_changes['proponent'].get('reason', '未知原因')
                    logger.warning(f"⚠️ ELO 更新被跳过: {skip_reason}")
                    yield {"type": "elo_update", "data": {"message": f"跳过ELO更新: {skip_reason}", "skip": True}}
                else:
                    logger.info(f"✅ ELO 更新完成: 正方 {elo_changes['proponent']['change']:+d}, 反方 {elo_changes['opponent']['change']:+d}")
                    yield {"type": "elo_update", "data": elo_changes}
            else:
                logger.warning("⚠️ 比赛结果为空，跳过 ELO 更新")
                yield {"type": "elo_update", "data": {"error": "比赛结果为空", "skip": True}}
        except Exception as e:
            logger.error(f"❌ ELO 更新失败: {type(e).__name__} - {e}", exc_info=True)
            yield {"type": "elo_update", "data": {"error": f"ELO更新失败: {str(e)}", "skip": True}}
    else:
        logger.info("⚠️ 同模型对战，跳过 ELO 更新")
        yield {"type": "elo_update", "data": {"message": "同模型对战，不计ELO", "skip": True}}
    
    # === 保存比赛 ===
    match.status = "FINISHED"
    await save_match(match)
    
    # 更新状态和 ELO 变化
    if elo_changes:
        await update_match_status(match.match_id, "FINISHED", elo_changes)
    
    logger.info(f"🏁 比赛结束: {match.match_id}")
    
    # 清理活跃比赛记录
    _active_matches.pop(match.match_id, None)
    
    yield {"type": "match_end", "match_id": match.match_id}


def cancel_match(match_id: str) -> bool:
    """
    中止正在进行的比赛
    
    Args:
        match_id: 比赛ID
    
    Returns:
        bool: 是否成功设置中止标志
    """
    logger.info(f"🔍 当前活跃比赛列表: {list(_active_matches.keys())}")
    
    if match_id in _active_matches:
        _active_matches[match_id]["should_stop"] = True
        logger.info(f"🛑 比赛中止标志已设置: {match_id}")
        return True
    else:
        logger.warning(f"⚠️ 尝试中止不存在的比赛: {match_id}")
        return False


def get_active_matches() -> List[str]:
    """获取所有活跃比赛的ID列表"""
    return list(_active_matches.keys())


async def execute_turn_stream(
    role: str,
    model_id: str,
    personality: PersonalityType,
    topic: str,
    topic_difficulty: DifficultyLevel,
    round_num: int,
    context: List[Turn],
    is_opening: bool,
    enabled_tools: List[str] = None,
    match_id: str = None
) -> AsyncGenerator[dict, None]:
    """
    执行单次辩论发言 (流式)
    
    Yields:
        {"type": "turn_delta", "speaker": "proponent", "delta": "...", "round": 1}
        {"type": "turn_tool_call", "speaker": "proponent", "tool_call": {...}}
        {"type": "turn_complete", "turn": Turn(...)}
    """
    
    logger.info(f"💬 {role} Round {round_num} 开始思考 (模型: {model_id}, 性格: {personality})")
    
    # 构建系统提示词，传递 enabled_tools
    system_prompt = build_debate_prompt(
        role=role,
        personality=personality,
        topic=topic,
        topic_difficulty=topic_difficulty,
        is_opening=is_opening,
        enabled_tools=enabled_tools or []
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
    
    # 根据 enabled_tools 过滤工具
    if enabled_tools is None:
        enabled_tools = []
    
    # 获取所有工具定义并按 enabled_tools 过滤
    all_tools = get_debate_tools()
    if enabled_tools:
        tools = [t for t in all_tools if t['function']['name'] in enabled_tools]
        logger.debug(f"使用工具: {[t['function']['name'] for t in tools]}")
    else:
        tools = []
        logger.debug("未启用任何工具")
    
    # 第一次流式调用 LLM (可能产生工具调用)
    accumulated_content = ""
    accumulated_tool_calls = []
    
    async for event in query_model_stream(
        model_id=model_id,
        messages=messages,
        tools=tools if tools else None,  # 如果没有工具，传 None
        temperature=0.7
    ):
        if event["type"] == "content":
            # 内容增量
            accumulated_content += event["delta"]
            yield {
                "type": "turn_delta",
                "speaker": role,
                "delta": event["delta"],
                "round": round_num
            }
            
        elif event["type"] == "tool_call":
            # 工具调用
            accumulated_tool_calls.append(event["tool_call"])
            logger.info(f"🔧 {role} 调用工具: {event['tool_call']['function']['name']}")
            yield {
                "type": "turn_tool_call",
                "speaker": role,
                "tool_call": event["tool_call"],
                "round": round_num
            }
            
        elif event["type"] == "done":
            # 完成第一次调用
            logger.debug(f"💬 {role} 第一次调用完成")
            break
            
        elif event["type"] == "error":
            logger.error(f"❌ {role} 调用失败: {event['error']}")
            yield {
                "type": "error",
                "content": f"{role} 调用失败: {event['error']}"
            }
            return
    
    # 处理工具调用
    tool_calls = []
    if accumulated_tool_calls:
        logger.info(f"🔧 开始执行 {len(accumulated_tool_calls)} 个工具")
        
        # 将第一次的助手回复加入消息历史
        assistant_message = {
            'role': 'assistant',
            'content': accumulated_content if accumulated_content else "",
            'tool_calls': accumulated_tool_calls
        }
        messages.append(assistant_message)
        
        # 执行工具并将结果加入消息历史
        for tc in accumulated_tool_calls:
            try:
                logger.debug(f"   执行工具: {tc['function']['name']}")
                result = await execute_tool(tc)
                
                # 格式化工具结果
                if isinstance(result, dict):
                    tool_result_content = result.get('response') or result.get('stdout') or result.get('result') or json.dumps(result, ensure_ascii=False)
                else:
                    tool_result_content = str(result)
                
                tool_calls.append({
                    "tool_name": tc['function']['name'],
                    "arguments": tc['function']['arguments'],
                    "result": result
                })
                logger.info(f"   ✅ 工具执行成功: {tc['function']['name']}")
                
                # 推送工具执行结果
                yield {
                    "type": "turn_tool_result",
                    "speaker": role,
                    "tool_name": tc['function']['name'],
                    "result": result,
                    "round": round_num
                }
                
                # 将工具结果加入消息历史
                tool_result_message = {
                    'role': 'tool',
                    'content': tool_result_content,
                    'tool_call_id': tc['id']
                }
                messages.append(tool_result_message)
                
            except Exception as e:
                logger.error(f"   ❌ 工具执行失败: {tc['function']['name']}, 错误: {e}")
                error_msg = f"工具执行失败: {str(e)}"
                tool_calls.append({
                    "tool_name": tc['function']['name'],
                    "arguments": tc['function']['arguments'],
                    "result": {"error": str(e)}
                })
                
                # 错误也要加入消息历史
                messages.append({
                    'role': 'tool',
                    'content': error_msg,
                    'tool_call_id': tc['id']
                })
        
        # 第二次调用 LLM，让模型基于工具结果生成最终回答
        logger.info(f"🔄 {role} 基于工具结果进行第二次调用")
        
        final_content = ""
        async for event in query_model_stream(
            model_id=model_id,
            messages=messages,
            tools=tools if tools else None,  # 如果没有工具，传 None
            temperature=0.7
        ):
            if event["type"] == "content":
                # 内容增量
                final_content += event["delta"]
                yield {
                    "type": "turn_delta",
                    "speaker": role,
                    "delta": event["delta"],
                    "round": round_num
                }
                
            elif event["type"] == "done":
                logger.debug(f"💬 {role} 第二次调用完成 (基于工具结果)")
                break
                
            elif event["type"] == "error":
                logger.error(f"❌ {role} 第二次调用失败: {event['error']}")
                yield {
                    "type": "error",
                    "content": f"{role} 第二次调用失败: {event['error']}"
                }
                return
        
        # 合并内容：第一次的内容 + 工具结果说明 + 第二次的内容
        if accumulated_content:
            accumulated_content = accumulated_content + "\n\n" + final_content
        else:
            accumulated_content = final_content
    
    # 创建 Turn 对象
    turn = Turn(
        round_number=round_num,
        speaker_role=role,
        model_id=model_id,
        content=accumulated_content,
        tool_calls=tool_calls,
        timestamp=datetime.utcnow()
    )
    
    logger.info(f"✅ {role} Round {round_num} 完成，内容: {len(accumulated_content)} 字符，工具: {len(tool_calls)} 个")
    
    # 推送完成事件 (将 Turn 对象转换为字典)
    yield {
        "type": "turn_complete",
        "turn": turn.model_dump(mode='json')
    }


def build_debate_prompt(
    role: str,
    personality: PersonalityType,
    topic: str,
    topic_difficulty: DifficultyLevel,
    is_opening: bool,
    enabled_tools: List[str] = None
) -> str:
    """构建辩论提示词"""
    
    position = "正方（支持方）" if role == "proponent" else "反方（反对方）"
    
    # 性格描述
    personality_traits = {
        PersonalityType.RATIONAL: "你是一个理性分析型辩手，善用逻辑推理。",
        PersonalityType.AGGRESSIVE: "你是一个激进攻击型辩手，言辞犀利，直击要害，不留情面。",
        PersonalityType.DIPLOMATIC: "你是一个温和外交型辩手，善于沟通，注重礼貌和说服力。",
        PersonalityType.HUMOROUS: "你是一个幽默讽刺型辩手，善用比喻和反讽，寓教于乐。",
        PersonalityType.ACADEMIC: "你是一个学术严谨型辩手，引经据典，强调权威和证据。"
    }
    
    personality_desc = personality_traits.get(personality, "")
    
    # 难度提示
    difficulty_hints = {
        DifficultyLevel.EASY: "这是一个相对简单的辩题，请用清晰的逻辑和常识进行论证。",
        DifficultyLevel.MEDIUM: "这是一个中等难度的辩题，需要一定的专业知识和论证深度。",
        DifficultyLevel.HARD: "这是一个困难的辩题，需要深度思考和强有力的证据支持。",
        DifficultyLevel.EXPERT: "这是一个专家级辩题，需要引用权威资料和复杂推理。"
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
    
    # 工具说明（根据实际启用的工具动态生成）
    tools_section = "- 无可用工具。"
    if enabled_tools:
        tool_descriptions = {
            'python_interpreter': '- `python_interpreter`: 运行代码证明你的观点',
            'web_search': '- `web_search`: 联网搜索权威资料',
            'calculator': '- `calculator`: 精确计算'
        }
        
        tool_list = '\n'.join([tool_descriptions[tool] for tool in enabled_tools if tool in tool_descriptions])
        
        tools_section = f"""
【工具使用】
你可以调用以下工具来增强论证：
{tool_list}
"""
    
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

{tools_section}

【禁止行为】
- 不要试图达成共识或妥协
- 不要承认对方的核心观点
- 你的目的是战胜对手，而非合作
"""
