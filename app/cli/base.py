"""
CLI命令处理器基类

定义统一的命令处理接口，为所有CLI命令提供标准化的处理框架。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import click
import logging
from pathlib import Path
import json
import yaml


class CommandResult:
    """命令执行结果封装类"""
    
    def __init__(self, success: bool = True, data: Any = None, message: str = "", 
                 error: Optional[Exception] = None):
        self.success = success
        self.data = data
        self.message = message
        self.error = error
        
    def __bool__(self):
        return self.success


class OutputFormatter:
    """输出格式化器"""
    
    @staticmethod
    def format_table(data: Dict[str, Any], title: str = "") -> str:
        """格式化为表格输出"""
        lines = []
        if title:
            lines.append(f"\n{title}")
            lines.append("=" * len(title))
        
        # 递归格式化数据
        def _format_dict(d: Dict, indent: int = 0) -> List[str]:
            result = []
            prefix = "  " * indent
            for key, value in d.items():
                if isinstance(value, dict):
                    result.append(f"{prefix}{key}:")
                    result.extend(_format_dict(value, indent + 1))
                elif isinstance(value, list):
                    result.append(f"{prefix}{key}: [{', '.join(map(str, value))}]")
                else:
                    result.append(f"{prefix}{key}: {value}")
            return result
        
        if isinstance(data, dict):
            lines.extend(_format_dict(data))
        else:
            lines.append(str(data))
            
        return "\n".join(lines)
    
    @staticmethod
    def format_json(data: Any) -> str:
        """格式化为JSON输出"""
        import json
        from datetime import datetime
        
        def json_serializer(obj):
            """JSON序列化器，处理特殊类型"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            else:
                return str(obj)
        
        return json.dumps(data, indent=2, ensure_ascii=False, default=json_serializer)
    
    @staticmethod
    def format_csv(data: Dict[str, Any], headers: List[str] = None) -> str:
        """格式化为CSV输出"""
        lines = []
        
        if headers:
            lines.append(",".join(headers))
        
        # 简化的CSV格式化
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    value = str(value).replace(',', ';')
                lines.append(f"{key},{value}")
        
        return "\n".join(lines)


class BaseCommandHandler(ABC):
    """CLI命令处理器抽象基类"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        初始化命令处理器
        
        Args:
            config: 系统配置
            logger: 日志记录器
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.formatter = OutputFormatter()
    
    @property
    @abstractmethod
    def command_name(self) -> str:
        """命令名称"""
        pass
    
    @property
    @abstractmethod
    def command_description(self) -> str:
        """命令描述"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> CommandResult:
        """
        执行命令的核心逻辑
        
        Args:
            **kwargs: 命令参数
            
        Returns:
            CommandResult: 执行结果
        """
        pass
    
    def validate_params(self, **kwargs) -> CommandResult:
        """
        验证命令参数
        
        Args:
            **kwargs: 命令参数
            
        Returns:
            CommandResult: 验证结果
        """
        # 默认实现：参数验证通过
        return CommandResult(success=True, message="参数验证通过")
    
    def pre_execute(self, **kwargs) -> CommandResult:
        """
        执行前的准备工作
        
        Args:
            **kwargs: 命令参数
            
        Returns:
            CommandResult: 准备结果
        """
        # 默认实现：无需准备工作
        return CommandResult(success=True, message="准备工作完成")
    
    def post_execute(self, result: CommandResult, **kwargs) -> CommandResult:
        """
        执行后的清理工作
        
        Args:
            result: 执行结果
            **kwargs: 命令参数
            
        Returns:
            CommandResult: 清理结果
        """
        # 默认实现：无需清理工作
        return result
    
    def format_output(self, result: CommandResult, output_format: str = 'table') -> str:
        """
        格式化输出结果
        
        Args:
            result: 命令执行结果
            output_format: 输出格式 ('table', 'json', 'csv')
            
        Returns:
            str: 格式化后的输出
        """
        if not result.success:
            return f"❌ 命令执行失败: {result.message}"
        
        if result.data is None:
            return result.message or "✅ 命令执行成功"
        
        try:
            if output_format == 'json':
                return self.formatter.format_json(result.data)
            elif output_format == 'csv':
                return self.formatter.format_csv(result.data)
            else:  # table
                return self.formatter.format_table(result.data, self.command_name)
        except Exception as e:
            self.logger.warning(f"格式化输出失败: {e}")
            return str(result.data)
    
    def handle_error(self, error: Exception, **kwargs) -> CommandResult:
        """
        处理命令执行错误
        
        Args:
            error: 异常对象
            **kwargs: 命令参数
            
        Returns:
            CommandResult: 错误处理结果
        """
        error_msg = f"{self.command_name}命令执行失败: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        return CommandResult(success=False, message=error_msg, error=error)
    
    def run(self, **kwargs) -> CommandResult:
        """
        运行命令的完整流程
        
        Args:
            **kwargs: 命令参数
            
        Returns:
            CommandResult: 最终执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self.validate_params(**kwargs)
            if not validation_result:
                return validation_result
            
            # 2. 执行前准备
            prep_result = self.pre_execute(**kwargs)
            if not prep_result:
                return prep_result
            
            # 3. 执行核心逻辑
            result = self.execute(**kwargs)
            
            # 4. 执行后清理
            final_result = self.post_execute(result, **kwargs)
            
            return final_result
            
        except Exception as e:
            return self.handle_error(e, **kwargs)
    
    def log_info(self, message: str):
        """记录信息日志"""
        if self.logger:
            self.logger.info(message)
    
    def log_warning(self, message: str):
        """记录警告日志"""
        if self.logger:
            self.logger.warning(message)
    
    def log_error(self, message: str, exc_info: bool = False):
        """记录错误日志"""
        if self.logger:
            self.logger.error(message, exc_info=exc_info)


class AnalysisCommandHandler(BaseCommandHandler):
    """股票分析命令处理器基类"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self._fetcher = None
        self._strategy = None
        self._risk_manager = None
    
    @property
    def fetcher(self):
        """延迟加载数据获取器"""
        if self._fetcher is None:
            from app.data.fetcher import get_fetcher
            self._fetcher = get_fetcher(use_mock=False)
        return self._fetcher
    
    @property
    def strategy(self):
        """延迟加载策略"""
        if self._strategy is None:
            from app.analysis.strategies import SupportResistanceStrategy
            # 传递配置字典而不是ConfigLoader对象
            config_dict = self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config
            self._strategy = SupportResistanceStrategy(config_dict)
        return self._strategy
    
    @property
    def risk_manager(self):
        """延迟加载风险管理器"""
        if self._risk_manager is None:
            from app.core.risk_manager import RiskManager
            # 传递配置字典而不是ConfigLoader对象
            config_dict = self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config
            self._risk_manager = RiskManager(config_dict)
        return self._risk_manager
    
    def get_stock_data(self, symbol: str, period: str = "1mo", use_mock: bool = False) -> CommandResult:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            period: 数据周期
            use_mock: 是否使用模拟数据
            
        Returns:
            CommandResult: 包含股票数据的结果
        """
        try:
            if use_mock:
                from app.data.fetcher import get_fetcher
                fetcher = get_fetcher(use_mock=True)
            else:
                fetcher = self.fetcher
            
            hist_data = fetcher.get_historical_data(symbol, period=period)
            
            if len(hist_data) < 15:
                return CommandResult(
                    success=False,
                    message=f"历史数据不足，无法进行分析。当前数据点: {len(hist_data)}, 最少需要: 15"
                )
            
            return CommandResult(
                success=True,
                data=hist_data,
                message=f"成功获取 {len(hist_data)} 条历史数据"
            )
            
        except Exception as e:
            return self.handle_error(e, symbol=symbol, period=period)


class ConfigCommandHandler(BaseCommandHandler):
    """配置管理命令处理器基类"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.config_path = Path(__file__).parent.parent.parent / "config" / "system.yaml"
    
    def load_config_file(self) -> CommandResult:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                return CommandResult(
                    success=False,
                    message=f"配置文件不存在: {self.config_path}"
                )
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            return CommandResult(
                success=True,
                data=config_data,
                message="配置文件加载成功"
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def save_config_file(self, config_data: Dict[str, Any]) -> CommandResult:
        """保存配置文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            return CommandResult(
                success=True,
                message="配置文件保存成功"
            )
            
        except Exception as e:
            return self.handle_error(e) 