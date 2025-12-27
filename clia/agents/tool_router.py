import json
from clia.agents import tools
from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class Tool:
    name: str
    desc: str
    schema: Dict[str, str]
    handler: Callable[..., str]
    

TOOLS = {
    "read_file": Tool(
        name="read_file",
        desc="Read a local file with size limit",
        schema={
            "path_str": "path of the file to read",
            "max_chars": "maximum number of characters to read"
        },
        handler=lambda path_str, max_chars: tools.read_file_safe(path_str, max_chars)
    ),
    "echo": Tool(
        name="echo",
        desc="Echo the input text",
        schema={
            "text": "the text to echo"
        },
        handler=lambda text: tools.echo(text)
    ),
    "http_get": Tool(
        name="http_get",
        desc="Send a HTTP GET request with timeout and basic error handling",
        schema={
            "url": "the URL to send the GET request to",
            "timeout": "the timeout for the request in seconds"
        },
        handler=lambda url, timeout: tools.http_get(url, timeout)
    )
}


def list_tools():
    return list(TOOLS.keys())


def run_tool(tool_name: str, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    if not any(k in TOOLS[tool_name].schema for k in kwargs):
        raise ValueError(f"Unknown arguments for tool {tool_name}: {TOOLS[tool_name].schema}")
    return TOOLS[tool_name].handler(**kwargs)

def tools_specs():
    lines = []
    for tool in TOOLS.values():
        lines.append(f' - {tool.name}: {tool.desc} | args: {json.dumps(tool.schema, ensure_ascii=False)}')
    return '\n'.join(lines)