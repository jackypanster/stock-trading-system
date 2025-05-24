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
import yaml
from datetime import datetime
import logging

# 版本信息
__version__ = "1.0.0"
__author__ = "Trading Assistant Team"

# 全局配置
CONFIG = None


def load_config():
    """加载系统配置"""
    global CONFIG
    
    config_path = PROJECT_ROOT / "config" / "system.yaml"
    if not config_path.exists():
        click.echo(f"❌ 配置文件不存在: {config_path}", err=True)
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            CONFIG = yaml.safe_load(f)
        click.echo("✅ 配置文件加载成功")
        return CONFIG
    except Exception as e:
        click.echo(f"❌ 配置文件加载失败: {e}", err=True)
        sys.exit(1)


def setup_logging():
    """设置日志系统"""
    if not CONFIG:
        return
    
    # 创建logs目录
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 配置日志
    log_level = CONFIG.get('logging', {}).get('level', 'INFO')
    log_format = CONFIG.get('logging', {}).get('format', 
                                                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / "trading_assistant.log")
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"美股日内套利助手 v{__version__} 启动")
    return logger


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='显示版本信息')
@click.option('--config', help='指定配置文件路径')
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.pass_context
def cli(ctx, version, config, debug):
    """
    美股日内套利助手 - 个人投资分析工具
    
    通过程序化分析识别高波动美股的日内套利机会，帮助个人投资者做出更明智的投资决策。
    
    Examples:
        python main.py --version
        python main.py analyze TSLA
        python main.py signals --today
        python main.py config show
    """
    # 确保有命令上下文
    ctx.ensure_object(dict)
    
    # 显示版本信息
    if version:
        click.echo(f"美股日内套利助手 v{__version__}")
        click.echo(f"作者: {__author__}")
        click.echo(f"Python版本: {sys.version}")
        ctx.exit()
    
    # 如果没有子命令，显示帮助
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return
    
    # 加载配置
    try:
        load_config()
        ctx.obj['config'] = CONFIG
        ctx.obj['debug'] = debug
        
        # 设置日志
        if debug:
            CONFIG['logging'] = CONFIG.get('logging', {})
            CONFIG['logging']['level'] = 'DEBUG'
        
        logger = setup_logging()
        ctx.obj['logger'] = logger
        
    except Exception as e:
        click.echo(f"❌ 初始化失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('symbol')
@click.option('--format', 'output_format', default='table', 
              type=click.Choice(['table', 'json', 'csv']), help='输出格式')
@click.option('--days', default=20, help='历史数据天数')
@click.option('--mock', is_flag=True, help='使用模拟数据')
@click.pass_context
def analyze(ctx, symbol, output_format, days, mock):
    """
    分析指定股票的技术指标和交易信号
    
    SYMBOL: 股票代码，如 TSLA, NVDA, AAPL
    """
    logger = ctx.obj.get('logger')
    
    click.echo(f"🔍 正在分析股票: {symbol.upper()}")
    click.echo(f"📊 分析周期: {days}天")
    click.echo(f"📋 输出格式: {output_format}")
    if mock:
        click.echo("🎭 使用模拟数据模式")
    
    try:
        # 导入必要模块
        from app.data.fetcher import get_fetcher, DataFetchError
        from app.analysis.indicators import analyze_stock_technical
        import json
        
        # 获取数据
        fetcher = get_fetcher(use_mock=mock)
        
        click.echo("⏳ 获取历史数据...")
        
        # 确定数据周期
        period_map = {
            5: "5d", 10: "10d", 20: "1mo", 30: "1mo", 
            60: "2mo", 90: "3mo", 180: "6mo", 365: "1y"
        }
        period = period_map.get(days, "1mo")
        
        # 获取历史数据
        hist_data = fetcher.get_historical_data(symbol, period=period)
        
        if len(hist_data) < 15:  # RSI至少需要15个数据点
            click.echo("❌ 历史数据不足，无法进行技术分析")
            click.echo(f"当前数据点: {len(hist_data)}, 最少需要: 15")
            return
        
        click.echo(f"✅ 获取到 {len(hist_data)} 条历史数据")
        
        # 进行技术分析
        click.echo("⏳ 计算技术指标...")
        
        analysis_result = analyze_stock_technical(hist_data)
        
        # 根据输出格式显示结果
        if output_format == 'json':
            click.echo("\n📋 技术分析结果 (JSON格式):")
            click.echo(json.dumps(analysis_result, indent=2, ensure_ascii=False))
            
        elif output_format == 'csv':
            click.echo("\n📋 技术分析结果 (CSV格式):")
            # 简化的CSV输出
            rsi_data = analysis_result['indicators']['rsi_14']
            macd_data = analysis_result['indicators']['macd']
            ma_data = analysis_result['indicators']['moving_averages']
            
            click.echo("指标,数值,状态")
            click.echo(f"当前价格,{analysis_result['current_price']},--")
            click.echo(f"RSI(14),{rsi_data['current_rsi']},{rsi_data['status']}")
            
            if 'error' not in macd_data:
                click.echo(f"MACD线,{macd_data['current_macd']},{macd_data['cross_signal']}")
                click.echo(f"MACD信号线,{macd_data['current_signal']},{macd_data['position']}")
                click.echo(f"MACD柱状图,{macd_data['current_histogram']},{macd_data['histogram_trend']}")
            else:
                click.echo(f"MACD,错误,{macd_data['error']}")
            
            click.echo(f"SMA(20),{ma_data['sma_20']},--")
            click.echo(f"SMA(50),{ma_data['sma_50']},--")
            click.echo(f"EMA(12),{ma_data['ema_12']},--")
            click.echo(f"EMA(26),{ma_data['ema_26']},--")
            
        else:  # table格式（默认）
            click.echo("\n📈 技术分析结果:")
            click.echo("=" * 60)
            
            # 基本信息
            click.echo(f"股票代码: {analysis_result['symbol']}")
            click.echo(f"当前价格: ${analysis_result['current_price']}")
            click.echo(f"分析时间: {analysis_result['analysis_date']}")
            
            # RSI分析
            rsi_data = analysis_result['indicators']['rsi_14']
            click.echo(f"\n📊 RSI (14) 分析:")
            click.echo(f"  当前RSI: {rsi_data['current_rsi']}")
            click.echo(f"  状态: {rsi_data['status']}")
            click.echo(f"  信号: {rsi_data['signal']}")
            click.echo(f"  超卖线: {rsi_data['oversold_level']}")
            click.echo(f"  超买线: {rsi_data['overbought_level']}")
            
            if rsi_data['statistics']['min'] is not None:
                stats = rsi_data['statistics']
                click.echo(f"  统计信息: 最小={stats['min']}, 最大={stats['max']}, 平均={stats['mean']}")
            
            # MACD分析
            macd_data = analysis_result['indicators']['macd']
            click.echo(f"\n📈 MACD (12,26,9) 分析:")
            if 'error' not in macd_data:
                click.echo(f"  MACD线: {macd_data['current_macd']}")
                click.echo(f"  信号线: {macd_data['current_signal']}")
                click.echo(f"  柱状图: {macd_data['current_histogram']}")
                click.echo(f"  交叉信号: {macd_data['cross_signal']}")
                click.echo(f"  信号类型: {macd_data['signal_type']}")
                click.echo(f"  零轴穿越: {macd_data['zero_cross']}")
                click.echo(f"  位置: {macd_data['position']}")
                click.echo(f"  柱状图趋势: {macd_data['histogram_trend']}")
            else:
                click.echo(f"  错误: {macd_data['error']}")
            
            # 移动平均线
            ma_data = analysis_result['indicators']['moving_averages']
            click.echo(f"\n📈 移动平均线:")
            click.echo(f"  SMA(20): ${ma_data['sma_20']}")
            click.echo(f"  SMA(50): ${ma_data['sma_50']}")
            click.echo(f"  EMA(12): ${ma_data['ema_12']}")
            click.echo(f"  EMA(26): ${ma_data['ema_26']}")
            
            # 价格位置分析
            pos_data = analysis_result['price_position']
            click.echo(f"\n📍 价格位置分析:")
            click.echo(f"  相对SMA(20): {pos_data['vs_sma_20']}")
            click.echo(f"  相对SMA(50): {pos_data['vs_sma_50']}")
            click.echo(f"  相对EMA(12): {pos_data['vs_ema_12']}")
            
            # 交易建议
            click.echo(f"\n💡 交易建议:")
            
            # RSI建议
            if rsi_data['signal'] != "无信号":
                if rsi_data['signal'] == "买入信号":
                    click.echo("  🟢 RSI显示超卖，可能是买入机会")
                elif rsi_data['signal'] == "卖出信号":
                    click.echo("  🔴 RSI显示超买，可能是卖出机会")
            else:
                click.echo("  ⚪ RSI处于正常范围，无明显信号")
            
            # MACD建议
            if 'error' not in macd_data and macd_data['signal_type'] != "无信号":
                if macd_data['signal_type'] == "买入信号":
                    click.echo("  🟢 MACD金叉，趋势转多")
                elif macd_data['signal_type'] == "卖出信号":
                    click.echo("  🔴 MACD死叉，趋势转空")
            elif 'error' not in macd_data:
                click.echo("  ⚪ MACD无明显交叉信号")
            
            # 零轴穿越提示
            if 'error' not in macd_data and macd_data['zero_cross'] != "无":
                if macd_data['zero_cross'] == "上穿零轴":
                    click.echo("  📈 MACD上穿零轴，确认多头趋势")
                elif macd_data['zero_cross'] == "下穿零轴":
                    click.echo("  📉 MACD下穿零轴，确认空头趋势")
            
            # 趋势分析
            above_count = sum(1 for v in pos_data.values() if v == "above")
            if above_count >= 2:
                click.echo("  📈 价格在多数均线上方，趋势偏多头")
            elif above_count <= 1:
                click.echo("  📉 价格在多数均线下方，趋势偏空头")
            else:
                click.echo("  ➡️ 价格在均线附近，趋势不明确")
        
        # 记录日志
        if logger:
            logger.info(f"技术分析完成: {symbol} (模拟模式: {mock})")
            
        click.echo(f"\n✅ 技术分析完成！")
        
    except ImportError as e:
        click.echo(f"❌ 导入分析模块失败: {e}")
        if logger:
            logger.error(f"分析模块导入失败: {e}")
    except DataFetchError as e:
        click.echo(f"❌ 数据获取失败: {e}")
        if logger:
            logger.error(f"数据获取失败: {e}")
    except Exception as e:
        click.echo(f"❌ 技术分析失败: {e}", err=True)
        if logger:
            logger.error(f"技术分析失败: {e}")


@cli.command()
@click.option('--today', is_flag=True, help='显示今日信号')
@click.option('--symbol', help='指定股票代码')
@click.option('--min-confidence', default=0.6, help='最小信号置信度')
@click.pass_context
def signals(ctx, today, symbol, min_confidence):
    """
    显示交易信号
    """
    logger = ctx.obj.get('logger')
    
    if today:
        click.echo("📡 获取今日交易信号...")
        date_filter = datetime.now().strftime("%Y-%m-%d")
    else:
        click.echo("📡 获取最新交易信号...")
        date_filter = "最新"
    
    if symbol:
        click.echo(f"🎯 股票筛选: {symbol.upper()}")
    
    click.echo(f"📊 置信度阈值: {min_confidence}")
    
    # TODO: 实现信号获取逻辑
    if logger:
        logger.info(f"获取交易信号 - 日期:{date_filter}, 股票:{symbol}, 置信度:{min_confidence}")
    
    # 模拟信号结果
    click.echo("\n📈 交易信号:")
    click.echo("暂无活跃信号 (信号生成功能开发中)")
    
    click.echo("\n⚠️  注意: 信号生成功能正在开发中")


@cli.group()
def config():
    """配置管理命令"""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """显示当前配置"""
    config = ctx.obj.get('config', {})
    
    click.echo("⚙️  当前系统配置:")
    click.echo(f"应用名称: {config.get('app', {}).get('name', 'N/A')}")
    click.echo(f"版本: {config.get('version', 'N/A')}")
    click.echo(f"日志级别: {config.get('logging', {}).get('level', 'N/A')}")
    click.echo(f"主数据源: {config.get('data', {}).get('primary_source', 'N/A')}")
    click.echo(f"最大总仓位: {config.get('risk', {}).get('max_total_exposure', 'N/A')}")


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """验证配置文件"""
    click.echo("🔍 验证配置文件...")
    
    # 验证主配置文件
    config_path = PROJECT_ROOT / "config" / "system.yaml"
    if config_path.exists():
        click.echo("✅ system.yaml 存在")
        try:
            with open(config_path, 'r') as f:
                yaml.safe_load(f)
            click.echo("✅ system.yaml 格式正确")
        except Exception as e:
            click.echo(f"❌ system.yaml 格式错误: {e}")
    else:
        click.echo("❌ system.yaml 不存在")
    
    # 验证股票配置目录
    stocks_dir = PROJECT_ROOT / "config" / "stocks"
    if stocks_dir.exists():
        stock_files = list(stocks_dir.glob("*.yaml"))
        click.echo(f"📁 找到 {len(stock_files)} 个股票配置文件")
        for stock_file in stock_files:
            try:
                with open(stock_file, 'r') as f:
                    yaml.safe_load(f)
                click.echo(f"✅ {stock_file.name} 格式正确")
            except Exception as e:
                click.echo(f"❌ {stock_file.name} 格式错误: {e}")
    else:
        click.echo("❌ stocks配置目录不存在")


@cli.command()
@click.argument('symbol')
@click.option('--days', default=5, help='测试数据天数')
@click.option('--mock', is_flag=True, help='使用模拟数据进行演示')
@click.pass_context
def test_data(ctx, symbol, days, mock):
    """
    测试数据获取功能
    
    SYMBOL: 股票代码
    """
    logger = ctx.obj.get('logger')
    
    click.echo(f"🧪 测试数据获取: {symbol.upper()}")
    click.echo(f"📅 数据天数: {days}天")
    if mock:
        click.echo("🎭 使用模拟数据模式")
    
    try:
        # 导入数据获取器
        from app.data.fetcher import get_fetcher, DataFetchError
        
        fetcher = get_fetcher(use_mock=mock)
        
        # 1. 测试连接
        click.echo("⏳ 测试数据源连接...")
        if fetcher.test_connection(symbol):
            click.echo("✅ 数据源连接成功")
        else:
            click.echo("❌ 数据源连接失败")
            return
        
        # 2. 获取当前价格
        click.echo(f"⏳ 获取 {symbol.upper()} 当前价格...")
        try:
            price_data = fetcher.get_current_price(symbol)
            
            click.echo("\n📊 当前价格信息:")
            click.echo(f"股票代码: {price_data['symbol']}")
            click.echo(f"当前价格: ${price_data['current_price']:.2f}")
            if price_data.get('change'):
                change_symbol = "📈" if price_data['change'] > 0 else "📉"
                click.echo(f"涨跌: {change_symbol} ${price_data['change']:.2f} ({price_data['change_percent']:.2f}%)")
            click.echo(f"开盘价: ${price_data['open_price']:.2f}")
            click.echo(f"最高价: ${price_data['day_high']:.2f}")
            click.echo(f"最低价: ${price_data['day_low']:.2f}")
            click.echo(f"成交量: {price_data['volume']:,}")
            click.echo(f"交易所: {price_data['exchange']}")
            
        except DataFetchError as e:
            click.echo(f"❌ 获取价格失败: {e}")
            return
        
        # 3. 获取历史数据
        period_map = {
            1: "1d", 2: "2d", 3: "5d", 4: "5d", 5: "5d",
            10: "10d", 20: "1mo", 30: "1mo"
        }
        period = period_map.get(days, "5d")
        
        click.echo(f"\n⏳ 获取 {days} 天历史数据...")
        try:
            hist_data = fetcher.get_historical_data(symbol, period=period)
            
            click.echo(f"\n📈 历史数据 (最近{len(hist_data)}条记录):")
            click.echo("日期\t\t开盘\t最高\t最低\t收盘\t成交量")
            click.echo("-" * 60)
            
            # 显示最近几天的数据
            for idx, (date, row) in enumerate(hist_data.tail(min(5, len(hist_data))).iterrows()):
                date_str = date.strftime("%Y-%m-%d")
                click.echo(f"{date_str}\t{row['Open']:.2f}\t{row['High']:.2f}\t{row['Low']:.2f}\t{row['Close']:.2f}\t{row['Volume']:,}")
            
            if len(hist_data) > 5:
                click.echo(f"... (共 {len(hist_data)} 条记录)")
                
        except DataFetchError as e:
            click.echo(f"❌ 获取历史数据失败: {e}")
        
        # 4. 获取股票信息
        click.echo(f"\n⏳ 获取 {symbol.upper()} 基本信息...")
        try:
            stock_info = fetcher.get_stock_info(symbol)
            
            click.echo(f"\n🏢 股票信息:")
            click.echo(f"公司名称: {stock_info.get('company_name', 'N/A')}")
            click.echo(f"行业: {stock_info.get('sector', 'N/A')} - {stock_info.get('industry', 'N/A')}")
            click.echo(f"国家: {stock_info.get('country', 'N/A')}")
            if stock_info.get('market_cap'):
                market_cap_b = stock_info['market_cap'] / 1e9
                click.echo(f"市值: ${market_cap_b:.1f}B")
            if stock_info.get('beta'):
                click.echo(f"Beta: {stock_info['beta']:.2f}")
            if stock_info.get('trailing_pe'):
                click.echo(f"市盈率: {stock_info['trailing_pe']:.2f}")
                
        except DataFetchError as e:
            click.echo(f"⚠️ 获取股票信息失败: {e}")
        
        # 记录日志
        if logger:
            logger.info(f"数据获取测试完成: {symbol} (模拟模式: {mock})")
            
        click.echo(f"\n✅ 数据获取测试完成！")
        
    except ImportError as e:
        click.echo(f"❌ 导入数据模块失败: {e}")
        if logger:
            logger.error(f"数据模块导入失败: {e}")
    except Exception as e:
        click.echo(f"❌ 数据获取测试失败: {e}", err=True)
        if logger:
            logger.error(f"数据获取测试失败: {e}")


@cli.command()
@click.argument('symbol')
@click.option('--calls', default=5, help='测试调用次数')
@click.pass_context
def test_backup(ctx, symbol, calls):
    """
    测试备用数据源切换机制
    
    SYMBOL: 股票代码
    """
    logger = ctx.obj.get('logger')
    
    click.echo(f"🧪 测试备用数据源机制: {symbol.upper()}")
    click.echo(f"📞 测试调用次数: {calls}")
    
    try:
        # 导入测试模块
        from app.data.fetcher import create_test_fetcher_with_failing_primary, DataFetchError
        
        # 创建会失败的数据获取器
        fetcher = create_test_fetcher_with_failing_primary()
        
        click.echo("\n🔄 开始测试数据源切换...")
        click.echo("预期：前2次成功，第3次主数据源失败并切换到备用源")
        
        for i in range(1, calls + 1):
            try:
                click.echo(f"\n--- 第 {i} 次调用 ---")
                
                # 获取数据源状态
                status = fetcher.get_source_status()
                click.echo(f"当前数据源: {status['current_source']}")
                click.echo(f"失败次数: {status['source_failures']}")
                
                # 尝试获取数据
                result = fetcher.test_get_current_price(symbol)
                
                click.echo(f"✅ 成功获取价格: ${result['current_price']}")
                click.echo(f"数据来源: {result.get('exchange', '未知')}")
                
            except DataFetchError as e:
                click.echo(f"❌ 获取失败: {e}")
                
                # 显示最终状态
                final_status = fetcher.get_source_status()
                click.echo(f"最终数据源: {final_status['current_source']}")
                click.echo(f"失败统计: {final_status['source_failures']}")
                break
        
        # 显示最终测试结果
        final_status = fetcher.get_source_status()
        click.echo(f"\n📊 测试完成!")
        click.echo(f"主数据源: {final_status['primary_source']}")
        click.echo(f"当前数据源: {final_status['current_source']}")
        click.echo(f"备用数据源: {final_status['backup_sources']}")
        click.echo(f"失败统计: {final_status['source_failures']}")
        
        # 验证切换是否成功
        if final_status['current_source'] != final_status['primary_source']:
            click.echo("✅ 备用数据源切换机制工作正常！")
        else:
            click.echo("⚠️ 未发生数据源切换")
        
        if logger:
            logger.info(f"备用数据源测试完成: {symbol}")
            
    except ImportError as e:
        click.echo(f"❌ 导入测试模块失败: {e}")
        if logger:
            logger.error(f"测试模块导入失败: {e}")
    except Exception as e:
        click.echo(f"❌ 备用数据源测试失败: {e}", err=True)
        if logger:
            logger.error(f"备用数据源测试失败: {e}")


@cli.command()
@click.pass_context
def status(ctx):
    """显示系统状态"""
    click.echo("🏥 系统状态检查...")
    
    # 检查配置
    if CONFIG:
        click.echo("✅ 配置系统: 正常")
    else:
        click.echo("❌ 配置系统: 异常")
    
    # 检查目录结构
    required_dirs = ['app', 'config', 'data', 'logs']
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            click.echo(f"✅ 目录 {dir_name}/: 存在")
        else:
            click.echo(f"❌ 目录 {dir_name}/: 缺失")
    
    # 检查关键文件
    required_files = [
        'config/system.yaml',
        'requirements.txt',
        'README.md'
    ]
    for file_name in required_files:
        file_path = PROJECT_ROOT / file_name
        if file_path.exists():
            click.echo(f"✅ 文件 {file_name}: 存在")
        else:
            click.echo(f"❌ 文件 {file_name}: 缺失")
    
    click.echo(f"\n📍 项目根目录: {PROJECT_ROOT}")
    click.echo(f"🐍 Python版本: {sys.version}")
    click.echo(f"📦 应用版本: v{__version__}")


def main():
    """主入口函数"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\n👋 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n❌ 程序执行错误: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 