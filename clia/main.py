import argparse
import sys
from pathlib import Path

from .config import Settings
from .agents import llm, prompts
from .agents.history import History
from .utils import get_multiline_input
import logging

COMMANDS = ('answer', 'explain', 'debug', 'fix', 'genarate')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="clia",
        description="An Efficient Minimalist CLI AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples: to-do
  """
    )

    # 添加默认参数
    parser.add_argument(
        'question',
        nargs='*',
        help='Question to ask the AI Agent')

    parser.add_argument(
        '--multiline', '-m',
        action='store_true',
        help='Enable multiline input')

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose mode'
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
        '--quiet',
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
    return parser


def parse_args() -> argparse.Namespace:
    parser = create_parser()
    sub_parsers = parser.add_subparsers(dest='command', required=False)

    # answer命令
    sub_parsers.add_parser(
        'answer',
        help='A Routine Q&A Assistant for General Tasks'
    )

    # explain命令
    sub_parsers.add_parser(
        'explain',
        help='Explain codes'
    )

    # debug命令
    sub_parsers.add_parser(
        'debug',
        help='Debug codes'
    )

    # fix命令
    sub_parsers.add_parser(
        'fix',
        help='Fix codes'
    )

    # generate命令
    sub_parsers.add_parser(
        'generate',
        help='Generate codes'
    )
    return parser.parse_args()


def main():
    """Main entry point for the CLI application."""
    try:
        args = parse_args()
        print(args)

        if not args.command:
            args.command = 'answer'

        if args.multiline:
            print('++++entering')
            question = ' '.join(args.question) + '\n' + get_multiline_input()
        else:
            question = ' '.join(args.question)

        # 设置日志级别
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.quiet:
            logging.getLogger().setLevel(logging.WARNING)

        # 如果不是quiet模式，显示欢迎信息
        if not args.quiet:
            print('-' * 28)
            print("Welcome to CLI AI Agent")
            print('-' * 28)

        logger.info(f"User Query: {question}")

        # 加载配置
        settings = Settings.load_openai()
        logger.info(f"Settings loaded: {settings}")

        # 应用命令行参数覆盖
        model = args.model or settings.model
        stream = args.stream or settings.stream
        temperature = args.temperature or settings.temperature
        top_p = args.top_p or settings.top_p
        max_retries = args.max_retries or settings.max_retries

        # 创建LLM客户端
        client = llm.openai_client(
            api_key=settings.api_key,
            base_url=settings.base_url,
            max_retries=max_retries
        )

        # 获取任务特定的prompt
        system_prompt, few_shots = prompts.get_prompt(args.command)
        messages = [
            {"role": "system", "content": system_prompt},
            *few_shots,
            {"role": "user", "content": question}
        ]

        logger.info(f"Messages prepared for {args.command} command: {messages}")

        # 调用LLM API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=settings.frequency_penalty,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout_seconds
        )

        # 处理响应
        full_response = []

        if not stream:
            # 非流式输出
            content = response.choices[0].message.content
            full_response.append(content)
            print(content)
        else:
            # 流式输出
            if not args.quiet:
                print('-' * 28)

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response.append(content)

            if not args.quiet:
                print('\n' + '-' * 28)

        # 保存历史记录
        if not args.no_history and args.history:
            history = History([
                {"role": "user", "content": args.question},
                {"role": "assistant", "content": ''.join(full_response)}
            ])
            history.save_jsonl(Path(args.history))
            logger.info(f"History saved to {args.history}")

        logger.info("Request completed successfully")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        if not args.quiet:
            print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
