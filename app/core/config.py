"""
配置管理模块
Configuration Management Module

提供统一的配置加载、验证和管理功能。
支持YAML配置文件、环境变量覆盖、配置验证等功能。
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置相关错误"""
    pass


class ConfigLoader:
    """
    配置加载器
    
    负责从YAML文件和环境变量加载配置，支持配置验证和热重载。
    """
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config文件夹
        """
        self._config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / "config"
        self._config = {}
        self._system_config_path = self._config_dir / "system.yaml"
        self._stocks_config_dir = self._config_dir / "stocks"
        self._strategies_config_dir = self._config_dir / "strategies"
        
        # 加载环境变量
        self._load_env_vars()
        
        # 加载配置
        self._load_all_configs()
    
    def _load_env_vars(self):
        """加载环境变量"""
        # 尝试从项目根目录加载.env文件
        env_path = self._config_dir.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"已加载环境变量文件: {env_path}")
        else:
            logger.debug("未找到.env文件，使用系统环境变量")
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """
        加载单个YAML文件
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            解析后的配置字典
            
        Raises:
            ConfigError: 文件不存在或格式错误
        """
        if not file_path.exists():
            raise ConfigError(f"配置文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if content is None:
                    return {}
                return content
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML文件格式错误 {file_path}: {e}")
        except Exception as e:
            raise ConfigError(f"读取配置文件失败 {file_path}: {e}")
    
    def _load_system_config(self) -> Dict[str, Any]:
        """加载系统主配置文件"""
        logger.info(f"加载系统配置: {self._system_config_path}")
        return self._load_yaml_file(self._system_config_path)
    
    def _load_stocks_config(self) -> Dict[str, Dict[str, Any]]:
        """
        加载所有股票配置文件
        
        Returns:
            以股票代码为键的配置字典
        """
        stocks_config = {}
        
        if not self._stocks_config_dir.exists():
            logger.warning(f"股票配置目录不存在: {self._stocks_config_dir}")
            return stocks_config
        
        for yaml_file in self._stocks_config_dir.glob("*.yaml"):
            try:
                config = self._load_yaml_file(yaml_file)
                if 'stock' in config and 'symbol' in config['stock']:
                    symbol = config['stock']['symbol'].upper()
                    stocks_config[symbol] = config
                    logger.debug(f"加载股票配置: {symbol}")
                else:
                    logger.warning(f"股票配置文件格式不正确: {yaml_file}")
            except ConfigError as e:
                logger.error(f"加载股票配置失败 {yaml_file}: {e}")
        
        logger.info(f"已加载 {len(stocks_config)} 个股票配置")
        return stocks_config
    
    def _load_strategies_config(self) -> Dict[str, Dict[str, Any]]:
        """
        加载所有策略配置文件
        
        Returns:
            以策略名称为键的配置字典
        """
        strategies_config = {}
        
        if not self._strategies_config_dir.exists():
            logger.info(f"策略配置目录不存在，创建: {self._strategies_config_dir}")
            self._strategies_config_dir.mkdir(parents=True, exist_ok=True)
            return strategies_config
        
        for yaml_file in self._strategies_config_dir.glob("*.yaml"):
            try:
                config = self._load_yaml_file(yaml_file)
                strategy_name = yaml_file.stem
                strategies_config[strategy_name] = config
                logger.debug(f"加载策略配置: {strategy_name}")
            except ConfigError as e:
                logger.error(f"加载策略配置失败 {yaml_file}: {e}")
        
        logger.info(f"已加载 {len(strategies_config)} 个策略配置")
        return strategies_config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用环境变量覆盖
        
        Args:
            config: 原始配置字典
            
        Returns:
            应用环境变量后的配置字典
        """
        # 环境变量映射规则
        env_mappings = {
            'APP_NAME': ('app', 'name'),
            'LOG_LEVEL': ('logging', 'level'),
            'DEBUG': ('app', 'debug'),
            'DATABASE_PATH': ('database', 'path'),
            'INITIAL_CAPITAL': ('trading', 'initial_capital'),
            'ALPHA_VANTAGE_API_KEY': ('data', 'api_keys', 'alpha_vantage'),
            'FINNHUB_API_KEY': ('data', 'api_keys', 'finnhub'),
            'POLYGON_API_KEY': ('data', 'api_keys', 'polygon'),
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 递归设置嵌套配置
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # 类型转换
                if env_var == 'DEBUG':
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                elif env_var in ['INITIAL_CAPITAL']:
                    try:
                        env_value = float(env_value)
                    except ValueError:
                        logger.warning(f"环境变量 {env_var} 不是有效数字: {env_value}")
                        continue
                
                current[config_path[-1]] = env_value
                logger.debug(f"环境变量覆盖: {env_var} -> {'.'.join(config_path)}")
        
        return config
    
    def _load_all_configs(self):
        """加载所有配置"""
        try:
            # 加载系统配置
            self._config = self._load_system_config()
            
            # 应用环境变量覆盖
            self._config = self._apply_env_overrides(self._config)
            
            # 加载股票配置
            self._config['stocks'] = self._load_stocks_config()
            
            # 加载策略配置
            self._config['strategies'] = self._load_strategies_config()
            
            # 验证配置
            self._validate_config()
            
            logger.info("所有配置加载完成")
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise ConfigError(f"配置加载失败: {e}")
    
    def _validate_config(self):
        """验证配置的有效性"""
        required_keys = [
            ('app', 'name'),
            ('version',),
            ('data', 'primary_source'),
        ]
        
        for key_path in required_keys:
            if not self._has_nested_key(self._config, key_path):
                raise ConfigError(f"缺少必需的配置项: {'.'.join(key_path)}")
        
        # 验证数值范围
        if self.get('risk.max_total_exposure', 0) > 1.0:
            raise ConfigError("最大总仓位不能超过100%")
        
        logger.debug("配置验证通过")
    
    def _has_nested_key(self, config: Dict[str, Any], key_path: tuple) -> bool:
        """检查嵌套键是否存在"""
        current = config
        for key in key_path:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        return True
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，用点分隔，如 'app.name'
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        current = self._config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_stock_config(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取指定股票的配置
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票配置字典或None
        """
        return self._config.get('stocks', {}).get(symbol.upper())
    
    def get_strategy_config(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定策略的配置
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略配置字典或None
        """
        return self._config.get('strategies', {}).get(strategy_name)
    
    def get_all_active_stocks(self) -> list:
        """
        获取所有激活的股票代码
        
        Returns:
            活跃股票代码列表
        """
        active_stocks = []
        for symbol, config in self._config.get('stocks', {}).items():
            if config.get('stock', {}).get('active', True):
                active_stocks.append(symbol)
        return active_stocks
    
    def reload(self):
        """重新加载所有配置"""
        logger.info("重新加载配置...")
        self._config = {}
        self._load_all_configs()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        获取完整配置字典
        
        Returns:
            完整的配置字典
        """
        return self._config.copy()
    
    def save_stock_config(self, symbol: str, config: Dict[str, Any]):
        """
        保存股票配置到文件
        
        Args:
            symbol: 股票代码
            config: 配置字典
        """
        symbol = symbol.upper()
        config_file = self._stocks_config_dir / f"{symbol}.yaml"
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            # 更新内存中的配置
            if 'stocks' not in self._config:
                self._config['stocks'] = {}
            self._config['stocks'][symbol] = config
            
            logger.info(f"股票配置已保存: {symbol}")
            
        except Exception as e:
            raise ConfigError(f"保存股票配置失败 {symbol}: {e}")


# 全局配置实例
_global_config: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """
    获取全局配置实例
    
    Returns:
        ConfigLoader实例
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader()
    return _global_config


def reload_config():
    """重新加载全局配置"""
    global _global_config
    if _global_config is not None:
        _global_config.reload()
    else:
        _global_config = ConfigLoader()


# 便捷函数
def get_app_config() -> Dict[str, Any]:
    """获取应用配置"""
    return get_config().get('app', {})


def get_data_config() -> Dict[str, Any]:
    """获取数据源配置"""
    return get_config().get('data', {})


def get_risk_config() -> Dict[str, Any]:
    """获取风险控制配置"""
    return get_config().get('risk', {})


def get_trading_hours() -> Dict[str, Any]:
    """获取交易时间配置"""
    return get_config().get('monitoring.trading_hours', {}) 