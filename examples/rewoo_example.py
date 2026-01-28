#!/usr/bin/env python3
"""
Example script demonstrating the ReWOO agent usage.

This script shows how to use the ReWOO agent programmatically.
Demonstrates parallel execution capabilities using the ReWOO pattern.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.rewoo_agent import rewoo_agent  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of ReWOO agent."""
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
    print("ReWOO Agent Example")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")
    print("Note: This agent executes independent tools in parallel using placeholders.")

    # Example 1: Basic usage
    print("\n" + "-" * 60)
    print("Example 1: Basic usage")
    print("-" * 60)
    try:
        response = rewoo_agent(
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
            verbose=True
        )

        print("\nFinal Response:")
        print(response)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Example 2: Using rewoo_agent with metadata
    print("\n" + "-" * 60)
    print("Example 2: Using rewoo_agent with metadata")
    print("-" * 60)
    try:
        result = rewoo_agent(
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

        # rewoo_agent returns tuple when return_metadata=True
        final_answer, metadata = result

        print("\nFinal Response:")
        print(final_answer)

        print("\nExecution Metadata:")
        print(f"  Plan: {metadata.get('plan')}")
        print(f"  Tools executed: {metadata.get('tools_executed')}")
        print(f"  Execution results: {list(metadata.get('execution_results', {}).keys())}")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
