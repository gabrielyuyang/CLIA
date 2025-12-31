from openai import OpenAI
from typing import List, Dict
import logging


logger = logging.getLogger(__name__)


def _openai_client(*,
                   api_key: str,
                   base_url: str,
                   max_retries: int) -> OpenAI:

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries
        )


def openai_completion(*,
                      api_key: str,
                      base_url: str,
                      max_retries: int,
                      model: str,
                      messages: List[Dict],
                      stream: bool,
                      temperature: float,
                      top_p: float,
                      frequency_penalty: float,
                      max_tokens: int,
                      timeout: float) -> str:

    logger.info("Creating OpenAI client")
    client = _openai_client(api_key=api_key,
                            base_url=base_url,
                            max_retries=max_retries)

    logger.info("Sending OpenAI completion request")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout
    )

    logger.info("Received OpenAI completion response")
    # 处理响应
    full_response = []
    if not stream:
        # 非流式输出
        content = response.choices[0].message.content
        full_response.append(content)
        logger.info("Non-streaming response received")
        # print("-" * 28 + "\n")
        print(content)
        # print("-" * 28 + "\n")
    else:
        # 流式输出
        # print("-" * 28 + "\n")
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response.append(content)
        # print("\n" + "-" * 28 + "\n")
        logger.info("Streaming response received")
    return '\n'.join(full_response)
