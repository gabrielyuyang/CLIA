# CLIA Examples

This directory contains example scripts demonstrating how to use CLIA agents programmatically.

## Available Examples

### 1. `react_example.py`
Demonstrates the ReAct agent usage with two approaches:
- Using `react_agent_simple()` for a simple string response
- Using `react_agent()` with metadata for reflection support

**Run:**
```bash
python examples/react_example.py
```

### 2. `plan_build_example.py`
Demonstrates the Plan-Build agent (default agent) usage:
- Basic usage without metadata
- Usage with metadata for reflection support

**Run:**
```bash
python examples/plan_build_example.py
```

### 3. `llm_compiler_example.py`
Demonstrates the LLMCompiler agent with parallel execution capabilities:
- Using `llm_compiler_agent_simple()` for a simple string response
- Using `llm_compiler_agent()` with metadata to see execution details

**Run:**
```bash
python examples/llm_compiler_example.py
```

### 4. `reflection_example.py`
Demonstrates how to use the reflection system to get self-critique from agents:
- Runs a ReAct agent with metadata
- Generates reflection on the agent's performance

**Run:**
```bash
python examples/reflection_example.py
```

### 5. `comprehensive_example.py`
A comprehensive example showing all three agent types solving the same task:
- Plan-Build agent
- ReAct agent
- LLMCompiler agent

This helps you understand the differences between agent approaches.

**Run:**
```bash
python examples/comprehensive_example.py
```

## Prerequisites

Before running any example, make sure you have:

1. **Installed CLIA:**
   ```bash
   pip install .
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root with:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=glm-4.6
   ```

## Usage Tips

- All examples use `Settings.load_openai()` to load configuration from environment variables
- Examples demonstrate both simple and advanced usage patterns
- The reflection example shows how to get performance analysis from agents
- The comprehensive example helps you choose the right agent for your task

## Customization

You can modify these examples to:
- Change the question/task
- Adjust agent parameters (temperature, max_iterations, etc.)
- Use different commands (ask, draft, explain, debug, fix, generate)
- Enable verbose mode for debugging
- Use different models or API endpoints

## See Also

- [Main README](../README.md) - Complete CLIA documentation
- [Plan-Build Agent Docs](../PLAN_BUILD_AGENT.md) - Detailed Plan-Build documentation
- [ReAct Agent Docs](../REACT_AGENT.md) - Detailed ReAct documentation
- [LLMCompiler Agent Docs](../LLM_COMPILER_AGENT.md) - Detailed LLMCompiler documentation
- [Reflection System Docs](../REFLECTION_AGENT.md) - Detailed reflection documentation
