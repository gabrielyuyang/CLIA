# LLMCompiler Agent Implementation

This document describes the LLMCompiler agent implementation for CLIA.

> **Note**: The LLMCompiler agent is experimental and may be deprecated in future versions. The Plan-Build agent is the default and recommended agent for most use cases.

## Overview

The LLMCompiler agent compiles tasks into a Directed Acyclic Graph (DAG) of tool calls and executes them efficiently. Key features:

1. **DAG Planning**: Generates a Directed Acyclic Graph with explicit dependencies
2. **Parallel Execution**: Executes independent tool calls in parallel
3. **Dependency Management**: Respects dependencies for sequential execution when needed

This agent is best suited for tasks with parallelizable operations, such as reading multiple files or making independent API calls.

## Architecture

### Key Components

1. **`llm_compiler_agent.py`**: Main LLMCompiler agent implementation
   - `llm_compiler_agent()`: Full-featured LLMCompiler agent with verbose logging
   - `llm_compiler_agent_simple()`: Simplified wrapper returning a single string
   - `_extract_plan()`: Extracts the DAG plan from LLM response
   - `_validate_plan()`: Validates that the plan is a valid DAG (no cycles)
   - `_build_compiler_prompt()`: Constructs the system prompt with LLMCompiler instructions
   - `_execute_plan_parallel()`: Executes the plan respecting dependencies and using parallel execution
   - `_execute_step()`: Executes a single step in the plan

2. **Integration**: The agent is integrated into `main.py` via the `--agent llm-compiler` flag

## Usage

### Command Line

```bash
# Use LLMCompiler agent
clia ask "Read file1.txt and file2.txt, then compare them" --agent llm-compiler

# With verbose output to see planning and execution phases
clia ask "Read multiple files" --agent llm-compiler --verbose

# With reflection to get performance analysis
clia ask "Complex parallel task" --agent llm-compiler --with-reflection
```

### Programmatic Usage

```python
from clia.agents.llm_compiler_agent import llm_compiler_agent, llm_compiler_agent_simple
from clia.config import Settings

settings = Settings.load_openai()

# Using llm_compiler_agent (returns string or tuple if return_metadata=True)
result = llm_compiler_agent(
    question="Read file1.txt and file2.txt, then compare them",
    command="ask",
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
    return_metadata=False
)

# If return_metadata=True, result is a tuple: (final_answer, metadata_dict)
if return_metadata:
    final_answer, metadata = result
else:
    final_answer = result

# Or use llm_compiler_agent_simple for a single string response
result = llm_compiler_agent_simple(
    question="Read file1.txt and file2.txt, then compare them",
    command="ask",
    api_key=settings.api_key,
    base_url=settings.base_url,
    max_retries=settings.max_retries,
    model=settings.model,
    stream=False,
    temperature=settings.temperature,
    top_p=settings.top_p,
    frequency_penalty=settings.frequency_penalty,
    max_tokens=settings.max_tokens,
    timeout=settings.timeout_seconds
)
```

## LLMCompiler Pattern Format

The agent expects LLM responses in this format:

```json
[
    {
        "id": "read1",
        "tool": "read_file",
        "args": {"path_str": "file1.txt", "max_chars": 1000},
        "dependencies": []
    },
    {
        "id": "read2",
        "tool": "read_file",
        "args": {"path_str": "file2.txt", "max_chars": 1000},
        "dependencies": []
    },
    {
        "id": "compare",
        "tool": "echo",
        "args": {"text": "Comparing files..."},
        "dependencies": ["read1", "read2"]
    },
    {
        "id": "final",
        "action": "final",
        "answer": "Based on the file contents, provide comparison",
        "dependencies": ["compare"]
    }
]
```

### Plan Structure

- **Step ID**: Each step must have a unique `id` for dependency tracking
- **Tool Steps**: Steps with `"tool"` field specify which tool to execute
  - `tool`: Name of the tool to use
  - `args`: Dictionary of arguments for the tool
  - `dependencies`: List of step IDs that must complete before this step

- **Final Step**: Step with `"action": "final"` provides the final answer
  - `answer`: The answer template or instruction
  - `dependencies`: List of step IDs whose results should be used

## Features

1. **Parallel Execution**: Independent steps execute simultaneously, reducing total execution time
2. **Dependency Management**: Steps wait for their dependencies before executing
3. **DAG Validation**: Ensures the plan is a valid Directed Acyclic Graph (no cycles)
4. **Error Handling**: Gracefully handles tool failures and continues with available results
5. **Verbose Mode**: Shows planning, execution rounds, and step completion
6. **Metadata Support**: Returns execution metadata for reflection and analysis

## Comparison with Other Agents

| Feature | Plan-Build | ReAct | LLMCompiler |
|---------|-----------|-------|-------------|
| Planning | Upfront, all steps | Iterative, step-by-step | DAG with dependencies |
| Execution | Sequential | Iterative | Parallel where possible |
| Adaptability | Low (fixed plan) | High (reacts to observations) | Medium (fixed DAG) |
| Complexity | Simple | Moderate | Complex |
| Best For | Predictable tasks | Exploratory tasks | Parallelizable tasks |
| Max Steps/Iterations | Configurable (default: 5) | Configurable (default: 10) | Unlimited (DAG-based) |
| Parallel Execution | No | No | Yes |

## Implementation Details

### Planning Phase

The planning phase:
1. Receives the user question
2. Generates a DAG plan with explicit dependencies
3. Validates the plan is acyclic (no circular dependencies)
4. Each step has a unique ID and lists its dependencies

### Execution Phase

The execution phase uses a round-based approach:

1. **Round 1**: Execute all steps with no dependencies (or empty dependencies)
2. **Round 2**: Execute steps whose dependencies are now satisfied
3. **Continue**: Repeat until all steps are completed

Steps within the same round execute in parallel using `ThreadPoolExecutor`.

### Plan Validation

The `_validate_plan()` function:
- Checks that all referenced dependencies exist in the plan
- Uses DFS (Depth-First Search) to detect cycles
- Returns `False` if cycles or missing dependencies are found

### Dependency Resolution

The execution engine:
- Tracks completed steps
- Identifies ready steps (all dependencies satisfied)
- Executes ready steps in parallel
- Continues until all steps are completed

### Error Handling

- **Invalid plans**: Returns error if plan contains cycles or missing dependencies
- **Tool failures**: Errors are captured and stored in results
- **Missing dependencies**: Steps with unsatisfied dependencies are skipped with error messages
- **Unknown tools**: Returns error message listing available tools

### Metadata

When `return_metadata=True`, the agent returns:
- `plan`: The original DAG plan generated
- `execution_results`: Dictionary mapping step IDs to their results
- `plan_valid`: Whether the plan passed validation

## Example Execution Flow

```
User: "Read file1.txt and file2.txt, then compare them"

Planning Phase:
  LLM generates DAG plan:
  [
    {
      "id": "read1",
      "tool": "read_file",
      "args": {"path_str": "file1.txt"},
      "dependencies": []
    },
    {
      "id": "read2",
      "tool": "read_file",
      "args": {"path_str": "file2.txt"},
      "dependencies": []
    },
    {
      "id": "final",
      "action": "final",
      "answer": "Compare the contents",
      "dependencies": ["read1", "read2"]
    }
  ]

Execution Phase:
  Round 1 (parallel):
    - Execute read1: "Contents of file1..."
    - Execute read2: "Contents of file2..."

  Round 2:
    - Execute final: "Comparison: ..."
```

## Performance Benefits

The parallel execution provides significant performance improvements:

- **Sequential**: If reading 3 files takes 1 second each = 3 seconds total
- **Parallel**: Reading 3 files in parallel = ~1 second total (limited by slowest operation)

This is especially beneficial for:
- Reading multiple files
- Making multiple HTTP requests
- Any I/O-bound operations that can run independently

## Future Enhancements

- [ ] Dynamic dependency resolution based on execution results
- [ ] Better error recovery (retry failed steps)
- [ ] Plan optimization (identifying more parallel opportunities)
- [ ] Resource limits (max concurrent executions)
- [ ] Step result caching
- [ ] Conditional execution (if-then-else based on step results)
- [ ] Progress tracking and reporting
- [ ] Support for nested plans (sub-plans)
