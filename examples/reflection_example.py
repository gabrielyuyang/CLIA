#!/usr/bin/env python3
"""
Example script demonstrating the Reflection system usage.

This script shows how to use reflection to get self-critique from agents.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.react_agent import react_agent  # noqa: E402
from clia.agents.reflection import reflect_react_agent  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of Reflection system with ReAct agent."""
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
    print("Reflection System Example")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")

    try:
        # Step 1: Run the agent with metadata
        print("\n" + "-" * 60)
        print("Step 1: Running ReAct agent")
        print("-" * 60)

        result = react_agent(
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
            timeout=settings.timeout_seconds,
            verbose=False,
            return_metadata=True
        )

        # Extract response and metadata
        response_list, metadata = result
        final_answer = "".join(response_list)

        print("\nAgent Response:")
        print(final_answer)

        # Step 2: Generate reflection
        print("\n" + "-" * 60)
        print("Step 2: Generating reflection")
        print("-" * 60)

        reflection = reflect_react_agent(
            question=question,
            conversation_history=metadata.get("conversation_history", []),
            final_answer=final_answer,
            iterations_used=metadata.get("iterations_used", 0),
            max_iterations=metadata.get("max_iterations", 5),
            api_key=settings.api_key,
            base_url=settings.base_url,
            max_retries=settings.max_retries,
            model=settings.model,
            temperature=0.3,  # Slightly higher for reflection
            top_p=settings.top_p,
            frequency_penalty=settings.frequency_penalty,
            max_tokens=2048,
            timeout=settings.timeout_seconds,
            verbose=False
        )

        print("\n" + "=" * 60)
        print("REFLECTION")
        print("=" * 60)
        print(reflection)
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
