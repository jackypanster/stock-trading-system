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
import json

# 版本信息
__version__ = "1.0.0"
__author__ = "Trading Assistant Team"

# 自定义JSON编码器，处理Timestamp等不可序列化对象
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'strftime'):  # 处理日期时间对象
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        if hasattr(obj, 'item'):  # 处理numpy类型
            return obj.item()
        if hasattr(obj, 'tolist'):  # 处理numpy数组
            return obj.tolist()
        if hasattr(obj, '__dict__'):  # 处理dataclass和其他对象
            return obj.__dict__
        return super().default(obj)


# 配置加载已移至 app.core.config 模块统一管理


def setup_logging(config):
    """设置日志系统"""
    if not config:
        return
    
    # 创建logs目录
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # 配置日志
    log_level = config.get('logging', {}).get('level', 'INFO')
    log_format = config.get('logging', {}).get('format', 
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
        from app.core.config import get_config
        config = get_config()
        ctx.obj['config'] = config
        ctx.obj['debug'] = debug
        
        # 设置日志
        if debug:
            config['logging'] = config.get('logging', {})
            config['logging']['level'] = 'DEBUG'
        
        logger = setup_logging(config)
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
@click.option('--with-signals', is_flag=True, help='包含交易信号分析')
@click.option('--with-risk', is_flag=True, help='包含风险管理分析')
@click.option('--portfolio-value', default=100000, help='投资组合价值（用于风险计算）')
@click.pass_context
def analyze(ctx, symbol, output_format, days, mock, with_signals, with_risk, portfolio_value):
    """
    分析指定股票的技术指标和交易信号
    
    SYMBOL: 股票代码，如 TSLA, NVDA, AAPL
    """
    logger = ctx.obj.get('logger')
    config = ctx.obj.get('config', {})
    
    click.echo(f"🔍 正在分析股票: {symbol.upper()}")
    click.echo(f"📊 分析周期: {days}天")
    click.echo(f"📋 输出格式: {output_format}")
    if mock:
        click.echo("🎭 使用模拟数据模式")
    if with_signals:
        click.echo("📡 包含交易信号分析")
    if with_risk:
        click.echo(f"🛡️ 包含风险管理分析 (投资组合价值: ${portfolio_value:,.2f})")
    
    try:
        # 导入必要模块
        from app.data.fetcher import get_fetcher, DataFetchError
        from app.analysis.indicators import analyze_stock_technical
        
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
        
        # 信号生成分析
        signals_result = None
        if with_signals:
            try:
                click.echo("⏳ 生成交易信号...")
                from app.analysis.strategies import SupportResistanceStrategy
                from app.analysis.confidence import ConfidenceCalculator
                from app.analysis.signal_filter import SignalFilter
                
                # 创建策略实例
                strategy = SupportResistanceStrategy(config)
                confidence_calc = ConfidenceCalculator(config)
                signal_filter = SignalFilter(config)
                
                # 生成信号
                all_signals = strategy.analyze(hist_data, analysis_result=analysis_result)
                
                # 分离买入和卖出信号
                buy_signals = [s for s in all_signals if s.signal_type == 'buy']
                sell_signals = [s for s in all_signals if s.signal_type == 'sell']
                
                # 信号已经包含置信度，无需重新计算
                # 策略在生成信号时已经计算了置信度
                
                # 过滤信号
                filter_result = signal_filter.filter_signals(all_signals)
                filtered_signals = filter_result.get('filtered_signals', [])
                
                signals_result = {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'filtered_signals': filtered_signals,
                    'filter_stats': filter_result.get('statistics', {})
                }
                
                click.echo(f"✅ 信号生成完成: {len(buy_signals)}个买入信号, {len(sell_signals)}个卖出信号")
                click.echo(f"📊 信号过滤: {len(all_signals)}个原始信号 → {len(filtered_signals)}个高质量信号")
                
            except Exception as e:
                click.echo(f"⚠️ 信号生成失败: {e}")
                if logger:
                    logger.warning(f"信号生成失败: {e}")
        
        # 风险管理分析
        risk_result = None
        if with_risk:
            try:
                click.echo("⏳ 计算风险管理指标...")
                from app.core.risk_manager import RiskManager
                from app.core.portfolio import Portfolio
                
                # 创建风险管理器
                risk_manager = RiskManager(config)
                
                # 获取当前价格
                current_price = analysis_result['current_price']
                
                # 获取股票配置
                stock_config = config.get('stocks', {}).get(symbol.upper(), {})
                if not stock_config:
                    # 使用默认配置
                    stock_config = {
                        'risk': {
                            'stop_loss_pct': 0.02,
                            'take_profit_pct': 0.05,
                            'max_position_pct': 0.15
                        },
                        'trading': {
                            'position_sizing': 'fixed_percent',
                            'min_trade_amount': 1000
                        }
                    }
                
                # 计算买入场景的风险指标
                buy_stop_loss, buy_take_profit = risk_manager.calculate_stop_loss_take_profit(
                    current_price, "BUY", stock_config
                )
                buy_position_size = risk_manager.calculate_position_size(
                    current_price, buy_stop_loss, portfolio_value * 0.8, stock_config  # 假设80%可用于交易
                )
                buy_risk_metrics = risk_manager.calculate_risk_metrics(
                    current_price, buy_stop_loss, buy_take_profit, buy_position_size, portfolio_value
                )
                
                # 计算卖出场景的风险指标
                sell_stop_loss, sell_take_profit = risk_manager.calculate_stop_loss_take_profit(
                    current_price, "SELL", stock_config
                )
                sell_position_size = risk_manager.calculate_position_size(
                    current_price, sell_stop_loss, portfolio_value * 0.8, stock_config
                )
                sell_risk_metrics = risk_manager.calculate_risk_metrics(
                    current_price, sell_stop_loss, sell_take_profit, sell_position_size, portfolio_value
                )
                
                # 评估投资组合风险（假设当前无持仓）
                portfolio_risk = risk_manager.assess_portfolio_risk([], portfolio_value)
                
                risk_result = {
                    'buy_scenario': {
                        'stop_loss': buy_stop_loss,
                        'take_profit': buy_take_profit,
                        'position_size': buy_position_size,
                        'risk_metrics': buy_risk_metrics
                    },
                    'sell_scenario': {
                        'stop_loss': sell_stop_loss,
                        'take_profit': sell_take_profit,
                        'position_size': sell_position_size,
                        'risk_metrics': sell_risk_metrics
                    },
                    'portfolio_risk': portfolio_risk,
                    'stock_config': stock_config
                }
                
                click.echo("✅ 风险管理分析完成")
                
            except Exception as e:
                click.echo(f"⚠️ 风险管理分析失败: {e}")
                if logger:
                    logger.warning(f"风险管理分析失败: {e}")
        
        # 根据输出格式显示结果
        if output_format == 'json':
            # JSON格式输出
            result = {
                'technical_analysis': analysis_result,
                'signals': signals_result,
                'risk_management': risk_result
            }
            click.echo("\n📋 完整分析结果 (JSON格式):")
            click.echo(json.dumps(result, indent=2, ensure_ascii=False, cls=CustomJSONEncoder))
            
        elif output_format == 'csv':
            # CSV格式输出（简化版）
            click.echo("\n📋 技术分析结果 (CSV格式):")
            
            # CSV头部
            click.echo("指标,数值,状态")
            
            # 基本信息
            click.echo(f"股票代码,{analysis_result['symbol']},--")
            click.echo(f"当前价格,{analysis_result['current_price']},--")
            
            # RSI数据
            rsi_data = analysis_result['indicators']['rsi_14']
            click.echo(f"RSI(14),{rsi_data['current_rsi']},{rsi_data['status']}")
            
            # MACD数据
            macd_data = analysis_result['indicators']['macd']
            if 'error' not in macd_data:
                click.echo(f"MACD线,{macd_data['current_macd']},{macd_data['cross_signal']}")
                click.echo(f"MACD信号线,{macd_data['current_signal']},{macd_data['position']}")
                click.echo(f"MACD柱状图,{macd_data['current_histogram']},{macd_data['histogram_trend']}")
            else:
                click.echo(f"MACD,错误,{macd_data['error']}")
            
            # ATR数据
            atr_data = analysis_result['indicators']['atr']
            if 'error' not in atr_data:
                click.echo(f"ATR(14),{atr_data['current_atr']},{atr_data['volatility_level']}")
                click.echo(f"ATR百分比,{atr_data['atr_percentage']}%,{atr_data['volatility_signal']}")
            else:
                click.echo(f"ATR,错误,{atr_data['error']}")
            
            # 移动平均线
            ma_data = analysis_result['indicators']['moving_averages']
            click.echo(f"SMA(20),{ma_data['sma_20']},--")
            click.echo(f"SMA(50),{ma_data['sma_50']},--")
            click.echo(f"EMA(12),{ma_data['ema_12']},--")
            click.echo(f"EMA(26),{ma_data['ema_26']},--")
            
            # 支撑阻力位信息
            if 'support_resistance' in analysis_result:
                sr_data = analysis_result['support_resistance']
                summary = sr_data.get('summary', {})
                click.echo(f"识别高点,{summary.get('identified_highs', 0)},个")
                click.echo(f"识别低点,{summary.get('identified_lows', 0)},个")
                click.echo(f"支撑位数量,{summary.get('support_levels', 0)},个")
                click.echo(f"阻力位数量,{summary.get('resistance_levels', 0)},个")
                
                # 显示最强的支撑阻力位
                sr_levels = sr_data.get('support_resistance', {})
                resistance_levels = sr_levels.get('resistance_levels', [])
                if resistance_levels:
                    top_resistance = resistance_levels[0]
                    click.echo(f"主要阻力位,${top_resistance['price']},{top_resistance['strength_rating']}")
                
                support_levels = sr_levels.get('support_levels', [])
                if support_levels:
                    top_support = support_levels[0]
                    click.echo(f"主要支撑位,${top_support['price']},{top_support['strength_rating']}")
                
                # 当前位置
                current_pos = sr_levels.get('current_position')
                if current_pos:
                    click.echo(f"当前位置,{current_pos['position_description']},--")
            
            # 信号和风险数据
            if signals_result:
                buy_signals = signals_result['buy_signals']
                sell_signals = signals_result['sell_signals']
                filtered_signals = signals_result['filtered_signals']
                click.echo(f"买入信号数量,{len(buy_signals)},个")
                click.echo(f"卖出信号数量,{len(sell_signals)},个")
                click.echo(f"高质量信号数量,{len(filtered_signals)},个")
            
            if risk_result:
                portfolio_risk = risk_result['portfolio_risk']
                buy_scenario = risk_result['buy_scenario']
                click.echo(f"投资组合价值,${portfolio_risk.total_value:,.2f},--")
                click.echo(f"风险级别,{portfolio_risk.risk_level},--")
                click.echo(f"买入建议仓位,{buy_scenario['position_size']},股")
                click.echo(f"买入止损价位,${buy_scenario['stop_loss']:.2f},--")
                click.echo(f"买入止盈价位,${buy_scenario['take_profit']:.2f},--")
            
        else:  # table格式（默认）
            # 显示技术分析结果
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
            
            # ATR分析
            atr_data = analysis_result['indicators']['atr']
            click.echo(f"\n📊 ATR (14) 波动率分析:")
            if 'error' not in atr_data:
                click.echo(f"  当前ATR: {atr_data['current_atr']}")
                click.echo(f"  ATR百分比: {atr_data['atr_percentage']}%")
                click.echo(f"  波动率水平: {atr_data['volatility_level']}")
                click.echo(f"  波动率信号: {atr_data['volatility_signal']}")
                click.echo(f"  ATR趋势: {atr_data['atr_trend']}")
                if atr_data['atr_change_5d'] != 0:
                    click.echo(f"  5日变化: {atr_data['atr_change_5d']:+.2f}%")
                
                # 显示建议止损位
                click.echo(f"  建议止损位:")
                for level, data in atr_data['stop_loss_levels'].items():
                    multiplier = level.replace('atr_', '').replace('x', '')
                    click.echo(f"    {multiplier}倍ATR: 多头止损${data['long_stop']}, 空头止损${data['short_stop']}")
                
                if atr_data['statistics']['min'] is not None:
                    stats = atr_data['statistics']
                    click.echo(f"  统计信息: 最小={stats['min']}, 最大={stats['max']}, 平均={stats['mean']}")
            else:
                click.echo(f"  错误: {atr_data['error']}")
            
            # 移动平均线
            ma_data = analysis_result['indicators']['moving_averages']
            click.echo(f"\n📈 移动平均线:")
            click.echo(f"  SMA(20): ${ma_data['sma_20']}")
            click.echo(f"  SMA(50): ${ma_data['sma_50']}")
            click.echo(f"  EMA(12): ${ma_data['ema_12']}")
            click.echo(f"  EMA(26): ${ma_data['ema_26']}")
            
            # 支撑阻力位分析
            if 'support_resistance' in analysis_result:
                sr_data = analysis_result['support_resistance']
                click.echo(f"\n🎯 支撑阻力位分析:")
                
                # 显示分析概要
                summary = sr_data.get('summary', {})
                click.echo(f"  识别高点: {summary.get('identified_highs', 0)}")
                click.echo(f"  识别低点: {summary.get('identified_lows', 0)}")
                click.echo(f"  支撑位: {summary.get('support_levels', 0)}")
                click.echo(f"  阻力位: {summary.get('resistance_levels', 0)}")
                
                # 显示关键支撑阻力位
                sr_levels = sr_data.get('support_resistance', {})
                
                # 显示主要阻力位
                resistance_levels = sr_levels.get('resistance_levels', [])
                if resistance_levels:
                    click.echo(f"  主要阻力位:")
                    for i, level in enumerate(resistance_levels[:3]):  # 显示前3个
                        strength = level['strength_rating']
                        touch_count = level['touch_count']
                        click.echo(f"    ${level['price']} (触及{touch_count}次, 强度:{strength})")
                
                # 显示主要支撑位
                support_levels = sr_levels.get('support_levels', [])
                if support_levels:
                    click.echo(f"  主要支撑位:")
                    for i, level in enumerate(support_levels[:3]):  # 显示前3个
                        strength = level['strength_rating']
                        touch_count = level['touch_count']
                        click.echo(f"    ${level['price']} (触及{touch_count}次, 强度:{strength})")
                
                # 显示当前位置分析
                current_pos = sr_levels.get('current_position')
                if current_pos:
                    click.echo(f"  当前位置: {current_pos['position_description']}")
                    
                    # 显示距离信息
                    if current_pos.get('resistance_distance'):
                        res_dist = current_pos['resistance_distance']
                        click.echo(f"  距离上方阻力位: ${res_dist['price_diff']} ({res_dist['percentage']:+.1f}%)")
                    
                    if current_pos.get('support_distance'):
                        sup_dist = current_pos['support_distance']
                        click.echo(f"  距离下方支撑位: ${sup_dist['price_diff']} ({sup_dist['percentage']:+.1f}%)")
                
                # 显示交易信号
                trading_signals = sr_data.get('trading_signals', {})
                if trading_signals.get('signals'):
                    click.echo(f"  📡 支撑阻力位信号:")
                    for signal in trading_signals['signals']:
                        signal_type = signal['type']
                        if signal_type == 'warning':
                            emoji = "⚠️"
                        elif signal_type == 'opportunity':
                            emoji = "💡"
                        else:
                            emoji = "📊"
                        click.echo(f"    {emoji} {signal['signal']}: {signal['description']}")
            
            # 显示交易信号分析
            if signals_result:
                click.echo(f"\n📡 交易信号分析:")
                click.echo("=" * 60)
                
                # 显示买入信号
                buy_signals = signals_result['buy_signals']
                if buy_signals:
                    click.echo(f"\n🟢 买入信号 ({len(buy_signals)}个):")
                    for i, signal in enumerate(buy_signals[:3], 1):  # 显示前3个
                        click.echo(f"  {i}. 价格: ${signal.price:.2f}")
                        click.echo(f"     置信度: {signal.confidence:.2%}")
                        click.echo(f"     原因: {signal.reason}")
                        if hasattr(signal, 'stop_loss') and signal.stop_loss:
                            click.echo(f"     止损: ${signal.stop_loss:.2f}")
                        if hasattr(signal, 'take_profit') and signal.take_profit:
                            click.echo(f"     止盈: ${signal.take_profit:.2f}")
                        click.echo()
                else:
                    click.echo(f"\n🟢 买入信号: 无")
                
                # 显示卖出信号
                sell_signals = signals_result['sell_signals']
                if sell_signals:
                    click.echo(f"\n🔴 卖出信号 ({len(sell_signals)}个):")
                    for i, signal in enumerate(sell_signals[:3], 1):  # 显示前3个
                        click.echo(f"  {i}. 价格: ${signal.price:.2f}")
                        click.echo(f"     置信度: {signal.confidence:.2%}")
                        click.echo(f"     原因: {signal.reason}")
                        if hasattr(signal, 'stop_loss') and signal.stop_loss:
                            click.echo(f"     止损: ${signal.stop_loss:.2f}")
                        if hasattr(signal, 'take_profit') and signal.take_profit:
                            click.echo(f"     止盈: ${signal.take_profit:.2f}")
                        click.echo()
                else:
                    click.echo(f"\n🔴 卖出信号: 无")
                
                # 显示过滤后的高质量信号
                filtered_signals = signals_result['filtered_signals']
                if filtered_signals:
                    click.echo(f"\n⭐ 高质量信号 ({len(filtered_signals)}个):")
                    for i, signal in enumerate(filtered_signals, 1):
                        action_emoji = "🟢" if signal.action == "BUY" else "🔴"
                        click.echo(f"  {i}. {action_emoji} {signal.action} @ ${signal.price:.2f}")
                        click.echo(f"     置信度: {signal.confidence:.2%}")
                        click.echo(f"     原因: {signal.reason}")
                        click.echo()
                else:
                    click.echo(f"\n⭐ 高质量信号: 无")
                
                # 显示过滤统计
                filter_stats = signals_result['filter_stats']
                if filter_stats:
                    click.echo(f"\n📊 信号过滤统计:")
                    click.echo(f"  原始信号: {filter_stats.get('total_signals', 0)}")
                    click.echo(f"  过滤后信号: {filter_stats.get('filtered_signals', 0)}")
                    click.echo(f"  过滤率: {filter_stats.get('filter_rate', 0):.1%}")
                    
                    reasons = filter_stats.get('filter_reasons', {})
                    if reasons:
                        click.echo(f"  过滤原因:")
                        for reason, count in reasons.items():
                            click.echo(f"    {reason}: {count}")
            
            # 显示风险管理分析
            if risk_result:
                click.echo(f"\n🛡️ 风险管理分析:")
                click.echo("=" * 60)
                
                # 投资组合风险概览
                portfolio_risk = risk_result['portfolio_risk']
                click.echo(f"\n📊 投资组合风险概览:")
                click.echo(f"  总价值: ${portfolio_risk.total_value:,.2f}")
                click.echo(f"  现金: ${portfolio_risk.available_cash:,.2f}")
                click.echo(f"  风险级别: {portfolio_risk.risk_level}")
                click.echo(f"  可用于新仓位: ${portfolio_risk.max_new_position:,.2f}")
                
                # 买入场景风险分析
                buy_scenario = risk_result['buy_scenario']
                buy_metrics = buy_scenario['risk_metrics']
                click.echo(f"\n🟢 买入场景风险分析:")
                click.echo(f"  建议仓位: {buy_scenario['position_size']} 股")
                click.echo(f"  仓位价值: ${buy_metrics.max_position_value:,.2f}")
                click.echo(f"  止损价位: ${buy_scenario['stop_loss']:.2f}")
                click.echo(f"  止盈价位: ${buy_scenario['take_profit']:.2f}")
                click.echo(f"  风险金额: ${buy_metrics.risk_amount:.2f}")
                click.echo(f"  收益金额: ${buy_metrics.reward_amount:.2f}")
                click.echo(f"  风险回报比: {buy_metrics.risk_reward_ratio:.2f}")
                click.echo(f"  投资组合风险: {buy_metrics.portfolio_risk_pct:.2%}")
                
                # 卖出场景风险分析
                sell_scenario = risk_result['sell_scenario']
                sell_metrics = sell_scenario['risk_metrics']
                click.echo(f"\n🔴 卖出场景风险分析:")
                click.echo(f"  建议仓位: {sell_scenario['position_size']} 股")
                click.echo(f"  仓位价值: ${sell_metrics.max_position_value:,.2f}")
                click.echo(f"  止损价位: ${sell_scenario['stop_loss']:.2f}")
                click.echo(f"  止盈价位: ${sell_scenario['take_profit']:.2f}")
                click.echo(f"  风险金额: ${sell_metrics.risk_amount:.2f}")
                click.echo(f"  收益金额: ${sell_metrics.reward_amount:.2f}")
                click.echo(f"  风险回报比: {sell_metrics.risk_reward_ratio:.2f}")
                click.echo(f"  投资组合风险: {sell_metrics.portfolio_risk_pct:.2%}")
            
            # 价格位置分析
            pos_data = analysis_result['price_position']
            click.echo(f"\n📍 价格位置分析:")
            click.echo(f"  相对SMA(20): {pos_data['vs_sma_20']}")
            click.echo(f"  相对SMA(50): {pos_data['vs_sma_50']}")
            click.echo(f"  相对EMA(12): {pos_data['vs_ema_12']}")
            
            # 综合交易建议
            click.echo(f"\n💡 综合交易建议:")
            
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
            
            # ATR波动率建议
            if 'error' not in atr_data:
                if atr_data['volatility_level'] == "高波动":
                    click.echo("  ⚠️ 当前处于高波动期，建议谨慎交易，适当减小仓位")
                elif atr_data['volatility_level'] == "低波动":
                    click.echo("  🔄 当前处于低波动期，可能即将出现突破，密切关注")
                else:
                    click.echo("  ✅ 波动率正常，适合正常交易策略")
                
                # ATR止损建议
                best_stop = atr_data['stop_loss_levels']['atr_2.0x']
                click.echo(f"  🛡️ 建议止损位: 多头${best_stop['long_stop']}, 空头${best_stop['short_stop']} (2倍ATR)")
            
            # 趋势分析
            above_count = sum(1 for v in pos_data.values() if v == "above")
            if above_count >= 2:
                click.echo("  📈 价格在多数均线上方，趋势偏多头")
            elif above_count <= 1:
                click.echo("  📉 价格在多数均线下方，趋势偏空头")
            else:
                click.echo("  ➡️ 价格在均线附近，趋势不明确")
            
            # 信号和风险综合建议
            if signals_result and risk_result:
                high_quality_signals = signals_result['filtered_signals']
                if high_quality_signals:
                    click.echo(f"\n🎯 操作建议:")
                    for signal in high_quality_signals[:2]:  # 显示前2个最佳信号
                        action_emoji = "🟢" if signal.action == "BUY" else "🔴"
                        scenario = risk_result['buy_scenario'] if signal.action == "BUY" else risk_result['sell_scenario']
                        metrics = scenario['risk_metrics']
                        
                        click.echo(f"  {action_emoji} {signal.action} 建议:")
                        click.echo(f"    入场价位: ${signal.price:.2f}")
                        click.echo(f"    建议仓位: {scenario['position_size']} 股")
                        click.echo(f"    止损价位: ${scenario['stop_loss']:.2f}")
                        click.echo(f"    止盈价位: ${scenario['take_profit']:.2f}")
                        click.echo(f"    风险回报比: {metrics.risk_reward_ratio:.2f}")
                        click.echo(f"    信号置信度: {signal.confidence:.2%}")
                        click.echo()
                else:
                    click.echo(f"\n🎯 操作建议: 当前无高质量交易信号，建议观望")
        
        # 记录日志
        if logger:
            logger.info(f"完整分析完成: {symbol} (信号:{with_signals}, 风险:{with_risk}, 模拟:{mock})")
            
        click.echo(f"\n✅ 完整分析完成！")
        
    except ImportError as e:
        click.echo(f"❌ 导入分析模块失败: {e}")
        if logger:
            logger.error(f"分析模块导入失败: {e}")
    except DataFetchError as e:
        click.echo(f"❌ 数据获取失败: {e}")
        if logger:
            logger.error(f"数据获取失败: {e}")
    except Exception as e:
        click.echo(f"❌ 分析失败: {e}", err=True)
        if logger:
            logger.error(f"分析失败: {e}")
        import traceback
        if ctx.obj.get('debug'):
            traceback.print_exc()


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
    """
    显示交易信号
    
    获取和显示符合条件的交易信号，支持多种筛选和输出格式。
    
    Examples:
        python main.py signals --today
        python main.py signals --symbol TSLA --min-confidence 0.7
        python main.py signals --watchlist --format json
    """
    logger = ctx.obj.get('logger')
    config = ctx.obj.get('config', {})
    
    # 显示执行参数
    if today:
        click.echo("📡 获取今日交易信号...")
        date_filter = datetime.now().strftime("%Y-%m-%d")
    else:
        click.echo("📡 获取最新交易信号...")
        date_filter = "最新"
    
    if symbol:
        click.echo(f"🎯 股票筛选: {symbol.upper()}")
    elif watchlist:
        click.echo("📋 扫描监控列表中的所有股票")
    
    click.echo(f"📊 置信度阈值: {min_confidence:.1%}")
    click.echo(f"🔍 信号类型: {action.upper()}")
    click.echo(f"📋 输出格式: {output_format}")
    click.echo(f"📈 最大显示数量: {limit}")
    
    if mock:
        click.echo("🎭 使用模拟数据模式")
    
    try:
        # 导入必要模块
        from app.data.fetcher import get_fetcher, DataFetchError
        from app.analysis.indicators import analyze_stock_technical
        from app.analysis.strategies import SupportResistanceStrategy
        from app.analysis.confidence import ConfidenceCalculator
        from app.analysis.signal_filter import SignalFilter
        
        # 获取数据获取器
        fetcher = get_fetcher(use_mock=mock)
        
        # 确定要分析的股票列表
        symbols_to_analyze = []
        
        if symbol:
            # 分析指定股票
            symbols_to_analyze = [symbol.upper()]
        elif watchlist:
            # 获取监控列表中的股票
            symbols_to_analyze = get_watchlist_symbols(config)
            if not symbols_to_analyze:
                click.echo("⚠️ 监控列表为空，使用默认股票列表")
                symbols_to_analyze = ['TSLA', 'NVDA', 'AAPL', 'MSFT', 'GOOGL']
        else:
            # 使用默认热门股票列表
            symbols_to_analyze = ['TSLA', 'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX']
        
        click.echo(f"🔍 分析股票: {', '.join(symbols_to_analyze)}")
        
        # 创建策略和分析器实例
        strategy = SupportResistanceStrategy()
        confidence_calc = ConfidenceCalculator()
        signal_filter = SignalFilter()
        
        # 收集所有信号
        all_signals = []
        analysis_summary = {
            'total_stocks': len(symbols_to_analyze),
            'successful_analysis': 0,
            'failed_analysis': 0,
            'total_signals': 0,
            'errors': []
        }
        
        click.echo("\n⏳ 开始信号扫描...")
        
        for i, stock_symbol in enumerate(symbols_to_analyze, 1):
            try:
                click.echo(f"📊 [{i}/{len(symbols_to_analyze)}] 分析 {stock_symbol}...")
                
                # 获取历史数据
                hist_data = fetcher.get_historical_data(stock_symbol, period="1mo")
                
                if len(hist_data) < 15:
                    click.echo(f"⚠️ {stock_symbol}: 数据不足，跳过")
                    analysis_summary['failed_analysis'] += 1
                    continue
                
                # 进行技术分析
                analysis_result = analyze_stock_technical(hist_data)
                
                # 生成信号
                signals = strategy.analyze(hist_data, analysis_result=analysis_result)
                
                # 信号已经包含置信度，只需要设置股票代码
                for signal in signals:
                    signal.symbol = stock_symbol  # 确保信号包含股票代码
                
                # 添加到总信号列表
                all_signals.extend(signals)
                analysis_summary['successful_analysis'] += 1
                analysis_summary['total_signals'] += len(signals)
                
                click.echo(f"✅ {stock_symbol}: 发现 {len(signals)} 个信号")
                
            except Exception as e:
                error_msg = f"{stock_symbol}: {str(e)}"
                analysis_summary['errors'].append(error_msg)
                analysis_summary['failed_analysis'] += 1
                click.echo(f"❌ {error_msg}")
                if logger:
                    logger.warning(f"信号分析失败: {error_msg}")
        
        click.echo(f"\n📊 扫描完成: {analysis_summary['successful_analysis']}/{analysis_summary['total_stocks']} 股票成功分析")
        click.echo(f"🔍 发现信号总数: {analysis_summary['total_signals']}")
        
        # 过滤信号（即使没有信号也要显示这个步骤）
        click.echo("⏳ 过滤和排序信号...")
        
        if not all_signals:
            # 即使没有信号，也要根据输出格式显示结果
            if output_format == 'json':
                result = {
                    'summary': analysis_summary,
                    'filter_criteria': {
                        'min_confidence': min_confidence,
                        'action_filter': action,
                        'date_filter': date_filter,
                        'limit': limit
                    },
                    'signals': []
                }
                click.echo("\n📋 交易信号 (JSON格式):")
                click.echo(json.dumps(result, indent=2, ensure_ascii=False, cls=CustomJSONEncoder))
            elif output_format == 'csv':
                click.echo("\n📋 交易信号 (CSV格式):")
                click.echo("股票代码,动作,价格,置信度,原因,时间,止损,止盈")
                click.echo("# 无信号数据")
            else:  # table格式
                click.echo("\n📈 交易信号列表:")
                click.echo("=" * 80)
                click.echo("\n📭 未发现任何交易信号")
                click.echo("\n📊 扫描统计:")
                click.echo("-" * 40)
                click.echo(f"🔍 分析股票数: {analysis_summary['total_stocks']}")
                click.echo(f"✅ 成功分析: {analysis_summary['successful_analysis']}")
                click.echo(f"❌ 失败分析: {analysis_summary['failed_analysis']}")
                click.echo(f"📡 发现信号: {analysis_summary['total_signals']}")
                click.echo(f"📊 置信度阈值: {min_confidence:.1%}")
                click.echo(f"🔍 信号类型筛选: {action.upper()}")
            
            if analysis_summary['errors']:
                click.echo("\n❌ 分析错误:")
                for error in analysis_summary['errors'][:3]:  # 显示前3个错误
                    click.echo(f"  • {error}")
            return
        
        # 按置信度过滤
        filtered_signals = [s for s in all_signals if s.confidence >= min_confidence]
        
        # 按动作类型过滤
        if action != 'all':
            filtered_signals = [s for s in filtered_signals if s.signal_type == action]
        
        # 按时间过滤（如果指定了today）
        if today:
            today_date = datetime.now().date()
            filtered_signals = [s for s in filtered_signals if hasattr(s, 'timestamp') and s.timestamp.date() == today_date]
        
        # 按置信度排序
        filtered_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # 限制数量
        if len(filtered_signals) > limit:
            filtered_signals = filtered_signals[:limit]
        
        click.echo(f"📋 过滤后信号数量: {len(filtered_signals)}")
        
        if not filtered_signals:
            click.echo(f"\n📭 没有符合条件的信号 (置信度 >= {min_confidence:.1%}, 类型: {action})")
            return
        
        # 根据输出格式显示结果
        if output_format == 'json':
            # JSON格式输出
            signals_data = []
            for signal in filtered_signals:
                signal_dict = {
                    'symbol': getattr(signal, 'symbol', 'N/A'),
                    'action': signal.signal_type.upper(),
                    'price': signal.price,
                    'confidence': signal.confidence,
                    'reason': signal.reason,
                    'timestamp': getattr(signal, 'timestamp', datetime.now()).isoformat(),
                    'stop_loss': getattr(signal, 'stop_loss', None),
                    'take_profit': getattr(signal, 'take_profit', None)
                }
                signals_data.append(signal_dict)
            
            result = {
                'summary': analysis_summary,
                'filter_criteria': {
                    'min_confidence': min_confidence,
                    'action_filter': action,
                    'date_filter': date_filter,
                    'limit': limit
                },
                'signals': signals_data
            }
            
            click.echo("\n📋 交易信号 (JSON格式):")
            click.echo(json.dumps(result, indent=2, ensure_ascii=False, cls=CustomJSONEncoder))
            
        elif output_format == 'csv':
            # CSV格式输出
            click.echo("\n📋 交易信号 (CSV格式):")
            click.echo("股票代码,动作,价格,置信度,原因,时间,止损,止盈")
            
            for signal in filtered_signals:
                symbol = getattr(signal, 'symbol', 'N/A')
                action_str = signal.signal_type.upper()
                price = signal.price
                confidence = f"{signal.confidence:.2%}"
                reason = signal.reason.replace(',', ';')  # 避免CSV分隔符冲突
                timestamp = getattr(signal, 'timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
                stop_loss = getattr(signal, 'stop_loss', '')
                take_profit = getattr(signal, 'take_profit', '')
                
                click.echo(f"{symbol},{action_str},{price},{confidence},{reason},{timestamp},{stop_loss},{take_profit}")
            
        else:  # table格式（默认）
            # 表格格式输出
            click.echo("\n📈 交易信号列表:")
            click.echo("=" * 80)
            
            # 按股票分组显示
            signals_by_symbol = {}
            for signal in filtered_signals:
                symbol = getattr(signal, 'symbol', 'N/A')
                if symbol not in signals_by_symbol:
                    signals_by_symbol[symbol] = []
                signals_by_symbol[symbol].append(signal)
            
            for symbol, symbol_signals in signals_by_symbol.items():
                click.echo(f"\n🏷️ {symbol} ({len(symbol_signals)} 个信号):")
                click.echo("-" * 60)
                
                for i, signal in enumerate(symbol_signals, 1):
                    action_emoji = "🟢" if signal.signal_type == "buy" else "🔴"
                    action_str = signal.signal_type.upper()
                    
                    click.echo(f"  {i}. {action_emoji} {action_str} @ ${signal.price:.2f}")
                    click.echo(f"     置信度: {signal.confidence:.2%}")
                    click.echo(f"     原因: {signal.reason}")
                    
                    # 显示止损止盈
                    if hasattr(signal, 'stop_loss') and signal.stop_loss:
                        click.echo(f"     止损: ${signal.stop_loss:.2f}")
                    if hasattr(signal, 'take_profit') and signal.take_profit:
                        click.echo(f"     止盈: ${signal.take_profit:.2f}")
                    
                    # 显示时间戳
                    if hasattr(signal, 'timestamp'):
                        time_str = signal.timestamp.strftime('%H:%M:%S')
                        click.echo(f"     时间: {time_str}")
                    
                    click.echo()
            
            # 显示统计信息
            click.echo("📊 信号统计:")
            click.echo("-" * 40)
            
            buy_signals = [s for s in filtered_signals if s.signal_type == 'buy']
            sell_signals = [s for s in filtered_signals if s.signal_type == 'sell']
            
            click.echo(f"🟢 买入信号: {len(buy_signals)}")
            click.echo(f"🔴 卖出信号: {len(sell_signals)}")
            click.echo(f"📈 总信号数: {len(filtered_signals)}")
            
            if filtered_signals:
                avg_confidence = sum(s.confidence for s in filtered_signals) / len(filtered_signals)
                max_confidence = max(s.confidence for s in filtered_signals)
                min_confidence_actual = min(s.confidence for s in filtered_signals)
                
                click.echo(f"📊 平均置信度: {avg_confidence:.2%}")
                click.echo(f"📊 最高置信度: {max_confidence:.2%}")
                click.echo(f"📊 最低置信度: {min_confidence_actual:.2%}")
            
            # 显示分析摘要
            if analysis_summary['errors']:
                click.echo(f"\n⚠️ 分析错误 ({len(analysis_summary['errors'])}):")
                for error in analysis_summary['errors'][:3]:
                    click.echo(f"  • {error}")
                if len(analysis_summary['errors']) > 3:
                    click.echo(f"  ... 还有 {len(analysis_summary['errors']) - 3} 个错误")
        
        # 记录日志
        if logger:
            logger.info(f"信号扫描完成 - 股票:{len(symbols_to_analyze)}, 信号:{len(filtered_signals)}, 置信度>={min_confidence:.1%}")
        
        click.echo(f"\n✅ 信号扫描完成！")
        
    except ImportError as e:
        click.echo(f"❌ 导入分析模块失败: {e}")
        if logger:
            logger.error(f"信号分析模块导入失败: {e}")
    except Exception as e:
        click.echo(f"❌ 信号获取失败: {e}", err=True)
        if logger:
            logger.error(f"信号获取失败: {e}")
        import traceback
        if ctx.obj.get('debug'):
            traceback.print_exc()


def get_watchlist_symbols(config):
    """获取监控列表中的股票代码"""
    import os
    from pathlib import Path
    
    symbols = []
    stocks_dir = PROJECT_ROOT / "config" / "stocks"
    
    if not stocks_dir.exists():
        return symbols
    
    # 扫描股票配置文件
    for yaml_file in stocks_dir.glob("*.yaml"):
        try:
            import yaml
            with open(yaml_file, 'r', encoding='utf-8') as f:
                stock_config = yaml.safe_load(f)
            
            # 检查股票是否激活
            if stock_config.get('stock', {}).get('active', False):
                symbol = stock_config.get('stock', {}).get('symbol')
                if symbol:
                    symbols.append(symbol.upper())
                    
        except Exception:
            # 忽略配置文件读取错误
            continue
    
    return symbols


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
    """显示当前配置"""
    config = ctx.obj.get('config', {})
    
    if output_format == 'json':
        # JSON格式输出 - 只输出JSON数据
        if section:
            section_data = config.get(section, {})
            json_output = json.dumps(section_data, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        else:
            json_output = json.dumps(config, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        
        # 直接输出到stdout，绕过click的输出系统
        import sys
        sys.stdout.write(json_output + '\n')
        sys.stdout.flush()
        return
    
    elif output_format == 'yaml':
        # YAML格式输出
        if section:
            section_data = config.get(section, {})
            click.echo(yaml.dump(section_data, default_flow_style=False, allow_unicode=True))
        else:
            click.echo(yaml.dump(config, default_flow_style=False, allow_unicode=True))
        return
    
    # 表格格式输出（默认）
    if section:
        # 显示指定配置节
        section_data = config.get(section, {})
        if not section_data:
            click.echo(f"❌ 配置节 '{section}' 不存在")
            return
        
        click.echo(f"⚙️ 配置节: {section}")
        click.echo("=" * 50)
        _display_config_section(section_data)
    
    elif stocks:
        # 显示股票配置
        _display_stock_configs()
    
    elif strategies:
        # 显示策略配置
        _display_strategy_configs()
    
    else:
        # 显示系统配置概览
        click.echo("⚙️ 系统配置概览:")
        click.echo("=" * 50)
        
        # 应用信息
        app_config = config.get('app', {})
        click.echo(f"📱 应用名称: {app_config.get('name', 'N/A')}")
        click.echo(f"📦 版本: {config.get('version', 'N/A')}")
        click.echo(f"🏷️ 环境: {app_config.get('environment', 'N/A')}")
        
        # 数据源配置
        data_config = config.get('data', {})
        click.echo(f"\n📊 数据源配置:")
        click.echo(f"  主数据源: {data_config.get('primary_source', 'N/A')}")
        click.echo(f"  备用数据源: {', '.join(data_config.get('backup_sources', []))}")
        click.echo(f"  缓存TTL: {data_config.get('cache_ttl', 'N/A')}秒")
        click.echo(f"  请求超时: {data_config.get('request_timeout', 'N/A')}秒")
        
        # 风险管理配置
        risk_config = config.get('risk', {})
        click.echo(f"\n🛡️ 风险管理配置:")
        click.echo(f"  最大总仓位: {risk_config.get('max_total_exposure', 'N/A')}")
        click.echo(f"  单股最大仓位: {risk_config.get('max_single_position', 'N/A')}")
        click.echo(f"  默认止损: {risk_config.get('default_stop_loss', 'N/A')}")
        click.echo(f"  默认止盈: {risk_config.get('default_take_profit', 'N/A')}")
        
        # 技术分析配置
        analysis_config = config.get('analysis', {})
        click.echo(f"\n📈 技术分析配置:")
        click.echo(f"  RSI周期: {analysis_config.get('rsi_period', 'N/A')}")
        click.echo(f"  MACD参数: {analysis_config.get('macd_fast', 'N/A')}, {analysis_config.get('macd_slow', 'N/A')}, {analysis_config.get('macd_signal', 'N/A')}")
        click.echo(f"  ATR周期: {analysis_config.get('atr_period', 'N/A')}")
        
        # 信号配置
        signals_config = config.get('signals', {})
        click.echo(f"\n📡 信号配置:")
        click.echo(f"  最小置信度: {signals_config.get('min_confidence', 'N/A')}")
        click.echo(f"  信号过期时间: {signals_config.get('signal_expiry', 'N/A')}分钟")
        click.echo(f"  最大信号数: {signals_config.get('max_signals', 'N/A')}")
        
        # 日志配置
        logging_config = config.get('logging', {})
        click.echo(f"\n📝 日志配置:")
        click.echo(f"  日志级别: {logging_config.get('level', 'N/A')}")
        click.echo(f"  日志格式: {logging_config.get('format', 'N/A')}")
        click.echo(f"  文件输出: {'启用' if logging_config.get('file_output', False) else '禁用'}")


def _display_config_section(section_data, indent=0):
    """递归显示配置节内容"""
    prefix = "  " * indent
    for key, value in section_data.items():
        if isinstance(value, dict):
            click.echo(f"{prefix}{key}:")
            _display_config_section(value, indent + 1)
        elif isinstance(value, list):
            click.echo(f"{prefix}{key}: [{', '.join(map(str, value))}]")
        else:
            click.echo(f"{prefix}{key}: {value}")


def _display_stock_configs():
    """显示股票配置"""
    click.echo("📈 股票配置:")
    click.echo("=" * 50)
    
    stocks_dir = PROJECT_ROOT / "config" / "stocks"
    if not stocks_dir.exists():
        click.echo("❌ 股票配置目录不存在")
        return
    
    stock_files = list(stocks_dir.glob("*.yaml"))
    if not stock_files:
        click.echo("📭 未找到股票配置文件")
        return
    
    for stock_file in stock_files:
        try:
            with open(stock_file, 'r', encoding='utf-8') as f:
                stock_config = yaml.safe_load(f)
            
            stock_info = stock_config.get('stock', {})
            symbol = stock_info.get('symbol', stock_file.stem)
            name = stock_info.get('name', 'N/A')
            active = stock_info.get('active', False)
            
            status_emoji = "✅" if active else "❌"
            click.echo(f"\n{status_emoji} {symbol} - {name}")
            click.echo(f"  文件: {stock_file.name}")
            click.echo(f"  状态: {'激活' if active else '禁用'}")
            
            # 显示风险配置
            risk_config = stock_config.get('risk', {})
            if risk_config:
                click.echo(f"  风险配置:")
                click.echo(f"    止损: {risk_config.get('stop_loss_pct', 'N/A')}")
                click.echo(f"    止盈: {risk_config.get('take_profit_pct', 'N/A')}")
                click.echo(f"    最大仓位: {risk_config.get('max_position_pct', 'N/A')}")
            
            # 显示交易配置
            trading_config = stock_config.get('trading', {})
            if trading_config:
                click.echo(f"  交易配置:")
                click.echo(f"    仓位计算: {trading_config.get('position_sizing', 'N/A')}")
                click.echo(f"    最小交易额: {trading_config.get('min_trade_amount', 'N/A')}")
                
        except Exception as e:
            click.echo(f"❌ 读取 {stock_file.name} 失败: {e}")


def _display_strategy_configs():
    """显示策略配置"""
    click.echo("🎯 策略配置:")
    click.echo("=" * 50)
    
    strategies_dir = PROJECT_ROOT / "config" / "strategies"
    if not strategies_dir.exists():
        click.echo("❌ 策略配置目录不存在")
        return
    
    strategy_files = list(strategies_dir.glob("*.yaml"))
    if not strategy_files:
        click.echo("📭 未找到策略配置文件")
        return
    
    for strategy_file in strategy_files:
        try:
            with open(strategy_file, 'r', encoding='utf-8') as f:
                strategy_config = yaml.safe_load(f)
            
            strategy_info = strategy_config.get('strategy', {})
            name = strategy_info.get('name', strategy_file.stem)
            description = strategy_info.get('description', 'N/A')
            active = strategy_info.get('active', False)
            
            status_emoji = "✅" if active else "❌"
            click.echo(f"\n{status_emoji} {name}")
            click.echo(f"  文件: {strategy_file.name}")
            click.echo(f"  描述: {description}")
            click.echo(f"  状态: {'激活' if active else '禁用'}")
            
            # 显示参数配置
            params = strategy_config.get('parameters', {})
            if params:
                click.echo(f"  参数:")
                for key, value in params.items():
                    click.echo(f"    {key}: {value}")
                
        except Exception as e:
            click.echo(f"❌ 读取 {strategy_file.name} 失败: {e}")


@config.command('validate')
@click.option('--fix', is_flag=True, help='自动修复发现的问题')
@click.pass_context
def config_validate(ctx, fix):
    """验证配置文件"""
    click.echo("🔍 验证配置文件...")
    
    validation_results = {
        'system_config': False,
        'stock_configs': [],
        'strategy_configs': [],
        'errors': [],
        'warnings': []
    }
    
    # 验证主配置文件
    config_path = PROJECT_ROOT / "config" / "system.yaml"
    if config_path.exists():
        click.echo("✅ system.yaml 存在")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                system_config = yaml.safe_load(f)
            click.echo("✅ system.yaml 格式正确")
            validation_results['system_config'] = True
            
            # 验证必需的配置节
            required_sections = ['app', 'data', 'risk', 'analysis', 'signals', 'logging']
            for section in required_sections:
                if section not in system_config:
                    error_msg = f"缺少必需的配置节: {section}"
                    validation_results['errors'].append(error_msg)
                    click.echo(f"❌ {error_msg}")
                else:
                    click.echo(f"✅ 配置节 {section} 存在")
            
            # 验证数据源配置
            data_config = system_config.get('data', {})
            if 'primary_source' not in data_config:
                validation_results['errors'].append("缺少主数据源配置")
                click.echo("❌ 缺少主数据源配置")
            
            if 'backup_sources' not in data_config:
                validation_results['warnings'].append("缺少备用数据源配置")
                click.echo("⚠️ 缺少备用数据源配置")
            
        except Exception as e:
            error_msg = f"system.yaml 格式错误: {e}"
            validation_results['errors'].append(error_msg)
            click.echo(f"❌ {error_msg}")
    else:
        error_msg = "system.yaml 不存在"
        validation_results['errors'].append(error_msg)
        click.echo(f"❌ {error_msg}")
    
    # 验证股票配置目录
    stocks_dir = PROJECT_ROOT / "config" / "stocks"
    if stocks_dir.exists():
        stock_files = list(stocks_dir.glob("*.yaml"))
        click.echo(f"📁 找到 {len(stock_files)} 个股票配置文件")
        
        for stock_file in stock_files:
            try:
                with open(stock_file, 'r', encoding='utf-8') as f:
                    stock_config = yaml.safe_load(f)
                
                # 验证股票配置结构
                if 'stock' not in stock_config:
                    error_msg = f"{stock_file.name}: 缺少 'stock' 配置节"
                    validation_results['errors'].append(error_msg)
                    click.echo(f"❌ {error_msg}")
                    continue
                
                stock_info = stock_config['stock']
                if 'symbol' not in stock_info:
                    error_msg = f"{stock_file.name}: 缺少股票代码"
                    validation_results['errors'].append(error_msg)
                    click.echo(f"❌ {error_msg}")
                else:
                    symbol = stock_info['symbol']
                    # 验证文件名与股票代码是否匹配
                    if stock_file.stem != symbol:
                        warning_msg = f"{stock_file.name}: 文件名与股票代码不匹配"
                        validation_results['warnings'].append(warning_msg)
                        click.echo(f"⚠️ {warning_msg}")
                
                validation_results['stock_configs'].append({
                    'file': stock_file.name,
                    'valid': True,
                    'symbol': stock_info.get('symbol', 'N/A')
                })
                click.echo(f"✅ {stock_file.name} 格式正确")
                
            except Exception as e:
                error_msg = f"{stock_file.name} 格式错误: {e}"
                validation_results['errors'].append(error_msg)
                validation_results['stock_configs'].append({
                    'file': stock_file.name,
                    'valid': False,
                    'error': str(e)
                })
                click.echo(f"❌ {error_msg}")
    else:
        warning_msg = "stocks配置目录不存在"
        validation_results['warnings'].append(warning_msg)
        click.echo(f"⚠️ {warning_msg}")
    
    # 验证策略配置目录
    strategies_dir = PROJECT_ROOT / "config" / "strategies"
    if strategies_dir.exists():
        strategy_files = list(strategies_dir.glob("*.yaml"))
        click.echo(f"📁 找到 {len(strategy_files)} 个策略配置文件")
        
        for strategy_file in strategy_files:
            try:
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    strategy_config = yaml.safe_load(f)
                
                # 验证策略配置结构
                if 'strategy' not in strategy_config:
                    error_msg = f"{strategy_file.name}: 缺少 'strategy' 配置节"
                    validation_results['errors'].append(error_msg)
                    click.echo(f"❌ {error_msg}")
                    continue
                
                validation_results['strategy_configs'].append({
                    'file': strategy_file.name,
                    'valid': True,
                    'name': strategy_config['strategy'].get('name', 'N/A')
                })
                click.echo(f"✅ {strategy_file.name} 格式正确")
                
            except Exception as e:
                error_msg = f"{strategy_file.name} 格式错误: {e}"
                validation_results['errors'].append(error_msg)
                validation_results['strategy_configs'].append({
                    'file': strategy_file.name,
                    'valid': False,
                    'error': str(e)
                })
                click.echo(f"❌ {error_msg}")
    else:
        validation_results['warnings'].append("strategies配置目录不存在")
        click.echo("⚠️ strategies配置目录不存在")
    
    # 显示验证总结
    click.echo(f"\n📊 验证总结:")
    click.echo(f"✅ 成功: {len([c for c in validation_results['stock_configs'] if c['valid']]) + len([c for c in validation_results['strategy_configs'] if c['valid']]) + (1 if validation_results['system_config'] else 0)}")
    click.echo(f"❌ 错误: {len(validation_results['errors'])}")
    click.echo(f"⚠️ 警告: {len(validation_results['warnings'])}")
    
    # 自动修复选项
    if fix and validation_results['errors']:
        click.echo(f"\n🔧 尝试自动修复...")
        _auto_fix_config_issues(validation_results)
    
    return len(validation_results['errors']) == 0


def _auto_fix_config_issues(validation_results):
    """自动修复配置问题"""
    fixed_count = 0
    
    for error in validation_results['errors']:
        if "system.yaml 不存在" in error:
            # 创建默认的system.yaml
            try:
                _create_default_system_config()
                click.echo("✅ 已创建默认的 system.yaml")
                fixed_count += 1
            except Exception as e:
                click.echo(f"❌ 创建 system.yaml 失败: {e}")
        
        elif "stocks配置目录不存在" in error:
            # 创建stocks目录
            try:
                stocks_dir = PROJECT_ROOT / "config" / "stocks"
                stocks_dir.mkdir(parents=True, exist_ok=True)
                click.echo("✅ 已创建 stocks 配置目录")
                fixed_count += 1
            except Exception as e:
                click.echo(f"❌ 创建 stocks 目录失败: {e}")
        
        elif "strategies配置目录不存在" in error:
            # 创建strategies目录
            try:
                strategies_dir = PROJECT_ROOT / "config" / "strategies"
                strategies_dir.mkdir(parents=True, exist_ok=True)
                click.echo("✅ 已创建 strategies 配置目录")
                fixed_count += 1
            except Exception as e:
                click.echo(f"❌ 创建 strategies 目录失败: {e}")
    
    click.echo(f"\n🔧 自动修复完成: {fixed_count} 个问题已修复")


def _create_default_system_config():
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
    
    config_path = PROJECT_ROOT / "config" / "system.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.option('--type', 'value_type', default='auto', 
              type=click.Choice(['auto', 'str', 'int', 'float', 'bool']), help='值类型')
@click.pass_context
def config_set(ctx, key, value, value_type):
    """设置配置值
    
    KEY: 配置键，使用点号分隔，如 risk.max_total_exposure
    VALUE: 配置值
    """
    click.echo(f"⚙️ 设置配置: {key} = {value}")
    
    # 类型转换
    try:
        if value_type == 'auto':
            # 自动推断类型
            if value.lower() in ('true', 'false'):
                converted_value = value.lower() == 'true'
            elif value.replace('.', '').replace('-', '').isdigit():
                converted_value = float(value) if '.' in value else int(value)
            else:
                converted_value = value
        elif value_type == 'str':
            converted_value = value
        elif value_type == 'int':
            converted_value = int(value)
        elif value_type == 'float':
            converted_value = float(value)
        elif value_type == 'bool':
            converted_value = value.lower() in ('true', '1', 'yes', 'on')
        else:
            converted_value = value
    except ValueError as e:
        click.echo(f"❌ 值类型转换失败: {e}")
        return
    
    # 更新配置文件
    try:
        config_path = PROJECT_ROOT / "config" / "system.yaml"
        
        # 读取现有配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
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
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        click.echo(f"✅ 配置已更新: {key} = {converted_value} ({type(converted_value).__name__})")
        
    except Exception as e:
        click.echo(f"❌ 设置配置失败: {e}")


@config.command('get')
@click.argument('key')
@click.option('--default', help='默认值')
@click.pass_context
def config_get(ctx, key, default):
    """获取配置值
    
    KEY: 配置键，使用点号分隔，如 risk.max_total_exposure
    """
    config = ctx.obj.get('config', {})
    
    # 获取嵌套键值
    keys = key.split('.')
    current = config
    
    try:
        for k in keys:
            current = current[k]
        
        click.echo(f"{key}: {current}")
        
    except (KeyError, TypeError):
        if default is not None:
            click.echo(f"{key}: {default} (默认值)")
        else:
            click.echo(f"❌ 配置键 '{key}' 不存在")


@config.command('list')
@click.option('--pattern', help='过滤模式')
@click.pass_context
def config_list(ctx, pattern):
    """列出所有配置键"""
    config = ctx.obj.get('config', {})
    
    def _list_keys(obj, prefix=''):
        keys = []
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                keys.extend(_list_keys(value, full_key))
            else:
                keys.append(full_key)
        return keys
    
    all_keys = _list_keys(config)
    
    if pattern:
        # 过滤键
        filtered_keys = [k for k in all_keys if pattern.lower() in k.lower()]
        click.echo(f"📋 匹配 '{pattern}' 的配置键:")
        for key in filtered_keys:
            click.echo(f"  {key}")
    else:
        click.echo("📋 所有配置键:")
        for key in all_keys:
            click.echo(f"  {key}")


@config.command('reset')
@click.argument('key', required=False)
@click.option('--confirm', is_flag=True, help='确认重置')
@click.pass_context
def config_reset(ctx, key, confirm):
    """重置配置到默认值
    
    KEY: 要重置的配置键，留空则重置所有配置
    """
    if not confirm:
        if key:
            click.echo(f"⚠️ 将重置配置键 '{key}' 到默认值")
        else:
            click.echo("⚠️ 将重置所有配置到默认值")
        click.echo("使用 --confirm 参数确认操作")
        return
    
    try:
        if key:
            # 重置指定键
            click.echo(f"🔄 重置配置键: {key}")
            # TODO: 实现单个键重置逻辑
            click.echo("⚠️ 单个键重置功能待实现")
        else:
            # 重置所有配置
            click.echo("🔄 重置所有配置到默认值...")
            _create_default_system_config()
            click.echo("✅ 配置已重置到默认值")
            
    except Exception as e:
        click.echo(f"❌ 重置配置失败: {e}")


@config.command('backup')
@click.option('--output', help='备份文件路径')
@click.pass_context
def config_backup(ctx, output):
    """备份当前配置"""
    import shutil
    from datetime import datetime
    
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"config_backup_{timestamp}.tar.gz"
    
    try:
        config_dir = PROJECT_ROOT / "config"
        if not config_dir.exists():
            click.echo("❌ 配置目录不存在")
            return
        
        # 创建备份
        backup_path = PROJECT_ROOT / output
        shutil.make_archive(str(backup_path).replace('.tar.gz', ''), 'gztar', config_dir)
        
        click.echo(f"✅ 配置已备份到: {backup_path}")
        
    except Exception as e:
        click.echo(f"❌ 备份配置失败: {e}")


@config.command('restore')
@click.argument('backup_file')
@click.option('--confirm', is_flag=True, help='确认恢复')
@click.pass_context
def config_restore(ctx, backup_file, confirm):
    """从备份恢复配置
    
    BACKUP_FILE: 备份文件路径
    """
    import shutil
    import tarfile
    
    if not confirm:
        click.echo(f"⚠️ 将从 {backup_file} 恢复配置，这将覆盖当前配置")
        click.echo("使用 --confirm 参数确认操作")
        return
    
    try:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            click.echo(f"❌ 备份文件不存在: {backup_file}")
            return
        
        config_dir = PROJECT_ROOT / "config"
        
        # 备份当前配置
        if config_dir.exists():
            backup_current = config_dir.parent / "config_backup_before_restore"
            if backup_current.exists():
                shutil.rmtree(backup_current)
            shutil.copytree(config_dir, backup_current)
            click.echo(f"✅ 当前配置已备份到: {backup_current}")
        
        # 删除当前配置目录
        if config_dir.exists():
            shutil.rmtree(config_dir)
        
        # 解压备份文件
        with tarfile.open(backup_path, 'r:gz') as tar:
            tar.extractall(config_dir.parent)
        
        click.echo(f"✅ 配置已从 {backup_file} 恢复")
        
    except Exception as e:
        click.echo(f"❌ 恢复配置失败: {e}")


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


@cli.group()
def scheduler():
    """数据调度器管理命令"""
    pass


@scheduler.command('start')
@click.option('--background', is_flag=True, help='后台运行')
@click.pass_context
def scheduler_start(ctx, background):
    """启动数据调度器"""
    logger = ctx.obj.get('logger')
    config = ctx.obj.get('config', {})
    
    try:
        from app.data.scheduler import start_scheduler, get_scheduler
        
        click.echo("🚀 启动数据调度器...")
        
        scheduler = start_scheduler(config)
        status = scheduler.get_status()
        
        click.echo("✅ 数据调度器启动成功")
        click.echo(f"📊 监控股票: {', '.join(status['watchlist'])}")
        click.echo(f"⏰ 更新间隔: {status['update_interval']}秒")
        click.echo(f"📞 每日限制: {status['max_daily_calls']}次")
        click.echo(f"🕐 市场状态: {'开盘' if status['market_open'] else '休市'}")
        
        if background:
            click.echo("🔄 调度器在后台运行中...")
        else:
            click.echo("⚠️ 调度器在前台运行，按Ctrl+C停止")
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                click.echo("\n🛑 停止调度器...")
                scheduler.stop()
                click.echo("✅ 调度器已停止")
        
        if logger:
            logger.info("数据调度器启动")
            
    except Exception as e:
        click.echo(f"❌ 启动调度器失败: {e}")
        if logger:
            logger.error(f"启动调度器失败: {e}")


@scheduler.command('stop')
@click.pass_context
def scheduler_stop(ctx):
    """停止数据调度器"""
    logger = ctx.obj.get('logger')
    
    try:
        from app.data.scheduler import stop_scheduler
        
        click.echo("🛑 停止数据调度器...")
        stop_scheduler()
        click.echo("✅ 数据调度器已停止")
        
        if logger:
            logger.info("数据调度器停止")
            
    except Exception as e:
        click.echo(f"❌ 停止调度器失败: {e}")
        if logger:
            logger.error(f"停止调度器失败: {e}")


@scheduler.command('status')
@click.option('--format', 'output_format', default='table', 
              type=click.Choice(['table', 'json']), help='输出格式')
@click.pass_context
def scheduler_status(ctx, output_format):
    """查看调度器状态"""
    logger = ctx.obj.get('logger')
    
    try:
        from app.data.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        if output_format == 'json':
            click.echo(json.dumps(status, indent=2, default=str, ensure_ascii=False))
        else:
            click.echo("📊 数据调度器状态")
            click.echo("=" * 40)
            click.echo(f"运行状态: {'🟢 运行中' if status['is_running'] else '🔴 已停止'}")
            click.echo(f"市场状态: {'🟢 开盘' if status['market_open'] else '🔴 休市'}")
            click.echo(f"监控股票: {', '.join(status['watchlist'])}")
            click.echo(f"更新间隔: {status['update_interval']}秒")
            click.echo(f"今日调用: {status['daily_calls']}/{status['max_daily_calls']}")
            click.echo(f"调用历史: {status['call_history_count']}条记录")
            click.echo(f"重置日期: {status['last_reset_date']}")
        
        if logger:
            logger.info("查看调度器状态")
            
    except Exception as e:
        click.echo(f"❌ 获取调度器状态失败: {e}")
        if logger:
            logger.error(f"获取调度器状态失败: {e}")


@scheduler.command('force-fetch')
@click.argument('symbol', required=False)
@click.pass_context
def scheduler_force_fetch(ctx, symbol):
    """强制获取数据"""
    logger = ctx.obj.get('logger')
    
    try:
        from app.data.scheduler import get_scheduler
        
        scheduler = get_scheduler()
        
        if symbol:
            click.echo(f"🔄 强制获取 {symbol.upper()} 数据...")
            scheduler.force_fetch(symbol)
            click.echo(f"✅ {symbol.upper()} 数据获取完成")
        else:
            click.echo("🔄 强制获取所有监控股票数据...")
            scheduler.force_fetch()
            click.echo("✅ 所有数据获取完成")
        
        if logger:
            logger.info(f"强制获取数据: {symbol or '全部'}")
            
    except Exception as e:
        click.echo(f"❌ 强制获取数据失败: {e}")
        if logger:
            logger.error(f"强制获取数据失败: {e}")


@cli.command()
@click.pass_context
def status(ctx):
    """显示系统状态"""
    logger = ctx.obj.get('logger')
    config = ctx.obj.get('config', {})
    
    click.echo("🏥 系统状态检查...")
    
    # 检查配置
    if config:
        click.echo("✅ 配置系统: 正常")
    else:
        click.echo("❌ 配置系统: 异常")
    
    # 检查调度器状态
    try:
        from app.data.scheduler import get_scheduler
        scheduler = get_scheduler()
        status_info = scheduler.get_status()
        click.echo(f"⏰ 调度器状态: {'🟢 运行中' if status_info['is_running'] else '🔴 已停止'}")
        click.echo(f"📊 市场状态: {'🟢 开盘' if status_info['market_open'] else '🔴 休市'}")
        click.echo(f"📞 今日调用: {status_info['daily_calls']}/{status_info['max_daily_calls']}")
    except Exception as e:
        click.echo(f"⏰ 调度器状态: ❌ 获取失败 ({e})")
    
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
    
    if logger:
        logger.info("系统状态检查完成")


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