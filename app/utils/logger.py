"""
日志管理模块
Logging Management Module

提供统一的日志配置和管理功能。
支持结构化日志、多种输出格式、日志轮转等功能。
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

# 支持结构化日志的格式化器
class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基础日志信息
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # 添加位置信息
        if record.pathname:
            log_entry['file'] = {
                'path': record.pathname,
                'line': record.lineno,
                'function': record.funcName
            }
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class TradingLogger:
    """交易系统日志管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志管理器
        
        Args:
            config: 日志配置字典
        """
        default_config = self._get_default_config()
        if config:
            # 深度合并配置
            self.config = self._merge_configs(default_config, config)
        else:
            self.config = default_config
        self._setup_logging()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认日志配置"""
        return {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'files': {
                'main': 'logs/trading_assistant.log',
                'errors': 'logs/errors.log',
                'trades': 'logs/trades.log'
            },
            'rotation': {
                'max_size': '10MB',
                'backup_count': 5
            },
            'structured': False,
            'colored_console': True
        }
    
    def _merge_configs(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并配置字典
        
        Args:
            default: 默认配置
            custom: 自定义配置
            
        Returns:
            合并后的配置
        """
        merged = default.copy()
        for key, value in custom.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def _setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        self._create_log_directories()
        
        # 获取根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config['level'].upper()))
        
        # 清除已有的处理器
        root_logger.handlers.clear()
        
        # 添加控制台处理器
        self._add_console_handler(root_logger)
        
        # 添加文件处理器
        self._add_file_handlers(root_logger)
        
        # 设置第三方库日志级别
        self._configure_third_party_loggers()
    
    def _create_log_directories(self):
        """创建日志目录"""
        for log_file in self.config['files'].values():
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _add_console_handler(self, logger: logging.Logger):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        
        if self.config.get('colored_console', True):
            formatter = ColoredConsoleFormatter(self.config['format'])
        else:
            formatter = logging.Formatter(self.config['format'])
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handlers(self, logger: logging.Logger):
        """添加文件处理器"""
        # 主日志文件
        main_handler = self._create_rotating_handler(
            self.config['files']['main'],
            level=logging.DEBUG
        )
        logger.addHandler(main_handler)
        
        # 错误日志文件
        error_handler = self._create_rotating_handler(
            self.config['files']['errors'],
            level=logging.ERROR
        )
        logger.addHandler(error_handler)
        
        # 交易日志文件
        trade_handler = self._create_rotating_handler(
            self.config['files']['trades'],
            level=logging.INFO
        )
        # 设置过滤器，仅记录交易相关日志
        trade_handler.addFilter(lambda record: 'trade' in record.name.lower())
        logger.addHandler(trade_handler)
    
    def _create_rotating_handler(self, filename: str, level: int) -> logging.Handler:
        """创建轮转文件处理器"""
        # 解析最大文件大小
        max_size = self._parse_size(self.config['rotation']['max_size'])
        
        handler = logging.handlers.RotatingFileHandler(
            filename=filename,
            maxBytes=max_size,
            backupCount=self.config['rotation']['backup_count'],
            encoding='utf-8'
        )
        
        handler.setLevel(level)
        
        # 设置格式化器
        if self.config.get('structured', False):
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(self.config['format'])
        
        handler.setFormatter(formatter)
        return handler
    
    def _parse_size(self, size_str: str) -> int:
        """解析文件大小字符串"""
        size_str = size_str.upper().strip()
        
        # 定义单位倍数
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        
        # 查找匹配的后缀
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                # 提取数字部分
                number_str = size_str[:-len(suffix)].strip()
                if number_str:  # 确保有数字部分
                    try:
                        if '.' in number_str:
                            return int(float(number_str) * multiplier)
                        else:
                            return int(number_str) * multiplier
                    except (ValueError, TypeError):
                        pass
        
        # 如果没有单位，默认按字节处理
        try:
            if '.' in size_str:
                return int(float(size_str))
            else:
                return int(size_str)
        except (ValueError, TypeError):
            # 如果解析失败，返回默认值 10MB
            return 10 * 1024 * 1024
    
    def _configure_third_party_loggers(self):
        """配置第三方库的日志级别"""
        third_party_configs = {
            'urllib3': logging.WARNING,
            'requests': logging.WARNING,
            'yfinance': logging.WARNING,
            'matplotlib': logging.WARNING,
            'PIL': logging.WARNING,
        }
        
        for logger_name, level in third_party_configs.items():
            logging.getLogger(logger_name).setLevel(level)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            日志器实例
        """
        return logging.getLogger(name)
    
    def get_trade_logger(self) -> logging.Logger:
        """获取交易专用日志器"""
        return logging.getLogger('trading.signals')
    
    def get_data_logger(self) -> logging.Logger:
        """获取数据相关日志器"""
        return logging.getLogger('data.fetcher')
    
    def get_analysis_logger(self) -> logging.Logger:
        """获取分析相关日志器"""
        return logging.getLogger('analysis.engine')


# 全局变量
_global_logger_manager: Optional[TradingLogger] = None
_loggers: Dict[str, logging.Logger] = {}  # 添加缺失的全局变量


def setup_logging(config: Optional[Dict[str, Any]] = None) -> TradingLogger:
    """
    设置全局日志系统
    
    Args:
        config: 日志配置字典
        
    Returns:
        日志管理器实例
    """
    global _global_logger_manager
    _global_logger_manager = TradingLogger(config)
    return _global_logger_manager


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    if _global_logger_manager is None:
        setup_logging()
    
    return _global_logger_manager.get_logger(name)


def get_trade_logger() -> logging.Logger:
    """获取交易日志器"""
    if _global_logger_manager is None:
        setup_logging()
    
    return _global_logger_manager.get_trade_logger()


def get_data_logger() -> logging.Logger:
    """获取数据日志器"""
    if _global_logger_manager is None:
        setup_logging()
    
    return _global_logger_manager.get_data_logger()


def get_analysis_logger() -> logging.Logger:
    """
    获取技术分析专用日志器
    
    Returns:
        配置好的日志器实例
    """
    logger_name = "analysis"
    
    if logger_name in _loggers:
        return _loggers[logger_name]
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # 防止重复添加处理器
    if not logger.handlers:
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(_get_colored_formatter())
        logger.addHandler(console_handler)
        
        # 文件处理器
        analysis_file_handler = _create_file_handler("analysis.log")
        if analysis_file_handler:
            logger.addHandler(analysis_file_handler)
    
    # 防止日志向上传播
    logger.propagate = False
    
    _loggers[logger_name] = logger
    return logger


# 便捷的日志记录函数
def log_trade_signal(symbol: str, signal_type: str, confidence: float, **kwargs):
    """
    记录交易信号
    
    Args:
        symbol: 股票代码
        signal_type: 信号类型 (BUY/SELL)
        confidence: 置信度
        **kwargs: 其他信号参数
    """
    logger = get_trade_logger()
    extra_fields = {
        'symbol': symbol,
        'signal_type': signal_type,
        'confidence': confidence,
        **kwargs
    }
    
    # 添加额外字段到日志记录
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.extra_fields = extra_fields
        return record
    
    logging.setLogRecordFactory(record_factory)
    logger.info(f"交易信号 {signal_type}: {symbol} (置信度: {confidence:.2f})")
    logging.setLogRecordFactory(old_factory)


def log_data_fetch(symbol: str, data_type: str, success: bool, **kwargs):
    """
    记录数据获取
    
    Args:
        symbol: 股票代码
        data_type: 数据类型
        success: 是否成功
        **kwargs: 其他参数
    """
    logger = get_data_logger()
    status = "成功" if success else "失败"
    logger.info(f"数据获取 {status}: {symbol} - {data_type}", extra={
        'symbol': symbol,
        'data_type': data_type,
        'success': success,
        **kwargs
    })


def _get_colored_formatter() -> ColoredConsoleFormatter:
    """获取彩色格式化器"""
    return ColoredConsoleFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def _create_file_handler(filename: str) -> Optional[logging.Handler]:
    """创建文件处理器"""
    try:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            logs_dir / filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        return handler
    except Exception:
        return None 