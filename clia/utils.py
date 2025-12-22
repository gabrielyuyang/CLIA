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
