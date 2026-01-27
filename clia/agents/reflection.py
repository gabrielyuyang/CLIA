"""
Reflection Module for CLIA Agents

This module provides reflection capabilities for agents to:
1. Self-critique their performance
2. Analyze what went well and what didn't
3. Identify areas for improvement
4. Learn from mistakes
"""

from typing import Dict, List, Optional, Any
import json
import logging
from .llm import openai_completion

logger = logging.getLogger(__name__)


class AgentReflection:
    """Represents a reflection on agent performance."""

    def __init__(
        self,
        question: str,
        agent_type: str,
        execution_summary: Dict[str, Any],
        final_answer: str,
        success: bool = True,
        errors: Optional[List[str]] = None,
        improvements: Optional[List[str]] = None,
        strengths: Optional[List[str]] = None
    ):
        self.question = question
        self.agent_type = agent_type
        self.execution_summary = execution_summary
        self.final_answer = final_answer
        self.success = success
        self.errors = errors or []
        self.improvements = improvements or []
        self.strengths = strengths or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert reflection to dictionary."""
        return {
            "question": self.question,
            "agent_type": self.agent_type,
            "execution_summary": self.execution_summary,
            "final_answer": self.final_answer,
            "success": self.success,
            "errors": self.errors,
            "improvements": self.improvements,
            "strengths": self.strengths
        }

    def __str__(self) -> str:
        """String representation of reflection."""
        lines = [
            f"Reflection for {self.agent_type} Agent",
            "=" * 60,
            f"Question: {self.question}",
            f"Success: {self.success}",
            ""
        ]

        if self.strengths:
            lines.append("Strengths:")
            for strength in self.strengths:
                lines.append(f"  ✓ {strength}")
            lines.append("")

        if self.errors:
            lines.append("Errors/Issues:")
            for error in self.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")

        if self.improvements:
            lines.append("Improvements:")
            for improvement in self.improvements:
                lines.append(f"  → {improvement}")
            lines.append("")

        return "\n".join(lines)


def reflect_on_execution(
    question: str,
    agent_type: str,
    execution_summary: Dict[str, Any],
    final_answer: str,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    temperature: float = 0.3,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 2048,
    timeout: float = 30.0,
    verbose: bool = False
) -> AgentReflection:
    """
    Generate a reflection on agent execution using LLM.

    Args:
        question: The original user question
        agent_type: Type of agent used (react, llm-compiler, plan-build)
        execution_summary: Summary of execution including:
            - iterations/steps taken
            - tools used
            - errors encountered
            - conversation history (optional)
        final_answer: The final answer provided by the agent
        api_key: OpenAI API key
        base_url: OpenAI API base URL
        max_retries: Maximum retries for API calls
        model: Model name
        temperature: Sampling temperature (lower for more focused reflection)
        top_p: Top-p sampling parameter
        frequency_penalty: Frequency penalty
        max_tokens: Maximum tokens in response
        timeout: Request timeout
        verbose: Whether to print reflection details

    Returns:
        AgentReflection object with analysis
    """
    # Build reflection prompt
    reflection_prompt = f"""You are an expert AI agent evaluator. Analyze the following agent execution and provide constructive feedback.

## Task:
{question}

## Agent Type:
{agent_type}

## Execution Summary:
{json.dumps(execution_summary, indent=2, ensure_ascii=False)}

## Final Answer:
{final_answer}

## Your Task:
Analyze this execution and provide:
1. **Strengths**: What did the agent do well? (2-4 points)
2. **Errors/Issues**: What went wrong or could be improved? (be specific)
3. **Improvements**: Concrete suggestions for better performance next time

Format your response as JSON:
{{
    "success": true/false,
    "strengths": ["strength1", "strength2", ...],
    "errors": ["error1", "error2", ...],
    "improvements": ["improvement1", "improvement2", ...]
}}

Be honest and constructive. Focus on actionable feedback."""

    messages = [
        {"role": "system", "content": "You are an expert AI agent evaluator. Provide honest, constructive feedback in JSON format."},
        {"role": "user", "content": reflection_prompt}
    ]

    try:
        if verbose:
            logger.info("Generating reflection...")

        response = openai_completion(
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

        # Extract JSON from response
        reflection_data = _extract_json(response)

        if not reflection_data:
            # Fallback: create basic reflection
            logger.warning("Could not parse reflection JSON, creating basic reflection")
            reflection_data = {
                "success": True,
                "strengths": ["Agent completed the task"],
                "errors": [],
                "improvements": []
            }

        reflection = AgentReflection(
            question=question,
            agent_type=agent_type,
            execution_summary=execution_summary,
            final_answer=final_answer,
            success=reflection_data.get("success", True),
            errors=reflection_data.get("errors", []),
            improvements=reflection_data.get("improvements", []),
            strengths=reflection_data.get("strengths", [])
        )

        if verbose:
            logger.info("\n" + str(reflection))

        return reflection

    except Exception as e:
        logger.error(f"Failed to generate reflection: {e}")
        # Return a basic reflection on error
        return AgentReflection(
            question=question,
            agent_type=agent_type,
            execution_summary=execution_summary,
            final_answer=final_answer,
            success=False,
            errors=[f"Reflection generation failed: {str(e)}"],
            improvements=["Retry reflection generation", "Check API connectivity"]
        )


def _extract_json(text: str) -> Optional[Dict]:
    """Extract JSON from text response."""
    import re

    # Try to find JSON in code blocks
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try parsing entire response as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    return None


def reflect_react_agent(
    question: str,
    conversation_history: List[Dict],
    final_answer: str,
    iterations_used: int,
    max_iterations: int,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    temperature: float = 0.3,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 2048,
    timeout: float = 30.0,
    verbose: bool = False
) -> AgentReflection:
    """
    Generate reflection specifically for ReAct agent execution.

    Args:
        question: The original user question
        conversation_history: List of conversation turns with components
        final_answer: The final answer provided
        iterations_used: Number of iterations actually used
        max_iterations: Maximum iterations allowed
        ... (other LLM parameters)

    Returns:
        AgentReflection object
    """
    # Count tools used
    tools_used = []
    errors_encountered = []

    for turn in conversation_history:
        if "action" in turn:
            tools_used.append(turn.get("action"))
        if "observation" in turn and "Error" in str(turn.get("observation", "")):
            errors_encountered.append(str(turn.get("observation")))

    execution_summary = {
        "iterations_used": iterations_used,
        "max_iterations": max_iterations,
        "tools_used": list(set(tools_used)),
        "errors_encountered": errors_encountered,
        "conversation_turns": len(conversation_history),
        "reached_max_iterations": iterations_used >= max_iterations
    }

    return reflect_on_execution(
        question=question,
        agent_type="react",
        execution_summary=execution_summary,
        final_answer=final_answer,
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout,
        verbose=verbose
    )


def reflect_llm_compiler_agent(
    question: str,
    plan: List[Dict],
    execution_results: Dict[str, str],
    final_answer: str,
    plan_valid: bool = True,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    temperature: float = 0.3,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 2048,
    timeout: float = 30.0,
    verbose: bool = False
) -> AgentReflection:
    """
    Generate reflection specifically for LLMCompiler agent execution.

    Args:
        question: The original user question
        plan: The DAG plan generated
        execution_results: Results from executing each step
        final_answer: The final answer provided
        plan_valid: Whether the plan was valid
        ... (other LLM parameters)

    Returns:
        AgentReflection object
    """
    # Analyze plan
    tools_used = []
    errors_encountered = []
    parallel_steps = 0

    for step in plan:
        if "tool" in step:
            tools_used.append(step["tool"])
        if step.get("id") in execution_results:
            result = execution_results[step["id"]]
            if "Error" in result:
                errors_encountered.append(result)

    # Count steps that could run in parallel (no dependencies)
    for step in plan:
        deps = step.get("dependencies", [])
        if not deps:
            parallel_steps += 1

    execution_summary = {
        "plan_valid": plan_valid,
        "total_steps": len(plan),
        "steps_executed": len(execution_results),
        "tools_used": list(set(tools_used)),
        "errors_encountered": errors_encountered,
        "parallel_opportunities": parallel_steps,
        "dependency_depth": _calculate_max_depth(plan)
    }

    return reflect_on_execution(
        question=question,
        agent_type="llm-compiler",
        execution_summary=execution_summary,
        final_answer=final_answer,
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout,
        verbose=verbose
    )


def reflect_plan_build_agent(
    question: str,
    plan: List[Dict],
    execution_results: List[Dict],
    final_answer: str,
    steps_executed: int,
    max_steps: int,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    temperature: float = 0.3,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 2048,
    timeout: float = 30.0,
    verbose: bool = False
) -> AgentReflection:
    """
    Generate reflection specifically for Plan-Build agent execution.

    Args:
        question: The original user question
        plan: The plan generated
        execution_results: Results from executing each step
        final_answer: The final answer provided
        steps_executed: Number of steps actually executed
        max_steps: Maximum steps allowed
        ... (other LLM parameters)

    Returns:
        AgentReflection object
    """
    # Analyze execution
    tools_used = []
    errors_encountered = []

    for result in execution_results:
        if isinstance(result, dict):
            if "tool" in result:
                tools_used.append(result["tool"])
            if "result" in result and "失败" in str(result.get("result", "")) or "Error" in str(result.get("result", "")):
                errors_encountered.append(str(result.get("result")))

    execution_summary = {
        "plan_length": len(plan),
        "steps_executed": steps_executed,
        "max_steps": max_steps,
        "tools_used": list(set(tools_used)),
        "errors_encountered": errors_encountered,
        "reached_max_steps": steps_executed >= max_steps
    }

    return reflect_on_execution(
        question=question,
        agent_type="plan-build",
        execution_summary=execution_summary,
        final_answer=final_answer,
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout,
        verbose=verbose
    )


def reflect_rewoo_agent(
    question: str,
    plan: List[Dict],
    execution_results: Dict[str, str],
    final_answer: str,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    temperature: float = 0.3,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 2048,
    timeout: float = 30.0,
    verbose: bool = False
) -> AgentReflection:
    """
    Generate reflection specifically for ReWOO agent execution.

    Args:
        question: The original user question
        plan: The plan generated with variable placeholders
        execution_results: Results from executing each step
        final_answer: The final answer provided
        ... (other LLM parameters)

    Returns:
        AgentReflection object
    """
    tools_used = []
    errors_encountered = []

    for step in plan:
        if "tool" in step:
            tools_used.append(step["tool"])
        if step.get("id") in execution_results:
            result = execution_results[step["id"]]
            if "Error" in result:
                errors_encountered.append(result)

    execution_summary = {
        "plan_length": len(plan),
        "tools_executed": len(execution_results),
        "tools_used": list(set(tools_used)),
        "errors_encountered": errors_encountered,
        "parallel_execution": True
    }

    return reflect_on_execution(
        question=question,
        agent_type="rewoo",
        execution_summary=execution_summary,
        final_answer=final_answer,
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout,
        verbose=verbose
    )

def reflect_tot_agent(
    question: str,
    all_thoughts: List[Dict],
    final_thoughts: List[Dict],
    final_answer: str,
    thoughts_explored: int,
    final_paths: int,
    max_depth: int,
    branching_factor: int,
    beam_width: int,
    best_score: float,
    api_key: str = None,
    base_url: str = None,
    max_retries: int = 5,
    model: str = None,
    temperature: float = 0.3,
    top_p: float = 0.85,
    frequency_penalty: float = 0.0,
    max_tokens: int = 2048,
    timeout: float = 30.0,
    verbose: bool = False
) -> AgentReflection:
    """
    Generate reflection specifically for Tree-of-Thoughts agent execution.

    Args:
        question: The original user question
        all_thoughts: All thoughts explored during tree search
        final_thoughts: Thoughts at maximum depth
        final_answer: The final answer provided
        thoughts_explored: Total number of thoughts explored
        final_paths: Number of paths at final depth
        max_depth: Maximum depth explored
        branching_factor: Branching factor used
        beam_width: Beam width used
        best_score: Highest thought score
        ... (other LLM parameters)

    Returns:
        AgentReflection object
    """
    # Analyze execution
    tools_suggested = []
    tools_executed = 0

    for thought_dict in all_thoughts:
        # Reconstruct Thought object from dict
        if "action" in thought_dict and thought_dict["action"]:
            tools_suggested.append(thought_dict["action"])
        if "result" in thought_dict and thought_dict["result"]:
            tools_executed += 1

    execution_summary = {
        "max_depth": max_depth,
        "branching_factor": branching_factor,
        "beam_width": beam_width,
        "thoughts_explored": thoughts_explored,
        "final_paths": final_paths,
        "tools_suggested": list(set(tools_suggested)),
        "tools_executed": tools_executed,
        "best_score": best_score,
        "exploration_efficiency": thoughts_explored / (max_depth * branching_factor) if max_depth * branching_factor > 0 else 0
    }

    return reflect_on_execution(
        question=question,
        agent_type="tree-of-thoughts",
        execution_summary=execution_summary,
        final_answer=final_answer,
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout,
        verbose=verbose
    )
