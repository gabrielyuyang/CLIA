"""
LLMCompiler Agent Implementation

LLMCompiler is an agent pattern that compiles a task into a Directed Acyclic Graph (DAG)
of tool calls and executes them in parallel where dependencies allow.

Key features:
1. Plans tool calls as a DAG with explicit dependencies
2. Executes independent tool calls in parallel
3. Follows dependency order for sequential execution when needed
"""

from typing import Dict, List, Optional, Set, Tuple
import json
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from .tool_router import run_tool, tools_specs, TOOLS
from clia.agents import llm, prompts

logger = logging.getLogger(__name__)

# Regex patterns to extract LLMCompiler plan components
PLAN_PATTERN = re.compile(r"```json\s*(\[.*?\])\s*```", re.DOTALL)
PLAN_PATTERN_SIMPLE = re.compile(r"\[.*?\]", re.DOTALL)


def _extract_plan(response: str) -> List[Dict]:
    """
    Extract the DAG plan from LLM response.

    Expected format:
    [
        {
            "id": "step1",
            "tool": "read_file",
            "args": {"path_str": "file.txt", "max_chars": 1000},
            "dependencies": []
        },
        {
            "id": "step2",
            "tool": "http_get",
            "args": {"url": "https://example.com", "timeout": 10.0},
            "dependencies": []
        },
        {
            "id": "step3",
            "tool": "echo",
            "args": {"text": "Processing..."},
            "dependencies": ["step1", "step2"]
        },
        {
            "id": "final",
            "action": "final",
            "answer": "...",
            "dependencies": ["step3"]
        }
    ]
    """
    # Try to find JSON in code blocks first
    match = PLAN_PATTERN.search(response)
    if match:
        try:
            plan = json.loads(match.group(1))
            if isinstance(plan, list):
                return plan
        except json.JSONDecodeError:
            pass

    # Try simple JSON array
    match = PLAN_PATTERN_SIMPLE.search(response)
    if match:
        try:
            plan = json.loads(match.group(0))
            if isinstance(plan, list):
                return plan
        except json.JSONDecodeError:
            pass

    # Fallback: try to parse the entire response as JSON
    try:
        plan = json.loads(response)
        if isinstance(plan, list):
            return plan
    except json.JSONDecodeError:
        pass

    # If no valid plan found, return a simple plan with final answer
    logger.warning("Could not extract valid plan, treating response as final answer")
    return [{"id": "final", "action": "final", "answer": response, "dependencies": []}]


def _validate_plan(plan: List[Dict]) -> bool:
    """Validate that the plan is a valid DAG."""
    # Check for cycles
    ids = {step.get("id") for step in plan if "id" in step}

    # Build dependency graph
    graph: Dict[str, Set[str]] = {step.get("id", ""): set() for step in plan if "id" in step}

    for step in plan:
        step_id = step.get("id")
        if not step_id:
            continue
        deps = step.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []

        # Verify all dependencies exist
        for dep in deps:
            if dep not in ids:
                logger.warning(f"Dependency {dep} not found in plan for step {step_id}")
                return False

        graph[step_id] = set(deps)

    # Check for cycles using DFS
    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def has_cycle(node: str) -> bool:
        if node in rec_stack:
            return True
        if node in visited:
            return False

        visited.add(node)
        rec_stack.add(node)

        for dep in graph.get(node, set()):
            if has_cycle(dep):
                return True

        rec_stack.remove(node)
        return False

    for node_id in graph:
        if node_id not in visited:
            if has_cycle(node_id):
                logger.error("Plan contains cycles - not a valid DAG")
                return False

    return True


def _build_compiler_prompt(command: str) -> str:
    """Build the LLMCompiler system prompt for the agent."""
    system_prompt, _ = prompts.get_prompt(command)

    compiler_system_prompt = f"""You are a helpful assistant that uses the LLMCompiler pattern to solve tasks efficiently.

{system_prompt}

## Available Tools:
{tools_specs()}

## LLMCompiler Pattern:
You must compile the task into a Directed Acyclic Graph (DAG) of tool calls that can be executed efficiently.

### Planning Phase:
Generate a JSON array where each element represents a step in the execution plan:

```json
[
    {{
        "id": "step1",
        "tool": "tool_name",
        "args": {{"arg1": "value1", "arg2": "value2"}},
        "dependencies": []
    }},
    {{
        "id": "step2",
        "tool": "another_tool",
        "args": {{"arg1": "value1"}},
        "dependencies": ["step1"]
    }},
    {{
        "id": "final",
        "action": "final",
        "answer": "Your final answer based on all tool results",
        "dependencies": ["step1", "step2"]
    }}
]
```

### Rules:
1. **Dependencies**: Use the "dependencies" field to specify which step IDs must complete before this step
2. **Parallel Execution**: Steps with no dependencies or the same dependencies can run in parallel
3. **Tool Steps**: For tool execution, use "tool" and "args" fields
4. **Final Step**: Always include a final step with "action": "final" that provides the answer
5. **DAG Requirement**: The plan must form a valid Directed Acyclic Graph (no cycles)
6. **Efficiency**: Minimize dependencies to maximize parallel execution
7. **Tool Names**: Only use tools listed above - do not make up tool names
8. **JSON Format**: Output must be valid JSON - wrap it in ```json code blocks

### Example:
If you need to read two files and then process them, you can run the reads in parallel:
```json
[
    {{
        "id": "read1",
        "tool": "read_file",
        "args": {{"path_str": "file1.txt", "max_chars": 1000}},
        "dependencies": []
    }},
    {{
        "id": "read2",
        "tool": "read_file",
        "args": {{"path_str": "file2.txt", "max_chars": 1000}},
        "dependencies": []
    }},
    {{
        "id": "final",
        "action": "final",
        "answer": "Processed both files: ...",
        "dependencies": ["read1", "read2"]
    }}
]
```

Now, generate the execution plan for the task below:"""

    return compiler_system_prompt


def _execute_step(step: Dict, results: Dict[str, str]) -> Tuple[str, str]:
    """Execute a single step and return (step_id, result)."""
    step_id = step.get("id", "unknown")

    # Check if this is a final answer step
    if step.get("action") == "final":
        answer = step.get("answer", "")
        return (step_id, answer)

    # Execute tool
    tool_name = step.get("tool")
    if not tool_name:
        return (step_id, f"Error: No tool specified in step {step_id}")

    if tool_name not in TOOLS:
        return (step_id, f"Error: Unknown tool '{tool_name}'. Available tools: {list(TOOLS.keys())}")

    tool_args = step.get("args", {})

    try:
        result = run_tool(tool_name, **tool_args)
        logger.debug(f"Step {step_id} ({tool_name}) completed: {result[:100]}...")
        return (step_id, result)
    except Exception as e:
        error_msg = f"Error executing {tool_name} in step {step_id}: {str(e)}"
        logger.error(error_msg)
        return (step_id, error_msg)


def _execute_plan_parallel(plan: List[Dict]) -> Dict[str, str]:
    """
    Execute the plan respecting dependencies and using parallel execution where possible.

    Returns:
        Dictionary mapping step IDs to their results
    """
    results: Dict[str, str] = {}
    completed: Set[str] = set()

    # Build dependency graph
    step_map: Dict[str, Dict] = {step.get("id"): step for step in plan if "id" in step}

    # Execute in rounds - each round can run steps whose dependencies are satisfied
    round_num = 0
    max_rounds = len(plan) * 2  # Safety limit

    while len(completed) < len(step_map) and round_num < max_rounds:
        round_num += 1

        # Find steps that can be executed (all dependencies completed)
        ready_steps = []
        for step_id, step in step_map.items():
            if step_id in completed:
                continue

            deps = set(step.get("dependencies", []))
            if deps.issubset(completed):
                ready_steps.append(step)

        if not ready_steps:
            # Check if we're stuck (might be a cycle or missing dependency)
            remaining = set(step_map.keys()) - completed
            logger.warning(f"No ready steps found. Remaining: {remaining}")
            break

        # Execute ready steps in parallel
        logger.debug(f"Round {round_num}: Executing {len(ready_steps)} steps in parallel")

        with ThreadPoolExecutor(max_workers=min(len(ready_steps), 10)) as executor:
            future_to_step = {
                executor.submit(_execute_step, step, results): step.get("id")
                for step in ready_steps
            }

            for future in as_completed(future_to_step):
                step_id, result = future.result()
                results[step_id] = result
                completed.add(step_id)
                logger.debug(f"Completed step: {step_id}")

    if len(completed) < len(step_map):
        remaining = set(step_map.keys()) - completed
        logger.warning(f"Some steps were not completed: {remaining}")
        for step_id in remaining:
            if step_id not in results:
                results[step_id] = f"Error: Step {step_id} was not executed (dependencies not satisfied)"

    return results


def llm_compiler_agent(
    question: str,
    command: str,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    stream: bool = False,
    temperature: float = 0.0,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 4096,
    timeout: float = 30.0,
    verbose: bool = False,
    return_metadata: bool = False,
    memory_manager = None
) -> str:
    """
    Run an LLMCompiler agent to solve a task.

    Args:
        question: The user's question or task
        command: The command type (ask, explain, debug, fix, generate, draft)
        api_key: OpenAI API key
        base_url: OpenAI API base URL
        max_retries: Maximum retries for API calls
        model: Model name
        stream: Whether to stream responses
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty
        max_tokens: Maximum tokens in response
        timeout: Request timeout
        verbose: Whether to print intermediate steps

    Returns:
        Final answer string
        If return_metadata is True, returns tuple of (final_answer, metadata_dict)
    """
    system_prompt = _build_compiler_prompt(command)

    # Phase 1: Planning - Get the DAG plan from LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    logger.info("=" * 60)
    logger.info("PHASE 1: Planning - Generating execution plan")
    logger.info("=" * 60)

    try:
        plan_response = llm.openai_completion(
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
    except Exception as e:
        logger.error(f"LLM call failed during planning: {e}")
        return f"Error: Failed to get plan from LLM: {e}"

    logger.info(f"\n[Planning Response]\n{plan_response}\n")

    # Extract and validate plan
    plan = _extract_plan(plan_response)
    plan_valid = _validate_plan(plan)

    if not plan_valid:
        logger.error("Invalid plan generated - contains cycles or missing dependencies")
        return "Error: Generated plan is invalid (contains cycles or missing dependencies). Please try again."

    logger.info(f"Plan validated: {len(plan)} steps")
    for step in plan:
        deps = step.get("dependencies", [])
        logger.info(f"  - {step.get('id')}: {step.get('tool', step.get('action', 'unknown'))} (deps: {deps})")

    # Phase 2: Execution - Execute the plan respecting dependencies
    logger.info("=" * 60)
    logger.info("PHASE 2: Execution - Running tool calls in parallel where possible")
    logger.info("=" * 60)

    results = _execute_plan_parallel(plan)

    logger.info(f"Execution completed: {len(results)} results")
    for step_id, result in results.items():
        logger.info(f"  - {step_id}: {result[:500]}...")

    logger.info("=" * 60)
    logger.info("Phase 3: Final Answer - Extract final answer or synthesize from results")
    logger.info("=" * 60)
    
    # Phase 3: Final Answer - Extract final answer or synthesize from results
    final_steps = [step for step in plan if step.get("action") == "final"]

    if final_steps:
        # Use the final step's answer, enriched with actual tool results
        final_step = final_steps[0]
        final_id = final_step.get("id", "final")
        base_answer = final_step.get("answer", "")

        # Check if there are tool results to incorporate
        tool_results = {k: v for k, v in results.items() if k != final_id}
        
        if tool_results:
            # Synthesize answer using tool results
            results_summary = "\n".join([
                f"{step_id}: {result[:500]}"
                for step_id, result in tool_results.items()
            ])
            
            synthesis_prompt = f"""Based on the following tool execution results, provide a comprehensive final answer to the user's question.

Question: {question}

Tool Results:
{results_summary}

Initial Answer: {base_answer}

Please provide a clear, comprehensive final answer that incorporates all relevant information from the tool results:"""
            
            messages_synthesis = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": synthesis_prompt}
            ]
            
            try:
                final_answer = llm.openai_completion(
                    api_key=api_key,
                    base_url=base_url,
                    max_retries=max_retries,
                    model=model,
                    messages=messages_synthesis,
                    stream=stream,
                    temperature=temperature,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
                logger.info("Successfully synthesized final answer from tool results")
            except Exception as e:
                logger.error(f"Failed to synthesize final answer: {e}")
                # Fall back to base answer with results appended
                final_answer = f"{base_answer}\n\nTool Results:\n{results_summary}"
        else:
            # No tool results, use the base answer
            final_answer = base_answer
    else:
        # No explicit final step - synthesize answer from results
        logger.warning("No final step found in plan, synthesizing answer from results")

        # Get results summary
        results_summary = "\n".join([
            f"{step_id}: {result[:200]}"
            for step_id, result in results.items()
        ])

        # Ask LLM to synthesize final answer
        synthesis_prompt = f"""Based on the following tool execution results, provide a final answer to the user's question.

Question: {question}

Tool Results:
{results_summary}

Provide a clear, concise final answer:"""

        messages_synthesis = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": synthesis_prompt}
        ]

        try:
            final_answer = llm.openai_completion(
                api_key=api_key,
                base_url=base_url,
                max_retries=max_retries,
                model=model,
                messages=messages_synthesis,
                stream=stream,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                max_tokens=max_tokens,
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Failed to synthesize final answer: {e}")
            final_answer = f"Tool execution completed but failed to generate final answer: {e}\n\nResults:\n{results_summary}"

    # Save to memory if memory manager is available
    if memory_manager:
        try:
            memory_manager.add_memory(
                question=question,
                answer=final_answer,
                command=command,
                agent_type="llm-compiler",
                metadata={
                    "plan_length": len(plan),
                    "plan_valid": plan_valid,
                    "steps_executed": len(results)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to save memory: {e}")

    if return_metadata:
        metadata = {
            "plan": plan,
            "execution_results": results,
            "plan_valid": plan_valid
        }
        return final_answer, metadata

    return final_answer


def llm_compiler_agent_simple(
    question: str,
    command: str = "ask",
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    stream: bool = False,
    temperature: float = 0.0,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 4096,
    timeout: float = 30.0
) -> str:
    """
    Simplified LLMCompiler agent that returns a single string response.

    This is a convenience wrapper around llm_compiler_agent for non-streaming use cases.
    """
    return llm_compiler_agent(
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
        timeout=timeout,
        verbose=False
    )