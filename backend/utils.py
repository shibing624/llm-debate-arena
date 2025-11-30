# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
Utility functions for LLM applications
"""

import uuid
import json
import re
from typing import Optional
from .llm_client import query_model

def generate_id() -> str:
    """生成唯一 ID"""
    return str(uuid.uuid4())

async def generate_conversation_title(user_query: str) -> str:
    """
    根据用户问题生成对话标题
    """
    title = user_query.strip()
    if len(title) > 20:
        title = title[:17] + "..."
    return title

def parse_json(content: str) -> dict:
    """
    从 LLM 响应中解析 JSON
    
    尝试多种策略提取 JSON，总是返回 dict
    """
    # 策略 1: 直接解析
    try:
        result = json.loads(content)
        # 如果是 list，尝试取第一个元素（如果是 dict）
        if isinstance(result, list):
            if result and isinstance(result[0], dict):
                return result[0]
            else:
                return {}
        elif isinstance(result, dict):
            return result
        else:
            return {}
    except:
        pass
    
    # 策略 2: 提取 JSON 代码块
    json_pattern = r'```json\s*\n(.*?)\n```'
    match = re.search(json_pattern, content, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group(1))
            if isinstance(result, list):
                if result and isinstance(result[0], dict):
                    return result[0]
                else:
                    return {}
            elif isinstance(result, dict):
                return result
        except:
            pass
    
    # 策略 3: 查找第一个 { } 对
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1:
        try:
            result = json.loads(content[start:end+1])
            if isinstance(result, dict):
                return result
        except:
            pass
    
    # 降级: 返回空字典
    return {}

def extract_confidence(content: str) -> float:
    """
    从模型回答中提取置信度
    
    查找类似 "confidence: 0.8" 或 "置信度: 80%" 的模式
    如果找不到，返回默认值 0.7
    """
    # 模式 1: confidence: 0.8
    pattern1 = r'confidence[:\s]+(\d+\.?\d*)'
    match = re.search(pattern1, content, re.IGNORECASE)
    if match:
        return float(match.group(1))
    
    # 模式 2: 置信度: 80%
    pattern2 = r'置信度[:\s]+(\d+)'
    match = re.search(pattern2, content)
    if match:
        return float(match.group(1)) / 100.0
    
    # 默认中等置信度
    return 0.7

def extract_code_block(content: str) -> str:
    """提取 Markdown 代码块"""
    # Python 代码块
    pattern = r'```python\s*\n(.*?)\n```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1)
    
    # 通用代码块
    pattern = r'```\s*\n(.*?)\n```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1)
    
    # 降级：返回全部内容
    return content

def extract_section(content: str, section_name: str) -> str:
    """提取 Markdown 章节"""
    pattern = f"## {section_name}\\n(.*?)(?=\\n##|$)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else content

def extract_first_line(content: str) -> str:
    """提取第一行"""
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            return line
    return content[:100] if content else ""
