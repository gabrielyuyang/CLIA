# ReAct Agent Implementation

This document describes the ReAct (Reasoning + Acting) agent implementation for CLIA.

> **Note**: The ReAct agent is experimental and may be deprecated in future versions. The Plan-Build agent is the default and recommended agent for most use cases.

## Overview

The ReAct agent follows an iterative pattern where the agent:
1. **Reasons** about what to do next
2. **Acts** by executing a tool
3. **Observes** the result
4. Repeats until the task is complete

This is different from the existing Plan-Build agent which plans all actions upfront and then executes them sequentially.

## Architecture

### Key Components

1. **`react_agent.py`**: Main ReAct agent implementation
   - `react_agent()`: Full-featured ReAct agent with verbose logging
   - `react_agent_simple()`: Simplified wrapper returning a single string
   - `_extract_react_components()`: Parses LLM responses to extract Thought, Action, Action Input, and Final Answer
   - `_build_react_prompt()`: Constructs the system prompt with ReAct instructions

2. **Integration**: The agent is integrated into `main.py` via the `--agent` flag

## Usage

### Command Line

```bash
# Use ReAct agent (default is plan-build)
clia ask "What is in file.txt?" --agent react

# With verbose output to see reasoning steps
clia ask "What is in file.txt?" --agent react --verbose

# Set maximum iterations
clia ask "Complex task" --agent react --max-iterations 15
```

### Programmatic Usage

```python
from clia.agents.react_agent import react_agent, react_agent_simple
from clia.config import Settings

settings = Settings.load_openai()

# Using react_agent (returns List[str] for streaming compatibility)
# If return_metadata=True, returns tuple of (response_list, metadata_dict)
responses = react_agent(
    question="What is in file.txt?",
    command="ask",
    max_iterations=10,
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
# responses is a list of strings, join them for full response
response = "".join(responses)

# Or use react_agent_simple for a single string response
response = react_agent_simple(
    question="What is in file.txt?",
    command="ask",
    max_iterations=10,
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

## ReAct Pattern Format

The agent expects LLM responses in this format:

```
Thought: [Your reasoning about what to do next]
Action: [tool_name]
Action Input: [JSON string with tool arguments]
```

After tool execution, the agent receives:
```
Observation: [result of the tool execution]
```

When ready to answer:
```
Final Answer: [your final answer to the user's question]
```

## Features

1. **Iterative Reasoning**: The agent can reason after each tool execution, allowing it to adapt to unexpected results
2. **Tool Integration**: Uses the same tool system as other agents (read_file, echo, http_get)
3. **Error Handling**: Gracefully handles tool failures and malformed responses
4. **Verbose Mode**: Can show intermediate reasoning steps for debugging
5. **Streaming Support**: Compatible with streaming LLM responses
6. **Metadata Support**: Can return execution metadata for reflection and analysis
7. **Task-Specific Prompts**: Uses command-specific prompts for better task understanding

## Comparison with Other Agents

| Feature | Plan-Build | ReAct | LLMCompiler |
|---------|-----------|-------|-------------|
| Planning | Upfront, all steps | Iterative, step-by-step | DAG with dependencies |
| Execution | Sequential | Iterative | Parallel where possible |
| Adaptability | Low (fixed plan) | High (reacts to observations) | Medium (fixed DAG) |
| Complexity | Simple | Moderate | Complex |
| Best For | Predictable tasks | Exploratory tasks | Parallelizable tasks |
| Max Steps/Iterations | Configurable (default: 5) | Configurable (default: 10) | Unlimited (DAG-based) |
| Return Metadata | Supported (for reflection) | Supported (for reflection) | Supported (for reflection) |

## Implementation Details

### Response Parsing

The agent uses regex patterns to extract:
- `Thought`: Reasoning before action
- `Action`: Tool name to execute
- `Action Input`: JSON arguments for the tool
- `Final Answer`: Final response to user

### Conversation History

The agent maintains conversation history including:
- All LLM responses
- Tool executions and results
- Iteration tracking

### Error Handling

- Unknown tools: Returns error message listing available tools
- JSON parsing errors: Attempts to extract JSON from malformed input
- Tool execution errors: Captures and includes in observation
- Max iterations: Provides graceful exit with current reasoning

## Future Enhancements

- [ ] Support for multi-turn conversations
- [ ] Better handling of malformed ReAct responses
- [ ] Tool result caching
- [ ] Parallel tool execution support
- [ ] Custom tool registration
- [ ] Memory/context management for long conversations
