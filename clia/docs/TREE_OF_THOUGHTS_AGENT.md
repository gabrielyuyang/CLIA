# Tree-of-Thoughts (ToT) Agent

The Tree-of-Thoughts (ToT) agent is an advanced reasoning agent that explores multiple reasoning paths in parallel, evaluates them, and selects the best approach to solve complex tasks. It's particularly effective for debugging, analysis, and multi-step problem-solving tasks.

## Overview

Unlike traditional single-path reasoning agents, the ToT agent:
- Generates multiple candidate thoughts at each step
- Evaluates and scores each thought for quality
- Uses beam search to explore the most promising paths
- Synthesizes a final answer from the best exploration paths
- Integrates with existing tools for enhanced capabilities

## Key Features

1. **Multi-Path Exploration**: Generates k candidate thoughts per step to explore diverse approaches
2. **Inline Evaluation**: Scores each thought before proceeding to ensure quality
3. **Beam Search**: Prunes less promising branches to balance exploration with computational cost
4. **Tool Integration**: Executes tools suggested by thoughts and incorporates results
5. **Synthesis**: Aggregates insights from multiple paths for comprehensive answers

## Installation

The ToT agent is included in the CLIA framework. Ensure you have the latest version installed:

```bash
pip install -e .
```

## Usage

### Basic Usage

```python
from clia.agents import tot_agent

# Simple question answering
result = tot_agent(
    question="What are the potential causes of a segmentation fault in C programs?",
    command="ask"
)

print(result)
```

### Advanced Configuration

```python
from clia.agents import tot_agent

# Debugging with custom parameters
result = tot_agent(
    question="My Python script is throwing unexpected exceptions. Help me debug it.",
    command="debug",
    max_depth=3,          # Maximum depth of exploration
    branching_factor=3,   # Number of thoughts to generate at each step
    beam_width=2,         # Number of top thoughts to keep at each level
    temperature=0.7,      # Higher for more diverse thoughts
    verbose=True          # Print intermediate steps
)

print(result)
```

### With Memory Integration

```python
from clia.agents import tot_agent
from clia.agents.memory import MemoryManager

# Create memory manager for persistent learning
memory_manager = MemoryManager("tot_memory.jsonl")

result = tot_agent(
    question="Analyze the performance bottlenecks in this algorithm.",
    command="ask",
    memory_manager=memory_manager
)
```

### Simple Wrapper Function

For convenience, there's also a simplified wrapper:

```python
from clia.agents import tot_agent_simple

result = tot_agent_simple(
    question="Explain the differences between BFS and DFS algorithms.",
    command="explain"
)

print(result)
```

## API Reference

### `tot_agent()`

Main function to run the Tree-of-Thoughts agent.

**Parameters:**

- `question` (str): The user's question or task
- `command` (str): The command type (ask, explain, debug, fix, generate, draft)
- `max_depth` (int, default=3): Maximum depth of thought tree exploration
- `branching_factor` (int, default=3): Number of thoughts to generate at each step
- `beam_width` (int, default=2): Number of top thoughts to keep at each level
- `api_key` (str, optional): OpenAI API key
- `base_url` (str, optional): OpenAI API base URL
- `max_retries` (int, default=5): Maximum retries for API calls
- `model` (str, optional): Model name
- `stream` (bool, default=False): Whether to stream responses
- `temperature` (float, default=0.7): Sampling temperature (higher for generation)
- `top_p` (float, default=0.85): Top-p sampling parameter
- `frequency_penalty` (float, default=0.0): Frequency penalty
- `max_tokens` (int, default=4096): Maximum tokens in response
- `timeout` (float, default=30.0): Request timeout
- `verbose` (bool, default=False): Whether to print intermediate steps
- `return_metadata` (bool, default=False): Whether to return metadata about exploration
- `memory_manager` (MemoryManager, optional): Memory manager for persistent learning

**Returns:**
- `str`: Final answer string
- `Tuple[str, dict]`: If `return_metadata=True`, returns (final_answer, metadata_dict)

### `tot_agent_simple()`

Simplified wrapper around `tot_agent` for basic use cases.

**Parameters:**
Same as `tot_agent`, but with `verbose=False` by default.

**Returns:**
- `str`: Final answer string

## Configuration Examples

### Debugging Complex Issues

```python
result = tot_agent(
    question="""
    I'm getting inconsistent results from my machine learning model.
    Sometimes it achieves 95% accuracy, other times only 60%.
    The model architecture and training data are the same.
    What could be causing this variance?
    """,
    command="debug",
    max_depth=4,
    branching_factor=4,
    beam_width=3,
    temperature=0.8  # High diversity for debugging hypotheses
)
```

### Code Analysis and Optimization

```python
result = tot_agent(
    question="""
    Analyze this Python function for potential optimizations:

    def fibonacci(n):
        if n <= 1:
            return n
        else:
            return fibonacci(n-1) + fibonacci(n-2)

    Suggest multiple approaches for improving its performance.
    """,
    command="ask",
    max_depth=3,
    branching_factor=3,
    beam_width=2,
    temperature=0.7
)
```

## Integration with Other Agents

The ToT agent follows the same patterns as other CLIA agents:

```python
from clia.agents import tot_agent, react_agent, llm_compiler_agent

# You can switch between agents based on task complexity
if task_is_complex:
    result = tot_agent(question, "ask")
elif task_needs_tools:
    result = llm_compiler_agent(question, "ask")
else:
    result = react_agent(question, "ask")
```

## Memory Integration

The ToT agent integrates with the CLIA memory system to persist learning:

```python
# Memory entries include exploration metadata
metadata = {
    "max_depth": 3,
    "branching_factor": 3,
    "beam_width": 2,
    "thoughts_explored": 18,
    "final_paths": 2,
    "best_score": 0.92
}
```

## Reflection Support

The ToT agent includes reflection capabilities for self-analysis:

```python
from clia.agents.reflection import reflect_tot_agent

# Reflect on agent performance
reflection = reflect_tot_agent(
    question="Original question",
    all_thoughts=all_thoughts_list,
    final_thoughts=final_thoughts_list,
    final_answer="Final answer",
    thoughts_explored=18,
    final_paths=2,
    max_depth=3,
    branching_factor=3,
    beam_width=2,
    best_score=0.92
)

print(reflection)
```

## Best Practices

1. **Adjust Parameters for Task Type**:
   - Use higher `temperature` (0.7-0.9) for creative tasks
   - Use lower `temperature` (0.3-0.5) for analytical tasks
   - Increase `max_depth` for complex multi-step problems
   - Increase `branching_factor` for broader exploration

2. **Use Appropriate Commands**:
   - `"debug"` for troubleshooting and bug analysis
   - `"ask"` for general question answering
   - `"explain"` for concept explanation
   - `"generate"` for code or content generation

3. **Monitor Computational Cost**:
   - The ToT agent makes multiple LLM calls
   - Balance `max_depth`, `branching_factor`, and `beam_width` based on your needs
   - Consider using `verbose=True` to monitor progress

4. **Leverage Tool Integration**:
   - Formulate thoughts that suggest actionable tool use
   - The agent can automatically execute file reads, shell commands, etc.

## Troubleshooting

### Common Issues

1. **High Token Usage**: Reduce `max_depth` or `branching_factor` to control costs
2. **Slow Responses**: Decrease exploration parameters or use a faster model
3. **Irrelevant Thoughts**: Adjust `temperature` - lower values for more focused thinking

### Error Handling

The ToT agent includes robust error handling:
- Falls back to simple thoughts when LLM calls fail
- Continues execution even if individual thoughts fail
- Provides meaningful error messages in final output

## Comparison with Other Agents

| Feature | ReAct | LLMCompiler | ReWOO | Tree-of-Thoughts |
|---------|-------|-------------|-------|------------------|
| Reasoning Paths | Single | Single (parallel tools) | Single (parallel tools) | Multiple |
| Exploration | Sequential | DAG-based | Parallel planning | Beam search |
| Tool Integration | Inline | Parallel | Parallel | Selective |
| Best For | Simple tasks | Tool-heavy tasks | Tool planning | Complex analysis |

## Contributing

To contribute to the ToT agent development:

1. Run unit tests: `python -m unittest clia/tests/test_tot_agent.py`
2. Run integration tests: `python clia/tests/integration_test_tot.py`
3. Check code style and patterns
4. Submit pull requests with clear descriptions

## License

This agent is part of the CLIA framework and follows the same licensing terms.