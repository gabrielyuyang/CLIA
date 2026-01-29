import argparse
import logging
import sys
from pathlib import Path

from .agents.history import History
from .agents.memory import MemoryManager
from .agents.chat_agent import chat_agent
from .agents.plan_build_agent import plan_build
from .agents.react_agent import react_agent
from .agents.llm_compiler_agent import llm_compiler_agent
from .agents.rewoo_agent import rewoo_agent
from .agents.tot_agent import tot_agent
from .agents.reflection import (
    reflect_react_agent,
    reflect_llm_compiler_agent,
    reflect_plan_build_agent,
    reflect_rewoo_agent,
    reflect_tot_agent
)
from .config import Settings
from .utils import get_multiline_input

COMMANDS = ("ask", "explain", "debug", "fix", "generate")

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
            help="Enable multiline input with 'EOF' as ending",
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

        # 输出格式
        command_parser.add_argument(
            "--output-format",
            choices=["markdown", "json", "text"],
            default="markdown",
            help="Output format (default: markdown)",
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
            choices=["chat", "plan-build", "react", "llm-compiler", "rewoo", "tot"],
            default="chat",
            help="Agent architecture to use: 'chat' (default, direct Q&A), 'plan-build', 'react' (ReAct pattern), 'llm-compiler' (parallel execution), 'rewoo' (ReWOO pattern), or 'tot' (Tree-of-Thoughts)"
        )

        command_parser.add_argument(
            "--max-iterations",
            type=int,
            default=10,
            help="Maximum iterations for ReAct agent (default: 10)"
        )

        # Tree-of-Thoughts specific arguments
        command_parser.add_argument(
            "--max-depth",
            type=int,
            default=3,
            help="Maximum depth for Tree-of-Thoughts agent (default: 3)"
        )

        command_parser.add_argument(
            "--branching-factor",
            type=int,
            default=3,
            help="Branching factor for Tree-of-Thoughts agent (default: 3)"
        )

        command_parser.add_argument(
            "--beam-width",
            type=int,
            default=2,
            help="Beam width for Tree-of-Thoughts agent (default: 2)"
        )

        # Memory management options
        command_parser.add_argument(
            "--memory-path",
            type=Path,
            help="Path to memory storage file (enables memory management)"
        )

        command_parser.add_argument(
            "--enable-memory",
            action="store_true",
            help="Enable memory management (uses default memory path)"
        )

        command_parser.add_argument(
            "--memory-limit",
            type=int,
            default=100,
            help="Maximum number of memories before summarization (default: 100)"
        )

        command_parser.add_argument(
            "--no-memory-summarization",
            action="store_true",
            help="Disable automatic memory summarization"
        )

        command_parser.add_argument(
            "--memory-context-limit",
            type=int,
            default=3,
            help="Maximum number of relevant memories to include in context (default: 3)"
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
        if args.quiet:
            logging.disable(logging.CRITICAL)
        elif args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        # 如果不是quiet模式，显示欢迎信息
        if not args.quiet:
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
        if args.quiet:
            stream = False
        temperature = args.temperature or settings.temperature
        top_p = args.top_p or settings.top_p
        max_retries = args.max_retries or settings.max_retries

        # Initialize memory manager if enabled
        memory_manager = None
        if args.enable_memory or args.memory_path:
            memory_path = args.memory_path or Path("clia/memories/memory.jsonl")
            try:
                memory_manager = MemoryManager(
                    memory_path=memory_path,
                    max_memories=args.memory_limit,
                    enable_summarization=not args.no_memory_summarization,
                    api_key=settings.api_key,
                    base_url=settings.base_url,
                    model=model,
                    max_retries=max_retries,
                    timeout=settings.timeout_seconds
                )
                logger.info(f"Memory management enabled: {memory_path}")
            except Exception as e:
                logger.warning(f"Failed to initialize memory manager: {e}")
                memory_manager = None

        # 选择agent架构
        execution_metadata = None
        if args.agent == "chat":
            logger.info("Using Chat agent architecture")
            result = chat_agent(
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
                return_metadata=args.with_reflection,
                memory_manager=memory_manager
            )
            if args.with_reflection:
                full_response, execution_metadata = result
            else:
                full_response = result
        elif args.agent == "rewoo":
            logger.info("Using ReWOO agent architecture")
            result = rewoo_agent(
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
                return_metadata=args.with_reflection,
                memory_manager=memory_manager
            )
            if args.with_reflection:
                full_response, execution_metadata = result
            else:
                full_response = result
        elif args.agent == "react":
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
                return_metadata=args.with_reflection,
                memory_manager=memory_manager
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
                return_metadata=args.with_reflection,
                memory_manager=memory_manager
            )
            if args.with_reflection:
                full_response, execution_metadata = result
            else:
                full_response = result
        elif args.agent == "tot":
            logger.info("Using Tree-of-Thoughts agent architecture")
            result = tot_agent(
                question=question,
                command=args.command,
                max_depth=args.max_depth,
                branching_factor=args.branching_factor,
                beam_width=args.beam_width,
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
                return_metadata=args.with_reflection,
                memory_manager=memory_manager
            )
            if args.with_reflection:
                full_response, execution_metadata = result
            else:
                full_response = result
        else:
            logger.info("Using Plan-Build agent architecture")
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
                return_metadata=args.with_reflection,
                memory_manager=memory_manager
            )
            if args.with_reflection:
                full_response, execution_metadata = result
            else:
                full_response = result

        # Print final agent output (non-streaming)
        if not stream:
            print(str(full_response))

        # Generate reflection if requested
        if args.with_reflection and execution_metadata:
            logger.info("\n" + "=" * 60)
            logger.info("Generating Reflection...")
            logger.info("=" * 60)

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
                elif args.agent == "rewoo":
                    reflection = reflect_rewoo_agent(
                        question=question,
                        plan=execution_metadata.get("plan", []),
                        execution_results=execution_metadata.get("execution_results", {}),
                        final_answer=final_answer_str,
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
                elif args.agent == "tot":
                    reflection = reflect_tot_agent(
                        question=question,
                        all_thoughts=execution_metadata.get("all_thoughts", []),
                        final_thoughts=execution_metadata.get("final_thoughts", []),
                        final_answer=final_answer_str,
                        thoughts_explored=execution_metadata.get("thoughts_explored", 0),
                        final_paths=execution_metadata.get("final_paths", 0),
                        max_depth=args.max_depth,
                        branching_factor=args.branching_factor,
                        beam_width=args.beam_width,
                        best_score=max([t.get("score", 0) for t in execution_metadata.get("final_thoughts", [])], default=0.0),
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
        if args.history:
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
        # Check if args exists before accessing args.quiet
        try:
            if not args.quiet:
                print(f"\nError: {e}")
        except NameError:
            # args not defined yet, print error anyway
            print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
