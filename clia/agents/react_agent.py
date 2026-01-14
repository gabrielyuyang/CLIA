"""
ReAct Agent Implementation

ReAct (Reasoning + Acting) is an iterative agent pattern where the agent:
1. Reasons about what to do next
2. Acts by executing a tool
3. Observes the result
4. Repeats until the task is complete
"""

from typing import Dict, List
import json
import re
import logging
from .tool_router import run_tool, tools_specs, TOOLS
from clia.agents import llm, prompts

logger = logging.getLogger(__name__)

# Regex patterns to extract ReAct components
THOUGHT_PATTERN = re.compile(
    r"Thought:\s*(.+?)(?=Action:|$)", re.DOTALL)
ACTION_PATTERN = re.compile(r"Action:\s*(\w+)", re.IGNORECASE)
ACTION_INPUT_PATTERN = re.compile(
    r"Action Input:\s*(.+?)(?=Observation:|$)", re.DOTALL)
FINAL_ANSWER_PATTERN = re.compile(
    r"Final Answer:\s*(.+?)$", re.DOTALL)


def _extract_react_components(response: str) -> Dict:
    """
    Extract Thought, Action, Action Input, and Final Answer from LLM response.

    Returns:
        Dict with keys: thought, action, action_input, final_answer
    """
    thought_match = THOUGHT_PATTERN.search(response)
    action_match = ACTION_PATTERN.search(response)
    action_input_match = ACTION_INPUT_PATTERN.search(response)
    final_answer_match = FINAL_ANSWER_PATTERN.search(response)

    result = {
        "thought": (thought_match.group(1).strip()
                    if thought_match else None),
        "action": (action_match.group(1).strip()
                   if action_match else None),
        "action_input": (action_input_match.group(1).strip()
                         if action_input_match else None),
        "final_answer": (final_answer_match.group(1).strip()
                          if final_answer_match else None),
    }

    return result


def _build_react_prompt(command: str) -> str:
    """Build the ReAct system prompt for the agent."""
    system_prompt, _ = prompts.get_prompt(command)

    react_system_prompt = f"""You are a helpful assistant that uses the ReAct (Reasoning + Acting) pattern to solve tasks.

{system_prompt}

## Available Tools:
{tools_specs()}

## ReAct Pattern:
You must follow this format exactly:

Thought: [Your reasoning about what to do next]
Action: [tool_name]
Action Input: [JSON string with tool arguments]

Then you will receive:
Observation: [result of the tool execution]

You can then continue with another Thought-Action-Action Input cycle, or provide:
Final Answer: [your final answer to the user's question]

## Rules:
1. Always start with a Thought explaining your reasoning
2. Use only the tools listed above - do not make up tool names
3. Action Input must be a valid JSON string
4. If you have enough information to answer, provide Final Answer instead of another Action
5. Be concise but thorough in your reasoning
6. If a tool fails, reason about what went wrong and try a different approach

Let's begin!"""

    return react_system_prompt


def react_agent(
    question: str,
    command: str,
    max_iterations: int = 10,
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
    return_metadata: bool = False
) -> List[str]:
    """
    Run a ReAct agent to solve a task.

    Args:
        question: The user's question or task
        command: The command type (ask, explain, debug, fix, generate, draft)
        max_iterations: Maximum number of reasoning-action-observation cycles
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
        List of response strings (for streaming compatibility)
        If return_metadata is True, returns tuple of (response_list, metadata_dict)
    """
    system_prompt = _build_react_prompt(command)

    # Initialize conversation history
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    conversation_history = []
    full_response = []

    for iteration in range(max_iterations):
        if verbose:
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteration {iteration + 1}/{max_iterations}")
            logger.info(f"{'='*60}\n")

        # Get LLM response
        try:
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
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return [f"Error: Failed to get response from LLM: {e}"]

        if verbose:
            print(f"\n[Agent Response]\n{response}\n")

        # Extract ReAct components
        components = _extract_react_components(response)

        # Add agent's response to conversation
        conversation_history.append({
            "iteration": iteration + 1,
            "response": response,
            "components": components
        })

        # Check for final answer
        if components["final_answer"]:
            if verbose:
                logger.info("Final answer received!")
            final_answer = components["final_answer"]
            full_response.append(final_answer)
            if not stream:
                print(final_answer)
            break

        # Check if we have an action to execute
        if not components["action"]:
            # No action specified - might be a direct answer or malformed response
            if verbose:
                logger.warning("No action found in response, treating as final answer")
            # Try to extract any meaningful content
            if components["thought"]:
                full_response.append(components["thought"])
                if not stream:
                    print(components["thought"])
            else:
                full_response.append(response)
                if not stream:
                    print(response)
            break

        # Execute the action
        action = components["action"]
        action_input_str = components["action_input"] or "{}"

        if verbose:
            logger.info(f"Action: {action}")
            logger.info(f"Action Input: {action_input_str}")

        # Parse action input (should be JSON)
        try:
            action_input = json.loads(action_input_str)
        except json.JSONDecodeError:
            # Try to extract JSON from the string if it's not pure JSON
            json_match = re.search(r'\{[^}]+\}', action_input_str)
            if json_match:
                try:
                    action_input = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    action_input = {"error": f"Could not parse action input: {action_input_str}"}
            else:
                action_input = {"error": f"Could not parse action input: {action_input_str}"}

        # Execute tool
        try:
            if action not in TOOLS:
                observation = f"Error: Unknown tool '{action}'. Available tools: {list(TOOLS.keys())}"
            else:
                observation = run_tool(action, **action_input)
        except Exception as e:
            observation = f"Error executing {action}: {str(e)}"
            logger.error(f"Tool execution error: {e}")

        if verbose:
            logger.info(f"Observation: {observation}")

        # Add to conversation history
        messages.append({"role": "assistant", "content": response})
        messages.append({
            "role": "user",
            "content": f"Observation: {observation}"
        })

        conversation_history.append({
            "action": action,
            "action_input": action_input,
            "observation": observation
        })

        # Check if we've exceeded max iterations
        if iteration == max_iterations - 1:
            logger.warning(f"Reached maximum iterations ({max_iterations})")
            # Try to extract a final answer from the last response
            if components["thought"]:
                full_response.append(f"{components['thought']}\n\n[Note: Reached maximum iterations]")
                if not stream:
                    print(f"{components['thought']}\n\n[Note: Reached maximum iterations]")
            else:
                full_response.append("I've reached the maximum number of iterations. Please refine your question or try again.")
                if not stream:
                    print("I've reached the maximum number of iterations. Please refine your question or try again.")

    response = full_response if full_response else ["No response generated"]

    if return_metadata:
        final_answer_str = "".join(response) if isinstance(response, list) else str(response)
        metadata = {
            "conversation_history": conversation_history,
            "iterations_used": iteration + 1,
            "max_iterations": max_iterations,
            "final_answer": final_answer_str
        }
        return response, metadata

    return response


def react_agent_simple(
    question: str,
    command: str = "ask",
    max_iterations: int = 10,
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
    Simplified ReAct agent that returns a single string response.

    This is a convenience wrapper around react_agent for non-streaming use cases.
    """
    responses = react_agent(
        question=question,
        command=command,
        max_iterations=max_iterations,
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
    return "\n".join(responses)
