# Reflection System Implementation

This document describes the Reflection system implementation for CLIA agents.

## Overview

The Reflection system provides self-critique capabilities for agents to:
1. **Self-critique** their performance after task completion
2. **Analyze** what went well and what didn't
3. **Identify** areas for improvement
4. **Learn** from mistakes and successes

Reflection is agent-agnostic and can be used with Plan-Build, ReAct, or LLMCompiler agents.

## Architecture

### Key Components

1. **`reflection.py`**: Main reflection module
   - `AgentReflection`: Class representing a reflection on agent performance
   - `reflect_on_execution()`: Generic reflection function using LLM
   - `reflect_react_agent()`: Reflection specifically for ReAct agent
   - `reflect_llm_compiler_agent()`: Reflection specifically for LLMCompiler agent
   - `reflect_plan_build_agent()`: Reflection specifically for Plan-Build agent
   - `_extract_json()`: Helper to extract JSON from LLM responses

2. **Integration**: Reflection is enabled via `--with-reflection` flag in `main.py`

## Usage

### Command Line

```bash
# Enable reflection with Plan-Build agent
clia ask "Complex task" --agent plan-build --with-reflection

# Enable reflection with ReAct agent
clia ask "Complex task" --agent react --with-reflection --verbose

# Enable reflection with LLMCompiler agent
clia ask "Read multiple files" --agent llm-compiler --with-reflection
```

### Programmatic Usage

```python
from clia.agents.reflection import reflect_plan_build_agent

reflection = reflect_plan_build_agent(
    question="What is in file.txt?",
    plan=[...],  # The plan that was executed
    execution_results=[...],  # Results from execution
    final_answer="The file contains...",
    steps_executed=2,
    max_steps=5,
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
    model="gpt-4",
    verbose=True
)

print(reflection)
```

## Reflection Output Format

Reflection output includes:

```
Reflection for plan-build Agent
============================================================
Question: What is in file.txt?
Success: True

Strengths:
  ✓ Successfully executed all planned steps
  ✓ Used appropriate tools for the task
  ✓ Generated clear and concise answer

Errors/Issues:
  ✗ Could have used fewer steps for this simple task

Improvements:
  → Consider combining steps when possible
  → Validate file existence before reading
```

## Features

1. **Agent-Specific Analysis**: Tailored reflection for each agent type
2. **Structured Output**: Provides strengths, errors, and improvements
3. **LLM-Powered**: Uses LLM to generate insightful critiques
4. **Error Handling**: Gracefully handles reflection generation failures
5. **Verbose Mode**: Shows detailed reflection generation process

## Agent-Specific Reflections

### ReAct Agent Reflection

Analyzes:
- **Iterations used**: How many reasoning-action cycles were needed
- **Tools used**: Which tools were utilized
- **Conversation flow**: Quality of reasoning and actions
- **Efficiency**: Whether max iterations were reached

Example metadata:
```python
{
    "iterations_used": 3,
    "max_iterations": 10,
    "tools_used": ["read_file"],
    "errors_encountered": [],
    "conversation_turns": 6,
    "reached_max_iterations": False
}
```

### LLMCompiler Agent Reflection

Analyzes:
- **Plan validity**: Whether the DAG was valid
- **Parallel opportunities**: How many steps could run in parallel
- **Dependency depth**: Maximum depth of the dependency graph
- **Execution efficiency**: How well parallel execution was utilized

Example metadata:
```python
{
    "plan_valid": True,
    "total_steps": 4,
    "steps_executed": 4,
    "tools_used": ["read_file", "read_file", "echo"],
    "errors_encountered": [],
    "parallel_opportunities": 2,
    "dependency_depth": 2
}
```

### Plan-Build Agent Reflection

Analyzes:
- **Plan length**: Number of steps in the plan
- **Steps executed**: How many steps were actually executed
- **Tool usage**: Which tools were used
- **Efficiency**: Whether max steps were reached

Example metadata:
```python
{
    "plan_length": 3,
    "steps_executed": 2,
    "max_steps": 5,
    "tools_used": ["read_file"],
    "errors_encountered": [],
    "reached_max_steps": False
}
```

## Implementation Details

### Reflection Generation Process

1. **Collect Metadata**: Agent execution metadata is collected
2. **Build Prompt**: Creates a detailed prompt with execution summary
3. **LLM Analysis**: LLM analyzes the execution and provides feedback
4. **Parse Response**: Extracts structured feedback from LLM response
5. **Create Reflection**: Builds `AgentReflection` object with analysis

### Reflection Prompt Structure

The reflection prompt includes:
- Original question/task
- Agent type used
- Execution summary (JSON format)
- Final answer provided
- Request for strengths, errors, and improvements

### JSON Extraction

The `_extract_json()` function:
- Looks for JSON in code blocks (```json ... ```)
- Tries to find JSON objects directly in text
- Attempts to parse entire response as JSON
- Falls back to basic reflection if parsing fails

### Error Handling

- **LLM failures**: Returns basic reflection with error information
- **JSON parsing errors**: Falls back to default reflection structure
- **Missing metadata**: Uses available information, marks missing fields

## AgentReflection Class

The `AgentReflection` class provides:

- **Attributes**:
  - `question`: Original user question
  - `agent_type`: Type of agent used
  - `execution_summary`: Summary of execution
  - `final_answer`: Final answer provided
  - `success`: Whether execution was successful
  - `strengths`: List of what went well
  - `errors`: List of errors/issues
  - `improvements`: List of improvement suggestions

- **Methods**:
  - `to_dict()`: Convert to dictionary
  - `__str__()`: Human-readable string representation

## Use Cases

### Development and Debugging

Reflection helps identify:
- Inefficient tool usage
- Unnecessary steps
- Better approaches for similar tasks
- Common failure patterns

### Performance Optimization

Reflection can reveal:
- Opportunities for parallelization
- Redundant operations
- Better planning strategies
- Resource usage patterns

### Learning and Improvement

Reflection enables:
- Understanding agent behavior
- Identifying best practices
- Learning from mistakes
- Continuous improvement

## Example Usage Scenarios

### Scenario 1: Optimizing Tool Usage

```bash
clia ask "Read file1.txt and file2.txt" --agent llm-compiler --with-reflection
```

Reflection might suggest:
- "Both file reads could have been parallelized (they were)"
- "Consider caching file reads if accessed multiple times"

### Scenario 2: Identifying Inefficiencies

```bash
clia ask "Simple question" --agent react --with-reflection --max-iterations 5
```

Reflection might reveal:
- "Used 3 iterations when 1 would have sufficed"
- "Could have provided direct answer without tool usage"

### Scenario 3: Debugging Failures

```bash
clia ask "Read non-existent file" --agent plan-build --with-reflection
```

Reflection might identify:
- "Failed to check file existence before reading"
- "Error handling could be improved"

## Future Enhancements

- [ ] Comparative reflection (compare multiple agent approaches)
- [ ] Reflection-based plan optimization
- [ ] Learning from reflections (store and reuse insights)
- [ ] Reflection metrics and analytics
- [ ] Custom reflection prompts per task type
- [ ] Reflection visualization
- [ ] Reflection-based agent selection
- [ ] Multi-agent reflection comparison
