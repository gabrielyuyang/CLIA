#!/usr/bin/env python3
"""
Example script demonstrating the Tree-of-Thoughts (ToT) agent usage.

This script shows how to use the ToT agent programmatically.
Demonstrates multi-path exploration and beam search for complex reasoning.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.tot_agent import tot_agent  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of ToT agent."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    # Example question that benefits from complex reasoning
    question = "Analyze the potential impacts of using different agent architectures for code generation"

    print("=" * 60)
    print("Tree-of-Thoughts Agent Example")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")
    print("Note: This agent explores multiple reasoning paths and selects the best one.")

    # Example 1: Basic usage
    print("\n" + "-" * 60)
    print("Example 1: Basic usage")
    print("-" * 60)
    try:
        response = tot_agent(
            question=question,
            command="ask",
            max_depth=3,
            branching_factor=2,
            beam_width=1,
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

    # Example 2: Using tot_agent with metadata
    print("\n" + "-" * 60)
    print("Example 2: Using tot_agent with metadata")
    print("-" * 60)
    try:
        result = tot_agent(
            question=question,
            command="ask",
            max_depth=2,
            branching_factor=2,
            beam_width=1,
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

        # tot_agent returns tuple when return_metadata=True
        final_answer, metadata = result

        print("\nFinal Response:")
        print(final_answer)

        print("\nExecution Metadata:")
        print(f"  Thoughts explored: {metadata.get('thoughts_explored')}")
        print(f"  Final paths: {metadata.get('final_paths')}")
        print(f"  Best score: {metadata.get('best_score')}")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
