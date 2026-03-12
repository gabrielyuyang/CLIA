"""
BabyAGI-style agent implementation.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from clia.agents import llm, prompts
from .tool_router import run_tool, tools_specs

logger = logging.getLogger(__name__)

_TASK_LIST_PATTERN = re.compile(r"\[[\s\S]*\]")


@dataclass
class Task:
    id: int
    description: str
    priority: float = 0.5


@dataclass
class TaskList:
    tasks: List[Task] = field(default_factory=list)
    _normalized: set[str] = field(default_factory=set)
    _counter: int = 0

    def add_task(self, description: str, priority: float = 0.5) -> bool:
        normalized = _normalize_task(description)
        if not normalized or normalized in self._normalized:
            return False
        self._counter += 1
        self.tasks.append(Task(id=self._counter, description=description.strip(), priority=priority))
        self._normalized.add(normalized)
        return True

    def pop_next(self) -> Optional[Task]:
        if not self.tasks:
            return None
        self.tasks.sort(key=lambda t: (-t.priority, t.id))
        return self.tasks.pop(0)

    def is_empty(self) -> bool:
        return len(self.tasks) == 0

    def as_lines(self) -> List[str]:
        return [f"{t.description} (priority={t.priority:.2f})" for t in self.tasks]


def _normalize_task(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _extract_json_array(text: str) -> Optional[str]:
    match = _TASK_LIST_PATTERN.search(text)
    return match.group(0) if match else None


def _build_task_execution_prompt(command: str) -> str:
    system_prompt, _ = prompts.get_prompt(command)
    return f"""You are a BabyAGI execution agent.

{system_prompt}

## Available Tools:
{tools_specs()}

## Output Format:
Return JSON with either:
- {{"response": "..."}}
- {{"tool": {{"name": "tool_name", "args": {{...}}}}}}

Rules:
- Use only listed tools
- Tool args must follow tool schema
- If no tool needed, return response
"""


def _build_task_generation_prompt(command: str) -> str:
    system_prompt, _ = prompts.get_prompt(command)
    return f"""You are a BabyAGI task generator.

{system_prompt}

Generate follow-up tasks based on the latest task result.
Return a JSON array of objects:
[{{"task": "...", "priority": 0.0}}]

Rules:
- 0.0 to 1.0 priority
- Avoid duplicates of existing tasks
- Keep tasks concise
"""


def _execute_task(
    task: Task,
    question: str,
    command: str,
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    stream: bool,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float
) -> str:
    system_prompt = _build_task_execution_prompt(command)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Overall goal: {question}\nTask: {task.description}"}
    ]

    response = llm.openai_completion(
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

    try:
        parsed = json.loads(response)
    except Exception:
        return response

    tool_info = parsed.get("tool") if isinstance(parsed, dict) else None
    if tool_info and isinstance(tool_info, dict):
        tool_name = tool_info.get("name")
        tool_args = tool_info.get("args", {})
        try:
            observation = run_tool(tool_name, **tool_args)
        except Exception as exc:
            observation = f"Error executing tool {tool_name}: {exc}"

        followup_messages = [
            {"role": "system", "content": prompts.get_prompt(command)[0]},
            {
                "role": "user",
                "content": f"Overall goal: {question}\nTask: {task.description}\nObservation: {observation}\nProvide the final response."
            }
        ]
        return llm.openai_completion(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            model=model,
            messages=followup_messages,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            max_tokens=max_tokens,
            timeout=timeout
        )

    if isinstance(parsed, dict) and "response" in parsed:
        return str(parsed.get("response"))

    return response


def _generate_tasks(
    question: str,
    task: Task,
    result: str,
    task_list: TaskList,
    command: str,
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    stream: bool,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float
) -> List[Dict]:
    system_prompt = _build_task_generation_prompt(command)
    existing = "\n".join(task_list.as_lines())
    prompt = (
        f"Overall goal: {question}\n"
        f"Current task: {task.description}\n"
        f"Result: {result}\n\n"
        f"Existing tasks:\n{existing if existing else '- (none)'}\n"
    )

    response = llm.openai_completion(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout
    )

    candidate = _extract_json_array(response)
    if not candidate:
        return []
    try:
        tasks = json.loads(candidate)
        if isinstance(tasks, list):
            return tasks
    except Exception:
        pass
    return []


def babyagi_agent(
    question: str,
    command: str,
    max_iterations: int = 10,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    stream: bool = False,
    temperature: float = 0.3,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 4096,
    timeout: float = 30.0,
    return_metadata: bool = False,
    memory_manager=None
) -> str | Tuple[str, Dict]:
    task_list = TaskList()
    task_list.add_task(question, priority=1.0)

    last_result = ""
    iterations = 0

    while not task_list.is_empty() and iterations < max_iterations:
        current_task = task_list.pop_next()
        if not current_task:
            break
        iterations += 1

        result = _execute_task(
            task=current_task,
            question=question,
            command=command,
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            model=model,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            max_tokens=max_tokens,
            timeout=timeout
        )
        last_result = result

        for item in _generate_tasks(
            question=question,
            task=current_task,
            result=result,
            task_list=task_list,
            command=command,
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            model=model,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            max_tokens=max_tokens,
            timeout=timeout
        ):
            if not isinstance(item, dict):
                continue
            description = item.get("task")
            if not description:
                continue
            priority = item.get("priority", 0.5)
            try:
                priority = float(priority)
            except Exception:
                priority = 0.5
            task_list.add_task(description, priority=priority)

    if memory_manager:
        try:
            memory_manager.add_memory(
                question=question,
                answer=last_result,
                command=command,
                agent_type="babyagi",
                metadata={
                    "iterations_used": iterations,
                    "max_iterations": max_iterations
                }
            )
        except Exception as exc:
            logger.warning(f"Failed to save memory: {exc}")

    if return_metadata:
        return last_result, {
            "iterations_used": iterations,
            "max_iterations": max_iterations
        }

    return last_result or "No response generated"
