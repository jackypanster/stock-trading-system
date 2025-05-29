#!/usr/bin/env python3
"""
美股日内套利助手 - 主程序入口
US Stock Intraday Arbitrage Assistant

一个专注于美股市场的个人投资助手工具，通过程序化分析识别高波动股票的日内套利机会。

Usage:
    python main.py --help
    python main.py --version
    python main.py analyze TSLA
    python main.py signals --today
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import click


def main():
    """主程序入口"""
    try:
        # 初始化应用
        config, logger = _initialize_app()
        
        # 创建CLI应用
        from app.cli import create_cli_app
        cli_app = create_cli_app(config, logger)
        
        # 运行CLI应用
        cli_app()
        
    except KeyboardInterrupt:
        click.echo("\n👋 程序已退出")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ 程序启动失败: {e}", err=True)
        sys.exit(1)


def _initialize_app():
    """
    初始化应用配置和日志
    
    Returns:
        tuple: (config, logger)
    """
    try:
        # 加载配置
        from app.core.config import get_config
        config = get_config()
        
        # 设置日志
        from app.utils.logging import setup_logging
        logger = setup_logging(config)
        
        return config, logger
        
    except Exception as e:
        # 如果初始化失败，使用基本配置
        click.echo(f"⚠️  配置加载失败，使用默认配置: {e}", err=True)
        
        from app.utils.logging import setup_logging
        logger = setup_logging()
        
        return {}, logger


if __name__ == "__main__":
    main() 