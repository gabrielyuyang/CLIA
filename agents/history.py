from typing import List, Dict, Literal
from pathlib import Path
import logger
import json

Role = Literal["system", "user", "assistant"]
Message = List[Dict[Role, str]]
logger = logger.logger


class History:
    def __init__(self, messages: Message = []) -> None:
        self._messages: Message = messages

    def save_jsonl(self, path: Path) -> None:
        if not self._messages:
            logger.error("No messages to save.")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as f:
            f.write(
                '\n'.join([json.dumps(msg, ensure_ascii=False)
                           for msg in self._messages])
                + '\n'
                )
            logger.info(f"Saved {len(self._messages)} messages to {path}.")
        return
