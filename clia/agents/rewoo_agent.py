"""
ReWOO Agent Implementation

ReWOO (Reasoning WithOut Observation) is an agent pattern that:
1. Plans all tool calls upfront with variable placeholders (#E1, #E2, etc.)
2. Executes all tools in parallel (worker phase)
3. Synthesizes final answer using all results (solver phase)

Key difference: Plans WITHOUT seeing intermediate observations, enabling full parallelization.
"""

from typing import Dict, List, Tuple
import json
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from .tool_router import run_tool, tools_specs, TOOLS
from clia.agents import llm, prompts

logger = logging.getLogger(__name__)

PLAN_PATTERN = re.compile(r"```json\s*(\[.*?\])\s*```", re.DOTALL)
PLAN_PATTERN_SIMPLE = re.compile(r"\[.*?\]", re.DOTALL)


def _extract_plan(response: str) -> List[Dict]:
    """Extract ReWOO plan from LLM response."""
    match = PLAN_PATTERN.search(response)
    if match:
        try:
            plan = json.loads(match.group(1))
            if isinstance(plan, list):
                return plan
        except json.JSONDecodeError:
            pass

    match = PLAN_PATTERN_SIMPLE.search(response)
    if match:
        try:
            plan = json.loads(match.group(0))
            if isinstance(plan, list):
                return plan
        except json.JSONDecodeError:
            pass

    logger.warning("Could not extract valid plan")
    return [{"id": "#E1", "action": "final", "answer": response}]


def _build_rewoo_prompt(command: str) -> str:
    """Build ReWOO system prompt."""
    system_prompt, _ = prompts.get_prompt(command)

    return f"""You are a helpful assistant using the ReWOO (Reasoning WithOut Observation) pattern.

{system_prompt}

## Available Tools:
{tools_specs()}

## ReWOO Pattern:
Generate a plan with tool calls using variable placeholders (#E1, #E2, etc.) for results.

Format:
```json
[
    {{
        "id": "#E1",
        "tool": "tool_name",
        "args": {{"arg": "value"}}
    }},
    {{
        "id": "#E2",
        "tool": "another_tool",
        "args": {{"arg": "#E1"}}
    }},
    {{
        "id": "final",
        "action": "final",
        "plan": "Use #E1 and #E2 to answer..."
    }}
]
```

Rules:
1. Use #E1, #E2, etc. as placeholders for tool results
2. Reference previous results in subsequent tool args using placeholders
3. End with "action": "final" and a "plan" describing how to use results
4. All tools execute in parallel where possible
5. Only use listed tools

Generate the plan:"""


def _planner(question: str, command: str, api_key: str, base_url: str, max_retries: int,
             model: str, stream: bool, temperature: float, top_p: float,
             frequency_penalty: float, max_tokens: int, timeout: float,
             memory_manager=None) -> List[Dict]:
    """Generate ReWOO plan with variable placeholders."""
    system_prompt = _build_rewoo_prompt(command)

    memory_context = ""
    if memory_manager and memory_manager.memories:
        from datetime import datetime, timedelta
        recent_memories = [m for m in memory_manager.memories
                          if (datetime.now() - datetime.fromisoformat(m.timestamp)) < timedelta(hours=1)]
        recent_memories = sorted(recent_memories, key=lambda m: m.timestamp, reverse=True)[:3]

        if recent_memories:
            memory_context = "\n\n## Previous Context:\n"
            for i, mem in enumerate(recent_memories, 1):
                memory_context += f"{i}. Q: {mem.question}\n   A: {mem.answer[:200]}{'...' if len(mem.answer) > 200 else ''}\n"

    if memory_context:
        system_prompt = system_prompt.rstrip() + memory_context

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    response = llm.openai_completion(
        api_key=api_key, base_url=base_url, max_retries=max_retries,
        model=model, messages=messages, stream=stream, temperature=temperature,
        top_p=top_p, frequency_penalty=frequency_penalty, max_tokens=max_tokens,
        timeout=timeout
    )

    return _extract_plan(response)


def _worker(plan: List[Dict]) -> Dict[str, str]:
    """Execute all tool calls in parallel."""
    results = {}
    tool_steps = [s for s in plan if s.get("tool")]

    def execute_step(step: Dict) -> Tuple[str, str]:
        step_id = step.get("id", "unknown")
        tool_name = step.get("tool")

        if tool_name not in TOOLS:
            return (step_id, f"Error: Unknown tool '{tool_name}'")

        tool_args = step.get("args", {})
        try:
            result = run_tool(tool_name, **tool_args)
            logger.debug(f"Step {step_id} completed")
            return (step_id, result)
        except Exception as e:
            logger.error(f"Step {step_id} failed: {e}")
            return (step_id, f"Error: {str(e)}")

    if not tool_steps:
        return {}

    with ThreadPoolExecutor(max_workers=max(1, min(len(tool_steps), 10))) as executor:
        futures = {executor.submit(execute_step, step): step for step in tool_steps}
        for future in as_completed(futures):
            step_id, result = future.result()
            results[step_id] = result

    return results


def _solver(question: str, plan: List[Dict], results: Dict[str, str],
            command: str, api_key: str, base_url: str, max_retries: int,
            model: str, stream: bool, temperature: float, top_p: float,
            frequency_penalty: float, max_tokens: int, timeout: float) -> str:
    """Generate final answer using all tool results."""
    system_prompt, _ = prompts.get_prompt(command)

    final_step = next((s for s in plan if s.get("action") == "final"), None)
    plan_desc = final_step.get("plan", "") if final_step else ""

    results_text = "\n".join([f"{k}: {v[:500]}" for k, v in results.items()])

    synthesis_prompt = f"""Question: {question}

Plan: {plan_desc}

Tool Results:
{results_text}

Provide the final answer:"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": synthesis_prompt}
    ]

    return llm.openai_completion(
        api_key=api_key, base_url=base_url, max_retries=max_retries,
        model=model, messages=messages, stream=stream, temperature=temperature,
        top_p=top_p, frequency_penalty=frequency_penalty, max_tokens=max_tokens,
        timeout=timeout
    )


def rewoo_agent(question: str, command: str, api_key: str = None, base_url: str = None,
                max_retries: int = 5, model: str = None, stream: bool = False,
                temperature: float = 0.0, top_p: float = 0.85,
                frequency_penalty: float = 0.0, max_tokens: int = 4096,
                timeout: float = 30.0, verbose: bool = False,
                return_metadata: bool = False, memory_manager=None) -> str:
    """
    Run ReWOO agent: Plan -> Work -> Solve.

    Returns:
        Final answer string, or tuple of (answer, metadata) if return_metadata=True
    """
    if verbose:
        logger.info("="*60)
        logger.info("PHASE 1: Planning")
        logger.info("="*60)

    plan = _planner(question, command, api_key, base_url, max_retries, model,
                    stream, temperature, top_p, frequency_penalty, max_tokens,
                    timeout, memory_manager)

    # If the plan only contains a direct answer (no tools), return it immediately
    if len(plan) == 1 and plan[0].get("action") == "final" and "answer" in plan[0]:
        final_answer = plan[0]["answer"]
        if memory_manager:
            try:
                memory_manager.add_memory(
                    question=question, answer=final_answer, command=command,
                    agent_type="rewoo",
                    metadata={"plan_length": 1, "tools_executed": 0, "direct_answer": True}
                )
            except Exception as e:
                logger.warning(f"Failed to save memory: {e}")

        if return_metadata:
            return final_answer, {
                "plan": plan,
                "execution_results": {},
                "tools_executed": 0
            }
        return final_answer

    if verbose:
        logger.info(f"Generated plan with {len(plan)} steps")
        for step in plan:
            logger.info(f"  {step.get('id')}: {step.get('tool', step.get('action'))}")

    if verbose:
        logger.info("="*60)
        logger.info("PHASE 2: Working")
        logger.info("="*60)

    results = _worker(plan)

    if verbose:
        logger.info(f"Executed {len(results)} tools")

    if verbose:
        logger.info("="*60)
        logger.info("PHASE 3: Solving")
        logger.info("="*60)

    final_answer = _solver(question, plan, results, command, api_key, base_url,
                           max_retries, model, stream, temperature, top_p,
                           frequency_penalty, max_tokens, timeout)

    if memory_manager:
        try:
            memory_manager.add_memory(
                question=question, answer=final_answer, command=command,
                agent_type="rewoo",
                metadata={"plan_length": len(plan), "tools_executed": len(results)}
            )
        except Exception as e:
            logger.warning(f"Failed to save memory: {e}")

    if return_metadata:
        return final_answer, {
            "plan": plan,
            "execution_results": results,
            "tools_executed": len(results)
        }

    return final_answer
