"""
日志设置工具模块

提供统一的日志配置和初始化功能。
"""

import sys
import logging
from pathlib import Path


def setup_logging(config=None, debug=False):
    """
    设置日志系统
    
    Args:
        config: 配置对象（ConfigLoader实例或字典）
        debug: 是否启用调试模式
        
    Returns:
        logger: 配置好的日志器
    """
    # 创建logs目录
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # 确定日志级别
    if debug:
        log_level = 'DEBUG'
    elif config:
        # 处理ConfigLoader对象
        if hasattr(config, 'get'):
            log_level = config.get('logging.level', 'INFO')
        # 处理字典配置
        elif isinstance(config, dict) and config.get('logging', {}).get('level'):
            log_level = config['logging']['level']
        else:
            log_level = 'INFO'
    else:
        log_level = 'INFO'
    
    # 确定日志格式
    if config:
        # 处理ConfigLoader对象
        if hasattr(config, 'get'):
            log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # 处理字典配置
        elif isinstance(config, dict) and config.get('logging', {}).get('format'):
            log_format = config['logging']['format']
        else:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    else:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / "trading_assistant.log")
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # 导入版本信息
    try:
        from .. import __version__
        logger.info(f"美股日内套利助手 v{__version__} 启动")
    except ImportError:
        logger.info("美股日内套利助手启动")
    
    return logger 