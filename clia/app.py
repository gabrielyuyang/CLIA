from agents import llm, prompts
from agents.history import History
from pathlib import Path
from config import Settings
from utils import to_bool
import argparse
import logger

logger = logger.logger


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="clia",
        description="An Efficient Minimalist CLI AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  clia -q "Hello, how are you?" -t general
  clia -q "Explain this Python code" -t explain
  clia -q "Generate a sorting algorithm" -t generate
  clia -q "Debug this error" -t debug
  clia -q "Fix this bug" -t fix
  """
    )
    return parser
        

def parse_args() -> argparse.Namespace:
    parser = create_parser()
    # parser.add_argument('--question', '-q', required=True, help="Question to ask Agent")
    # parser.add_argument('--task', '-t', choices=['general', 'explain', 'generate', 'debug', 'fix'], default='general', help="Task to perform")
    # parser.add_argument('--model', default=None, help="Model to override the default")
    # parser.add_argument('--stream', default=False, help="Streaming the answer")
    # parser.add_argument('--temperature', default=0, help="Temperature to override the default")
    # parser.add_argument('--top_p', default=0.85, help="Top P to override the default")
    # parser.add_argument('--max_retries', default=5, help="Max retries to override the default")
    # parser.add_argument('--format', '-f', choices=['markdown', 'json', 'text'], default='markdown', help="Format of the answer")
    # parser.add_argument('--history', default=None, help="Designate the history file")   
    
    # 主要参数
    parser.add_argument(
        'question', 
        nargs='+',
        help='Question to ask the AI Agent'
    )
    
    parser.add_argument(
        '-t', '--task',
        choices=['general', 'explain', 'generate', 'debug', 'fix'],
        default='general',
        help='Task type to perform (default: general)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['markdown', 'json', 'text'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    # 模型参数
    parser.add_argument(
        '--model',
        help='Model to override the default'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        help='Temperature to override the default'
    )
    
    parser.add_argument(
        '--top_p',
        type=float,
        help='Top P to override the default'
    )
    
    parser.add_argument(
        '--max_retries',
        type=int,
        help='Max retries to override the default'
    )
    
    # 输出控制
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Enable streaming output'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )
    
    # 历史记录
    parser.add_argument(
        '--history',
        help='Path to save conversation history'
    )
    
    parser.add_argument(
        '--no-history',
        action='store_true',
        help='Disable history saving'
    )

    return parser.parse_args()


if __name__ == "__main__":
    print('-' * 28)
    print("Welcome to the CLI AI Agent")
    print('-' * 28)
    args = parse_args()
    logger.info(f"User Query:\n{args}\n")

    settings = Settings.load_openai()
    logger.info(f"Initial Settings:\n{settings}\n")
    model = args.model or settings.model
    stream = to_bool(args.stream) or settings.stream
    temperature = float(args.temperature) or settings.temperature
    top_p = float(args.top_p) or settings.top_p
    max_retries = int(args.max_retries) or settings.max_retries
    logger.info(
        f"Final Settings:\nmodel={model},\
        stream={stream},\
        temperature={temperature},\
        top_p={top_p},\
        max_retries={max_retries}\n"
        )

    client = llm.openai_client(
        api_key=settings.api_key,
        base_url=settings.base_url,
        max_retries=max_retries
        )

    system_prompt, few_shorts = prompts.get_prompt(args.task)
    message = [
        {
            "role": "system",
            "content": system_prompt
        },
        *few_shorts,
        {
            "role": "user",
            "content": args.question
        }
    ]
    logger.info(f"Message:\n{message}")
    print('-' * 28 + '\n')

    response = client.chat.completions.create(
        model=model,
        messages=message,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=settings.frequency_penalty,
        max_tokens=settings.max_tokens,
        timeout=settings.timeout_seconds
        )

    full_response = []
    if not stream:
        full_response.append(response.choices[0].message.content)
        logger.info(f"Response:\n{''.join(full_response)}")
    else:
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
                full_response.append(chunk.choices[0].delta.content)
        print('\n' + '-' * 28 + '\n')
        logger.info(f"Response:\n{''.join(full_response)}")

    if args.history:
        history = History(
            [
                message[-1],
                {
                    "role": "assistant",
                    "content": full_response
                }
            ]
        )
        history.save_jsonl(Path(args.history))
