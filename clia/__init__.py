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