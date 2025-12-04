# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
FastAPI Main Application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json
import sys
sys.path.append(".")
sys.path.append("..")

from backend.log import logger
from backend.models import MatchRequest, MatchRenameRequest, CompetitorProfile, DebateTopic, UserRegister, UserLogin, UserProfile, UserModel
from backend.database import (
    init_db, get_db, get_all_competitors, get_all_topics,
    get_match, get_match_history, get_model_statistics,
    delete_match, rename_match
)
from backend.tournament import run_tournament_match
from backend.auth import hash_password, verify_password, create_access_token, decode_access_token

app = FastAPI(
    title="LLM Debate Arena API",
    description="竞技对抗型 AI 辩论挑战赛",
    version="4.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化数据库
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 LLM Debate Arena 启动中...")
    logger.info("📦 初始化数据库...")
    init_db()
    logger.info("✅ 数据库初始化完成")
    logger.info("🎯 API 服务已就绪")


# ========== 健康检查 ==========

@app.get("/")
async def root():
    logger.debug("根路径访问")
    return {
        "message": "LLM Debate Arena API",
        "version": "4.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ========== 比赛相关 ==========

@app.post("/api/tournament/match/stream")
async def match_stream_sse(request: MatchRequest):
    """
    SSE 流式推送比赛数据
    """
    logger.info(f"📝 收到 SSE 比赛请求: {request.topic[:50]}...")
    
    # 验证参数
    if not request.topic or len(request.topic) < 3:
        logger.warning(f"❌ 辩题太短: {request.topic}")
        raise HTTPException(status_code=400, detail="辩题太短，请输入至少3个字符")
    
    # 允许相同模型对战（不计ELO）
    same_model_battle = request.proponent_model == request.opponent_model
    if same_model_battle:
        logger.info(f"⚠️ 同模型对战模式: {request.proponent_model} (不计ELO)")
    
    if len(request.judges) < 2:
        logger.warning(f"❌ 裁判数量不足: {len(request.judges)}")
        raise HTTPException(status_code=400, detail="至少需要2个裁判")
    
    logger.info(f"✅ 比赛配置验证通过")
    logger.info(f"   正方: {request.proponent_model} ({request.proponent_personality})")
    logger.info(f"   反方: {request.opponent_model} ({request.opponent_personality})")
    logger.info(f"   裁判团: {request.judges}")
    logger.info(f"   可用工具: {request.enabled_tools}")
    logger.info(f"   轮数: {request.rounds}")
    logger.info(f"   用户ID: {request.user_id}")
    
    async def event_generator():
        """SSE 事件生成器"""
        event_count = 0
        try:
            async for event in run_tournament_match(
                topic=request.topic,
                topic_difficulty=request.topic_difficulty,
                prop_model_id=request.proponent_model,
                opp_model_id=request.opponent_model,
                prop_personality=request.proponent_personality,
                opp_personality=request.opponent_personality,
                rounds=request.rounds,
                judges=request.judges,
                enabled_tools=request.enabled_tools,
                same_model_battle=same_model_battle,
                user_id=request.user_id  # 传递用户ID
            ):
                # SSE 格式: data: {json}\n\n
                event_json = json.dumps(event, ensure_ascii=False)
                yield f"data: {event_json}\n\n"
                event_count += 1
        except Exception as e:
            # 修复 logger 格式化错误
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(f"❌ SSE 比赛过程出错: {error_msg}", exc_info=True)
            error_event = json.dumps({
                "type": "error",
                "content": str(e)
            }, ensure_ascii=False)
            yield f"data: {error_event}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@app.get("/api/tournament/match/{match_id}")
async def get_match_detail(match_id: str):
    """
    获取比赛详情（公开接口，用于分享）
    """
    logger.info(f"📖 查询比赛详情: {match_id}")
    
    match = await get_match(match_id)
    if not match:
        logger.warning(f"❌ 比赛不存在: {match_id}")
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    logger.info(f"✅ 返回比赛详情: {match_id}")
    
    return {
        "match_id": match.match_id,
        "topic": match.topic,
        "custom_title": match.custom_title,
        "topic_difficulty": match.topic_difficulty,
        "proponent_model_id": match.proponent_model_id,
        "opponent_model_id": match.opponent_model_id,
        "status": match.status,
        "transcript": match.transcript,
        "judge_result": match.judge_result,
        "elo_changes": match.elo_changes,
        "created_at": match.created_at.isoformat(),
        "finished_at": match.finished_at.isoformat() if match.finished_at else None
    }


@app.delete("/api/tournament/match/{match_id}")
async def delete_match_api(match_id: str, user_id: int = None):
    """
    删除比赛记录
    """
    logger.info(f"🗑️ 删除比赛: {match_id}, user_id={user_id}")
    
    success = await delete_match(match_id, user_id)
    if not success:
        logger.warning(f"❌ 删除失败，比赛不存在或无权限: {match_id}")
        raise HTTPException(status_code=404, detail="比赛不存在或无权限删除")
    
    logger.info(f"✅ 比赛已删除: {match_id}")
    return {"message": "删除成功"}


@app.put("/api/tournament/match/{match_id}/rename")
async def rename_match_api(match_id: str, request: MatchRenameRequest, user_id: int = None):
    """
    重命名比赛
    """
    logger.info(f"✏️ 重命名比赛: {match_id} -> {request.title}")
    
    success = await rename_match(match_id, request.title, user_id)
    if not success:
        logger.warning(f"❌ 重命名失败，比赛不存在或无权限: {match_id}")
        raise HTTPException(status_code=404, detail="比赛不存在或无权限重命名")
    
    logger.info(f"✅ 比赛已重命名: {match_id}")
    return {"message": "重命名成功"}


# ========== 排行榜 ==========

@app.get("/api/tournament/leaderboard", response_model=List[CompetitorProfile])
async def get_leaderboard():
    """
    获取排行榜
    """
    logger.info("📊 获取排行榜")
    
    try:
        competitors = await get_all_competitors()
        logger.info(f"✅ 返回 {len(competitors)} 个参赛者")
        return competitors
    except Exception as e:
        logger.error(f"❌ 获取排行榜失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 辩题 ==========

@app.get("/api/tournament/topics", response_model=List[DebateTopic])
async def get_topics():
    """
    获取辩题列表
    """
    logger.info("📚 获取辩题列表")
    
    try:
        topics = await get_all_topics()
        logger.info(f"✅ 返回 {len(topics)} 个辩题")
        return topics
    except Exception as e:
        logger.error(f"❌ 获取辩题失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 历史记录 ==========

@app.get("/api/tournament/matches/history")
async def get_history(limit: int = 20, model_id: str = None, user_id: int = None, db: Session = Depends(get_db)):
    """
    获取历史记录（支持按模型和用户筛选）
    """
    logger.info(f"📜 获取历史记录 (limit={limit}, model_id={model_id}, user_id={user_id})")
    
    try:
        matches = await get_match_history(limit, model_id=model_id, user_id=user_id)
        logger.info(f"✅ 返回 {len(matches)} 场比赛")
        
        return [
            {
                "match_id": m.match_id,
                "topic": m.topic,
                "custom_title": m.custom_title,
                "proponent_model_id": m.proponent_model_id,
                "opponent_model_id": m.opponent_model_id,
                "status": m.status,
                "judge_result": m.judge_result,
                "same_model_battle": m.proponent_model_id == m.opponent_model_id,
                "created_at": m.created_at.isoformat(),
                "finished_at": m.finished_at.isoformat() if m.finished_at else None
            }
            for m in matches
        ]
    except Exception as e:
        logger.error(f"❌ 获取历史记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========== 模型统计（脱敏） ==========

@app.get("/api/tournament/model/{model_id}/stats")
async def get_model_stats(model_id: str, db: Session = Depends(get_db)):
    """
    获取模型的统计数据（脱敏版本，不包含具体辩题内容）
    """
    logger.info(f"📊 获取模型统计数据: {model_id}")
    
    try:
        stats = await get_model_statistics(model_id)
        
        logger.info(f"✅ 返回统计数据: {model_id}")
        return stats
    except Exception as e:
        logger.error(f"❌ 获取统计数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# ========== 用户认证 ==========

@app.post("/api/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    logger.info(f"📝 用户注册请求: {user_data.username}")
    
    # 检查用户名是否已存在
    existing_user = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing_user:
        logger.warning(f"❌ 用户名已存在: {user_data.username}")
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    existing_email = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing_email:
        logger.warning(f"❌ 邮箱已存在: {user_data.email}")
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        display_name=user_data.username,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"✅ 用户注册成功: {user_data.username}")
    
    # 生成永久token
    token = create_access_token({"user_id": new_user.id, "username": new_user.username})
    
    return {
        "message": "注册成功",
        "token": token,
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }


@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录（支持邮箱或用户名）"""
    logger.info(f"🔑 用户登录请求: {user_data.username}")
    
    # 查找用户（支持邮箱或用户名）
    user = db.query(UserModel).filter(
        (UserModel.username == user_data.username) | 
        (UserModel.email == user_data.username)
    ).first()
    
    if not user:
        logger.warning(f"❌ 用户不存在: {user_data.username}")
        raise HTTPException(status_code=401, detail="邮箱/用户名或密码错误")
    
    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        logger.warning(f"❌ 密码错误: {user_data.username}")
        raise HTTPException(status_code=401, detail="邮箱/用户名或密码错误")
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"✅ 用户登录成功: {user.username}")
    
    # 生成永久token
    token = create_access_token({"user_id": user.id, "username": user.username})
    
    return {
        "message": "登录成功",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name,
            "matches_count": user.matches_count
        }
    }


@app.get("/api/auth/me")
async def get_current_user(token: str, db: Session = Depends(get_db)):
    """获取当前用户信息"""
    logger.info(f"👤 获取用户信息")
    
    payload = decode_access_token(token)
    if not payload:
        logger.warning("❌ Token无效")
        raise HTTPException(status_code=401, detail="Token无效")
    
    user_id = payload.get("user_id")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if not user:
        logger.warning(f"❌ 用户不存在: user_id={user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    logger.info(f"✅ 返回用户信息: {user.username}")
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "matches_count": user.matches_count,
        "created_at": user.created_at.isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
