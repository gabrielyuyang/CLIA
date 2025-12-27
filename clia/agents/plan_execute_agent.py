from token import tok_name
from typing import Dict, Optional, Tuple, List
import json
import re
from tool_router import run_tool, tools_specs
from openai.types.responses import response
import llm
import prompts

PLAN_RE = re.compile(r"\[.*\]", re.DOTALL)

def _extract_plan(plan: str) -> List[Dict]:
    match = PLAN_RE.search(plan)
    candidate = match.group(0) if match else None
    if not candidate:
        return [{"action": "final", "answer": plan}]
    try:
        plan = json.loads(candidate)
        if isinstance(plan, list):
            return plan
    except Exception:
        pass
    return [{"action": "final", "answer": plan}]

def _planner(question: str,
             api_key: str,
             base_url: str,
             max_retries: int,
             model: str,
             stream: bool,
             temperature: float,
             top_p: float,
             frequency_penalty: float,
             max_tokens: int,
             timeout: float) -> List[Dict]:
        
    # 创建LLM客户端
    client = llm.openai_client(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries
    )

    # 获取任务特定的prompt
    PLAN_PROMPT = """
你是一个规划-执行助手，请先给出步骤计划。输出 JSON 数组，每个元素形如：
{"action": "tool", "tool": "<name>", "args": {...}, "note": "why"} 或 {"action": "final", "answer": "<string>"}
规则：
- 仅使用系统提示中列出的工具，不要编造。
- 步数尽量精简，通常 1-3 步。
- 如果已经能直接回答，给一个 final。
- 如果需要工具，先列出工具步骤，最后一个步骤给 final。"""

    messages = [
        {"role": "system", "content": PLAN_PROMPT + "\n\n可用工具:\n" + tools_specs()},
        {"role": "user", "content": question}
    ]

    # logger.info(
    #     f"Messages prepared for {args.command} command: {messages}")

    # 调用LLM API
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
    
    # TO-DO：支持流式输出
    response = _extract_plan(response.choices[0].message.content)
    return response

def _executor(question: str,
              plan: List[Dict],
              command: str,
              max_steps: int,
              api_key: str,
              base_url: str,
              max_retries: int,
              model: str,
              stream: bool,
              temperature: float,
              top_p: float,
              frequency_penalty: float,
              max_tokens: int,
              timeout: float) -> str:
    # 创建LLM客户端
    client = llm.openai_client(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries
    )

    results_steps: List[Dict] = []
    final_answer: Optional[str] = None
    
    for idx, step in enumerate(plan[: max_steps]):
        if step["action"] == "tool":
            tool_name = step.get("tool")
            tool_args = step.get("args", {})
            try:
                result = run_tool(tool_name, **tool_args)
            except Exception as e:
                result = f"[工具执行失败] {tool_name}: {e}"
            results_steps.append({"step": idx, "tool": tool_name, "args": tool_args, "result": result})
        elif step["action"] == "final":
            final_answer = step["answer"]
            break
        
    if final_answer:
        return final_answer
    
    # 获取任务特定的prompt
    system_prompt, few_shots = prompts.get_prompt(command)
    results_text = "\n".join([json.dumps(step, ensure_ascii=False) for step in results_steps])
    messages = [
        {"role": "system", "content": system_prompt + "\n你同时需要根据工具执行的结果, 给出回答。"},
        *few_shots,
        {"role": "user", "content": question},
        {"role": "user", "content": "工具执行结果：\n" + results_text}
    ]
    
    final_answer = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout
    )
    
    # TO-DO：支持with_calibration参数
    # TO-DO：支持流式输出
    
    return final_answer


def plan_execute(question: str,
                 command: str,
                 max_steps: int,
                 api_key: str,
                 base_url: str,
                 max_retries: int,
                 model: str,
                 stream: bool,
                 temperature: float,
                 top_p: float,
                 frequency_penalty: float,
                 max_tokens: int,
                 timeout: float) -> str:
    
    plan = _planner(question=question,
                    api_key=api_key,
                    base_url=base_url,
                    max_retries=max_retries,
                    model=model,
                    stream=stream,
                    temperature=temperature,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    max_tokens=max_tokens,
                    timeout=timeout) 
    return _executor(question=question,
                     plan=plan,
                     command=command,
                     max_steps=max_steps,
                     api_key=api_key,
                     base_url=base_url,
                     max_retries=max_retries,
                     model=model,
                     stream=stream,
                     temperature=temperature,
                     top_p=top_p,
                     frequency_penalty=frequency_penalty,
                     max_tokens=max_tokens,
                     timeout=timeout)
