#!/usr/bin/env python3
"""
Example script demonstrating the ReAct agent usage.

This script shows how to use the ReAct agent programmatically.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.react_agent import react_agent_simple
from clia.config import Settings


def main():
    """Example usage of ReAct agent."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    # Example question
    question = "Read the file README.md and tell me what it says"

    print("=" * 60)
    print("ReAct Agent Example")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")

    # Run ReAct agent
    try:
        response = react_agent_simple(
            question=question,
            command="ask",
            max_iterations=5,
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

        print("\n" + "=" * 60)
        print("Final Response:")
        print("=" * 60)
        print(response)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
