from pathlib import Path
from typing import Optional
import httpx
import subprocess
import shutil


def read_file_safe(path_str: str, max_chars: int = 4000) -> str:
    "Read local file safely with size limit"
    path = Path(path_str).expanduser().resolve()
    if not path.exists() or not path.is_file():
        return f"[File {path_str} not found]"
    with path.open('r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        if len(content) > max_chars:
            return f"[File {path_str} is too large]"
        return content


def echo_safe(text: str, max_chars: int = 4000) -> str:
    "Echo text safely with size limit"
    if len(text) > max_chars:
        return f"[Text is too large]"
    return text


def http_get(url: str, timeout: float = 10.0) -> str:
    "Simple HTTP GET request with timeout and basic error handling"
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except httpx.TimeoutException as e:
        return f"[HTTP GET timeout: {e}]"
    except httpx.HTTPStatusError as e:
        return f"[HTTP GET status error: {e}]"
    except httpx.RequestError as e:
        return f"[HTTP GET request error: {e}]"
    except httpx.ConnectError as e:
        return f"[HTTP GET connection error: {e}]"
    except Exception as e:
        return f"[HTTP GET error: {e}]"


def write_file_safe(path_str: str, content: str, backup: bool = True) -> str:
    "Write content to file with optional backup"
    try:
        path = Path(path_str).expanduser().resolve()

        # Create backup if file exists and backup is enabled
        if backup and path.exists():
            backup_path = path.with_suffix(path.suffix + '.bak')
            shutil.copy2(path, backup_path)

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        with path.open('w', encoding='utf-8') as f:
            f.write(content)

        return f"[File written successfully to {path_str}]"
    except Exception as e:
        return f"[Error writing file {path_str}: {e}]"


def shell_exec(command: str, timeout: float = 30.0, cwd: Optional[str] = None) -> str:
    "Execute shell command with timeout"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        output = result.stdout + result.stderr
        return output if output else "[Command executed successfully with no output]"
    except subprocess.TimeoutExpired:
        return f"[Command timeout after {timeout}s]"
    except Exception as e:
        return f"[Shell execution error: {e}]"
