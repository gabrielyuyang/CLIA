from typing import Dict, Optional, List
import json
import re
import logging
from .tool_router import run_tool, tools_specs, TOOLS
from clia.agents import llm, prompts


logger = logging.getLogger(__name__)
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

    # 获取任务特定的prompt
    PLAN_PROMPT = """
你是一个规划-执行助手，请先给出步骤计划。输出 JSON 数组，每个元素形如：
{"action": "tool", "tool": "<name>", "args": {...}, "note": "why"}
或 {"action": "final", "answer": "<string>"}
规则：
- 仅使用系统提示中列出的工具，不要编造。
- 步数尽量精简，通常 1-3 步。
- 如果已经能直接回答，给一个 final, 而且answer中不能包含tool。
- 如果需要工具，先列出工具步骤，最后一个步骤给 final。"""

    messages = [
        {"role": "system", "content": PLAN_PROMPT + "\n\n可用工具:\n" + tools_specs()},
        {"role": "user", "content": question}
    ]

    # 调用LLM API
    response = llm.openai_completion(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty,
        timeout=timeout
    )

    response = _extract_plan(response)
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

    results_steps: List[Dict] = []
    final_answer: Optional[str] = None

    for idx, step in enumerate(plan[: max_steps]):
        if step["action"] == "tool" or step["action"] in TOOLS:
            tool_name = step.get("tool")
            tool_args = step.get("args", {})
            try:
                logger.debug(f"Running tool: {tool_name} with args: {tool_args}")
                result = run_tool(tool_name, **tool_args)
                logger.debug(f"Tool execution result: {result}")
            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name}: {e}")
                result = f"[工具执行失败] {tool_name}: {e}"
            results_steps.append(
                {"step": idx,
                 "tool": tool_name,
                 "args": tool_args,
                 "result": result})
        elif step["action"] == "final":
            logger.debug(f"Final answer in step: {step['answer']}")
            results_steps.append(step["answer"])
            break

    if final_answer:
        logger.info(f"Final answer: {final_answer}")
        return final_answer

    # 获取任务特定的prompt
    system_prompt, few_shots = prompts.get_prompt(command)
    results_text = "\n".join([
        json.dumps(step, ensure_ascii=False) for step in results_steps])
    messages = [
        {"role": "system", "content": system_prompt + "\n你同时需要根据工具执行的结果, 给出回答。"},
        *few_shots,
        {"role": "user", "content": question},
        {"role": "user", "content": "工具执行结果：\n" + results_text}
    ]

    final_answer = llm.openai_completion(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
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
