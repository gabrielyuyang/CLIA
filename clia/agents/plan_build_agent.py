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
    PLAN_PROMPT = f"""
你是一个规划-执行助手，必须按以下规则生成步骤计划：

1. 输出格式必须是 JSON 数组，每个元素包含以下两种结构之一：
   - 工具步骤：{{"action": "tool", "tool": "<name>", "args": {...}, "note": "why"}}
   - 最终步骤：{{"action": "final", "answer": "<string>"}}

2. 可用工具规范：
{tools_specs()}

3. 强制规则：
   - 必须以 {{"action": "final"}} 结尾，无论是否使用了工具
   - 如果无需工具，直接返回 [{{"action": "final", "answer": "..."}}]
   - 如果需要工具，格式为：[工具步骤1, ...,{{"action": "final", "answer": "..."}}]
   - "answer" 字段中禁止出现任何工具名称或工具调用语法
   - 工具参数必须严格符合工具规范要求

4. 示例：
   直接回答示例：
   [{{"action": "final", "answer": "这是一个编程助手"}}]
   需要工具示例：
   [
     {{"action": "tool", "tool": "read_file", "args": {{"path_str": "test.txt", "max_chars": 1000}}, "note": "读取文件内容"}},
     {{"action": "final", "answer": "文件内容显示..."}}
   ]

5. 限制：
   - 仅使用上述明确列出的工具
   - 总步骤数控制在 1-3 步（含 final 步骤）
   - 确保 JSON 格式严格有效
   - 工具参数必须完整且符合 schema 定义
"""
    print(PLAN_PROMPT)

    messages = [
        {"role": "system", "content": PLAN_PROMPT},
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


def _builder(question: str,
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
              timeout: float,
              return_metadata: bool = False) -> str:

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

    if return_metadata:
        steps_executed = len([s for s in results_steps if isinstance(s, dict)])
        metadata = {
            "plan": plan,
            "execution_results": results_steps,
            "steps_executed": steps_executed,
            "max_steps": max_steps
        }
        return final_answer, metadata

    return final_answer


def plan_build(question: str,
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
                 timeout: float,
                 return_metadata: bool = False) -> str:
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
    return _builder(question=question,
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
                     timeout=timeout,
                     return_metadata=return_metadata)
