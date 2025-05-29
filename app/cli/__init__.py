"""
CLI命令处理模块

提供统一的CLI命令处理框架和具体的命令处理器实现。
"""

from .base import (
    BaseCommandHandler,
    AnalysisCommandHandler, 
    ConfigCommandHandler,
    CommandResult,
    OutputFormatter
)
from .analyze_handler import AnalyzeCommandHandler
from .signals_handler import SignalsCommandHandler
from .router import create_cli_app

__all__ = [
    'BaseCommandHandler',
    'AnalysisCommandHandler',
    'ConfigCommandHandler', 
    'CommandResult',
    'OutputFormatter',
    'AnalyzeCommandHandler',
    'SignalsCommandHandler',
    'create_cli_app'
]
