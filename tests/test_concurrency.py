#!/usr/bin/env python3
"""并发测试脚本 - 验证多个辩题可以真正并发执行"""

import asyncio
import aiohttp
import time
from datetime import datetime

async def start_debate(session: aiohttp.ClientSession, topic: str, debate_id: int):
    """发起一个辩题"""
    start_time = time.time()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 辩题 {debate_id} 开始: {topic}")
    
    try:
        async with session.post(
            'http://localhost:8000/api/tournament/match/stream',
            json={
                'topic': topic,
                'proponent_model': 'gpt-4o-mini',
                'opponent_model': 'gpt-4o-mini',
                'proponent_personality': 'rational',
                'opponent_personality': 'rational',
                'rounds': 1,  # 只打1轮，快速测试
                'judges': ['gpt-4o', 'gpt-4o-mini'],
                'enabled_tools': [],
                'user_id': None
            },
            timeout=aiohttp.ClientTimeout(total=300)
        ) as resp:
            async for line in resp.content:
                if line:
                    # 只打印关键事件
                    line_str = line.decode('utf-8')
                    if 'match_start' in line_str:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 辩题 {debate_id} 已开始流式输出")
                    elif 'match_end' in line_str:
                        elapsed = time.time() - start_time
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 辩题 {debate_id} 完成 (耗时: {elapsed:.1f}秒)")
                        break
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 辩题 {debate_id} 出错: {e}")

async def test_concurrent_debates():
    """测试并发辩题"""
    print("=" * 80)
    print("并发测试：同时发起 3 个辩题")
    print("=" * 80)
    print("\n如果日志显示交叉输出（例如：辩题1开始 → 辩题2开始 → 辩题1完成），说明并发成功！")
    print("如果日志显示串行（辩题1开始 → 辩题1完成 → 辩题2开始），说明还有阻塞问题。\n")
    
    topics = [
        "AI 是否会取代人类程序员",
        "远程办公是否比办公室办公更高效",
        "量子计算会在10年内改变世界"
    ]
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # 并发发起 3 个辩题
        tasks = [
            start_debate(session, topic, i+1)
            for i, topic in enumerate(topics)
        ]
        
        await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"总耗时: {total_time:.1f} 秒")
    
    if total_time < 60:  # 假设单个辩题需要 30 秒
        print("✅ 并发测试通过！多个辩题确实在并行执行。")
    else:
        print("⚠️  可能仍有串行问题，总耗时过长。")
    print("=" * 80)

if __name__ == "__main__":
    print("\n请确保后端服务已启动：")
    print("  uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0\n")
    
    try:
        asyncio.run(test_concurrent_debates())
    except KeyboardInterrupt:
        print("\n\n测试被中断")
