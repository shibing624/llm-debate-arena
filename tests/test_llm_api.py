
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.llm_client import query_model_stream, query_model

TEST_MODELS = [
    # 'claude-opus-4-1-20250805',
    'deepseek-r1',
    # 'gemini-2.5-flash',
    # 'gemini-3-pro-preview',
    # 'gpt-5',
    'gpt-4o',
    'gpt-4o-mini',
    'kimi-k2',
]


async def probe_model(model_id: str) -> None:
    """尝试流式调用指定模型，打印增量与最终状态。"""
    print(f'\n===== 测试模型: {model_id} =====')
    messages = [{'role': 'user', 'content': '你好，一句话介绍一下你自己。'}]
    try:
        async for chunk in query_model_stream(
            model_id=model_id,
            messages=messages,
        ):
            print(chunk)
    except Exception as err:
        print(f'调用 {model_id} 失败: {err}')


async def main():
    for model in TEST_MODELS:
        await probe_model(model)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())