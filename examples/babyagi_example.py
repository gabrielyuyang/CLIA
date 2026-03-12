#!/usr/bin/env python3
"""
Example script demonstrating the BabyAGI agent usage.

This script shows how to use the BabyAGI agent programmatically.
Demonstrates the task generation and execution loop.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.babyagi_agent import babyagi_agent  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of BabyAGI agent."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    # Example question
    question = "Read README.md and summarize its main features"

    print("=" * 60)
    print("BabyAGI Agent Example")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")
    print("Note: This agent generates follow-up tasks and executes them iteratively.")

    print("\n" + "-" * 60)
    print("Example: Basic usage")
    print("-" * 60)
    try:
        response = babyagi_agent(
            question=question,
            command="ask",
            api_key=settings.api_key,
            base_url=settings.base_url,
            max_retries=settings.max_retries,
            model=settings.model,
            stream=settings.stream,
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


if __name__ == "__main__":
    main()
