#!/usr/bin/env python3
"""
Example script demonstrating code fixer usage with ReAct agent.

This script shows how the ReAct agent can use the fix_code tool
to automatically fix code errors.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.react_agent import react_agent_simple  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of code fixer with ReAct agent."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    print("=" * 60)
    print("Code Fixer with ReAct Agent Example")
    print("=" * 60)

    # Create a buggy Python file for testing
    test_file = Path(__file__).parent / "test_buggy.py"
    buggy_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers
        total += num
    return total / len(numbers)

# Test the function
result = calculate_average([10, 20, 30, 40, 50])
print(f"Average: {result}")
"""

    test_file.write_text(buggy_code)
    print(f"\nCreated test file: {test_file}")
    print(f"Content:\n{buggy_code}")

    # Example: Ask ReAct agent to fix the syntax error
    print("\n" + "-" * 60)
    print("Asking ReAct agent to fix the syntax error")
    print("-" * 60)

    question = f"""
Fix the syntax error in the file {test_file}.
The error is: SyntaxError: invalid syntax at line 4

Use the fix_code tool to analyze and fix the error, then write the fixed code back to the file.
"""

    try:
        response = react_agent_simple(
            question=question,
            command="fix",
            max_iterations=10,
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

        print("\nAgent Response:")
        print(response)

        # Check if file was fixed
        if test_file.exists():
            fixed_code = test_file.read_text()
            print(f"\nFixed file content:\n{fixed_code}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
            print(f"\nCleaned up test file: {test_file}")


if __name__ == "__main__":
    main()
