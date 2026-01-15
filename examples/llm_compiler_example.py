#!/usr/bin/env python3
"""
Example script demonstrating the LLMCompiler agent usage.

This script shows how to use the LLMCompiler agent programmatically.
Demonstrates parallel execution capabilities.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.llm_compiler_agent import (  # noqa: E402
    llm_compiler_agent, llm_compiler_agent_simple
)
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of LLMCompiler agent."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    # Example question that benefits from parallel execution
    question = "Read README.md and setup.py, then compare their purposes"

    print("=" * 60)
    print("LLMCompiler Agent Example")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")
    print("Note: This agent can execute independent steps in parallel.")

    # Example 1: Using llm_compiler_agent_simple (returns single string)
    print("\n" + "-" * 60)
    print("Example 1: Using llm_compiler_agent_simple")
    print("-" * 60)
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

        print("\nFinal Response:")
        print(response)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Example 2: Using llm_compiler_agent with metadata
    print("\n" + "-" * 60)
    print("Example 2: Using llm_compiler_agent with metadata")
    print("-" * 60)
    try:
        result = llm_compiler_agent(
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
            timeout=settings.timeout_seconds,
            verbose=True,
            return_metadata=True
        )

        # llm_compiler_agent returns tuple when return_metadata=True
        final_answer, metadata = result

        print("\nFinal Response:")
        print(final_answer)

        print("\nExecution Metadata:")
        print(f"  Plan valid: {metadata.get('plan_valid', 'N/A')}")
        print(f"  Total steps: {len(metadata.get('plan', []))}")
        exec_results = metadata.get('execution_results', {})
        print(f"  Steps executed: {len(exec_results)}")
        if metadata.get('plan'):
            plan = metadata['plan']
            parallel_ops = sum(
                1 for step in plan if not step.get('dependencies')
            )
            print(f"  Parallel opportunities: {parallel_ops}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
