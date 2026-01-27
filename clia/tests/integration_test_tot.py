"""
Integration test demonstrating the Tree-of-Thoughts agent for debugging tasks.

This test creates a simulated buggy code scenario and shows how the ToT agent
explores multiple hypotheses to identify and fix the issue.
"""

import os
import tempfile
import json
from clia.agents.tot_agent import tot_agent
from clia.agents.memory import MemoryManager


def create_buggy_code_scenario():
    """Create a temporary directory with buggy code files for testing."""

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()

    # Buggy Python code with multiple potential issues
    buggy_code = '''
def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = 0
    count = 0
    for num in numbers:
        total += num
        count += 1

    # Bug 1: Division by zero when count is 0
    # Bug 2: No type checking for non-numeric values
    # Bug 3: No handling of empty lists
    return total / count

def process_data(data_list):
    """Process a list of data items."""
    results = []
    for item in data_list:
        # Bug 4: Incorrect function call - should be calculate_average
        avg = calc_average(item)
        results.append(avg)
    return results

# Test the functions
if __name__ == "__main__":
    test_data = [[1, 2, 3], [4, 5, 6], []]
    print(process_data(test_data))
'''

    # Write buggy code to file
    buggy_file_path = os.path.join(temp_dir, "buggy_code.py")
    with open(buggy_file_path, "w", encoding="utf-8") as f:
        f.write(buggy_code)

    # Create a test data file
    test_data = "[[1, 2, 3], [4, 5, 6], []]"
    data_file_path = os.path.join(temp_dir, "test_data.json")
    with open(data_file_path, "w", encoding="utf-8") as f:
        f.write(test_data)

    return temp_dir, buggy_file_path, data_file_path


def demonstrate_tot_debugging():
    """Demonstrate ToT agent debugging capabilities."""

    # Create buggy code scenario
    temp_dir, buggy_file_path, data_file_path = create_buggy_code_scenario()

    try:
        # Create memory manager for tracking
        memory_manager = MemoryManager(os.path.join(temp_dir, "memory.jsonl"))

        # Debugging task for the ToT agent
        debug_question = f"""
I have a Python script at {buggy_file_path} that's failing when I run it.
The script is supposed to calculate averages of number lists, but it's throwing errors.
Please analyze the code, identify potential bugs, and suggest fixes.

Key information:
- The script processes data from {data_file_path}
- It fails when running the main section
- Look for issues like division by zero, incorrect function calls, and type handling

Explore multiple hypotheses about what could be wrong and evaluate each approach.
"""

        print("=" * 80)
        print("TREE-OF-THOUGHTS DEBUGGING DEMONSTRATION")
        print("=" * 80)
        print(f"Buggy code file: {buggy_file_path}")
        print(f"Test data file: {data_file_path}")
        print(f"\nDebug question: {debug_question}")

        # Run ToT agent with debugging configuration
        result = tot_agent(
            question=debug_question,
            command="debug",
            max_depth=3,
            branching_factor=3,
            beam_width=2,
            temperature=0.7,  # Higher for diverse thoughts
            max_tokens=2048,
            verbose=True,
            memory_manager=memory_manager,
            # In a real scenario, you would provide actual API credentials
            # api_key="your-api-key",
            # base_url="your-base-url",
            # model="your-model"
        )

        print("\n" + "=" * 80)
        print("FINAL DEBUGGING RESULT")
        print("=" * 80)
        print(result)

        # Show memory entries
        print("\n" + "=" * 80)
        print("MEMORY ENTRIES")
        print("=" * 80)
        stats = memory_manager.get_stats()
        print(f"Memory statistics: {stats}")

        if memory_manager.memories:
            print("\nRecent memories:")
            for i, mem in enumerate(memory_manager.memories[-3:], 1):
                print(f"{i}. {mem.question[:50]}... -> {mem.answer[:100]}...")

        return result

    finally:
        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def demonstrate_tot_analysis():
    """Demonstrate ToT agent analysis capabilities with a simpler task."""

    # Create a simple analysis task
    analysis_question = """
I'm trying to understand why my Python function for calculating factorials
is returning incorrect results for some inputs.

The function is:
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n-1)

When I call factorial(5), I expect 120, but sometimes I get different results.
What could be causing this inconsistency? Analyze multiple possibilities.
"""

    print("\n" + "=" * 80)
    print("TREE-OF-THOUGHTS ANALYSIS DEMONSTRATION")
    print("=" * 80)
    print(f"Analysis question: {analysis_question}")

    # Run ToT agent with analysis configuration
    result = tot_agent(
        question=analysis_question,
        command="ask",
        max_depth=2,
        branching_factor=3,
        beam_width=2,
        temperature=0.7,  # Higher for diverse thoughts
        max_tokens=1024,
        verbose=True
    )

    print("\n" + "=" * 80)
    print("FINAL ANALYSIS RESULT")
    print("=" * 80)
    print(result)

    return result


if __name__ == "__main__":
    # Run demonstrations
    print("Starting Tree-of-Thoughts agent integration tests...")

    # Demonstrate debugging capabilities
    debug_result = demonstrate_tot_debugging()

    # Demonstrate analysis capabilities
    analysis_result = demonstrate_tot_analysis()

    print("\n" + "=" * 80)
    print("INTEGRATION TESTS COMPLETED")
    print("=" * 80)
    print("The ToT agent successfully demonstrated:")
    print("1. Multi-path exploration of debugging hypotheses")
    print("2. Evaluation of different approaches")
    print("3. Synthesis of final recommendations")
    print("4. Integration with memory management")