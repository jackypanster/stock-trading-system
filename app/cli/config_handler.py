"""
配置管理命令处理器

负责处理config命令的所有逻辑，包括配置查看、设置、验证、备份、恢复等功能。
"""

import json
import yaml
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .base import BaseCommandHandler, CommandResult, OutputFormatter


class ConfigCommandHandler(BaseCommandHandler):
    """配置管理命令处理器"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = self.project_root / "config" / "system.yaml"
        
        # 如果config是ConfigLoader对象，转换为字典
        if hasattr(config, 'to_dict'):
            self.config = config.to_dict()
        elif hasattr(config, '_config'):
            self.config = config._config
        else:
            self.config = config
    
    @property
    def command_name(self) -> str:
        """命令名称"""
        return "config"
    
    @property
    def command_description(self) -> str:
        """命令描述"""
        return "配置管理命令"
        
    def execute(self, **kwargs) -> CommandResult:
        """
        处理config命令
        
        Args:
            action: 子命令动作 (show/set/get/list/validate/reset/backup/restore)
            section: 配置节名称
            output_format: 输出格式 (table/json/yaml)
            stocks: 是否显示股票配置
            strategies: 是否显示策略配置
            key: 配置键
            value: 配置值
            value_type: 值类型
            default: 默认值
            pattern: 过滤模式
            confirm: 确认操作
            fix: 自动修复
            output: 输出文件路径
            backup_file: 备份文件路径
            
        Returns:
            CommandResult: 命令执行结果
        """
        try:
            action = kwargs.get('action', 'show')
            
            if action == 'show':
                return self._handle_show(**kwargs)
            elif action == 'set':
                return self._handle_set(**kwargs)
            elif action == 'get':
                return self._handle_get(**kwargs)
            elif action == 'list':
                return self._handle_list(**kwargs)
            elif action == 'validate':
                return self._handle_validate(**kwargs)
            elif action == 'reset':
                return self._handle_reset(**kwargs)
            elif action == 'backup':
                return self._handle_backup(**kwargs)
            elif action == 'restore':
                return self._handle_restore(**kwargs)
            else:
                return CommandResult(
                    success=False,
                    error=f"未知的配置命令动作: {action}",
                    data=None
                )
                
        except Exception as e:
            error_msg = f"配置命令执行失败: {e}"
            if self.logger:
                self.logger.error(error_msg)
            
            return CommandResult(
                success=False,
                error=error_msg,
                data=None
            )
    
    def _handle_show(self, **kwargs) -> CommandResult:
        """处理show子命令"""
        section = kwargs.get('section')
        output_format = kwargs.get('output_format', 'table')
        stocks = kwargs.get('stocks', False)
        strategies = kwargs.get('strategies', False)
        
        if output_format == 'json':
            return self._show_json_format(section)
        elif output_format == 'yaml':
            return self._show_yaml_format(section)
        else:  # table格式
            return self._show_table_format(section, stocks, strategies)
    
    def _show_json_format(self, section: Optional[str]) -> CommandResult:
        """JSON格式显示配置"""
        if section:
            section_data = self.config.get(section, {})
            json_output = json.dumps(section_data, indent=2, ensure_ascii=False, 
                                   cls=self._get_json_encoder())
        else:
            json_output = json.dumps(self.config, indent=2, ensure_ascii=False, 
                                   cls=self._get_json_encoder())
        
        return CommandResult(
            success=True,
            data={'json_output': json_output},
            message="配置JSON格式输出完成"
        )
    
    def _show_yaml_format(self, section: Optional[str]) -> CommandResult:
        """YAML格式显示配置"""
        if section:
            section_data = self.config.get(section, {})
            yaml_output = yaml.dump(section_data, default_flow_style=False, allow_unicode=True)
        else:
            yaml_output = yaml.dump(self.config, default_flow_style=False, allow_unicode=True)
        
        return CommandResult(
            success=True,
            data={'yaml_output': yaml_output},
            message="配置YAML格式输出完成"
        )
    
    def _show_table_format(self, section: Optional[str], stocks: bool, strategies: bool) -> CommandResult:
        """表格格式显示配置"""
        if section:
            return self._show_config_section(section)
        elif stocks:
            return self._show_stock_configs()
        elif strategies:
            return self._show_strategy_configs()
        else:
            return self._show_system_overview()
    
    def _show_config_section(self, section: str) -> CommandResult:
        """显示指定配置节"""
        section_data = self.config.get(section, {})
        if not section_data:
            return CommandResult(
                success=False,
                error=f"配置节 '{section}' 不存在",
                data=None
            )
        
        return CommandResult(
            success=True,
            data={
                'section_name': section,
                'section_data': section_data
            },
            message=f"配置节 {section} 显示完成"
        )
    
    def _show_stock_configs(self) -> CommandResult:
        """显示股票配置"""
        stocks_dir = self.project_root / "config" / "stocks"
        if not stocks_dir.exists():
            return CommandResult(
                success=False,
                error="股票配置目录不存在",
                data=None
            )
        
        stock_files = list(stocks_dir.glob("*.yaml"))
        if not stock_files:
            return CommandResult(
                success=True,
                data={'stock_configs': []},
                message="未找到股票配置文件"
            )
        
        stock_configs = []
        for stock_file in stock_files:
            try:
                with open(stock_file, 'r', encoding='utf-8') as f:
                    stock_config = yaml.safe_load(f)
                
                stock_info = stock_config.get('stock', {})
                config_data = {
                    'file': stock_file.name,
                    'symbol': stock_info.get('symbol', stock_file.stem),
                    'name': stock_info.get('name', 'N/A'),
                    'active': stock_info.get('active', False),
                    'risk_config': stock_config.get('risk', {}),
                    'trading_config': stock_config.get('trading', {})
                }
                stock_configs.append(config_data)
                
            except Exception as e:
                stock_configs.append({
                    'file': stock_file.name,
                    'error': str(e),
                    'valid': False
                })
        
        return CommandResult(
            success=True,
            data={'stock_configs': stock_configs},
            message="股票配置显示完成"
        )
    
    def _show_strategy_configs(self) -> CommandResult:
        """显示策略配置"""
        strategies_dir = self.project_root / "config" / "strategies"
        if not strategies_dir.exists():
            return CommandResult(
                success=False,
                error="策略配置目录不存在",
                data=None
            )
        
        strategy_files = list(strategies_dir.glob("*.yaml"))
        if not strategy_files:
            return CommandResult(
                success=True,
                data={'strategy_configs': []},
                message="未找到策略配置文件"
            )
        
        strategy_configs = []
        for strategy_file in strategy_files:
            try:
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    strategy_config = yaml.safe_load(f)
                
                strategy_info = strategy_config.get('strategy', {})
                config_data = {
                    'file': strategy_file.name,
                    'name': strategy_info.get('name', strategy_file.stem),
                    'description': strategy_info.get('description', 'N/A'),
                    'active': strategy_info.get('active', False),
                    'parameters': strategy_config.get('parameters', {})
                }
                strategy_configs.append(config_data)
                
            except Exception as e:
                strategy_configs.append({
                    'file': strategy_file.name,
                    'error': str(e),
                    'valid': False
                })
        
        return CommandResult(
            success=True,
            data={'strategy_configs': strategy_configs},
            message="策略配置显示完成"
        )
    
    def _show_system_overview(self) -> CommandResult:
        """显示系统配置概览"""
        overview_data = {
            'app': self.config.get('app', {}),
            'data': self.config.get('data', {}),
            'risk': self.config.get('risk', {}),
            'analysis': self.config.get('analysis', {}),
            'signals': self.config.get('signals', {}),
            'logging': self.config.get('logging', {})
        }
        
        return CommandResult(
            success=True,
            data={'system_overview': overview_data},
            message="系统配置概览显示完成"
        )
    
    def _handle_set(self, **kwargs) -> CommandResult:
        """处理set子命令"""
        key = kwargs.get('key')
        value = kwargs.get('value')
        value_type = kwargs.get('value_type', 'auto')
        
        if not key or value is None:
            return CommandResult(
                success=False,
                error="缺少必需的参数: key 和 value",
                data=None
            )
        
        # 类型转换
        try:
            converted_value = self._convert_value(value, value_type)
        except ValueError as e:
            return CommandResult(
                success=False,
                error=f"值类型转换失败: {e}",
                data=None
            )
        
        # 更新配置文件
        try:
            # 读取现有配置
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}
            
            # 设置嵌套键值
            keys = key.split('.')
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = converted_value
            
            # 写回配置文件
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            return CommandResult(
                success=True,
                data={
                    'key': key,
                    'value': converted_value,
                    'value_type': type(converted_value).__name__
                },
                message=f"配置已更新: {key} = {converted_value}"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"设置配置失败: {e}",
                data=None
            )
    
    def _handle_get(self, **kwargs) -> CommandResult:
        """处理get子命令"""
        key = kwargs.get('key')
        default = kwargs.get('default')
        
        if not key:
            return CommandResult(
                success=False,
                error="缺少必需的参数: key",
                data=None
            )
        
        # 获取嵌套键值
        keys = key.split('.')
        current = self.config
        
        try:
            for k in keys:
                current = current[k]
            
            return CommandResult(
                success=True,
                data={'key': key, 'value': current},
                message=f"配置值获取成功: {key}"
            )
            
        except (KeyError, TypeError):
            if default is not None:
                return CommandResult(
                    success=True,
                    data={'key': key, 'value': default, 'is_default': True},
                    message=f"配置键不存在，返回默认值: {key}"
                )
            else:
                return CommandResult(
                    success=False,
                    error=f"配置键 '{key}' 不存在",
                    data=None
                )
    
    def _handle_list(self, **kwargs) -> CommandResult:
        """处理list子命令"""
        pattern = kwargs.get('pattern')
        
        def _list_keys(obj, prefix=''):
            keys = []
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    keys.extend(_list_keys(value, full_key))
                else:
                    keys.append(full_key)
            return keys
        
        all_keys = _list_keys(self.config)
        
        if pattern:
            # 过滤键
            filtered_keys = [k for k in all_keys if pattern.lower() in k.lower()]
            return CommandResult(
                success=True,
                data={'keys': filtered_keys, 'pattern': pattern},
                message=f"匹配 '{pattern}' 的配置键列表"
            )
        else:
            return CommandResult(
                success=True,
                data={'keys': all_keys},
                message="所有配置键列表"
            )
    
    def _handle_validate(self, **kwargs) -> CommandResult:
        """处理validate子命令"""
        fix = kwargs.get('fix', False)
        
        validation_results = {
            'system_config': False,
            'stock_configs': [],
            'strategy_configs': [],
            'errors': [],
            'warnings': []
        }
        
        # 验证主配置文件
        self._validate_system_config(validation_results)
        
        # 验证股票配置
        self._validate_stock_configs(validation_results)
        
        # 验证策略配置
        self._validate_strategy_configs(validation_results)
        
        # 自动修复选项
        if fix and validation_results['errors']:
            fixed_count = self._auto_fix_config_issues(validation_results)
            validation_results['fixed_count'] = fixed_count
        
        success = len(validation_results['errors']) == 0
        
        return CommandResult(
            success=success,
            data=validation_results,
            message="配置验证完成"
        )
    
    def _handle_reset(self, **kwargs) -> CommandResult:
        """处理reset子命令"""
        key = kwargs.get('key')
        confirm = kwargs.get('confirm', False)
        
        if not confirm:
            message = f"将重置配置键 '{key}' 到默认值" if key else "将重置所有配置到默认值"
            return CommandResult(
                success=False,
                error=f"需要确认操作: {message}",
                data={'requires_confirmation': True}
            )
        
        try:
            if key:
                # 重置指定键
                return CommandResult(
                    success=False,
                    error="单个键重置功能待实现",
                    data=None
                )
            else:
                # 重置所有配置
                self._create_default_system_config()
                return CommandResult(
                    success=True,
                    data={'reset_type': 'all'},
                    message="配置已重置到默认值"
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"重置配置失败: {e}",
                data=None
            )
    
    def _handle_backup(self, **kwargs) -> CommandResult:
        """处理backup子命令"""
        output = kwargs.get('output')
        
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"config_backup_{timestamp}.tar.gz"
        
        try:
            config_dir = self.project_root / "config"
            if not config_dir.exists():
                return CommandResult(
                    success=False,
                    error="配置目录不存在",
                    data=None
                )
            
            # 创建备份
            backup_path = self.project_root / output
            shutil.make_archive(str(backup_path).replace('.tar.gz', ''), 'gztar', config_dir)
            
            return CommandResult(
                success=True,
                data={'backup_path': str(backup_path)},
                message=f"配置已备份到: {backup_path}"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"备份配置失败: {e}",
                data=None
            )
    
    def _handle_restore(self, **kwargs) -> CommandResult:
        """处理restore子命令"""
        backup_file = kwargs.get('backup_file')
        confirm = kwargs.get('confirm', False)
        
        if not backup_file:
            return CommandResult(
                success=False,
                error="缺少必需的参数: backup_file",
                data=None
            )
        
        if not confirm:
            return CommandResult(
                success=False,
                error=f"需要确认操作: 将从 {backup_file} 恢复配置，这将覆盖当前配置",
                data={'requires_confirmation': True}
            )
        
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                return CommandResult(
                    success=False,
                    error=f"备份文件不存在: {backup_file}",
                    data=None
                )
            
            config_dir = self.project_root / "config"
            
            # 备份当前配置
            backup_current = None
            if config_dir.exists():
                backup_current = config_dir.parent / "config_backup_before_restore"
                if backup_current.exists():
                    shutil.rmtree(backup_current)
                shutil.copytree(config_dir, backup_current)
            
            # 删除当前配置目录
            if config_dir.exists():
                shutil.rmtree(config_dir)
            
            # 解压备份文件
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(config_dir.parent)
            
            return CommandResult(
                success=True,
                data={
                    'backup_file': backup_file,
                    'current_backup': str(backup_current) if backup_current else None
                },
                message=f"配置已从 {backup_file} 恢复"
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"恢复配置失败: {e}",
                data=None
            )
    
    def _convert_value(self, value: str, value_type: str):
        """转换值类型"""
        if value_type == 'auto':
            # 自动推断类型
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            elif value.replace('.', '').replace('-', '').isdigit():
                return float(value) if '.' in value else int(value)
            else:
                return value
        elif value_type == 'str':
            return value
        elif value_type == 'int':
            return int(value)
        elif value_type == 'float':
            return float(value)
        elif value_type == 'bool':
            return value.lower() in ('true', '1', 'yes', 'on')
        else:
            return value
    
    def _validate_system_config(self, validation_results: Dict[str, Any]):
        """验证主配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    system_config = yaml.safe_load(f)
                validation_results['system_config'] = True
                
                # 验证必需的配置节
                required_sections = ['app', 'data', 'risk', 'analysis', 'signals', 'logging']
                for section in required_sections:
                    if section not in system_config:
                        validation_results['errors'].append(f"缺少必需的配置节: {section}")
                
                # 验证数据源配置
                data_config = system_config.get('data', {})
                if 'primary_source' not in data_config:
                    validation_results['errors'].append("缺少主数据源配置")
                
                if 'backup_sources' not in data_config:
                    validation_results['warnings'].append("缺少备用数据源配置")
                
            except Exception as e:
                validation_results['errors'].append(f"system.yaml 格式错误: {e}")
        else:
            validation_results['errors'].append("system.yaml 不存在")
    
    def _validate_stock_configs(self, validation_results: Dict[str, Any]):
        """验证股票配置"""
        stocks_dir = self.project_root / "config" / "stocks"
        if stocks_dir.exists():
            stock_files = list(stocks_dir.glob("*.yaml"))
            
            for stock_file in stock_files:
                try:
                    with open(stock_file, 'r', encoding='utf-8') as f:
                        stock_config = yaml.safe_load(f)
                    
                    # 验证股票配置结构
                    if 'stock' not in stock_config:
                        validation_results['errors'].append(f"{stock_file.name}: 缺少 'stock' 配置节")
                        continue
                    
                    stock_info = stock_config['stock']
                    if 'symbol' not in stock_info:
                        validation_results['errors'].append(f"{stock_file.name}: 缺少股票代码")
                    else:
                        symbol = stock_info['symbol']
                        # 验证文件名与股票代码是否匹配
                        if stock_file.stem != symbol:
                            validation_results['warnings'].append(f"{stock_file.name}: 文件名与股票代码不匹配")
                    
                    validation_results['stock_configs'].append({
                        'file': stock_file.name,
                        'valid': True,
                        'symbol': stock_info.get('symbol', 'N/A')
                    })
                    
                except Exception as e:
                    validation_results['errors'].append(f"{stock_file.name} 格式错误: {e}")
                    validation_results['stock_configs'].append({
                        'file': stock_file.name,
                        'valid': False,
                        'error': str(e)
                    })
        else:
            validation_results['warnings'].append("stocks配置目录不存在")
    
    def _validate_strategy_configs(self, validation_results: Dict[str, Any]):
        """验证策略配置"""
        strategies_dir = self.project_root / "config" / "strategies"
        if strategies_dir.exists():
            strategy_files = list(strategies_dir.glob("*.yaml"))
            
            for strategy_file in strategy_files:
                try:
                    with open(strategy_file, 'r', encoding='utf-8') as f:
                        strategy_config = yaml.safe_load(f)
                    
                    # 验证策略配置结构
                    if 'strategy' not in strategy_config:
                        validation_results['errors'].append(f"{strategy_file.name}: 缺少 'strategy' 配置节")
                        continue
                    
                    validation_results['strategy_configs'].append({
                        'file': strategy_file.name,
                        'valid': True,
                        'name': strategy_config['strategy'].get('name', 'N/A')
                    })
                    
                except Exception as e:
                    validation_results['errors'].append(f"{strategy_file.name} 格式错误: {e}")
                    validation_results['strategy_configs'].append({
                        'file': strategy_file.name,
                        'valid': False,
                        'error': str(e)
                    })
        else:
            validation_results['warnings'].append("strategies配置目录不存在")
    
    def _auto_fix_config_issues(self, validation_results: Dict[str, Any]) -> int:
        """自动修复配置问题"""
        fixed_count = 0
        
        for error in validation_results['errors']:
            if "system.yaml 不存在" in error:
                # 创建默认的system.yaml
                try:
                    self._create_default_system_config()
                    fixed_count += 1
                except Exception:
                    pass
            
            elif "stocks配置目录不存在" in error:
                # 创建stocks目录
                try:
                    stocks_dir = self.project_root / "config" / "stocks"
                    stocks_dir.mkdir(parents=True, exist_ok=True)
                    fixed_count += 1
                except Exception:
                    pass
            
            elif "strategies配置目录不存在" in error:
                # 创建strategies目录
                try:
                    strategies_dir = self.project_root / "config" / "strategies"
                    strategies_dir.mkdir(parents=True, exist_ok=True)
                    fixed_count += 1
                except Exception:
                    pass
        
        return fixed_count
    
    def _create_default_system_config(self):
        """创建默认的系统配置文件"""
        default_config = {
            'app': {
                'name': '美股日内套利助手',
                'version': '1.0.0',
                'environment': 'development'
            },
            'data': {
                'primary_source': 'yfinance',
                'backup_sources': ['alpha_vantage'],
                'cache_ttl': 300,
                'request_timeout': 30
            },
            'risk': {
                'max_total_exposure': 0.8,
                'max_single_position': 0.15,
                'default_stop_loss': 0.02,
                'default_take_profit': 0.05
            },
            'analysis': {
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'atr_period': 14
            },
            'signals': {
                'min_confidence': 0.6,
                'signal_expiry': 60,
                'max_signals': 50
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_output': True
            }
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def _get_json_encoder(self):
        """获取JSON编码器"""
        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                elif isinstance(obj, Path):
                    return str(obj)
                elif hasattr(obj, '__dict__'):
                    return obj.__dict__
                return super().default(obj)
        
        return CustomJSONEncoder 