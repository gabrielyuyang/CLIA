import json
from clia.agents import tools
from clia.agents import code_fixer
from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class Tool:
    name: str
    desc: str
    args: Dict[str, str]
    handler: Callable[..., str]


TOOLS = {
    "read_file": Tool(
        name="read_file",
        desc="Read a local file with size limit",
        args={
            "path_str": "path of the file to read",
            "max_chars": "maximum number of characters to read (default: 4000)"
        },
        handler=lambda path_str, max_chars: tools.read_file_safe(path_str, max_chars)
    ),
    "write_file": Tool(
        name="write_file",
        desc="Write content to a file (creates or overwrites) with optional backup",
        args={
            "path_str": "path of the file to write",
            "content": "content to write to the file",
            "backup": "whether to backup existing file (default: True)"
        },
        handler=lambda path_str, content, backup=True: tools.write_file_safe(path_str, content, backup)
    ),
    "shell": Tool(
        name="shell",
        desc="Execute shell command with timeout",
        args={
            "command": "shell command to execute",
            "timeout": "timeout in seconds (default: 30.0)",
            "cwd": "working directory for command execution"
        },
        handler=lambda command, timeout=30.0, cwd=None: tools.shell_exec(command, timeout, cwd)
    ),
    "echo": Tool(
        name="echo",
        desc="Echo the input text",
        args={
            "text": "the text to echo"
        },
        handler=lambda text: tools.echo_safe(text)
    ),
    "http_get": Tool(
        name="http_get",
        desc="Send a HTTP GET request with timeout and basic error handling",
        args={
            "url": "the URL to send the GET request to",
            "timeout": "the timeout for the request in seconds (default: 10.0)"
        },
        handler=lambda url, timeout: tools.http_get(url, timeout)
    ),
    "fix_code": Tool(
        name="fix_code",
        desc="Fix code errors with optional test execution and iteration. Handles syntax errors, runtime errors, test failures, and logical errors. Returns diff and optionally writes back to file.",
        args={
            "error_input": "error message, stack trace, or test output",
            "code_context": "code string or file path to fix",
            "max_iterations": "maximum fix iterations (default: 3)",
            "auto_run_tests": "whether to automatically run tests (default: False)",
            "test_command": "test command to run (e.g., 'pytest tests/')",
            "iterate_until_passing": "keep iterating until tests pass (default: False)",
            "write_back": "whether to write fixed code back to file (default: False)",
            "file_path": "target file path for write-back (uses code_context path if not specified)",
            "backup_original": "whether to backup original file (default: True)",
            "api_key": "OpenAI API key",
            "base_url": "OpenAI API base URL",
            "model": "model to use for fixing",
            "temperature": "temperature for LLM (default: 0.1)",
            "verbose": "verbose output (default: False)"
        },
        handler=lambda **kwargs: code_fixer.fix_code_tool(**kwargs)
    )
}


def list_tools():
    return list(TOOLS.keys())


def run_tool(tool_name: str, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    if not any(k in TOOLS[tool_name].args for k in kwargs):
        raise ValueError(f"Unknown arguments for tool {tool_name}: {TOOLS[tool_name].args}")
    return TOOLS[tool_name].handler(**kwargs)


def tools_specs():
    lines = []
    for tool in TOOLS.values():
        lines.append(f' - {tool.name}: {tool.desc} | args: {json.dumps(tool.args, ensure_ascii=False)}')
    return '\n'.join(lines)