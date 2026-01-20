#!/usr/bin/env python3
"""
Example script demonstrating standalone code fixer usage.

This script shows how to use the code fixer directly without agents.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.code_fixer import fix_code, CodeFixerConfig  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of standalone code fixer."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    print("=" * 60)
    print("Code Fixer Standalone Example")
    print("=" * 60)

    # Example 1: Fix syntax error
    print("\n" + "-" * 60)
    print("Example 1: Fix Python syntax error")
    print("-" * 60)

    buggy_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers
        total += num
    return total

result = calculate_sum([1, 2, 3, 4, 5])
print(result)
"""

    error_message = "SyntaxError: invalid syntax at line 4"

    try:
        result = fix_code(
            error_input=error_message,
            code_context=buggy_code,
            config=CodeFixerConfig(
                auto_run_tests=False,
                max_iterations=1
            ),
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=settings.model,
            temperature=0.1,
            verbose=True
        )

        print(f"\nSuccess: {result.success}")
        print(f"Iterations: {result.iterations_used}")
        print(f"\nError Analysis:\n{result.error_analysis}")
        print(f"\nFix Explanation:\n{result.fix_explanation}")
        print(f"\nFixed Code:\n{result.fixed_code}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    # Example 2: Fix with test execution
    print("\n" + "-" * 60)
    print("Example 2: Fix with test execution")
    print("-" * 60)

    buggy_code_with_logic_error = """
def divide(a, b):
    return a + b  # Wrong operation!

def test_divide():
    assert divide(10, 2) == 5
    assert divide(20, 4) == 5
"""

    test_error = """
FAILED test_divide - AssertionError: assert 12 == 5
"""

    try:
        result = fix_code(
            error_input=test_error,
            code_context=buggy_code_with_logic_error,
            config=CodeFixerConfig(
                auto_run_tests=False,
                max_iterations=1
            ),
            api_key=settings.api_key,
            base_url=settings.base_url,
            model=settings.model,
            temperature=0.1,
            verbose=True
        )

        print(f"\nSuccess: {result.success}")
        print(f"\nFixed Code:\n{result.fixed_code}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
