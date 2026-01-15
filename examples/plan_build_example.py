#!/usr/bin/env python3
"""
Example script demonstrating the Plan-Build agent usage.

This script shows how to use the Plan-Build agent programmatically.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.plan_build_agent import plan_build  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of Plan-Build agent."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    # Example question
    question = "Read the file README.md and summarize its main features"

    print("=" * 60)
    print("Plan-Build Agent Example")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")

    # Example 1: Basic usage without metadata
    print("\n" + "-" * 60)
    print("Example 1: Basic usage")
    print("-" * 60)
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

        print("\nFinal Response:")
        print(response)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Example 2: With metadata for reflection
    print("\n" + "-" * 60)
    print("Example 2: With metadata")
    print("-" * 60)
    try:
        result = plan_build(
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
            return_metadata=True
        )

        # plan_build returns tuple when return_metadata=True
        final_answer, metadata = result

        print("\nFinal Response:")
        print(final_answer)

        print("\nExecution Metadata:")
        print(f"  Steps executed: {metadata.get('steps_executed', 'N/A')}")
        print(f"  Max steps: {metadata.get('max_steps', 'N/A')}")
        print(f"  Plan length: {len(metadata.get('plan', []))}")
        print(f"  Tools used: {[step.get('tool') for step in metadata.get('plan', []) if step.get('action') == 'tool']}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
