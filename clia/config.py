import os
from dataclasses import dataclass
from dotenv import load_dotenv
from .utils import to_bool


load_dotenv()

@dataclass
class Settings:
    """Configuration settings for CLIA."""

    api_key: str
    base_url: str
    model: str
    temperature: float
    stream: bool
    max_tokens: int
    timeout_seconds: int
    max_retries: int
    top_p: float
    frequency_penalty: float

    @classmethod
    def load_openai(cls):
        """Load OpenAI settings from environment variables."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY not set in environment variables')

        return cls(
            api_key=api_key,
            base_url=os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            model=os.getenv('OPENAI_MODEL', 'glm-4.6'),
            stream=to_bool(os.getenv('OPENAI_STREAM', 'False')),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.0')),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '4096')),
            max_retries=int(os.getenv('OPENAI_MAX_RETRIES', '5')),
            timeout_seconds=int(os.getenv('OPENAI_TIMEOUT_SECONDS', '30')),
            top_p=float(os.getenv('OPENAI_TOP_P', '0.85')),
            frequency_penalty=float(os.getenv('OPENAI_FREQUENCY_PENALTY', '0'))
        )


if __name__ == '__main__':
    print(Settings.load_openai())
