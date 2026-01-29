"""
Tree-of-Thoughts (ToT) Agent Implementation

ToT explores multiple reasoning paths in parallel, evaluates them, and selects the best approach.
Key features:
1. Multi-path exploration: Generate k candidate thoughts per step
2. Inline evaluation: Score each thought before proceeding
3. Beam search: Prune less promising branches
4. Tool integration: Execute tools suggested by thoughts
5. Synthesis: Aggregate insights from multiple paths
"""

import json
import re
import logging
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from .tool_router import run_tool, tools_specs, TOOLS
from clia.agents import llm, prompts

logger = logging.getLogger(__name__)

@dataclass
class Thought:
    """Represents a single thought in the reasoning tree."""
    id: str
    content: str
    depth: int
    parent_id: Optional[str]
    score: float
    action: Optional[Dict] = None  # Tool call if applicable
    result: Optional[str] = None   # Tool result if executed

    def to_dict(self):
        return asdict(self)

def _build_tot_prompt(command: str) -> str:
    """Build the ToT system prompt for the agent."""
    system_prompt, _ = prompts.get_prompt(command)

    tot_system_prompt = f"""You are a helpful assistant that uses the Tree-of-Thoughts (ToT) pattern to solve complex tasks.

{system_prompt}

## Available Tools:
{tools_specs()}

## Tree-of-Thoughts Pattern:
You will explore multiple reasoning paths to find the best solution.

### Thought Generation:
Generate diverse thoughts at each step. Each thought should represent a distinct approach or perspective.

### Thought Evaluation:
Score each thought on quality (0.0-1.0) based on:
- Relevance: How well does it address the question?
- Feasibility: Is it practically achievable?
- Progress: Does it move toward a solution?

### Tool Integration:
If a thought needs a tool, include a structured action object.

## Rules:
1. Be creative and explore diverse approaches
2. Evaluate thoughts objectively
3. Only use tools listed above
4. Focus on debugging and analysis tasks
5. If a tool is needed, include a structured action with "tool" and "args"

Let's begin!"""

    return tot_system_prompt

def _generate_thoughts(
    question: str,
    command: str,
    current_state: List[Tuple[str, str]],  # [(thought_id, content), ...]
    depth: int,
    branching_factor: int,
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float
) -> List[Thought]:
    """Generate k candidate thoughts for the current state."""

    # Build context from previous thoughts
    context = ""
    if current_state:
        context = "\nPrevious thoughts:\n"
        for thought_id, content in current_state:
            context += f"- {thought_id}: {content}\n"

    system_prompt = _build_tot_prompt(command)

    generation_prompt = f"""Question: {question}

{context}

Generate {branching_factor} diverse thoughts for the next step in solving this problem.
Each thought should represent a different approach or perspective.

Respond with a JSON array:
[
    {{"thought": "First approach description", "action": {{"tool": "read_file", "args": {{"path_str": "a.py", "max_chars": 1000}}}}}},
    {{"thought": "Second approach description"}},
    ...
]"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": generation_prompt}
    ]

    try:
        response = llm.openai_completion(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            model=model,
            messages=messages,
            stream=False,
            temperature=temperature,  # Higher temp for diversity
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            max_tokens=max_tokens,
            timeout=timeout
        )

        # Extract JSON array
        json_match = re.search(r'\[[^\]]*\]', response, re.DOTALL)
        if json_match:
            thoughts_data = json.loads(json_match.group(0))
            thoughts = []
            for i, item in enumerate(thoughts_data):
                thought_content = item.get("thought", "")
                action = item.get("action")
                if thought_content:
                    thought = Thought(
                        id=f"thought_{depth}_{i}_{uuid.uuid4().hex[:8]}",
                        content=thought_content,
                        depth=depth,
                        parent_id=current_state[-1][0] if current_state else None,
                        score=0.0,
                        action=action if isinstance(action, dict) else None
                    )
                    thoughts.append(thought)
            return thoughts
    except Exception as e:
        logger.error(f"Error generating thoughts: {e}")
        # Fallback: create simple thoughts
        return [
            Thought(
                id=f"fallback_{depth}_{i}",
                content=f"Fallback approach {i+1} for depth {depth}",
                depth=depth,
                parent_id=current_state[-1][0] if current_state else None,
                score=0.5
            )
            for i in range(branching_factor)
        ]

    return []

def _evaluate_thought(
    thought: Thought,
    question: str,
    command: str,
    current_state: List[Tuple[str, str]],
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float
) -> float:
    """Evaluate and score a thought (0.0-1.0)."""

    # Build context from previous thoughts
    context = ""
    if current_state:
        context = "\nPrevious thoughts:\n"
        for thought_id, content in current_state:
            context += f"- {thought_id}: {content}\n"

    system_prompt, _ = prompts.get_prompt(command)

    evaluation_prompt = f"""Question: {question}

{context}

Evaluate this thought on quality (0.0-1.0):

Thought: {thought.content}

Scoring criteria:
- Relevance: How well does it address the question?
- Feasibility: Is it practically achievable?
- Progress: Does it move toward a solution?

Respond with ONLY a JSON object:
{{"score": 0.8}}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": evaluation_prompt}
    ]

    try:
        response = llm.openai_completion(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            model=model,
            messages=messages,
            stream=False,
            temperature=0.3,  # Lower temp for consistent scoring
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            max_tokens=max_tokens,
            timeout=timeout
        )

        # Extract score
        json_match = re.search(r'\{[^}]*\}', response)
        if json_match:
            score_data = json.loads(json_match.group(0))
            score = score_data.get("score", 0.5)
            return float(score)
    except Exception as e:
        logger.error(f"Error evaluating thought: {e}")
        return 0.5  # Neutral score on error

    return 0.5

def _execute_thought_action(
    thought: Thought,
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float
) -> Optional[str]:
    """Execute any tool action suggested by the thought."""
    if not thought.action:
        return None
    tool_name = thought.action.get("tool")
    tool_args = thought.action.get("args", {})
    if not tool_name or not isinstance(tool_args, dict):
        return "Error: Invalid tool action format"
    try:
        return run_tool(tool_name, **tool_args)
    except Exception as e:
        return f"Error executing tool {tool_name}: {e}"

def _search_tree(
    question: str,
    command: str,
    max_depth: int,
    branching_factor: int,
    beam_width: int,
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float,
    verbose: bool = False
) -> Tuple[List[Thought], List[Thought]]:
    """Perform beam search through the thought tree.

    Returns:
        Tuple of (all_explored_thoughts, final_thoughts_at_max_depth)
    """
    all_thoughts = []
    current_level_thoughts = []  # [(thought, score), ...]

    # Start with empty initial state
    current_state = []

    for depth in range(max_depth):
        if verbose:
            logger.info(f"Exploring depth {depth + 1}/{max_depth}")

        # Generate thoughts for current level
        if depth == 0:
            # Initial thoughts
            new_thoughts = _generate_thoughts(
                question, command, [], depth, branching_factor,
                api_key, base_url, max_retries, model,
                temperature, top_p, frequency_penalty, max_tokens, timeout
            )
        else:
            # Generate thoughts for each of the top beam_width thoughts from previous level
            new_thoughts = []
            for thought, _ in current_level_thoughts[:beam_width]:
                # Build state from root to this thought
                state_path = []
                temp_thought = thought
                while temp_thought:
                    state_path.append((temp_thought.id, temp_thought.content))
                    # Find parent thought in all_thoughts
                    if temp_thought.parent_id:
                        parent_thought = next((t for t in all_thoughts if t.id == temp_thought.parent_id), None)
                        temp_thought = parent_thought
                    else:
                        temp_thought = None
                state_path.reverse()

                branch_thoughts = _generate_thoughts(
                    question, command, state_path, depth, branching_factor,
                    api_key, base_url, max_retries, model,
                    temperature, top_p, frequency_penalty, max_tokens, timeout
                )
                new_thoughts.extend(branch_thoughts)

        if not new_thoughts:
            if verbose:
                logger.warning(f"No thoughts generated at depth {depth}")
            break

        # Evaluate all new thoughts
        evaluated_thoughts = []
        for thought in new_thoughts:
            score = _evaluate_thought(
                thought, question, command, current_state,
                api_key, base_url, max_retries, model,
                temperature, top_p, frequency_penalty, max_tokens, timeout
            )
            thought.score = score
            evaluated_thoughts.append((thought, score))

            # Try to execute any tool actions
            result = _execute_thought_action(
                thought, api_key, base_url, max_retries, model,
                temperature, top_p, frequency_penalty, max_tokens, timeout
            )
            if result:
                thought.result = result

            all_thoughts.append(thought)

            if verbose:
                logger.info(f"Thought {thought.id}: {thought.content[:100]}... (score: {score:.2f})")

        # Sort by score and keep top beam_width for next iteration
        evaluated_thoughts.sort(key=lambda x: x[1], reverse=True)
        current_level_thoughts = evaluated_thoughts

        if verbose:
            logger.info(f"Top thoughts at depth {depth + 1}:")
            for thought, score in evaluated_thoughts[:beam_width]:
                logger.info(f"  {thought.id}: {thought.content[:80]}... (score: {score:.2f})")

    # Return all thoughts and final level thoughts
    final_thoughts = [thought for thought, _ in current_level_thoughts[:beam_width]]
    return all_thoughts, final_thoughts

def _synthesize_answer(
    question: str,
    command: str,
    final_thoughts: List[Thought],
    all_thoughts: List[Thought],
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float
) -> str:
    """Synthesize final answer from explored thought paths."""

    if not final_thoughts:
        return "No thoughts were generated to form an answer."

    # Build summary of top paths
    path_summaries = []
    for i, thought in enumerate(final_thoughts):
        # Reconstruct path from root to this thought
        path = []
        temp_thought = thought
        while temp_thought:
            path.append(temp_thought)
            if temp_thought.parent_id:
                parent_thought = next((t for t in all_thoughts if t.id == temp_thought.parent_id), None)
                temp_thought = parent_thought
            else:
                temp_thought = None
        path.reverse()

        path_summary = f"Path {i+1} (score: {thought.score:.2f}):\n"
        for j, t in enumerate(path):
            path_summary += f"  {j+1}. {t.content}\n"
            if t.result:
                path_summary += f"     Result: {t.result[:200]}...\n"
        path_summaries.append(path_summary)

    system_prompt, _ = prompts.get_prompt(command)

    synthesis_prompt = f"""Question: {question}

Explored reasoning paths:
{''.join(path_summaries)}

Based on these reasoning paths, provide a comprehensive final answer to the question.
Use the highest-scoring path as your primary approach, but incorporate insights from other paths where relevant.

Answer:"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": synthesis_prompt}
    ]

    try:
        final_answer = llm.openai_completion(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            model=model,
            messages=messages,
            stream=False,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            max_tokens=max_tokens,
            timeout=timeout
        )
        return final_answer
    except Exception as e:
        logger.error(f"Error synthesizing final answer: {e}")
        # Fallback to best individual thought
        best_thought = max(final_thoughts, key=lambda t: t.score)
        return f"Best reasoning path (score: {best_thought.score:.2f}): {best_thought.content}"

def tot_agent(
    question: str,
    command: str,
    max_depth: int = 3,
    branching_factor: int = 3,
    beam_width: int = 2,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    stream: bool = False,
    temperature: float = 0.7,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 4096,
    timeout: float = 30.0,
    verbose: bool = False,
    return_metadata: bool = False,
    memory_manager = None
) -> str:
    """
    Run a Tree-of-Thoughts agent to solve a task.

    Args:
        question: The user's question or task
        command: The command type (ask, explain, debug, fix, generate, draft)
        max_depth: Maximum depth of thought tree exploration
        branching_factor: Number of thoughts to generate at each step
        beam_width: Number of top thoughts to keep at each level
        api_key: OpenAI API key
        base_url: OpenAI API base URL
        max_retries: Maximum retries for API calls
        model: Model name
        stream: Whether to stream responses (not used in ToT)
        temperature: Sampling temperature (higher for generation, lower for evaluation)
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty
        max_tokens: Maximum tokens in response
        timeout: Request timeout
        verbose: Whether to print intermediate steps
        return_metadata: Whether to return metadata about the exploration

    Returns:
        Final answer string
        If return_metadata is True, returns tuple of (final_answer, metadata_dict)
    """
    if verbose:
        logger.info("=" * 60)
        logger.info("TREE-OF-THOUGHTS AGENT STARTING")
        logger.info("=" * 60)
        logger.info(f"Question: {question}")
        logger.info(f"Parameters: depth={max_depth}, branching={branching_factor}, beam={beam_width}")

    # Perform tree search
    all_thoughts, final_thoughts = _search_tree(
        question, command, max_depth, branching_factor, beam_width,
        api_key, base_url, max_retries, model,
        temperature, top_p, frequency_penalty, max_tokens, timeout,
        verbose
    )

    if verbose:
        logger.info("=" * 60)
        logger.info("SYNTHESIZING FINAL ANSWER")
        logger.info("=" * 60)

    # Synthesize final answer
    final_answer = _synthesize_answer(
        question, command, final_thoughts, all_thoughts,
        api_key, base_url, max_retries, model,
        temperature, top_p, frequency_penalty, max_tokens, timeout
    )

    # Save to memory if memory manager is available
    if memory_manager:
        try:
            memory_manager.add_memory(
                question=question,
                answer=final_answer,
                command=command,
                agent_type="tree-of-thoughts",
                metadata={
                    "max_depth": max_depth,
                    "branching_factor": branching_factor,
                    "beam_width": beam_width,
                    "thoughts_explored": len(all_thoughts),
                    "final_paths": len(final_thoughts),
                    "best_score": max((t.score for t in final_thoughts), default=0.0)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to save memory: {e}")

    if return_metadata:
        metadata = {
            "all_thoughts": [t.to_dict() for t in all_thoughts],
            "final_thoughts": [t.to_dict() for t in final_thoughts],
            "thoughts_explored": len(all_thoughts),
            "final_paths": len(final_thoughts)
        }
        return final_answer, metadata

    return final_answer

def tot_agent_simple(
    question: str,
    command: str = "ask",
    max_depth: int = 3,
    branching_factor: int = 3,
    beam_width: int = 2,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    stream: bool = False,
    temperature: float = 0.7,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 4096,
    timeout: float = 30.0
) -> str:
    """
    Simplified Tree-of-Thoughts agent that returns a single string response.

    This is a convenience wrapper around tot_agent for non-streaming use cases.
    """
    return tot_agent(
        question=question,
        command=command,
        max_depth=max_depth,
        branching_factor=branching_factor,
        beam_width=beam_width,
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
