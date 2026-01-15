# Plan-Build Agent Implementation

This document describes the Plan-Build agent implementation for CLIA.

## Overview

The Plan-Build agent follows a two-phase approach:
1. **Planning Phase**: Analyzes the request and creates a step-by-step plan using available tools
2. **Building Phase**: Executes the plan sequentially and synthesizes the final response

This is the default agent architecture in CLIA and is best suited for predictable, well-defined tasks.

## Architecture

### Key Components

1. **`plan_build_agent.py`**: Main Plan-Build agent implementation
   - `plan_build()`: Main entry point that orchestrates planning and building phases
   - `_planner()`: Generates a step-by-step execution plan
   - `_builder()`: Executes the plan and synthesizes the final answer
   - `_extract_plan()`: Parses LLM response to extract the plan JSON array

2. **Integration**: The agent is the default in `main.py` and can be explicitly selected via `--agent plan-build`

## Usage

### Command Line

```bash
# Use Plan-Build agent (default)
clia ask "What is in file.txt?"

# Explicitly specify plan-build agent
clia ask "What is in file.txt?" --agent plan-build

# With verbose output to see planning steps
clia ask "Read file.txt and summarize" --agent plan-build --verbose

# With reflection to get performance analysis
clia ask "Complex task" --agent plan-build --with-reflection
```

### Programmatic Usage

```python
from clia.agents.plan_build_agent import plan_build

result = plan_build(
    question="What is in file.txt?",
    command="ask",
    max_steps=5,
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
    model="gpt-4",
    stream=False,
    temperature=0.0,
    top_p=0.85,
    frequency_penalty=0.0,
    max_tokens=4096,
    timeout=30.0,
    return_metadata=False
)
```

## Plan-Build Pattern Format

The agent expects LLM responses in this format during the planning phase:

```json
[
    {
        "action": "tool",
        "tool": "read_file",
        "args": {"path_str": "file.txt", "max_chars": 4000},
        "note": "Read the file to get its contents"
    },
    {
        "action": "final",
        "answer": "Based on the file contents, provide the answer"
    }
]
```

### Plan Structure

- **Tool Steps**: Steps with `"action": "tool"` specify which tool to execute
  - `tool`: Name of the tool to use (must be from available tools)
  - `args`: Dictionary of arguments for the tool
  - `note`: Optional explanation of why this step is needed

- **Final Step**: Step with `"action": "final"` provides the final answer
  - `answer`: The answer template or instruction for generating the final response

## Features

1. **Upfront Planning**: All steps are planned before execution, providing a clear roadmap
2. **Sequential Execution**: Steps are executed in order, ensuring predictable behavior
3. **Tool Integration**: Uses the same tool system as other agents (read_file, echo, http_get)
4. **Error Handling**: Gracefully handles tool failures and continues execution
5. **Metadata Support**: Can return execution metadata for reflection and analysis
6. **Task-Specific Prompts**: Uses command-specific prompts for better task understanding

## Comparison with Other Agents

| Feature | Plan-Build | ReAct | LLMCompiler |
|---------|-----------|-------|-------------|
| Planning | Upfront, all steps | Iterative, step-by-step | DAG with dependencies |
| Execution | Sequential | Iterative | Parallel where possible |
| Adaptability | Low (fixed plan) | High (reacts to observations) | Medium (fixed DAG) |
| Complexity | Simple | Moderate | Complex |
| Best For | Predictable tasks | Exploratory tasks | Parallelizable tasks |
| Max Steps | Configurable (default: 5) | Configurable iterations (default: 10) | Unlimited (DAG-based) |

## Implementation Details

### Planning Phase

The planner:
1. Receives the user question
2. Generates a JSON array of execution steps
3. Each step can be either a tool call or a final answer instruction
4. Plans are typically 1-3 steps for efficiency

### Building Phase

The builder:
1. Executes tool steps sequentially
2. Collects results from each tool execution
3. Passes all results to the LLM for final answer synthesis
4. Uses task-specific prompts to generate appropriate responses

### Plan Extraction

The `_extract_plan()` function:
- Uses regex to find JSON arrays in the LLM response
- Handles cases where the LLM wraps JSON in code blocks or provides extra text
- Falls back to treating the entire response as a final answer if no plan is found

### Error Handling

- **Tool failures**: Errors are captured and included in results, allowing the builder to handle them
- **Invalid plans**: If no valid plan is extracted, the response is treated as a direct answer
- **Missing tools**: Unknown tools are reported as errors in the execution results

### Metadata

When `return_metadata=True`, the agent returns:
- `plan`: The original plan generated
- `execution_results`: List of step execution results
- `steps_executed`: Number of tool steps actually executed
- `max_steps`: Maximum steps allowed

## Example Execution Flow

```
User: "Read file.txt and tell me what it says"

Planning Phase:
  LLM generates plan:
  [
    {
      "action": "tool",
      "tool": "read_file",
      "args": {"path_str": "file.txt"},
      "note": "Read the file contents"
    },
    {
      "action": "final",
      "answer": "Summarize the file contents"
    }
  ]

Building Phase:
  Step 1: Execute read_file("file.txt")
    Result: "File contents here..."
  
  Step 2: Generate final answer
    Input: Question + Tool results
    Output: "The file contains: ..."
```

## Future Enhancements

- [ ] Support for `--with-calibration` parameter for code testing
- [ ] Better streaming support during execution
- [ ] Plan validation before execution
- [ ] Plan optimization (removing redundant steps)
- [ ] Support for conditional planning (if-then-else steps)
- [ ] Plan caching for similar queries
- [ ] Multi-turn conversation support with plan updates
