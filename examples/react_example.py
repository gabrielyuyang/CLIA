#!/usr/bin/env python3
"""
Example script demonstrating the ReAct agent usage.

This script shows how to use the ReAct agent programmatically.
Demonstrates both react_agent (returns List[str]) and
react_agent_simple (returns str).
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.react_agent import (  # noqa: E402
    react_agent, react_agent_simple
)
from clia.agents import MemoryManager  # noqa: E402
from clia.config import Settings  # noqa: E402


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

    # Example 1: Using react_agent_simple (returns single string)
    print("\n" + "-" * 60)
    print("Example 1: Using react_agent_simple")
    print("-" * 60)
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

        print("\nFinal Response:")
        print(response)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Example 2: Using react_agent (returns List[str], supports metadata)
    print("\n" + "-" * 60)
    print("Example 2: Using react_agent with metadata")
    print("-" * 60)
    try:
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
            verbose=True,
            return_metadata=True
        )

        # react_agent returns tuple when return_metadata=True
        response_list, metadata = result
        response = "".join(response_list)

        print("\nFinal Response:")
        print(response)

        print("\nExecution Metadata:")
        print(f"  Iterations used: {metadata.get('iterations_used', 'N/A')}")
        print(f"  Tools used: {metadata.get('tools_used', [])}")
        turns = metadata.get('conversation_turns', 'N/A')
        print(f"  Conversation turns: {turns}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Example 3: Using react_agent with memory management
    print("\n" + "-" * 60)
    print("Example 3: Using react_agent with memory management")
    print("-" * 60)
    print("Memory management enables short-term context for follow-up questions.")
    try:
        # Initialize memory manager
        memory_path = Path(__file__).parent.parent / "clia" / "memories" / "memory.jsonl"
        memory_manager = MemoryManager(
            memory_path=memory_path,
            max_memories=100,
            enable_summarization=True,
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=settings.model,
            max_retries=settings.max_retries,
            timeout=settings.timeout_seconds
        )

        # First question
        first_question = "What is Python?"
        print(f"\nFirst Question: {first_question}")
        result1 = react_agent(
            question=first_question,
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
            memory_manager=memory_manager
        )
        response1 = "".join(result1) if isinstance(result1, list) else result1
        print(f"\nResponse: {response1[:200]}...")

        # Follow-up question that uses previous context
        follow_up = "Give me an example of how to use it"
        print(f"\nFollow-up Question: {follow_up}")
        result2 = react_agent(
            question=follow_up,
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
            memory_manager=memory_manager
        )
        response2 = "".join(result2) if isinstance(result2, list) else result2
        print(f"\nResponse: {response2[:200]}...")

        # Show memory stats
        stats = memory_manager.get_stats()
        print(f"\nMemory Stats:")
        print(f"  Total memories: {stats.get('total_memories', 0)}")
        print(f"  By agent type: {stats.get('by_agent_type', {})}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
