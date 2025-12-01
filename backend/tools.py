# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
工具执行模块
"""

import asyncio
import http.client
import json
import os
import math
from typing import Any, List, Union
from datetime import datetime
from loguru import logger
from .config import SERPER_API_KEY


async def execute_tool(tool_call: dict) -> Any:
    """
    执行工具调用
    """
    tool_name = tool_call['function']['name']
    arguments = json.loads(tool_call['function']['arguments']) if isinstance(tool_call['function']['arguments'], str) else tool_call['function']['arguments']
    
    logger.debug(f"执行工具: {tool_name}, 参数: {arguments}")
    
    if tool_name == "python_interpreter":
        r = await execute_python(arguments['code'])
    elif tool_name == "web_search":
        r = await execute_search(arguments['query'])
    elif tool_name == "calculator":
        r = await execute_calculator(arguments['expression'])
    else:
        r = {"error": f"Unknown tool: {tool_name}"}
    # logger.debug(f"工具执行结果: {r}")
    return r


async def execute_python(code: str, timeout: int = 30) -> dict:
    """
    执行 Python 代码 (沙盒)
    """
    import io
    import sys
    import time
    import traceback
    
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    start_time = time.time()
    result = {
        'stdout': '',
        'stderr': '',
        'time': 0,
        'success': False
    }
    
    try:
        # 受限命名空间
        safe_namespace = {
            '__builtins__': __builtins__,
            'print': print,
            'range': range,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'time': __import__('time'),
            'math': __import__('math'),
        }
        
        compiled_code = compile(code, '<string>', 'exec')
        exec(compiled_code, safe_namespace)
        
        result['stdout'] = new_stdout.getvalue().strip()
        result['success'] = True
        
    except Exception as e:
        result['stderr'] = f"Error: {str(e)}\n{traceback.format_exc()}"
        result['success'] = False
    
    finally:
        sys.stdout = old_stdout
        new_stdout.close()
        result['time'] = time.time() - start_time
    logger.debug(f"execute_python result: {result}, code: {code}")
    return result


async def execute_search(query: Union[str, List[str]]) -> dict:
    """
    执行网络搜索 (使用 Serper API)
    
    支持单个查询或批量查询（最多5个）
    """
    
    def contains_chinese_basic(text: str) -> bool:
        return any('\u4E00' <= char <= '\u9FFF' for char in text)
    
    def google_search_with_serp(q: str) -> str:
        """单个查询的搜索实现"""
        if not SERPER_API_KEY:
            return "SERPER_API_KEY is not set. Please set the SERPER_API_KEY environment variable."
        
        conn = http.client.HTTPSConnection("google.serper.dev")
        
        if contains_chinese_basic(q):
            payload = json.dumps({
                "q": q,
                "location": "China",
                "gl": "cn",
                "hl": "zh-cn"
            })
        else:
            payload = json.dumps({
                "q": q,
                "location": "United States",
                "gl": "us",
                "hl": "en"
            })
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        res = None
        for i in range(5):
            try:
                conn.request("POST", "/search", payload, headers)
                res = conn.getresponse()
                break
            except Exception as e:
                if i == 4:
                    return f"Google search Timeout for query '{q}'. Please try again later."
                continue
        
        data = res.read()
        results = json.loads(data.decode("utf-8"))
        
        try:
            if "organic" not in results:
                raise Exception(f"No results found for query: '{q}'")
            
            web_snippets = []
            idx = 0
            if "organic" in results:
                for page in results["organic"]:
                    idx += 1
                    date_published = ""
                    if "date" in page:
                        date_published = "\nDate published: " + page["date"]
                    
                    source = ""
                    if "source" in page:
                        source = "\nSource: " + page["source"]
                    
                    snippet = ""
                    if "snippet" in page:
                        snippet = "\n" + page["snippet"]
                    
                    redacted_version = f"{idx}. [{page['title']}]({page['link']}){date_published}{source}\n{snippet}"
                    redacted_version = redacted_version.replace("Your browser can't play this video.", "")
                    web_snippets.append(redacted_version)
            
            content = f"A Google search for '{q}' found {len(web_snippets)} results:\n\n## Web Results\n" + "\n\n".join(web_snippets)
            return content
        except:
            return f"No results found for '{q}'. Try with a more general query."
    
    # 处理单个或多个查询
    if isinstance(query, str):
        response = google_search_with_serp(query)
    else:
        # 批量查询（最多5个）
        queries = query[:5]  # 限制最多5个
        responses = []
        for q in queries:
            responses.append(google_search_with_serp(q))
        response = "\n=======\n".join(responses)
    logger.debug(f"execute_search response: {response}, query: {query}")
    return {
        "query": query,
        "response": response,
        "timestamp": datetime.now().isoformat()
    }


async def execute_calculator(expression: str) -> dict:
    """
    执行精确数学计算
    
    避免 LLM 的数学幻觉问题
    """
    
    result = {
        'expression': expression,
        'result': None,
        'error': None
    }
    
    try:
        # 安全的数学命名空间
        safe_math_namespace = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pow': pow,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
            '__builtins__': {}  # 禁用内置函数
        }
        
        # 计算表达式
        result['result'] = eval(expression, safe_math_namespace)
        
    except Exception as e:
        result['error'] = f"计算错误: {str(e)}"
    logger.debug(f"execute_calculator result: {result}, expression: {expression}")
    return result


def get_debate_tools() -> List[dict]:
    """
    获取辩论工具集（正方和反方共享）
    
    工具使用场景：
    - 正方：证明代码能运行、提供性能数据、查证技术文档
    - 反方：验证正方的断言、寻找反例、压力测试
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "python_interpreter",
                "description": "执行 Python 代码验证算法、测试代码、计算复杂度",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的 Python 代码"
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "执行 Google 搜索，用于查找事实、数据、最新信息。支持批量搜索（最多5个查询）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": ["string", "array"],
                            "items": {
                                "type": "string"
                            },
                            "description": "搜索查询字符串，或字符串数组（批量搜索，最多5个）"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "执行精确的数学计算（避免 LLM 幻觉）。支持基本运算、三角函数、对数等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，例如: '2 + 2', 'sqrt(16)', 'sin(pi/2)'"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]
