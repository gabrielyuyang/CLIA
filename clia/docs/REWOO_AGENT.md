# ReWOO Agent

ReWOO (Reasoning WithOut Observation) is an efficient agent architecture designed for tasks that can benefit from parallel tool execution. Unlike ReAct or Plan-Build, ReWOO generates a complete execution plan with variable placeholders (#E1, #E2, etc.) and executes all independent tool calls simultaneously.

## How it Works

1. **Planner**: The LLM generates a full plan of tool calls upfront. It uses placeholders (e.g., `#E1`) to represent the output of a step. Subsequent steps can reference these placeholders.
2. **Worker**: The agent parses the plan and identifies which tools can be run. It executes all tool calls in parallel using a thread pool.
3. **Solver**: Once all tool results are collected, the LLM receives the original question, the plan, and all execution results to synthesize the final answer.

## Key Benefits

- **Speed**: By executing tools in parallel, ReWOO significantly reduces the total time taken for tasks involving multiple independent tool calls (e.g., reading multiple files, fetching several URLs).
- **Efficiency**: Reduces the number of LLM calls compared to ReAct, as the entire plan is generated in one go.
- **Robustness**: Independent tool failures don't necessarily stop the entire process.

## Usage

### CLI Usage

```bash
clia ask "Read file1.txt and file2.txt, then compare them" --agent rewoo --verbose
```

### Programmatic Usage

```python
from clia.agents.rewoo_agent import rewoo_agent
from clia.config import Settings

settings = Settings.load_openai()

result = rewoo_agent(
    question="Read data.json and analyze its structure",
    command="ask",
    api_key=settings.api_key,
    base_url=settings.base_url,
    model=settings.model,
    verbose=True
)

print(result)
```

## Plan Format

ReWOO expects plans in a specific JSON format:

```json
[
    {
        "id": "#E1",
        "tool": "read_file",
        "args": {"path_str": "file1.txt"}
    },
    {
        "id": "#E2",
        "tool": "read_file",
        "args": {"path_str": "file2.txt"}
    },
    {
        "id": "final",
        "action": "final",
        "plan": "Compare the contents of #E1 and #E2"
    }
]
```

## Comparison with Other Agents

| Feature | Plan-Build | ReAct | LLMCompiler | ReWOO | ToT |
|---------|------------|-------|-------------|-------|-----|
| **Execution** | Sequential | Iterative | Parallel (DAG) | Parallel (Full) | Multi-Path |
| **LLM Calls** | 2 | 1 per step | 2+ | 2 | Many |
| **Adaptability**| Low | High | Medium | Medium | Very High |
| **Speed** | Medium | Slow | Fast | Very Fast | Slow |

## Best For

- Tasks requiring multiple independent tool calls.
- Scenarios where latency is a primary concern.
- Predictable workflows that can be planned entirely upfront.
