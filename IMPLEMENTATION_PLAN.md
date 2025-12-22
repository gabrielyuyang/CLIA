# CLIA命令行工具实现方案

## 🎯 目标

让CLIA能够直接在terminal中运行：
```bash
clia -q "五色花朵该怎么培育？" -t general
```

## 📋 实现步骤

### 1. 创建包安装配置

#### setup.py 文件
```python
"""
CLIA - An Efficient Minimalist CLI AI Agent
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="clia",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An Efficient Minimalist CLI AI Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/clia",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "clia=clia.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "clia": ["*.json", "*.yaml", "*.yml"],
    },
)
```

### 2. 重构项目结构

#### 新的目录结构
```
clia/
├── setup.py                    # 包安装配置
├── requirements.txt             # 依赖列表
├── README.md                  # 项目说明
├── .env.example              # 环境变量示例
├── clia/                    # 主包目录
│   ├── __init__.py          # 包初始化
│   ├── main.py              # 命令行入口
│   ├── config.py           # 配置管理
│   ├── utils.py            # 工具函数
│   ├── logger.py           # 日志管理
│   └── agents/            # Agent模块
│       ├── __init__.py
│       ├── llm.py         # LLM客户端
│       ├── prompts.py     # Prompt管理
│       └── history.py     # 历史记录
└── tests/                 # 测试文件
    └── test_clia.py
```

### 3. 创建包初始化文件

#### clia/__init__.py
```python
"""
CLIA - An Efficient Minimalist CLI AI Agent

A simple, efficient CLI tool for AI assistance with multiple task types.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .main import main
from .config import Settings

__all__ = ["main", "Settings", "__version__"]
```

### 4. 创建命令行入口

#### clia/main.py
```python
#!/usr/bin/env python3
"""
CLIA Main Entry Point

This module provides the main entry point for the CLI command.
"""

import argparse
import sys
from pathlib import Path

from .config import Settings
from .agents import llm, prompts
from .agents.history import History
from .utils import to_bool
import logging

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
Examples:
  clia -q "Hello, how are you?" -t general
  clia -q "Explain this Python code" -t explain
  clia -q "Generate a sorting algorithm" -t generate
  clia -q "Debug this error" -t debug
  clia -q "Fix this bug" -t fix
        """
    )
    
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
    
    return parser


def main():
    """Main entry point for the CLI application."""
    try:
        parser = create_parser()
        args = parser.parse_args()
        
        # 处理问题参数
        if isinstance(args.question, list):
            args.question = ' '.join(args.question)
        
        # 设置日志级别
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif args.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        
        # 如果不是quiet模式，显示欢迎信息
        if not args.quiet:
            print('-' * 28)
            print("Welcome to CLI AI Agent")
            print('-' * 28 + '\n')
        
        logger.info(f"User Query: {args.question}")
        logger.info(f"Task: {args.task}")
        
        # 加载配置
        settings = Settings.load_openai()
        logger.info(f"Settings loaded: model={settings.model}")
        
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
        system_prompt, few_shots = prompts.get_prompt(args.task)
        messages = [
            {"role": "system", "content": system_prompt},
            *few_shots,
            {"role": "user", "content": args.question}
        ]
        
        logger.info(f"Messages prepared for {args.task} task")
        
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
                print('-' * 28 + '\n')
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response.append(content)
            
            if not args.quiet:
                print('\n' + '-' * 28 + '\n')
        
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
```

### 5. 更新现有模块

#### 更新 config.py
```python
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from .utils import to_bool

# 加载环境变量
load_dotenv()

# 确保包根目录在Python路径中
package_root = Path(__file__).parent.parent
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))


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
```

#### 更新 agents/__init__.py
```python
"""
CLIA Agents Module

This module provides the core agent functionality including LLM integration,
prompt management, and conversation history.
"""

from .llm import openai_client
from .prompts import get_prompt
from .history import History

__all__ = ["openai_client", "get_prompt", "History"]
```

## 🚀 安装和使用步骤

### 1. 开发环境安装
```bash
# 在项目根目录下
cd 大模型/clia

# 安装为可编辑包
pip install -e .

# 或者使用开发模式安装
python setup.py develop
```

### 2. 生产环境安装
```bash
# 从GitHub安装
pip install git+https://github.com/your-repo/clia.git

# 或者从PyPI安装（如果发布到PyPI）
pip install clia
```

### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
# OPENAI_API_KEY=your_api_key_here
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=glm-4.6
```

### 4. 使用命令
```bash
# 基础用法
clia "五色花朵该怎么培育？" -t general

# 指定任务类型
clia "解释一下Python装饰器" -t explain

# 代码生成
clia "写一个快速排序算法" -t generate

# 启用流式输出
clia "介绍一下机器学习" --stream

# 保存历史记录
clia "帮我调试这段代码" -t debug --history conversation.jsonl

# 详细输出
clia "生成一个Web服务器" -t generate --verbose

# 静默模式
clia "修复这个bug" -t fix --quiet
```

## 🔧 高级配置

### 自定义配置文件
```bash
# 使用自定义配置文件
export CLIA_CONFIG_PATH=/path/to/config.yaml
clia "你的问题"
```

### 多模型支持
```bash
# 使用不同模型
clia "你的问题" --model=gpt-4
clia "你的问题" --model=claude-3-sonnet
```

## 🐛 故障排除

### 常见问题

1. **命令未找到**
   ```bash
   # 确保已正确安装
   pip install -e .
   
   # 检查PATH
   echo $PATH | grep python
   ```

2. **API密钥错误**
   ```bash
   # 检查环境变量
   echo $OPENAI_API_KEY
   
   # 重新加载环境变量
   source ~/.bashrc  # 或 ~/.zshrc
   ```

3. **模块导入错误**
   ```bash
   # 重新安装包
   pip uninstall clia
   pip install -e .
   ```

## 📋 测试

### 单元测试
```bash
# 运行测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_clia.py::test_main
```

### 集成测试
```bash
# 测试命令行接口
clia "测试问题" -t general --verbose

# 测试所有任务类型
for task in general explain generate debug fix; do
    echo "Testing $task task..."
    clia "测试 $task 任务" -t $task
done
```

## 📦 发布准备

### 构建包
```bash
# 构建源码包和wheel包
python setup.py sdist bdist_wheel

# 检查包
twine check dist/*
```

### 发布到PyPI
```bash
# 上传到测试PyPI
twine upload --repository testpypi dist/*

# 上传到正式PyPI
twine upload dist/*
```

---

这个实现方案将让你的CLIA成为一个真正的命令行工具，用户可以直接在terminal中使用 `clia` 命令。