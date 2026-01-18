"""
Memory Management System for CLIA Agents

This module provides persistent memory management capabilities:
1. Store conversation history across sessions
2. Retrieve relevant past conversations
3. Summarize old conversations to reduce token usage
4. Search and filter memories by content, time, or metadata
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import json
import logging
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Represents a single memory entry."""
    timestamp: str
    question: str
    answer: str
    command: str
    agent_type: str
    metadata: Dict[str, Any]
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary."""
        return cls(**data)

    def get_content_hash(self) -> str:
        """Get hash of question+answer for deduplication."""
        content = f"{self.question}{self.answer}"
        return hashlib.md5(content.encode()).hexdigest()


class MemoryManager:
    """
    Manages persistent memory for CLIA agents.

    Features:
    - Store conversations in JSON format
    - Retrieve relevant memories based on similarity
    - Summarize old memories to save tokens
    - Filter by time, command, agent type
    """

    def __init__(
        self,
        memory_path: Path,
        max_memories: int = 100,
        enable_summarization: bool = True,
        summary_threshold: int = 50,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        max_retries: int = 5,
        timeout: float = 30.0
    ):
        """
        Initialize memory manager.

        Args:
            memory_path: Path to store memory file
            max_memories: Maximum number of memories to keep before summarization
            enable_summarization: Whether to summarize old memories
            summary_threshold: Number of memories before summarization kicks in
            api_key: API key for LLM summarization (optional)
            base_url: Base URL for LLM API (optional)
            model: Model name for summarization (optional)
            max_retries: Max retries for API calls
            timeout: Timeout for API calls
        """
        self.memory_path = Path(memory_path)
        self.max_memories = max_memories
        self.enable_summarization = enable_summarization
        self.summary_threshold = summary_threshold
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

        # Ensure memory directory exists
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing memories
        self.memories: List[MemoryEntry] = self._load_memories()
        logger.info(f"Loaded {len(self.memories)} memories from {self.memory_path}")

    def _load_memories(self) -> List[MemoryEntry]:
        """Load memories from file."""
        if not self.memory_path.exists():
            return []

        try:
            with self.memory_path.open('r', encoding='utf-8') as f:
                memories = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        memories.append(MemoryEntry.from_dict(data))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse memory entry: {e}")
                        continue
                return memories
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            return []

    def _save_memories(self) -> None:
        """Save memories to file."""
        try:
            with self.memory_path.open('w', encoding='utf-8') as f:
                for memory in self.memories:
                    f.write(json.dumps(memory.to_dict(), ensure_ascii=False) + '\n')
            logger.debug(f"Saved {len(self.memories)} memories to {self.memory_path}")
        except Exception as e:
            logger.error(f"Failed to save memories: {e}")

    def add_memory(
        self,
        question: str,
        answer: str,
        command: str,
        agent_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a new memory entry.

        Args:
            question: User question
            answer: Agent answer
            command: Command type (ask, explain, etc.)
            agent_type: Agent type (react, plan-build, llm-compiler)
            metadata: Additional metadata
        """
        memory = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            question=question,
            answer=answer,
            command=command,
            agent_type=agent_type,
            metadata=metadata or {}
        )

        # Check for duplicates
        content_hash = memory.get_content_hash()
        existing_hashes = {m.get_content_hash() for m in self.memories}
        if content_hash in existing_hashes:
            logger.debug("Skipping duplicate memory entry")
            return

        self.memories.append(memory)

        # Manage memory size
        if len(self.memories) > self.max_memories:
            self._manage_memory_size()

        self._save_memories()
        logger.info(f"Added memory entry (total: {len(self.memories)})")

    def _manage_memory_size(self) -> None:
        """Manage memory size by summarizing old entries."""
        if not self.enable_summarization:
            # Just remove oldest entries
            excess = len(self.memories) - self.max_memories
            self.memories = self.memories[excess:]
            logger.info(f"Removed {excess} oldest memories")
            return

        # Summarize old memories if we exceed threshold
        if len(self.memories) > self.summary_threshold:
            num_to_summarize = len(self.memories) - self.max_memories + 10
            old_memories = self.memories[:num_to_summarize]

            # Summarize old memories
            summary = self._summarize_memories(old_memories)

            # Replace old memories with summary
            summary_entry = MemoryEntry(
                timestamp=old_memories[0].timestamp,
                question="[Summarized Past Conversations]",
                answer=summary,
                command="summary",
                agent_type="system",
                metadata={"original_count": len(old_memories)},
                summary=summary
            )

            self.memories = [summary_entry] + self.memories[num_to_summarize:]
            logger.info(f"Summarized {num_to_summarize} memories into 1 entry")

    def _summarize_memories(self, memories: List[MemoryEntry]) -> str:
        """Summarize a list of memories using LLM."""
        if not self.api_key or not self.model:
            # Fallback: simple text summary
            return self._simple_summary(memories)

        try:
            from .llm import openai_completion

            # Build summary prompt
            memory_texts = []
            for mem in memories:
                memory_texts.append(
                    f"Q: {mem.question}\nA: {mem.answer[:500]}..."
                )

            summary_prompt = f"""Summarize the following past conversations into a concise summary that captures:
1. Key topics discussed
2. Important information or facts shared
3. Patterns or recurring themes

Conversations:
{chr(10).join(memory_texts)}

Provide a concise summary (200-300 words):"""

            messages = [
                {"role": "system", "content": "You are a helpful assistant that summarizes conversation history."},
                {"role": "user", "content": summary_prompt}
            ]

            summary = openai_completion(
                api_key=self.api_key,
                base_url=self.base_url,
                max_retries=self.max_retries,
                model=self.model,
                messages=messages,
                stream=False,
                temperature=0.3,
                top_p=0.85,
                frequency_penalty=0.0,
                max_tokens=500,
                timeout=self.timeout
            )

            return summary.strip()
        except Exception as e:
            logger.warning(f"Failed to generate LLM summary: {e}, using simple summary")
            return self._simple_summary(memories)

    def _simple_summary(self, memories: List[MemoryEntry]) -> str:
        """Create a simple text summary without LLM."""
        topics = {}
        for mem in memories:
            # Extract key words from question
            words = mem.question.lower().split()[:5]
            for word in words:
                if len(word) > 3:  # Skip short words
                    topics[word] = topics.get(word, 0) + 1

        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
        topic_list = ", ".join([t[0] for t in top_topics])

        return f"Summary of {len(memories)} past conversations covering topics: {topic_list}. " \
               f"Time range: {memories[0].timestamp} to {memories[-1].timestamp}."


    def clear_memories(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear memories, optionally filtering by age.

        Args:
            older_than_days: If provided, only clear memories older than this

        Returns:
            Number of memories cleared
        """
        if older_than_days:
            from datetime import datetime, timedelta
            cutoff = datetime.now() - timedelta(days=older_than_days)
            original_count = len(self.memories)
            self.memories = [
                m for m in self.memories
                if datetime.fromisoformat(m.timestamp) >= cutoff
            ]
            cleared = original_count - len(self.memories)
        else:
            cleared = len(self.memories)
            self.memories = []

        self._save_memories()
        logger.info(f"Cleared {cleared} memories")
        return cleared

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.memories:
            return {
                "total_memories": 0,
                "by_command": {},
                "by_agent_type": {},
                "oldest": None,
                "newest": None
            }

        by_command = {}
        by_agent_type = {}

        for mem in self.memories:
            by_command[mem.command] = by_command.get(mem.command, 0) + 1
            by_agent_type[mem.agent_type] = by_agent_type.get(mem.agent_type, 0) + 1

        timestamps = [datetime.fromisoformat(m.timestamp) for m in self.memories]

        return {
            "total_memories": len(self.memories),
            "by_command": by_command,
            "by_agent_type": by_agent_type,
            "oldest": min(timestamps).isoformat(),
            "newest": max(timestamps).isoformat()
        }
