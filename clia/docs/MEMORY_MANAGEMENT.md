# Memory Management System

The CLIA project now includes a comprehensive memory management system that enables agents to remember past conversations and use that context to provide better responses.

## Features

### 1. Persistent Memory Storage
- Conversations are stored in JSONL format for easy inspection and backup
- Each memory entry includes:
  - Timestamp
  - Question and answer
  - Command type (ask, explain, debug, etc.)
  - Agent type (react, plan-build, llm-compiler)
  - Metadata (iterations, steps, etc.)

### 2. Intelligent Retrieval
- Automatically retrieves relevant past conversations based on query similarity
- Filters by command type, agent type, and age
- Limits context to prevent token overflow

### 3. Automatic Summarization
- When memory limit is exceeded, old conversations are summarized
- Uses LLM to create concise summaries preserving key information
- Falls back to simple keyword-based summarization if LLM unavailable

### 4. Integration with All Agents
- Works seamlessly with Plan-Build, ReAct, and LLMCompiler agents
- Automatically adds relevant context to agent prompts
- Saves conversations after each interaction

## Usage

### Command-Line Options

#### Enable Memory Management

```bash
# Enable with default memory path
clia ask "Your question" --enable-memory

# Specify custom memory path
clia ask "Your question" --memory-path ./my_memories.jsonl

# Configure memory limit (default: 100)
clia ask "Your question" --enable-memory --memory-limit 50

# Disable summarization
clia ask "Your question" --enable-memory --no-memory-summarization

# Limit context memories (default: 3)
clia ask "Your question" --enable-memory --memory-context-limit 5
```

### Environment Variables

You can also configure memory via environment variables in `.env`:

```bash
CLIA_ENABLE_MEMORY=True
CLIA_MEMORY_PATH=clia/memories/memory.jsonl
CLIA_MEMORY_LIMIT=100
CLIA_MEMORY_SUMMARIZATION=True
```

### Programmatic Usage

```python
from clia.agents import MemoryManager, react_agent
from clia.config import Settings
from pathlib import Path

settings = Settings.load_openai()

# Initialize memory manager
memory_manager = MemoryManager(
    memory_path=Path("clia/memories/memory.jsonl"),
    max_memories=100,
    enable_summarization=True,
    api_key=settings.api_key,
    base_url=settings.base_url,
    model=settings.model
)

# Use with agent
response = react_agent(
    question="What is Python?",
    command="ask",
    memory_manager=memory_manager,
    api_key=settings.api_key,
    base_url=settings.base_url,
    model=settings.model,
    # ... other parameters
)

# Retrieve relevant memories
relevant = memory_manager.retrieve_relevant(
    query="Python programming",
    limit=5,
    command="ask"
)

# Get memory statistics
stats = memory_manager.get_stats()
print(f"Total memories: {stats['total_memories']}")
print(f"By command: {stats['by_command']}")

# Clear old memories
cleared = memory_manager.clear_memories(older_than_days=30)
print(f"Cleared {cleared} memories older than 30 days")
```

## Memory File Format

Memories are stored as JSONL (JSON Lines), one entry per line:

```json
{"timestamp": "2024-01-15T10:30:00", "question": "What is Python?", "answer": "Python is...", "command": "ask", "agent_type": "react", "metadata": {"iterations_used": 3}, "summary": null}
{"timestamp": "2024-01-15T11:00:00", "question": "How do I use lists?", "answer": "Lists in Python...", "command": "ask", "agent_type": "plan-build", "metadata": {"plan_length": 2}, "summary": null}
```

## How It Works

1. **Memory Addition**: After each agent interaction, the question and answer are automatically saved to memory (if memory is enabled).

2. **Context Retrieval**: Before processing a new query, the system:
   - Searches past memories for relevant entries
   - Scores them based on keyword overlap and content similarity
   - Selects top N most relevant memories
   - Formats them as conversation messages

3. **Context Injection**: Relevant memories are added to the agent's prompt as previous conversation context, helping the agent:
   - Remember past interactions
   - Maintain consistency
   - Build on previous knowledge

4. **Memory Management**: When memory limit is exceeded:
   - Oldest memories are selected for summarization
   - LLM creates a concise summary preserving key information
   - Summary replaces the original memories
   - Process repeats as needed

## Benefits

- **Context Awareness**: Agents remember past conversations and can reference them
- **Consistency**: Responses are more consistent across sessions
- **Efficiency**: Summarization prevents memory from growing unbounded
- **Flexibility**: Can be enabled/disabled per command or globally
- **Privacy**: All memories stored locally, no external services required

## Limitations

- Current retrieval uses simple keyword matching (can be enhanced with embeddings)
- Summarization requires LLM API access (falls back to simple summary if unavailable)
- Memory files grow over time (managed through summarization)
- No built-in encryption (store sensitive data at your own risk)

## Future Enhancements

- Vector embeddings for semantic search
- Memory clustering and topic modeling
- User-specific memory isolation
- Memory export/import functionality
- Advanced filtering and search capabilities
