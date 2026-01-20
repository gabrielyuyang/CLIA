from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import re
import ast
import difflib
from clia.agents.llm import openai_completion
from clia.agents import tools as tool_funcs


@dataclass
class FixResult:
    success: bool
    fixed_code: str
    error_analysis: str
    fix_explanation: str
    diff: Optional[str] = None
    test_results: Optional[str] = None
    iterations_used: int = 0


@dataclass
class CodeFixerConfig:
    max_iterations: int = 3
    auto_run_tests: bool = True
    test_command: Optional[str] = None
    iterate_until_passing: bool = False
    backup_original: bool = True
    write_back: bool = False
    file_path: Optional[str] = None


def _parse_error_input(error_input: str) -> dict:
    """Parse error input and extract structured information"""
    error_info = {
        "type": "unknown",
        "message": error_input,
        "file": None,
        "line": None,
        "traceback": None
    }

    # Python traceback pattern
    if "Traceback" in error_input or "File \"" in error_input:
        error_info["type"] = "python_traceback"
        error_info["traceback"] = error_input

        # Extract file and line
        file_match = re.search(r'File "([^"]+)", line (\d+)', error_input)
        if file_match:
            error_info["file"] = file_match.group(1)
            error_info["line"] = int(file_match.group(2))

        # Extract error type and message
        error_match = re.search(r'(\w+Error): (.+)$', error_input, re.MULTILINE)
        if error_match:
            error_info["message"] = f"{error_match.group(1)}: {error_match.group(2)}"

    # Test output pattern
    elif "FAILED" in error_input or "AssertionError" in error_input:
        error_info["type"] = "test_failure"

    # Syntax error pattern
    elif "SyntaxError" in error_input or "invalid syntax" in error_input:
        error_info["type"] = "syntax_error"

    return error_info


def _validate_python_syntax(code: str) -> tuple[bool, Optional[str]]:
    """Validate Python code syntax"""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def _analyze_error(error_input: str, code_context: str, api_key: str, base_url: str,
                   model: str, temperature: float) -> str:
    """Use LLM to analyze the error and identify root cause"""
    messages = [
        {"role": "system", "content": """You are a code analysis expert. Analyze the error and code to identify the root cause.
Provide a concise analysis focusing on:
1. What the error is
2. Why it occurred
3. What needs to be fixed

Be specific and actionable."""},
        {"role": "user", "content": f"""Error:
{error_input}

Code:
{code_context}

Analyze this error and provide root cause analysis."""}
    ]

    return openai_completion(
        api_key=api_key,
        base_url=base_url,
        max_retries=2,
        model=model,
        messages=messages,
        stream=False,
        temperature=temperature,
        top_p=1.0,
        frequency_penalty=0.0,
        max_tokens=2000,
        timeout=30.0
    )


def _generate_fix(error_input: str, code_context: str, error_analysis: str,
                 api_key: str, base_url: str, model: str, temperature: float) -> tuple[str, str]:
    """Use LLM to generate fixed code"""
    messages = [
        {"role": "system", "content": """You are a code fixing expert. Generate corrected code based on the error analysis.
Requirements:
- Make MINIMAL changes - only fix what's broken
- Preserve code style and structure
- Return ONLY the fixed code, no explanations in the code
- After the code, provide a brief explanation of what you changed"""},
        {"role": "user", "content": f"""Error:
{error_input}

Original Code:
{code_context}

Error Analysis:
{error_analysis}

Provide the fixed code followed by a brief explanation of changes."""}
    ]

    response = openai_completion(
        api_key=api_key,
        base_url=base_url,
        max_retries=2,
        model=model,
        messages=messages,
        stream=False,
        temperature=temperature,
        top_p=1.0,
        frequency_penalty=0.0,
        max_tokens=4000,
        timeout=30.0
    )

    # Try to extract code and explanation
    if "```" in response:
        parts = response.split("```")
        code_part = parts[1] if len(parts) > 1 else response
        # Remove language identifier
        code_part = re.sub(r'^python\n', '', code_part, flags=re.IGNORECASE)
        explanation = parts[2] if len(parts) > 2 else "Code fixed"
        return code_part.strip(), explanation.strip()

    return response, "Code fixed"


def _generate_diff(original: str, fixed: str, filename: str = "code") -> str:
    """Generate unified diff between original and fixed code"""
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile=f"{filename} (original)",
        tofile=f"{filename} (fixed)",
        lineterm=""
    )
    return "".join(diff)


def fix_code(
    error_input: str,
    code_context: Optional[str],
    config: CodeFixerConfig,
    api_key: str,
    base_url: str,
    model: str,
    temperature: float = 0.1,
    verbose: bool = False
) -> FixResult:
    """Main entry point for code fixing"""

    # Parse error
    error_info = _parse_error_input(error_input)

    # Store original code for diff
    original_code = code_context
    source_file = None

    # If code_context is a file path, read it
    if code_context and Path(code_context).exists():
        source_file = code_context
        code_context = tool_funcs.read_file_safe(code_context, max_chars=10000)
        original_code = code_context

    if not code_context:
        return FixResult(
            success=False,
            fixed_code="",
            error_analysis="No code context provided",
            fix_explanation="Cannot fix without code context",
            iterations_used=0
        )

    # Analyze error
    if verbose:
        print(f"Analyzing error: {error_info['type']}")

    error_analysis = _analyze_error(error_input, code_context, api_key, base_url, model, temperature)

    # Generate fix
    if verbose:
        print("Generating fix...")

    fixed_code, fix_explanation = _generate_fix(error_input, code_context, error_analysis,
                                                 api_key, base_url, model, temperature)

    # Validate syntax for Python code
    if error_info["type"] in ["python_traceback", "syntax_error"]:
        is_valid, syntax_error = _validate_python_syntax(fixed_code)
        if not is_valid:
            diff = _generate_diff(original_code, fixed_code, source_file or "code")
            return FixResult(
                success=False,
                fixed_code=fixed_code,
                error_analysis=error_analysis,
                fix_explanation=f"Generated code has syntax error: {syntax_error}",
                diff=diff,
                iterations_used=1
            )

    # Generate diff
    diff = _generate_diff(original_code, fixed_code, source_file or "code")

    # Write back to file if configured
    if config.write_back and (config.file_path or source_file):
        target_file = config.file_path or source_file
        tool_funcs.write_file_safe(target_file, fixed_code, config.backup_original)

    # Run tests if configured
    test_results = None
    if config.auto_run_tests and config.test_command:
        if verbose:
            print(f"Running tests: {config.test_command}")
        test_results = tool_funcs.shell_exec(config.test_command, timeout=60.0)

        # Check if tests passed
        tests_passed = "FAILED" not in test_results and "ERROR" not in test_results

        if not tests_passed and config.iterate_until_passing and config.max_iterations > 1:
            # Iterative fixing
            for iteration in range(1, config.max_iterations):
                if verbose:
                    print(f"Iteration {iteration + 1}: Tests failed, attempting to fix...")

                # Re-analyze with test results
                new_error_input = f"{error_input}\n\nTest Results:\n{test_results}"
                error_analysis = _analyze_error(new_error_input, fixed_code, api_key, base_url, model, temperature)
                fixed_code, fix_explanation = _generate_fix(new_error_input, fixed_code, error_analysis,
                                                            api_key, base_url, model, temperature)

                # Run tests again
                test_results = tool_funcs.shell_exec(config.test_command, timeout=60.0)
                tests_passed = "FAILED" not in test_results and "ERROR" not in test_results

                if tests_passed:
                    diff = _generate_diff(original_code, fixed_code, source_file or "code")
                    if config.write_back and (config.file_path or source_file):
                        target_file = config.file_path or source_file
                        tool_funcs.write_file_safe(target_file, fixed_code, config.backup_original)
                    return FixResult(
                        success=True,
                        fixed_code=fixed_code,
                        error_analysis=error_analysis,
                        fix_explanation=fix_explanation,
                        diff=diff,
                        test_results=test_results,
                        iterations_used=iteration + 1
                    )

            return FixResult(
                success=False,
                fixed_code=fixed_code,
                error_analysis=error_analysis,
                fix_explanation=f"Tests still failing after {config.max_iterations} iterations",
                diff=diff,
                test_results=test_results,
                iterations_used=config.max_iterations
            )

        return FixResult(
            success=tests_passed,
            fixed_code=fixed_code,
            error_analysis=error_analysis,
            fix_explanation=fix_explanation,
            diff=diff,
            test_results=test_results,
            iterations_used=1
        )

    return FixResult(
        success=True,
        fixed_code=fixed_code,
        error_analysis=error_analysis,
        fix_explanation=fix_explanation,
        diff=diff,
        iterations_used=1
    )


def fix_code_tool(**kwargs) -> str:
    """Tool wrapper that formats FixResult as string for agents"""
    result = fix_code(
        error_input=kwargs.get("error_input", ""),
        code_context=kwargs.get("code_context"),
        config=CodeFixerConfig(
            max_iterations=kwargs.get("max_iterations", 3),
            auto_run_tests=kwargs.get("auto_run_tests", False),
            test_command=kwargs.get("test_command"),
            iterate_until_passing=kwargs.get("iterate_until_passing", False),
            backup_original=kwargs.get("backup_original", True),
            write_back=kwargs.get("write_back", False),
            file_path=kwargs.get("file_path")
        ),
        api_key=kwargs.get("api_key"),
        base_url=kwargs.get("base_url"),
        model=kwargs.get("model"),
        temperature=kwargs.get("temperature", 0.1),
        verbose=kwargs.get("verbose", False)
    )

    output = f"""Fix Result:
Success: {result.success}
Iterations: {result.iterations_used}

Error Analysis:
{result.error_analysis}

Fix Explanation:
{result.fix_explanation}

Diff:
{result.diff if result.diff else '(no changes)'}

Fixed Code:
{result.fixed_code}
"""

    if result.test_results:
        output += f"\nTest Results:\n{result.test_results}"

    return output
