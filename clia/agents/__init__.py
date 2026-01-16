"""
CLIA Agents Module

This module provides the core agent functionality including LLM integration,
prompt management, conversation history, and reflection capabilities.
"""

from .llm import openai_completion
from .prompts import get_prompt
from .history import History
from .memory import MemoryManager, MemoryEntry
from .react_agent import react_agent, react_agent_simple
from .plan_build_agent import plan_build
from .llm_compiler_agent import llm_compiler_agent, llm_compiler_agent_simple
from .reflection import (
    AgentReflection,
    reflect_on_execution,
    reflect_react_agent,
    reflect_llm_compiler_agent,
    reflect_plan_build_agent
)

__all__ = [
    "openai_completion",
    "get_prompt",
    "History",
    "MemoryManager",
    "MemoryEntry",
    "react_agent",
    "react_agent_simple",
    "plan_build",
    "llm_compiler_agent",
    "llm_compiler_agent_simple",
    "AgentReflection",
    "reflect_on_execution",
    "reflect_react_agent",
    "reflect_llm_compiler_agent",
    "reflect_plan_build_agent"
]