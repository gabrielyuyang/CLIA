from agents import llm
from config import Settings
from utils import to_bool
import argparse
import logging


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="An Minimalist CLI AI Agent")
    parser.add_argument('--question', '-q', required=True, help="Question to ask Agent")
    parser.add_argument('--task', '-t', choices=['general', 'explain', 'generate', 'debug', 'fix'], default='general', help="Task to perform")
    parser.add_argument('--model', default=None, help="Model to override the default")
    parser.add_argument('--stream', default=False, help="Streaming the answer")
    parser.add_argument('--temperature', default=None, help="Temperature to override the default")
    parser.add_argument('--top_p', default=None, help="Top P to override the default")
    parser.add_argument('--max_retries', default=None, help="Max retries to override the default")
    parser.add_argument('--format', '-f', choices=['markdown', 'json', 'text'], default='markdown', help="Format of the answer")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger.info(f"User Query: {args}")

    settings = Settings.load_openai()
    logger.info(f"Initial Settings: {settings}")
    model = args.model or settings.model
    stream = to_bool(args.stream) or settings.stream
    temperature = args.temperature or settings.temperature
    top_p = args.top_p or settings.top_p
    max_retries = args.max_retries or settings.max_retries
    logger.info(
        f"Final Settings: model={model},\
        stream={stream},\
        temperature={temperature},\
        top_p={top_p},\
        max_retries={max_retries}"
        )

    client = llm.openai_client(
        api_key=settings.api_key,
        base_url=settings.base_url,
        max_retries=max_retries
        )
    message = [{"role": "user", "content": args.question}]
    logger.info(f"Message: {message}")

    response = client.chat.completions.create(
        model=model,
        messages=message,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        )
    logger.info(f"Response: {response.choices[0].message.content}")
