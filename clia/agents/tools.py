from pathlib import Path
import httpx


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
