import os
import sys
from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path


load_dotenv()
root = Path(__name__).parent.parent
if root not in sys.path:
    sys.path.insert(0, str(root))


@dataclass
class Settings:
    api_key: str
    url_base: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    max_retries: int
    top_p: float
    frequency_penalty: float

    @classmethod
    def load_openai(cls):
        """
        Docstring for load_openai
        1. 只有API_KEY是必须提供的, 其他参数都有默认值, 可以不提供
        2. 有些API代理服务是使用API_AUTH_TOKEN的, 此时需要同步修改.env以及这里的api_key -> api_auth_token

        :param cls: class_method
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY not set')
        return cls(
            api_key=api_key,
            url_base=os.getenv('OPENAI_URL_BASE', 'https://api.openai.com/v1'),
            model=os.getenv('OPENAI_MODEL', 'glm-4.6'),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', 0.0)),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', 4096)),
            timeout_seconds=int(os.getenv('OPENAI_TIMEOUT_SECONDS', 30)),
            max_retries=int(os.getenv('OPENAI_MAX_RETRIES', 10)),
            top_p=float(os.getenv('OPENAI_TOP_P', 7)),
            frequency_penalty=float(os.getenv('OPENAI_FREQUENCY_PENALTY', 0))
        )


if __name__ == '__main__':
    print(Settings.load_openai())
