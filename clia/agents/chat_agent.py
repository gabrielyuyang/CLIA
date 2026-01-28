"""
Simple Chat Agent - Direct Q&A without complex reasoning patterns
"""

from typing import Optional, Dict, Tuple
import logging
from .llm import openai_completion
from .prompts import get_prompt

logger = logging.getLogger(__name__)


def chat_agent(
    question: str,
    command: str,
    api_key: str,
    base_url: str,
    max_retries: int,
    model: str,
    stream: bool,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    max_tokens: int,
    timeout: float,
    verbose: bool = False,
    return_metadata: bool = False,
    memory_manager=None
) -> str | Tuple[str, Dict]:
    """
    Simple chat agent that directly answers questions without complex reasoning.

    Args:
        question: User's question
        command: Command type (ask, explain, debug, etc.)
        Other args: LLM configuration parameters

    Returns:
        Response string or tuple of (response, metadata) if return_metadata=True
    """
    logger.info("Starting chat agent")

    # Build system message based on command
    prompt_data = get_prompt(command)
    if prompt_data is None:
        prompt_data = get_prompt("ask")
    system_message = prompt_data[0]

    # Prepare messages
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": question}
    ]

    # Add memory context if available
    if memory_manager and memory_manager.memories:
        try:
            # Get recent memories (last 3 entries)
            recent_memories = memory_manager.memories[-3:]
            if recent_memories:
                memory_context = "\n\nRelevant context from previous conversations:\n"
                memory_context += "\n".join([
                    f"- Q: {mem.question}\n  A: {mem.answer[:200]}..." 
                    if len(mem.answer) > 200 else f"- Q: {mem.question}\n  A: {mem.answer}"
                    for mem in recent_memories
                ])
                messages[0]["content"] += memory_context
                logger.info(f"Added {len(recent_memories)} relevant memories to context")
        except Exception as e:
            logger.warning(f"Failed to retrieve memories: {e}")

    # Get response from LLM
    response = openai_completion(
        api_key=api_key,
        base_url=base_url,
        max_retries=max_retries,
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_tokens=max_tokens,
        timeout=timeout
    )

    # Save to memory if available
    if memory_manager:
        try:
            memory_manager.add_memory(
                question=question,
                answer=response,
                command=command,
                agent_type="chat",
                metadata={}
            )
            logger.info("Saved interaction to memory")
        except Exception as e:
            logger.warning(f"Failed to save memory: {e}")

    logger.info("Chat agent completed")

    if return_metadata:
        metadata = {
            "agent": "chat",
            "command": command,
            "model": model
        }
        return response, metadata

    return response
