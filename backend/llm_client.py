# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: LLM 客户端 - 兼容 OpenAI SDK"""

from openai import (
    AsyncOpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError
)
import json
from typing import List, Dict, AsyncGenerator, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.log import logger
from backend.config import LLM_CONFIG

# 使用异步客户端，支持真正的并发
client = AsyncOpenAI(
    api_key=LLM_CONFIG['api_key'],
    base_url=LLM_CONFIG['base_url'],
    timeout=LLM_CONFIG['timeout']
)


async def query_model_stream(
    model_id: str, 
    messages: List[Dict], 
    temperature: float = 0.7,
    tools: Optional[List[Dict]] = None
) -> AsyncGenerator[Dict, None]:
    """
    流式查询 LLM (支持工具调用)
    
    Yields:
        {"type": "content", "delta": "..."}
        {"type": "tool_call", "tool_call": {...}}
        {"type": "done", "content": "...", "tool_calls": [...]}
    """
    logger.info(f"开始流式调用模型: {model_id}, 消息数: {len(messages)}")
    
    try:
        # 格式化消息
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_msg = {'role': msg['role'], 'content': msg.get('content', '')}
                # 保留 tool_calls（助手消息）
                if 'tool_calls' in msg and msg['tool_calls']:
                    formatted_msg['tool_calls'] = msg['tool_calls']
                # 保留 tool_call_id（工具结果消息）
                if 'tool_call_id' in msg:
                    formatted_msg['tool_call_id'] = msg['tool_call_id']
                formatted_messages.append(formatted_msg)
            else:
                formatted_msg = {'role': msg.role, 'content': msg.content or ''}
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    formatted_msg['tool_calls'] = [
                        {
                            'id': tc.id,
                            'type': tc.type,
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                if hasattr(msg, 'tool_call_id'):
                    formatted_msg['tool_call_id'] = msg.tool_call_id
                formatted_messages.append(formatted_msg)
        
        # 构建请求参数
        request_params = {
            "model": model_id,
            "messages": formatted_messages,
            "temperature": temperature,
            "stream": True
        }
        
        if tools:
            request_params["tools"] = tools
            logger.debug(f"使用工具: {[t['function']['name'] for t in tools]}")
        
        # 流式调用（使用 await 异步调用）
        logger.debug(f"请求参数: {request_params}")
        stream = await client.chat.completions.create(**request_params)
        
        # 累积内容和工具调用
        accumulated_content = ""
        accumulated_tool_calls = []
        tool_call_buffer = {}
        
        # 使用 async for 异步迭代，不阻塞事件循环
        async for chunk in stream:
            if not hasattr(chunk, 'choices') or not chunk.choices:
                continue
            
            choice = chunk.choices[0]
            
            # 处理内容增量
            if hasattr(choice, 'delta') and choice.delta:
                delta = choice.delta
                
                # 内容增量
                if hasattr(delta, 'content') and delta.content:
                    accumulated_content += delta.content
                    # logger.debug(f"内容增量: {delta.content}")
                    yield {
                        "type": "content",
                        "delta": delta.content
                    }
                
                # 工具调用增量
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        
                        # 初始化工具调用缓冲区
                        if idx not in tool_call_buffer:
                            tool_call_buffer[idx] = {
                                "id": "",
                                "type": "function",
                                "function": {
                                    "name": "",
                                    "arguments": ""
                                }
                            }
                        
                        # 累积工具调用数据
                        if hasattr(tc_delta, 'id') and tc_delta.id:
                            tool_call_buffer[idx]["id"] = tc_delta.id
                        
                        if hasattr(tc_delta, 'function') and tc_delta.function:
                            if hasattr(tc_delta.function, 'name') and tc_delta.function.name:
                                tool_call_buffer[idx]["function"]["name"] = tc_delta.function.name
                            if hasattr(tc_delta.function, 'arguments') and tc_delta.function.arguments:
                                tool_call_buffer[idx]["function"]["arguments"] += tc_delta.function.arguments
            
        # 整理工具调用
        if tool_call_buffer:
            accumulated_tool_calls = [tool_call_buffer[i] for i in sorted(tool_call_buffer.keys())]
            logger.info(f"检测到工具调用: {[tc['function']['name'] for tc in accumulated_tool_calls]}")
            
            for tc in accumulated_tool_calls:
                yield {
                    "type": "tool_call",
                    "tool_call": tc
                }
        
        # 最终完成
        yield {
            "type": "done",
            "content": accumulated_content,
            "tool_calls": accumulated_tool_calls
        }
        # logger.info(f"模型调用完成，内容长度: {len(accumulated_content)}, 工具调用: {len(accumulated_tool_calls)}")
    except RateLimitError as e:
        error_msg = f"API 限流错误 (QPM/RPM 超限): {str(e)}"
        logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
        yield {"type": "error", "error": error_msg, "error_type": "rate_limit"}
    except APITimeoutError as e:
        error_msg = f"API 超时错误: {str(e)}"
        logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
        yield {"type": "error", "error": error_msg, "error_type": "timeout"}
    except APIConnectionError as e:
        error_msg = f"API 连接错误 (网络问题): {str(e)}"
        logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
        yield {"type": "error", "error": error_msg, "error_type": "connection"}
    except AuthenticationError as e:
        error_msg = f"API 认证错误 (API Key 无效): {str(e)}"
        logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
        yield {"type": "error", "error": error_msg, "error_type": "auth"}
    except BadRequestError as e:
        error_msg = f"API 请求错误 (参数无效): {str(e)}"
        logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
        yield {"type": "error", "error": error_msg, "error_type": "bad_request"}
    except APIError as e:
        error_msg = f"API 通用错误: {str(e)}"
        logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
        yield {"type": "error", "error": error_msg, "error_type": "api_error"}
    except Exception as e:
        error_msg = f"未知错误: {type(e).__name__} - {str(e)}"
        logger.error(f"流式调用失败 [{model_id}]: {error_msg}", exc_info=True)
        yield {"type": "error", "error": error_msg, "error_type": "unknown"}


async def query_model(model_id: str, messages: List[Dict], temperature: float = 0.7) -> Dict:
    """
    查询 LLM (非流式，用于裁判评分等不需要流式的场景)
    
    返回: {"content": "...", "tool_calls": [...]}
    """
    logger.info(f"调用模型 (非流式): {model_id}")
    
    try:
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_messages.append({'role': msg['role'], 'content': msg['content']})
            else:
                formatted_messages.append({'role': msg.role, 'content': msg.content})
        
        # 使用 await 异步调用
        response = await client.chat.completions.create(
            model=model_id,
            messages=formatted_messages,
            temperature=temperature,
            stream=False
        )
        
        choice = response.choices[0]
        result = {
            "content": choice.message.content or "",
            "tool_calls": []
        }
        
        if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in choice.message.tool_calls
            ]
        
        logger.info(f"模型调用成功，内容长度: {len(result['content'])}, result: {result}")
        return result
        
    except RateLimitError as e:
        error_msg = f"API 限流错误 (QPM/RPM 超限): {str(e)}"
        logger.error(f"模型调用失败 [{model_id}]: {error_msg}", exc_info=True)
        return {"content": f"Error: {error_msg}", "tool_calls": [], "error_type": "rate_limit"}
    except APITimeoutError as e:
        error_msg = f"API 超时错误: {str(e)}"
        logger.error(f"模型调用失败 [{model_id}]: {error_msg}", exc_info=True)
        return {"content": f"Error: {error_msg}", "tool_calls": [], "error_type": "timeout"}
    except APIConnectionError as e:
        error_msg = f"API 连接错误 (网络问题): {str(e)}"
        logger.error(f"模型调用失败 [{model_id}]: {error_msg}", exc_info=True)
        return {"content": f"Error: {error_msg}", "tool_calls": [], "error_type": "connection"}
    except AuthenticationError as e:
        error_msg = f"API 认证错误 (API Key 无效): {str(e)}"
        logger.error(f"模型调用失败 [{model_id}]: {error_msg}", exc_info=True)
        return {"content": f"Error: {error_msg}", "tool_calls": [], "error_type": "auth"}
    except BadRequestError as e:
        error_msg = f"API 请求错误 (参数无效): {str(e)}"
        logger.error(f"模型调用失败 [{model_id}]: {error_msg}", exc_info=True)
        return {"content": f"Error: {error_msg}", "tool_calls": [], "error_type": "bad_request"}
    except APIError as e:
        error_msg = f"API 通用错误: {str(e)}"
        logger.error(f"模型调用失败 [{model_id}]: {error_msg}", exc_info=True)
        return {"content": f"Error: {error_msg}", "tool_calls": [], "error_type": "api_error"}
    except Exception as e:
        error_msg = f"未知错误: {type(e).__name__} - {str(e)}"
        logger.error(f"模型调用失败 [{model_id}]: {error_msg}", exc_info=True)
        return {"content": f"Error: {error_msg}", "tool_calls": [], "error_type": "unknown"}


# add demo
async def main():
    print("=" * 60)
    print("工具调用完整流程演示：搜索故宫并基于结果回答")
    print("=" * 60)
    
    from backend.tools import get_debate_tools, execute_tool
    
    # 从 tools.py 获取工具列表，只使用 web_search 工具
    all_tools = get_debate_tools()
    search_tool = [tool for tool in all_tools if tool['function']['name'] == 'web_search']
    
    # 初始化消息列表
    messages = [{'role': 'user', 'content': '谷歌搜索故宫,基于搜索结果回答故宫成立时间'}]
    
    # 第一次调用：模型决定使用工具
    print("\n[第一步] 模型分析问题并决定调用工具...")
    print("-" * 60)
    
    accumulated_content = ""
    tool_calls = []
    
    async for chunk in query_model_stream(
        model_id='gpt-4o-mini', 
        messages=messages, 
        tools=search_tool
    ):
        if chunk['type'] == 'content':
            accumulated_content += chunk['delta']
            print(chunk['delta'], end='', flush=True)
        elif chunk['type'] == 'tool_call':
            tool_calls.append(chunk['tool_call'])
            print(f"\n\n[工具调用] {chunk['tool_call']['function']['name']}")
            print(f"参数: {chunk['tool_call']['function']['arguments']}")
        elif chunk['type'] == 'done':
            if chunk.get('tool_calls'):
                tool_calls = chunk['tool_calls']
    
    print("\n")
    
    # 如果有工具调用，执行工具并将结果添加到消息中
    if tool_calls:
        print("\n[第二步] 执行工具调用...")
        print("-" * 60)
        
        # 添加助手的回复（包含工具调用）到消息历史
        assistant_message = {
            'role': 'assistant',
            'content': accumulated_content if accumulated_content else "",
            'tool_calls': [
                {
                    'id': tc['id'],
                    'type': tc['type'],
                    'function': {
                        'name': tc['function']['name'],
                        'arguments': tc['function']['arguments']
                    }
                }
                for tc in tool_calls
            ]
        }
        messages.append(assistant_message)
        
        # 执行每个工具调用
        tool_results = []
        for tool_call in tool_calls:
            print(f"\n执行工具: {tool_call['function']['name']}")
            print(f"参数: {tool_call['function']['arguments']}")
            
            try:
                result = await execute_tool(tool_call)
                print(f"工具执行结果类型: {type(result)}")
                
                # 格式化工具结果
                if isinstance(result, dict):
                    # 对于搜索工具，result 是 dict，包含 response 字段
                    tool_result_content = result.get('response', json.dumps(result, ensure_ascii=False))
                else:
                    tool_result_content = str(result)
                
                # 添加工具结果到消息历史
                tool_result_message = {
                    'role': 'tool',
                    'content': tool_result_content,
                    'tool_call_id': tool_call['id']
                }
                messages.append(tool_result_message)
                tool_results.append({
                    'tool_call_id': tool_call['id'],
                    'result': tool_result_content[:200] + '...' if len(tool_result_content) > 200 else tool_result_content
                })
                
                print(f"✓ 工具执行成功 (结果长度: {len(tool_result_content)} 字符)")
                
            except Exception as e:
                error_msg = f"工具执行失败: {str(e)}"
                print(f"✗ {error_msg}")
                messages.append({
                    'role': 'tool',
                    'content': error_msg,
                    'tool_call_id': tool_call['id']
                })
        
        # 第二次调用：模型基于工具结果回答
        print("\n[第三步] 模型基于工具结果回答问题...")
        print("-" * 60)
        
        async for chunk in query_model_stream(
            model_id='gpt-4o-mini', 
            messages=messages, 
            tools=search_tool
        ):
            if chunk['type'] == 'content':
                print(chunk['delta'], end='', flush=True)
            elif chunk['type'] == 'done':
                final_content = chunk.get('content', '')
                print(f"\n\n[完成] 最终回答长度: {len(final_content)} 字符")
    else:
        print("\n[注意] 模型没有调用工具，直接返回了答案")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())