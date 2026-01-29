# CLIA: An Efficient Minimalist CLI AI Agent

CLIA is a powerful command-line AI agent that implements multiple agent architectures (Chat, Plan-Build, ReAct, LLMCompiler, ReWOO, and Tree-of-Thoughts) to help developers with various coding tasks. It leverages OpenAI-compatible APIs to provide intelligent assistance with a focus on simplicity, efficiency, and flexibility.

## Features

### Multiple Agent Architectures

- **Chat Agent** (Default): Direct Q&A for general tasks. Best for simple queries and conversations.
- **Plan-Build Agent**: Plans all steps upfront, then executes them sequentially. Best for predictable, well-defined tasks.
- **ReAct Agent**: Iterative reasoning-action-observation pattern. Adapts dynamically to results. Best for complex, exploratory tasks.
- **LLMCompiler Agent**: Compiles tasks into a Directed Acyclic Graph (DAG) and executes independent steps in parallel. Best for tasks with parallelizable operations.
- **ReWOO Agent**: Reasoning Without Observation. Generates a plan with tool placeholders and executes all tools in parallel.
- **Tree-of-Thoughts Agent**: Explores multiple reasoning paths in parallel, evaluates them, and selects the best approach. Best for complex analysis, debugging, and multi-step problem-solving tasks.

#### Notes: ReAct, LLMCompiler, and ReWOO agents are experimental and may be deprecated in future versions.

### Task Types

- **ask**: General Q&A assistant for routine questions
- **draft**: Spec-driven development - analyze specifications and generate implementations
- **explain**: Code explanation with clear breakdowns
- **debug**: Identify and locate bugs in code
- **fix**: Fix bugs and generate test cases
- **generate**: Generate ready-to-run code examples

### Advanced Features

- **Memory Management**: Short-term conversation memory enables context-aware responses across multiple interactions
- **Reflection Mode**: Self-critique agent performance and identify improvements
- **Tool Integration**: Built-in tools for file reading, HTTP requests, and text operations
- **Conversation History**: Optional history saving in JSONL format
- **Streaming Support**: Real-time streaming output for faster responses
- **Multiline Input**: Support for complex multi-line queries
- **Customizable Parameters**: Override model settings via command-line arguments
- **Multiple Output Formats**: Markdown, JSON, or plain text output
- **Flexible API Configuration**: Works with any OpenAI-compatible API

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

Clone the repository and install CLIA:

```bash
git clone https://gitcode.com/gabrielyuyang/clia
cd clia
pip install .
```

### Install Dependencies

CLIA requires the following dependencies (automatically installed with pip install):

- `python-dotenv` - For environment variable management
- `httpx` - For HTTP client functionality
- `openai` - For OpenAI API compatibility
- `pydantic` - For data validation
- `tqdm` - For progress bars

See `requirements.txt` for the complete list of dependencies with versions.

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=glm-4.6
OPENAI_STREAM=False
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_TOKENS=4096
OPENAI_MAX_RETRIES=5
OPENAI_TIMEOUT_SECONDS=30
OPENAI_TOP_P=0.85
OPENAI_FREQUENCY_PENALTY=0.0
```

**Note**: The default model is `glm-4.6`. You can override it with any OpenAI-compatible model.

### Using Custom API Providers

CLIA works with any OpenAI-compatible API. For example, to use ModelScope:

```bash
OPENAI_API_KEY=your-modelscope-key
OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1
OPENAI_MODEL="Qwen/Qwen3-Coder-30B-A3B-Instruct"
```

## Usage

### Basic Syntax

```bash
clia <command> [question] [options]
```

### Available Commands

#### `ask` - General Q&A Assistant

Routine question answering for general tasks.

```bash
clia ask "How do I reverse a list in Python?"
clia ask "Explain the concept of recursion" --verbose
```

#### `draft` - Spec-Driven Development

Analyze specifications and generate code implementation.

```bash
clia draft "Create a REST API for user management" --file spec.md
clia draft "Build a todo app with CRUD operations" --multiline
```

#### `explain` - Code Explanation

Explain code snippets and concepts with clear breakdowns.

```bash
clia explain "What does this code do?" --file example.py
clia explain "Explain decorators in Python"
```

#### `debug` - Code Debugging

Identify and fix bugs in code.

```bash
clia debug "This function returns None, why?" --file buggy.py
clia debug "Fix the infinite loop in this code"
```

#### `fix` - Code Fixing with Tests

Locate bugs, provide patches, and generate test cases.

```bash
clia fix "The sorting is not working correctly" --file sort.py
clia fix "Add error handling to this function"
```

#### `generate` - Code Generation

Generate ready-to-run code examples and functions.

```bash
clia generate "Create a function to validate email addresses"
clia generate "Write a web scraper for news articles"
```

### Command-Line Options

#### Input Options

- `question` - The question or task description (can be omitted with `--multiline`)
- `--multiline`, `-m` - Enable multiline input (type `EOF` to end input)
- `--file <path>` - Read question from a file or provide code context

#### Model Parameters

- `--model <name>` - Override the default model
- `--temperature <float>` - Set temperature (0.0-2.0, default from config)
- `--top_p <float>` - Set top_p sampling parameter
- `--max_retries <int>` - Override maximum retry attempts

#### Output Control

- `--stream` - Enable streaming output
- `--quiet` - Suppress all logging output (forces non-streaming output)
- `--output-format {markdown,json,text}` - Set output format (default: markdown)

#### Logging & History

- `--verbose`, `-v` - Enable verbose logging
- `--history <path>` - Save conversation history to a JSONL file

#### Agent Selection

- `--agent {chat,plan-build,react,llm-compiler,rewoo,tot}` - Choose agent architecture (default: chat)
- `--max-iterations <int>` - Maximum iterations for ReAct agent (default: 10)
- `--max-depth <int>` - Maximum depth for Tree-of-Thoughts agent (default: 3)
- `--branching-factor <int>` - Branching factor for Tree-of-Thoughts agent (default: 3)
- `--beam-width <int>` - Beam width for Tree-of-Thoughts agent (default: 2)

#### Memory Management

- `--enable-memory` - Enable memory management (uses default memory path)
- `--memory-path <path>` - Path to memory storage file (enables memory management)
- `--memory-limit <int>` - Maximum number of memories before summarization (default: 100)
- `--memory-context-limit <int>` - Maximum number of relevant memories to include in context (default: 3)
- `--no-memory-summarization` - Disable automatic memory summarization

**Note**: Memory management enables short-term conversation context. Recent conversations (within the last hour) are automatically retrieved and included in the prompt to provide context-aware responses.

#### Advanced Features

- `--with-interaction` - Enable interactive mode (planned feature, not yet fully implemented)
- `--with-reflection` - Enable reflection mode - agent will self-critique its performance

### Usage Examples

#### Example 1: Simple Question with Default Agent

```bash
clia ask "What is the difference between list and tuple in Python?"
```

#### `tot` - Tree-of-Thoughts Agent

Explore multiple reasoning paths for complex analysis and debugging tasks.

```bash
clia ask "Analyze why this code is producing inconsistent results" --agent tot --verbose
clia debug "My neural network training is unstable, suggest multiple hypotheses" --agent tot
```

#### Example 2: Using ReAct Agent

```bash
clia ask "Read file.txt and summarize its contents" --agent react --verbose
```

#### Example 3: Using LLMCompiler Agent for Parallel Execution

```bash
clia ask "Read file1.txt and file2.txt, then compare them" --agent llm-compiler
```

#### Example 4: Using Tree-of-Thoughts Agent for Complex Analysis

```bash
clia debug "My Python script gives different results on different runs. Analyze potential causes." --agent tot --verbose
clia ask "Compare multiple approaches to optimize this algorithm" --agent tot --max-depth 4 --branching-factor 3
```

#### Example 5: File-Based Code Explanation

```bash
clia explain "Explain the main algorithm" --file algorithms.py
```

#### Example 6: Debugging with Custom Model

```bash
clia debug "Fix the segmentation fault" --file crash.c --model gpt-4 --verbose
```

#### Example 7: Generate with Streaming

```bash
clia generate "Create a REST API endpoint for user authentication" --stream
```

#### Example 8: Save History

```bash
clia ask "Explain machine learning concepts" --history conversations.jsonl
```

#### Example 9: Reflection Mode

```bash
clia ask "Complex task requiring multiple steps" --agent react --with-reflection
```

#### Example 10: Memory Management - Enable Short-Term Context

```bash
# Enable memory management with default path
clia ask "What is the difference between list and tuple?" --enable-memory

# Follow-up question that uses previous context
clia ask "Give me an example of each" --enable-memory

# Use custom memory path
clia ask "Your question" --memory-path ./my_memories.jsonl

# Adjust memory settings
clia ask "Your question" --enable-memory --memory-limit 50 --memory-context-limit 5
```

#### Example 11: Spec-Driven Development

```bash
clia draft --file requirements.txt
```

## Architecture

### Agent Architectures

#### Plan-Build Agent (Default)

The Plan-Build agent follows a two-phase approach:

1. **Planning Phase**: Analyzes the request and creates a step-by-step plan using available tools
2. **Building Phase**: Executes the plan sequentially and synthesizes the final response

**Best for**: Simple, predictable tasks with clear requirements

#### ReAct Agent

The ReAct (Reasoning + Acting) agent follows an iterative pattern:

1. **Reason**: Think about what to do next
2. **Act**: Execute a tool
3. **Observe**: Process the result
4. **Repeat**: Continue until the task is complete

**Best for**: Complex, exploratory tasks that require adaptive reasoning

**Format**:
```
Thought: [reasoning]
Action: [tool_name]
Action Input: [JSON arguments]
Observation: [tool result]
...
Final Answer: [final response]
```

#### Tree-of-Thoughts Agent

The Tree-of-Thoughts (ToT) agent explores multiple reasoning paths in parallel, evaluates them, and selects the best approach to solve complex tasks.

1. **Multi-Path Exploration**: Generates k candidate thoughts per step to explore diverse approaches
2. **Inline Evaluation**: Scores each thought before proceeding to ensure quality
3. **Beam Search**: Prunes less promising branches to balance exploration with computational cost
4. **Tool Integration**: Executes tools suggested by thoughts and incorporates results
5. **Synthesis**: Aggregates insights from multiple paths for comprehensive answers

**Best for**: Complex analysis, debugging, and multi-step problem-solving tasks

**Format**:
```
Thought 1: [approach A]
Thought 2: [approach B]
Thought 3: [approach C]
...
[Evaluation and selection of best path]
Final Answer: [comprehensive response]
```

### Available Tools

CLIA provides the following built-in tools:

- **`read_file`**: Read local files with size limits
  - Args: `path_str` (file path), `max_chars` (max characters, default: 4000)

- **`write_file`**: Write content to a file (creates or overwrites) with optional backup
  - Args: `path_str` (file path), `content` (content to write), `backup` (default: True)

- **`shell`**: Execute shell command with timeout
  - Args: `command` (shell command), `timeout` (default: 30.0), `cwd` (working directory)

- **`echo`**: Echo text with size validation
  - Args: `text` (text to echo)

- **`http_get`**: Perform HTTP GET requests with timeout handling
  - Args: `url` (target URL), `timeout` (timeout in seconds, default: 10.0)

- **`fix_code`**: Advanced tool to fix code errors with optional test execution and iteration
  - Args: `error_input`, `code_context`, `max_iterations`, `auto_run_tests`, etc.

### Reflection System

When `--with-reflection` is enabled, CLIA generates a self-critique after task completion:

- **Strengths**: What the agent did well
- **Errors/Issues**: What went wrong or could be improved
- **Improvements**: Concrete suggestions for better performance

Reflection is agent-specific and analyzes:
- **ReAct**: Iterations used, tools used, conversation flow
- **LLMCompiler**: Plan validity, parallel execution opportunities, dependency depth
- **Plan-Build**: Plan length, steps executed, tool usage
- **Tree-of-Thoughts**: Exploration depth, branching factor, beam width, thoughts evaluated

### Workflow Diagram

```
┌─────────────┐
│  User Input │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Agent Selection │
│  (chat/plan-build│
│   react/rewoo/   │
│   llm-compiler/  │
│   tot)           │
└──────┬───────────┘
       │
       ├───────────────┬──────────────┬───────────────┬───────────────┬────────────────┐
       ▼               ▼              ▼               ▼               ▼                ▼
┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│    Chat     │ │ Plan-Build  │ │   ReAct    │ │   ReWOO     │ │ LLMCompiler │ │    ToT      │
│    Agent    │ │    Agent    │ │   Agent    │ │   Agent     │ │    Agent    │ │    Agent    │
└──────┬──────┘ └──────┬──────┘ └──────┬─────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │              │               │               │                │
       ▼               ▼              ▼               ▼               ▼                ▼
┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Direct    │ │   Plan      │ │  Thought   │ │  Plan with  │ │  DAG Plan   │ │  Multi-Path │
│   Response  │ │   Steps     │ │  Action    │ │  Placeholders│ │  Generation │ │  Exploration│
└──────┬──────┘ └──────┬──────┘ └──────┬─────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │              │               │               │                │
       ▼               ▼              ▼               ▼               ▼                ▼
┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Synthesize│ │  Execute    │ │  Execute   │ │  Parallel   │ │  Parallel   │ │  Beam Search│
│   Answer    │ │ Sequentially│ │ Iteratively│ │  Execution  │ │  Execution  │ │  Evaluation │
└──────┬──────┘ └──────┬──────┘ └──────┬─────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │              │               │               │                │
       └───────────────┴──────────────┴───────────────┴───────────────┴────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Final Answer   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Reflection    │
              │   (optional)    │
              └─────────────────┘
```

## Advanced Configuration

### Overriding Settings

You can override any configuration via command-line arguments:

```bash
clia ask "Your question" --temperature 0.7 --top_p 0.9 --max_retries 3
```

### Using Different Output Formats

```bash
# JSON output for programmatic use
clia ask "Generate JSON data" --output-format json

# Plain text for simple processing
clia ask "Simple answer" --output-format text
```

### Memory Management

Enable memory management to provide context-aware responses based on recent conversations:

```bash
# Enable memory with default settings
clia ask "What is Python?" --enable-memory

# Follow-up question uses previous context
clia ask "Give me an example" --enable-memory

# Custom memory path and settings
clia ask "Your question" --memory-path ./memories.jsonl --memory-limit 50
```

**How it works:**
- Memory manager stores recent conversations (question-answer pairs)
- When enabled, agents automatically retrieve the 3 most recent conversations from the last hour
- This context is included in the system prompt to enable follow-up questions and contextual understanding
- Works with all agent types: Plan-Build, ReAct, LLMCompiler, and Tree-of-Thoughts

### Reflection Mode

Enable reflection to get self-critique after task completion:

```bash
clia ask "Complex task" --agent react --with-reflection --verbose
```

## Project Structure

```
clia/
├── clia/                       # Main package directory
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── chat_agent.py           # Direct Q&A agent
│   │   ├── code_fixer.py           # Tool for fixing code errors
│   │   ├── history.py              # Conversation history management
│   │   ├── llm.py                  # LLM API interface
│   │   ├── llm_compiler_agent.py   # LLMCompiler agent implementation
│   │   ├── memory.py               # Memory management for short-term context
│   │   ├── plan_build_agent.py     # Plan-build orchestration
│   │   ├── prompts.py              # Task-specific prompts
│   │   ├── react_agent.py          # ReAct agent implementation
│   │   ├── reflection.py           # Reflection and self-critique
│   │   ├── rewoo_agent.py          # ReWOO agent implementation
│   │   ├── tool_router.py          # Tool routing and execution
│   │   ├── tot_agent.py            # Tree-of-Thoughts agent implementation
│   │   └── tools.py                # Available tools
│   ├── docs/                       # Detailed agent documentation
│   ├── histories/                  # Conversation history storage
│   ├── memories/                   # Memory storage for short-term context
│   ├── tests/                      # Test files
│   ├── config.py                   # Configuration management
│   ├── main.py                     # CLI entry point
│   ├── utils.py                    # Utility functions
│   └── __init__.py
├── examples/                       # Example scripts demonstrating usage
│   ├── README.md
│   ├── rewoo_example.py
│   ├── tot_example.py
│   └── ...
├── setup.py                        # Package setup configuration
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Documentation

Detailed documentation for each agent architecture is available:

- **[Plan-Build Agent](clia/docs/PLAN_BUILD_AGENT.md)**: Two-phase planning and execution approach
- **[ReAct Agent](clia/docs/REACT_AGENT.md)**: Iterative reasoning-action-observation pattern
- **[LLMCompiler Agent](clia/docs/LLM_COMPILER_AGENT.md)**: DAG-based parallel execution
- **[ReWOO Agent](clia/docs/REWOO_AGENT.md)**: Reasoning Without Observation parallel execution
- **[Tree-of-Thoughts Agent](clia/docs/TREE_OF_THOUGHTS_AGENT.md)**: Multi-path exploration and beam search
- **[Reflection System](clia/docs/REFLECTION_AGENT.md)**: Self-critique and performance analysis

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Programmatic Usage

You can also use CLIA agents programmatically:

#### Using ReAct Agent

```python
from clia.agents.react_agent import react_agent, react_agent_simple
from clia.config import Settings

settings = Settings.load_openai()

# Using react_agent (returns List[str] for streaming compatibility)
# With memory management for context-aware responses
from clia.agents import MemoryManager
from pathlib import Path

memory_manager = MemoryManager(
    memory_path=Path("clia/memories/memory.jsonl"),
    max_memories=100,
    enable_summarization=True,
    api_key=settings.api_key,
    base_url=settings.base_url,
    model=settings.model,
    max_retries=settings.max_retries,
    timeout=settings.timeout_seconds
)

response_list = react_agent(
    question="What is in file.txt?",
    command="ask",
    max_iterations=10,
    api_key=settings.api_key,
    base_url=settings.base_url,
    model=settings.model,
    stream=False,
    temperature=settings.temperature,
    top_p=settings.top_p,
    frequency_penalty=settings.frequency_penalty,
    max_tokens=settings.max_tokens,
    timeout=settings.timeout_seconds,
    verbose=True,
    memory_manager=memory_manager  # Enable short-term memory
)
# response_list is a list of strings, join them for full response
response = "".join(response_list)

# Or use react_agent_simple for a single string response
response = react_agent_simple(
    question="What is in file.txt?",
    command="ask",
    max_iterations=10,
    api_key=settings.api_key,
    base_url=settings.base_url,
    model=settings.model,
    stream=False,
    temperature=settings.temperature,
    top_p=settings.top_p,
    frequency_penalty=settings.frequency_penalty,
    max_tokens=settings.max_tokens,
    timeout=settings.timeout_seconds
)
```

#### Using Plan-Build Agent

```python
from clia.agents.plan_build_agent import plan_build
from clia.config import Settings

settings = Settings.load_openai()

response = plan_build(
    question="What is in file.txt?",
    command="ask",
    max_steps=5,
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

See `examples/react_example.py` for a complete example.

## Troubleshooting

### API Connection Issues

If you encounter connection errors:
1. Verify your `OPENAI_API_KEY` is correct
2. Check the `OPENAI_BASE_URL` is accessible
3. Ensure your network allows connections to the API endpoint

### Timeout Errors

Increase timeout settings in `.env`:

```bash
OPENAI_TIMEOUT_SECONDS=60
```

### Large File Reading

The `read_file` tool has a default 4000 character limit. Adjust in your code if needed.

### Agent Selection

- Use **plan-build** for simple, predictable tasks
- Use **react** for complex tasks requiring adaptive reasoning
- Use **llm-compiler** for tasks with parallelizable operations

## Comparison of Agent Architectures

| Feature | Chat | Plan-Build | ReAct | LLMCompiler | ReWOO | Tree-of-Thoughts |
|---------|------|-----------|-------|-------------|-------|------------------|
| Planning | None | Upfront, all steps | Iterative, step-by-step | DAG with dependencies | Upfront with placeholders | Multi-path with beam search |
| Execution | Direct | Sequential | Iterative | Parallel where possible | Parallel (all tools) | Beam search evaluation |
| Adaptability | None | Low (fixed plan) | High (reacts to observations) | Medium (fixed DAG) | Low (fixed plan) | High (evaluates multiple paths) |
| Complexity | Simplest | Simple | Moderate | Complex | Moderate | Most Complex |
| Best For | Simple Q&A | Predictable tasks | Exploratory tasks | Parallelizable tasks | Independent operations | Complex analysis/debugging |
| Max Steps/Iterations | 1 | Configurable (default: 5) | Configurable (default: 10) | Unlimited (DAG-based) | Unlimited (parallel) | Configurable (default: 3 depth) |
| Tool Usage | None | Sequential | Iterative | Parallel with dependencies | Parallel independent | Parallel with evaluation |
| Response Time | Fastest | Fast | Moderate | Moderate | Moderate | Slowest |
| Return Metadata | No | Supported (for reflection) | Supported (for reflection) | Supported (for reflection) | Supported (for reflection) | Supported (for reflection) |
| Memory Support | Yes | Yes | Yes | Yes | Yes | Yes |

## License

[Specify your license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.

## References

- **ReAct**: [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- **LLMCompiler**: [LLMCompiler: Optimizing LLM Queries](https://arxiv.org/abs/2312.04511)
- **COTA**: Calibration of Thoughts and Actions (implementation reference)

## Additional Resources

- **Repository**: [https://gitcode.com/gabrielyuyang/clia](https://gitcode.com/gabrielyuyang/clia)
- **Agent Documentation**: See the `*.md` files in the repository root for detailed agent documentation
- **Examples**: Check the `examples/` directory for usage examples
