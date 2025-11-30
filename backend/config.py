# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
Configuration for LLM Debate Arena
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "LaIqD4byuVHXcu59j02fJcRs@4228")

# OpenRouter API endpoint
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "http://v2.open.venus.oa.com/llmproxy/v1")

LLM_CONFIG = {
    'api_key': OPENROUTER_API_KEY,
    'base_url': OPENROUTER_API_URL,
    'timeout': 300.0
}

# ========== 裁判团配置 ==========

JUDGE_PANEL = [
    "gpt-4o",
    "gpt-4o-mini",
]

# ========== 数据库配置 ==========

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./debate_arena.db")

# ========== 辩论配置 ==========

DEBATE_CONFIG = {
    "max_rounds": 3,
    "enable_tools": True,
    "tools": ["python_interpreter", "web_search", "calculator"]
}

# ========== ELO 配置 ==========

ELO_CONFIG = {
    "initial_rating": 1200,
    "k_factor_new": 64,      # 新手期 (< 10 场)
    "k_factor_mid": 32,      # 成长期 (10-30 场)
    "k_factor_stable": 16,   # 成熟期 (> 30 场)
}
