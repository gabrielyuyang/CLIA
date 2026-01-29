import json
from clia.agents import tools
from clia.agents import code_fixer
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Set, Tuple


@dataclass
class Tool:
    name: str
    desc: str
    args: Dict[str, str]
    handler: Callable[..., str]
    required: Set[str] = field(default_factory=set)
    defaults: Dict[str, Any] = field(default_factory=dict)
    arg_types: Dict[str, Any] = field(default_factory=dict)


TOOLS = {
    "read_file": Tool(
        name="read_file",
        desc="Read a local file with size limit",
        args={
            "path_str": "path of the file to read",
            "max_chars": "maximum number of characters to read (default: 4000)"
        },
        handler=lambda path_str, max_chars: tools.read_file_safe(path_str, max_chars)
        ,
        required={"path_str"},
        defaults={"max_chars": 4000},
        arg_types={"path_str": str, "max_chars": int}
    ),
    "write_file": Tool(
        name="write_file",
        desc="Write content to a file (creates or overwrites) with optional backup",
        args={
            "path_str": "path of the file to write",
            "content": "content to write to the file",
            "backup": "whether to backup existing file (default: True)"
        },
        handler=lambda path_str, content, backup=True: tools.write_file_safe(path_str, content, backup),
        required={"path_str", "content"},
        defaults={"backup": True},
        arg_types={"path_str": str, "content": str, "backup": bool}
    ),
    "shell": Tool(
        name="shell",
        desc="Execute shell command with timeout",
        args={
            "command": "shell command to execute",
            "timeout": "timeout in seconds (default: 30.0)",
            "cwd": "working directory for command execution"
        },
        handler=lambda command, timeout=30.0, cwd=None: tools.shell_exec(command, timeout, cwd),
        required={"command"},
        defaults={"timeout": 30.0, "cwd": None},
        arg_types={"command": str, "timeout": (int, float), "cwd": (str, type(None))}
    ),
    "echo": Tool(
        name="echo",
        desc="Echo the input text",
        args={
            "text": "the text to echo"
        },
        handler=lambda text: tools.echo_safe(text),
        required={"text"},
        arg_types={"text": str}
    ),
    "http_get": Tool(
        name="http_get",
        desc="Send a HTTP GET request with timeout and basic error handling",
        args={
            "url": "the URL to send the GET request to",
            "timeout": "the timeout for the request in seconds (default: 10.0)"
        },
        handler=lambda url, timeout: tools.http_get(url, timeout),
        required={"url"},
        defaults={"timeout": 10.0},
        arg_types={"url": str, "timeout": (int, float)}
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
        handler=lambda **kwargs: code_fixer.fix_code_tool(**kwargs),
        defaults={
            "max_iterations": 3,
            "auto_run_tests": False,
            "iterate_until_passing": False,
            "write_back": False,
            "backup_original": True,
            "temperature": 0.1,
            "verbose": False
        },
        arg_types={
            "error_input": str,
            "code_context": str,
            "max_iterations": int,
            "auto_run_tests": bool,
            "test_command": str,
            "iterate_until_passing": bool,
            "write_back": bool,
            "file_path": str,
            "backup_original": bool,
            "api_key": str,
            "base_url": str,
            "model": str,
            "temperature": (int, float),
            "verbose": bool
        }
    )
}


def list_tools():
    return list(TOOLS.keys())


def _validate_args(tool: Tool, kwargs: Dict[str, Any]) -> Tuple[Dict[str, Any], Set[str]]:
    unknown = set(kwargs.keys()) - set(tool.args.keys())
    merged = {**tool.defaults, **kwargs}
    missing = tool.required - set(merged.keys())
    return merged, unknown.union(missing)


def _validate_types(tool: Tool, kwargs: Dict[str, Any]) -> Set[str]:
    invalid = set()
    for key, expected in tool.arg_types.items():
        if key not in kwargs:
            continue
        value = kwargs[key]
        if value is None:
            continue
        if isinstance(expected, tuple):
            if not isinstance(value, expected):
                invalid.add(key)
        else:
            if not isinstance(value, expected):
                invalid.add(key)
    return invalid


def run_tool(tool_name: str, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    tool = TOOLS[tool_name]
    merged, invalid_names = _validate_args(tool, kwargs)
    if invalid_names:
        raise ValueError(f"Invalid or missing arguments for tool {tool_name}: {sorted(list(invalid_names))}")
    invalid_types = _validate_types(tool, merged)
    if invalid_types:
        raise ValueError(f"Invalid argument types for tool {tool_name}: {sorted(list(invalid_types))}")
    return tool.handler(**merged)


def tools_specs():
    lines = []
    for tool in TOOLS.values():
        lines.append(f' - {tool.name}: {tool.desc} | args: {json.dumps(tool.args, ensure_ascii=False)}')
    return '\n'.join(lines)
