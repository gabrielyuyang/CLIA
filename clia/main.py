import argparse
import logging
import sys
from pathlib import Path

from .agents.history import History
from .agents.plan_build_agent import plan_build
from .agents.react_agent import react_agent
from .agents.llm_compiler_agent import llm_compiler_agent
from .agents.reflection import (
    reflect_react_agent,
    reflect_llm_compiler_agent,
    reflect_plan_build_agent
)
from .config import Settings
from .utils import get_multiline_input

COMMANDS = ("ask", "explain", "debug", "fix", "genarate")

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
  """,
    )
    return parser


def parse_args() -> argparse.ArgumentParser:
    parser = create_parser()
    sub_parsers = parser.add_subparsers(dest="command", required=True)

    PARSER_DICT = {
        # ask命令
        "ask_parser": sub_parsers.add_parser(
            "ask", help="A Routine Q&A Assistant for General Tasks"),
        # draft命令
        "draft_parser": sub_parsers.add_parser(
            "draft", help="Parse user spec"),
        # explain命令
        "explain_parser": sub_parsers.add_parser(
            "explain", help="Explain codes"),
        # debug命令
        "debug_parser": sub_parsers.add_parser(
            "debug", help="Debug codes"),
        # fix命令
        "fix_parser": sub_parsers.add_parser(
            "fix", help="Fix codes"),
        # generate命令
        "generate_parser": sub_parsers.add_parser(
            "generate", help="Generate codes"),
    }

    # 添加通用参数
    for command_parser in PARSER_DICT.values():
        # 默认参数
        command_parser.add_argument(
            "question", nargs="*", help="Question to ask the AI Agent"
        )

        command_parser.add_argument(
            "--multiline",
            "-m",
            action="store_true",
            help="Enable multiline input with 'EOF' as endding",
        )

        command_parser.add_argument(
            "--verbose", "-v", action="store_true", help="Enable verbose mode"
        )

        command_parser.add_argument(
            "--file", type=Path, help="Path to the file for codes or specs"
        )

        # 模型参数
        command_parser.add_argument("--model", help="Model to override the default")

        command_parser.add_argument(
            "--temperature", type=float, help="Temperature to override the default"
        )

        command_parser.add_argument(
            "--top_p", type=float, help="Top P to override the default"
        )

        command_parser.add_argument(
            "--max_retries", type=int, help="Max retries to override the default"
        )

        # 输出控制
        command_parser.add_argument(
            "--stream", action="store_true", help="Enable streaming output"
        )

        command_parser.add_argument(
            "--quiet", action="store_true", help="Suppress non-essential output"
        )

        # 历史记录
        command_parser.add_argument(
            "--history", help="Path to save conversation history"
        )

        command_parser.add_argument(
            "--no-history", action="store_true", help="Disable history saving"
        )

        # 输出格式
        command_parser.add_argument(
            "--output-format",
            choices=["markdown", "json", "text"],
            default="markdown",
            help="Output format (default: markdown)",
        )

        # 校准模式
        command_parser.add_argument(
            "--with-calibration", action="store_true", help="Enable calibration mode"
        )

        # 输入模式
        command_parser.add_argument(
            "--with-interaction", action="store_true", help="Enable interaction mode"
        )

        # Reflection模式
        command_parser.add_argument(
            "--with-reflection", action="store_true", help="Enable reflection mode - agent will self-critique its performance"
        )

        # Agent模式选择
        command_parser.add_argument(
            "--agent",
            choices=["plan-build", "react", "llm-compiler"],
            default="plan-build",
            help="Agent architecture to use: 'plan-build' (default), 'react' (ReAct pattern), or 'llm-compiler' (parallel execution)"
        )

        command_parser.add_argument(
            "--max-iterations",
            type=int,
            default=10,
            help="Maximum iterations for ReAct agent (default: 10)"
        )
    return parser.parse_args()


def main():
    """Main entry point for the CLI application."""
    try:
        args = parse_args()

        if args.multiline:
            question = " ".join(args.question) + "\n" + get_multiline_input()
        else:
            question = " ".join(args.question)

        # 设置日志级别
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.quiet:
            logging.getLogger().setLevel(logging.WARNING)

        # 如果不是quiet模式，显示欢迎信息
        print("-" * 28)
        print("Welcome to CLI AI Agent")
        print("-" * 28 + "\n")

        logger.info(f"User Query: {question}")
        logger.info(f"Command line arguments: {args}")

        # 加载配置
        settings = Settings.load_openai()
        logger.info(f"Settings loaded: {settings}")

        # 应用命令行参数覆盖
        model = args.model or settings.model
        stream = args.stream or settings.stream
        temperature = args.temperature or settings.temperature
        top_p = args.top_p or settings.top_p
        max_retries = args.max_retries or settings.max_retries

        # 选择agent架构
        execution_metadata = None
        if args.agent == "react":
            logger.info("Using ReAct agent architecture")
            result = react_agent(
                question=question,
                command=args.command,
                max_iterations=args.max_iterations,
                api_key=settings.api_key,
                base_url=settings.base_url,
                max_retries=max_retries,
                model=model,
                stream=stream,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=settings.frequency_penalty,
                max_tokens=settings.max_tokens,
                timeout=settings.timeout_seconds,
                verbose=args.verbose,
                return_metadata=args.with_reflection
            )
            if args.with_reflection:
                full_response, execution_metadata = result
            else:
                full_response = result
        elif args.agent == "llm-compiler":
            logger.info("Using LLMCompiler agent architecture")
            result = llm_compiler_agent(
                question=question,
                command=args.command,
                api_key=settings.api_key,
                base_url=settings.base_url,
                max_retries=max_retries,
                model=model,
                stream=stream,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=settings.frequency_penalty,
                max_tokens=settings.max_tokens,
                timeout=settings.timeout_seconds,
                verbose=args.verbose,
                return_metadata=args.with_reflection
            )
            if args.with_reflection:
                full_response, execution_metadata = result
                full_response = [full_response]
            else:
                full_response = result
                # LLMCompiler returns a string, wrap it in a list for consistency
                if isinstance(full_response, str):
                    full_response = [full_response]
        else:
            logger.info("Using Plan-Build agent architecture")
            # TO-DO: 添加支持with_calibration参数
            result = plan_build(
                question=question,
                command=args.command,
                max_steps=5,
                api_key=settings.api_key,
                base_url=settings.base_url,
                max_retries=max_retries,
                model=model,
                stream=stream,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=settings.frequency_penalty,
                max_tokens=settings.max_tokens,
                timeout=settings.timeout_seconds,
                return_metadata=args.with_reflection
            )
            if args.with_reflection:
                full_response, execution_metadata = result
                full_response = [full_response]
            else:
                full_response = result
                if isinstance(full_response, str):
                    full_response = [full_response]

        # Generate reflection if requested
        if args.with_reflection and execution_metadata:
            logger.info("\n" + "=" * 60)
            logger.info("Generating Reflection...")
            logger.info("=" * 60)

            # Handle both string and list responses for final answer
            if isinstance(full_response, list):
                final_answer_str = "".join(full_response)
            else:
                final_answer_str = str(full_response)

            try:
                if args.agent == "react":
                    reflection = reflect_react_agent(
                        question=question,
                        conversation_history=execution_metadata.get("conversation_history", []),
                        final_answer=final_answer_str,
                        iterations_used=execution_metadata.get("iterations_used", 0),
                        max_iterations=execution_metadata.get("max_iterations", args.max_iterations),
                        api_key=settings.api_key,
                        base_url=settings.base_url,
                        max_retries=max_retries,
                        model=model,
                        temperature=temperature,
                        top_p=top_p,
                        frequency_penalty=settings.frequency_penalty,
                        max_tokens=settings.max_tokens,
                        timeout=settings.timeout_seconds,
                        verbose=args.verbose
                    )
                elif args.agent == "llm-compiler":
                    reflection = reflect_llm_compiler_agent(
                        question=question,
                        plan=execution_metadata.get("plan", []),
                        execution_results=execution_metadata.get("execution_results", {}),
                        final_answer=final_answer_str,
                        plan_valid=True,  # Assume valid if we got here
                        api_key=settings.api_key,
                        base_url=settings.base_url,
                        max_retries=max_retries,
                        model=model,
                        temperature=temperature,
                        top_p=top_p,
                        frequency_penalty=settings.frequency_penalty,
                        max_tokens=settings.max_tokens,
                        timeout=settings.timeout_seconds,
                        verbose=args.verbose
                    )
                else:  # plan-build
                    reflection = reflect_plan_build_agent(
                        question=question,
                        plan=execution_metadata.get("plan", []),
                        execution_results=execution_metadata.get("execution_results", []),
                        final_answer=final_answer_str,
                        steps_executed=execution_metadata.get("steps_executed", 0),
                        max_steps=execution_metadata.get("max_steps", 5),
                        api_key=settings.api_key,
                        base_url=settings.base_url,
                        max_retries=max_retries,
                        model=model,
                        temperature=temperature,
                        top_p=top_p,
                        frequency_penalty=settings.frequency_penalty,
                        max_tokens=settings.max_tokens,
                        timeout=settings.timeout_seconds,
                        verbose=args.verbose
                    )

                # Print reflection
                if not args.quiet:
                    print("\n" + "=" * 60)
                    print("REFLECTION")
                    print("=" * 60)
                    print(str(reflection))
                    print("=" * 60 + "\n")

                logger.info("Reflection generated successfully")
            except Exception as e:
                logger.error(f"Failed to generate reflection: {e}")
                if args.verbose:
                    print(f"\nWarning: Reflection generation failed: {e}\n")

        # 保存历史记录
        if not args.no_history and args.history:
            # Handle both string and list responses
            if isinstance(full_response, list):
                response_content = "".join(full_response)
            else:
                response_content = str(full_response)
            history = History(
                [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": response_content},
                ]
            )
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
