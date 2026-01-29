#!/usr/bin/env python3
"""Simple test script to verify all imports work correctly."""

import sys

def test_imports():
    """Test all critical imports."""
    errors = []
    
    try:
        from clia.config import Settings
        print("[OK] Settings import successful")
    except Exception as e:
        errors.append(f"Settings import failed: {e}")
    
    try:
        from clia.agents.plan_build_agent import plan_build
        print("[OK] plan_build_agent import successful")
    except Exception as e:
        errors.append(f"plan_build_agent import failed: {e}")
    
    try:
        from clia.agents.react_agent import react_agent
        print("[OK] react_agent import successful")
    except Exception as e:
        errors.append(f"react_agent import failed: {e}")
    
    try:
        from clia.agents.llm_compiler_agent import llm_compiler_agent
        print("[OK] llm_compiler_agent import successful")
    except Exception as e:
        errors.append(f"llm_compiler_agent import failed: {e}")
    
    try:
        from clia.agents.reflection import (
            reflect_react_agent,
            reflect_llm_compiler_agent,
            reflect_plan_build_agent
        )
        print("[OK] reflection imports successful")
    except Exception as e:
        errors.append(f"reflection imports failed: {e}")
    
    try:
        from clia.agents.tools import read_file_safe, echo_safe, http_get
        print("[OK] tools imports successful")
    except Exception as e:
        errors.append(f"tools imports failed: {e}")
    
    try:
        from clia.agents.tool_router import run_tool, tools_specs, TOOLS
        print("[OK] tool_router imports successful")
    except Exception as e:
        errors.append(f"tool_router imports failed: {e}")
    
    try:
        from clia.agents.prompts import get_prompt
        print("[OK] prompts import successful")
    except Exception as e:
        errors.append(f"prompts import failed: {e}")
    
    try:
        from clia.utils import to_bool, get_multiline_input
        print("[OK] utils imports successful")
    except Exception as e:
        errors.append(f"utils imports failed: {e}")
    
    try:
        from clia.agents.history import History
        print("[OK] history import successful")
    except Exception as e:
        errors.append(f"history import failed: {e}")
    
    if errors:
        print("\n[ERROR] Import errors found:")
        for error in errors:
            print(f"  - {error}")
        assert False, f"Import errors found: {len(errors)}"
    else:
        print("\n[SUCCESS] All imports successful!")

if __name__ == "__main__":
    try:
        test_imports()
        sys.exit(0)
    except AssertionError:
        sys.exit(1)
