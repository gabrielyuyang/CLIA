from typing import Any


def to_bool(value: Any, default: bool = False) -> bool:
    """
    将各种类型的值转换为布尔值

    Args:
        value: 要转换的值
        default: 默认值

    Returns:
        布尔值
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'y', 'yes', 'on')

    return default


def get_multiline_input() -> str:
    """获取多行输入, 直到遇到EOF"""
    # print("Enter your question with EOF as the endding:")
    lines = []
    while True:
        try:
            line = input()
            if line == "EOF":
                break
            lines.append(line)
        except EOFError:
            break
    print(lines)
    return "\n".join(lines)
