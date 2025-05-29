"""
CLI路由模块

负责定义所有CLI命令的路由和参数配置，将具体的业务逻辑委托给相应的处理器。
"""

import sys
import click
import logging
from pathlib import Path

from .analyze_handler import AnalyzeCommandHandler
from .signals_handler import SignalsCommandHandler
from .config_handler import ConfigCommandHandler


def create_cli_app(config, logger, debug=False):
    """创建CLI应用实例"""
    
    @click.group(invoke_without_command=True)
    @click.option('--version', is_flag=True, help='显示版本信息')
    @click.option('--config-file', help='指定配置文件路径')
    @click.option('--debug-mode', is_flag=True, help='启用调试模式')
    @click.pass_context
    def cli(ctx, version, config_file, debug_mode):
        """
        美股日内套利助手 - 个人投资分析工具
        
        通过程序化分析识别高波动美股的日内套利机会，帮助个人投资者做出更明智的投资决策。
        """
        ctx.ensure_object(dict)
        ctx.obj['config'] = config
        ctx.obj['logger'] = logger
        ctx.obj['debug'] = debug or debug_mode
        
        if version:
            from .. import __version__, __author__
            click.echo(f"美股日内套利助手 v{__version__}")
            click.echo(f"作者: {__author__}")
            click.echo(f"Python版本: {sys.version}")
            ctx.exit()
        
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @cli.command()
    @click.argument('symbol')
    @click.option('--format', 'output_format', default='table', 
                  type=click.Choice(['table', 'json', 'csv']), help='输出格式')
    @click.option('--days', default=20, help='历史数据天数')
    @click.option('--mock', is_flag=True, help='使用模拟数据')
    @click.option('--with-signals', is_flag=True, help='包含交易信号分析')
    @click.option('--with-risk', is_flag=True, help='包含风险管理分析')
    @click.option('--portfolio-value', default=100000, help='投资组合价值（用于风险计算）')
    @click.pass_context
    def analyze(ctx, symbol, output_format, days, mock, with_signals, with_risk, portfolio_value):
        """分析指定股票的技术指标和交易信号"""
        try:
            # 确保配置是字典格式
            config_dict = ctx.obj['config']
            if hasattr(config_dict, 'to_dict'):
                config_dict = config_dict.to_dict()
            
            handler = AnalyzeCommandHandler(
                config=config_dict,
                logger=ctx.obj['logger']
            )
            
            result = handler.run(
                symbol=symbol,
                output_format=output_format,
                days=days,
                mock=mock,
                with_signals=with_signals,
                with_risk=with_risk,
                portfolio_value=portfolio_value
            )
            
            if result.success:
                click.echo(handler.format_output(result, output_format))
            else:
                click.echo(f"❌ 分析失败: {result.message}", err=True)
                if ctx.obj.get('debug') and result.error:
                    click.echo(f"错误详情: {result.error}", err=True)
                sys.exit(1)
                
        except Exception as e:
            _handle_command_error(e, ctx.obj.get('debug', False))

    @cli.command()
    @click.option('--today', is_flag=True, help='显示今日信号')
    @click.option('--symbol', help='指定股票代码')
    @click.option('--min-confidence', default=0.6, help='最小信号置信度')
    @click.option('--format', 'output_format', default='table', 
                  type=click.Choice(['table', 'json', 'csv']), help='输出格式')
    @click.option('--action', type=click.Choice(['buy', 'sell', 'all']), default='all', help='信号类型筛选')
    @click.option('--limit', default=20, help='最大显示信号数量')
    @click.option('--mock', is_flag=True, help='使用模拟数据')
    @click.option('--watchlist', is_flag=True, help='扫描监控列表中的所有股票')
    @click.pass_context
    def signals(ctx, today, symbol, min_confidence, output_format, action, limit, mock, watchlist):
        """扫描和显示交易信号"""
        try:
            # 确保配置是字典格式
            config_dict = ctx.obj['config']
            if hasattr(config_dict, 'to_dict'):
                config_dict = config_dict.to_dict()
            
            handler = SignalsCommandHandler(
                config=config_dict,
                logger=ctx.obj['logger']
            )
            
            result = handler.run(
                today=today,
                symbol=symbol,
                min_confidence=min_confidence,
                output_format=output_format,
                action=action,
                limit=limit,
                mock=mock,
                watchlist=watchlist
            )
            
            if result.success:
                click.echo(handler.format_output(result, output_format))
            else:
                click.echo(f"❌ 信号扫描失败: {result.message}", err=True)
                if ctx.obj.get('debug') and result.error:
                    click.echo(f"错误详情: {result.error}", err=True)
                sys.exit(1)
                
        except Exception as e:
            _handle_command_error(e, ctx.obj.get('debug', False))

    # 配置管理命令组
    @cli.group()
    def config():
        """配置管理命令"""
        pass

    @config.command('show')
    @click.option('--section', help='显示指定配置节')
    @click.option('--format', 'output_format', default='table', 
                  type=click.Choice(['table', 'json', 'yaml']), help='输出格式')
    @click.option('--stocks', is_flag=True, help='显示股票配置')
    @click.option('--strategies', is_flag=True, help='显示策略配置')
    @click.pass_context
    def config_show(ctx, section, output_format, stocks, strategies):
        """显示配置信息"""
        try:
            # 确保配置是字典格式
            config_dict = ctx.obj['config']
            if hasattr(config_dict, 'to_dict'):
                config_dict = config_dict.to_dict()
            
            handler = ConfigCommandHandler(
                config=config_dict,
                logger=ctx.obj['logger']
            )
            
            result = handler.show(
                section=section,
                output_format=output_format,
                stocks=stocks,
                strategies=strategies
            )
            
            if result.success:
                click.echo(handler.format_output(result, output_format))
            else:
                click.echo(f"❌ 配置显示失败: {result.message}", err=True)
                sys.exit(1)
                
        except Exception as e:
            _handle_command_error(e, ctx.obj.get('debug', False))

    @config.command('validate')
    @click.option('--fix', is_flag=True, help='自动修复发现的问题')
    @click.pass_context
    def config_validate(ctx, fix):
        """验证配置文件"""
        try:
            # 确保配置是字典格式
            config_dict = ctx.obj['config']
            if hasattr(config_dict, 'to_dict'):
                config_dict = config_dict.to_dict()
            
            handler = ConfigCommandHandler(
                config=config_dict,
                logger=ctx.obj['logger']
            )
            
            result = handler.validate(fix=fix)
            
            if result.success:
                click.echo(handler.format_output(result, 'table'))
            else:
                click.echo(f"❌ 配置验证失败: {result.message}", err=True)
                sys.exit(1)
                
        except Exception as e:
            _handle_command_error(e, ctx.obj.get('debug', False))

    # 添加其他配置命令的简化版本
    _add_config_commands(config)
    
    # 添加其他工具命令
    _add_utility_commands(cli)
    
    return cli


def _add_config_commands(config_group):
    """添加配置管理的其他命令"""
    
    @config_group.command('set')
    @click.argument('key')
    @click.argument('value')
    @click.option('--type', 'value_type', default='auto', 
                  type=click.Choice(['auto', 'str', 'int', 'float', 'bool']), help='值类型')
    @click.pass_context
    def config_set(ctx, key, value, value_type):
        """设置配置项"""
        _execute_config_command(ctx, 'set', key=key, value=value, value_type=value_type)

    @config_group.command('get')
    @click.argument('key')
    @click.option('--default', help='默认值')
    @click.pass_context
    def config_get(ctx, key, default):
        """获取配置项"""
        _execute_config_command(ctx, 'get', key=key, default=default)

    @config_group.command('list')
    @click.option('--pattern', help='过滤模式')
    @click.pass_context
    def config_list(ctx, pattern):
        """列出配置项"""
        _execute_config_command(ctx, 'list', pattern=pattern)

    @config_group.command('reset')
    @click.argument('key', required=False)
    @click.option('--confirm', is_flag=True, help='确认重置')
    @click.pass_context
    def config_reset(ctx, key, confirm):
        """重置配置项"""
        _execute_config_command(ctx, 'reset', key=key, confirm=confirm)

    @config_group.command('backup')
    @click.option('--output', help='备份文件路径')
    @click.pass_context
    def config_backup(ctx, output):
        """备份配置"""
        _execute_config_command(ctx, 'backup', output=output)

    @config_group.command('restore')
    @click.argument('backup_file')
    @click.option('--confirm', is_flag=True, help='确认恢复')
    @click.pass_context
    def config_restore(ctx, backup_file, confirm):
        """恢复配置"""
        _execute_config_command(ctx, 'restore', backup_file=backup_file, confirm=confirm)


def _add_utility_commands(cli):
    """添加工具命令"""
    
    @cli.command()
    @click.argument('symbol')
    @click.option('--days', default=5, help='测试数据天数')
    @click.option('--mock', is_flag=True, help='使用模拟数据进行演示')
    @click.pass_context
    def test_data(ctx, symbol, days, mock):
        """测试数据获取功能"""
        try:
            from app.data import DataManager
            
            data_manager = DataManager(ctx.obj['config'])
            
            if mock:
                click.echo(f"🔄 使用模拟数据测试 {symbol}...")
                data = data_manager.get_mock_data(symbol, days)
            else:
                click.echo(f"🔄 获取 {symbol} 最近 {days} 天的真实数据...")
                data = data_manager.get_stock_data(symbol, days)
            
            if data is not None and not data.empty:
                click.echo(f"✅ 成功获取 {len(data)} 条数据记录")
                click.echo(f"📊 数据范围: {data.index[0]} 到 {data.index[-1]}")
                click.echo(f"💰 最新价格: ${data['Close'].iloc[-1]:.2f}")
            else:
                click.echo(f"❌ 未能获取到 {symbol} 的数据")
                sys.exit(1)
                
        except Exception as e:
            _handle_command_error(e, ctx.obj.get('debug', False))

    @cli.command()
    @click.pass_context
    def status(ctx):
        """显示系统状态"""
        try:
            from app.core.config import get_config
            from app.data import DataManager
            
            config = ctx.obj['config']
            click.echo("📊 美股日内套利助手 - 系统状态")
            click.echo("=" * 50)
            
            # 配置状态
            click.echo(f"⚙️  配置文件: {'✅ 已加载' if config else '❌ 未加载'}")
            
            # 数据管理器状态
            try:
                data_manager = DataManager(config)
                click.echo(f"📈 数据管理器: ✅ 正常")
            except Exception:
                click.echo(f"📈 数据管理器: ❌ 异常")
            
            # 缓存状态
            cache_dir = Path("data/cache")
            if cache_dir.exists():
                cache_files = list(cache_dir.glob("*.pkl"))
                click.echo(f"💾 数据缓存: ✅ {len(cache_files)} 个文件")
            else:
                click.echo(f"💾 数据缓存: ❌ 目录不存在")
            
            # 日志状态
            log_dir = Path("logs")
            if log_dir.exists():
                log_files = list(log_dir.glob("*.log"))
                click.echo(f"📝 日志文件: ✅ {len(log_files)} 个文件")
            else:
                click.echo(f"📝 日志文件: ❌ 目录不存在")
            
            click.echo("=" * 50)
            click.echo("✅ 系统状态检查完成")
            
        except Exception as e:
            _handle_command_error(e, ctx.obj.get('debug', False))


def _execute_config_command(ctx, command, **kwargs):
    """执行配置命令的通用方法"""
    try:
        # 确保配置是字典格式
        config_dict = ctx.obj['config']
        if hasattr(config_dict, 'to_dict'):
            config_dict = config_dict.to_dict()
        
        handler = ConfigCommandHandler(
            config=config_dict,
            logger=ctx.obj['logger']
        )
        
        method = getattr(handler, command)
        result = method(**kwargs)
        
        if result.success:
            click.echo(handler.format_output(result, 'table'))
        else:
            click.echo(f"❌ 配置操作失败: {result.message}", err=True)
            sys.exit(1)
            
    except Exception as e:
        _handle_command_error(e, ctx.obj.get('debug', False))


def _handle_command_error(error, debug=False):
    """统一的命令错误处理"""
    click.echo(f"❌ 命令执行失败: {error}", err=True)
    if debug:
        import traceback
        click.echo(traceback.format_exc(), err=True)
    sys.exit(1) 