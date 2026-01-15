#!/usr/bin/env python3
"""
Comprehensive example demonstrating all agent types and features.

This script shows how to use Plan-Build, ReAct, and LLMCompiler agents,
and demonstrates reflection capabilities.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.plan_build_agent import plan_build  # noqa: E402
from clia.agents.react_agent import react_agent_simple  # noqa: E402
from clia.agents.llm_compiler_agent import (  # noqa: E402
    llm_compiler_agent_simple
)
from clia.config import Settings  # noqa: E402


def main():
    """Comprehensive example showing all agent types."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    question = "What is the purpose of this project?"

    print("=" * 60)
    print("Comprehensive CLIA Agent Examples")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")

    # Example 1: Plan-Build Agent (Default)
    print("\n" + "=" * 60)
    print("1. Plan-Build Agent (Default)")
    print("=" * 60)
    print("Best for: Predictable, well-defined tasks")
    try:
        response = plan_build(
            question=question,
            command="ask",
            max_steps=5,
            api_key=settings.api_key,
            base_url=settings.base_url,
            max_retries=settings.max_retries,
            model=settings.model,
            stream=False,
            temperature=settings.temperature,
            top_p=settings.top_p,
            frequency_penalty=settings.frequency_penalty,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout_seconds,
            return_metadata=False
        )
        print("\nResponse:")
        print(response[:200] + "..." if len(response) > 200 else response)
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: ReAct Agent
    print("\n" + "=" * 60)
    print("2. ReAct Agent")
    print("=" * 60)
    print("Best for: Complex, exploratory tasks requiring adaptive reasoning")
    try:
        response = react_agent_simple(
            question=question,
            command="ask",
            max_iterations=5,
            api_key=settings.api_key,
            base_url=settings.base_url,
            max_retries=settings.max_retries,
            model=settings.model,
            stream=False,
            temperature=settings.temperature,
            top_p=settings.top_p,
            frequency_penalty=settings.frequency_penalty,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout_seconds
        )
        print("\nResponse:")
        print(response[:200] + "..." if len(response) > 200 else response)
    except Exception as e:
        print(f"Error: {e}")

    # Example 3: LLMCompiler Agent
    print("\n" + "=" * 60)
    print("3. LLMCompiler Agent")
    print("=" * 60)
    print("Best for: Tasks with parallelizable operations")
    try:
        response = llm_compiler_agent_simple(
            question=question,
            command="ask",
            api_key=settings.api_key,
            base_url=settings.base_url,
            max_retries=settings.max_retries,
            model=settings.model,
            stream=False,
            temperature=settings.temperature,
            top_p=settings.top_p,
            frequency_penalty=settings.frequency_penalty,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout_seconds
        )
        print("\nResponse:")
        print(response[:200] + "..." if len(response) > 200 else response)
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("""
All three agents can solve the same task, but with different approaches:

- Plan-Build: Plans all steps upfront, then executes sequentially
- ReAct: Iteratively reasons, acts, and observes until complete
- LLMCompiler: Creates a DAG and executes independent steps in parallel

Choose the agent based on your task characteristics:
- Simple, predictable tasks → Plan-Build (default)
- Complex, exploratory tasks → ReAct
- Tasks with parallelizable operations → LLMCompiler
    """)


if __name__ == "__main__":
    main()
