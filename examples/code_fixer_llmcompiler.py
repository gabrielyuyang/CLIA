#!/usr/bin/env python3
"""
Example script demonstrating code fixer usage with LLMCompiler agent.

This script shows how the LLMCompiler agent can use the fix_code tool
to fix multiple files in parallel.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clia
sys.path.insert(0, str(Path(__file__).parent.parent))

from clia.agents.llm_compiler_agent import llm_compiler_agent  # noqa: E402
from clia.config import Settings  # noqa: E402


def main():
    """Example usage of code fixer with LLMCompiler agent."""
    # Load settings
    try:
        settings = Settings.load_openai()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    print("=" * 60)
    print("Code Fixer with LLMCompiler Agent Example")
    print("=" * 60)

    # Create multiple buggy Python files for testing
    test_dir = Path(__file__).parent / "test_files"
    test_dir.mkdir(exist_ok=True)

    file1 = test_dir / "buggy1.py"
    buggy_code1 = """
def add_numbers(a, b)
    return a + b

result = add_numbers(5, 3)
print(result)
"""

    file2 = test_dir / "buggy2.py"
    buggy_code2 = """
def multiply(x, y):
    return x + y  # Wrong operation

result = multiply(4, 5)
print(f"Result: {result}")
"""

    file1.write_text(buggy_code1)
    file2.write_text(buggy_code2)

    print(f"\nCreated test files:")
    print(f"  {file1}")
    print(f"  {file2}")

    # Example: Ask LLMCompiler agent to fix both files in parallel
    print("\n" + "-" * 60)
    print("Asking LLMCompiler agent to fix both files in parallel")
    print("-" * 60)

    question = f"""
Fix the errors in these two files in parallel:

1. {file1} - has a syntax error (missing colon)
2. {file2} - has a logical error (wrong operation)

Use the fix_code tool for each file, then write the fixed code back.
"""

    try:
        response = llm_compiler_agent(
            question=question,
            command="fix",
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

        # Check if files were fixed
        print("\n" + "-" * 60)
        print("Fixed file contents:")
        print("-" * 60)

        if file1.exists():
            print(f"\n{file1}:")
            print(file1.read_text())

        if file2.exists():
            print(f"\n{file2}:")
            print(file2.read_text())

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if file1.exists():
            file1.unlink()
        if file2.exists():
            file2.unlink()
        if test_dir.exists():
            test_dir.rmdir()
        print(f"\nCleaned up test files")


if __name__ == "__main__":
    main()
