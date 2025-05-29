"""
信号扫描命令处理器

负责处理signals命令的所有逻辑，包括信号扫描、过滤、格式化输出等功能。
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import traceback

from .base import BaseCommandHandler, CommandResult, OutputFormatter
from ..data.fetcher import get_fetcher, DataFetchError
from ..analysis.indicators import analyze_stock_technical
from ..analysis.strategies import SupportResistanceStrategy
from ..analysis.confidence import ConfidenceCalculator
from ..analysis.signal_filter import SignalFilter


class SignalsCommandHandler(BaseCommandHandler):
    """信号扫描命令处理器"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
    
    @property
    def command_name(self) -> str:
        """命令名称"""
        return "signals"
    
    @property
    def command_description(self) -> str:
        """命令描述"""
        return "扫描多只股票的交易信号"
        
    def execute(self, **kwargs) -> CommandResult:
        """
        处理signals命令
        
        Args:
            today: 是否只显示今日信号
            symbol: 指定股票代码
            min_confidence: 最小信号置信度
            output_format: 输出格式 (table/json/csv)
            action: 信号类型筛选 (buy/sell/all)
            limit: 最大显示信号数量
            mock: 是否使用模拟数据
            watchlist: 是否扫描监控列表
            
        Returns:
            CommandResult: 命令执行结果
        """
        try:
            # 提取参数
            today = kwargs.get('today', False)
            symbol = kwargs.get('symbol')
            min_confidence = kwargs.get('min_confidence', 0.6)
            output_format = kwargs.get('output_format', 'table')
            action = kwargs.get('action', 'all')
            limit = kwargs.get('limit', 20)
            mock = kwargs.get('mock', False)
            watchlist = kwargs.get('watchlist', False)
            
            # 显示执行参数
            self._display_execution_params(today, symbol, min_confidence, output_format, 
                                         action, limit, mock, watchlist)
            
            # 获取要分析的股票列表
            symbols_to_analyze = self._get_symbols_to_analyze(symbol, watchlist)
            
            # 执行信号扫描
            scan_result = self._scan_signals(symbols_to_analyze, mock)
            
            # 过滤和排序信号
            filtered_signals = self._filter_and_sort_signals(
                scan_result['all_signals'], min_confidence, action, today, limit
            )
            
            # 格式化输出
            output_data = self._format_output(
                filtered_signals, scan_result['analysis_summary'], 
                min_confidence, action, today, limit, output_format
            )
            
            # 记录日志
            if self.logger:
                self.logger.info(
                    f"信号扫描完成 - 股票:{len(symbols_to_analyze)}, "
                    f"信号:{len(filtered_signals)}, 置信度>={min_confidence:.1%}"
                )
            
            return CommandResult(
                success=True,
                data=output_data,
                message="信号扫描完成"
            )
            
        except Exception as e:
            error_msg = f"信号获取失败: {e}"
            if self.logger:
                self.logger.error(error_msg, exc_info=True)
            
            # 打印完整的错误堆栈
            print(f"❌ 错误详情: {traceback.format_exc()}")
            
            return CommandResult(
                success=False,
                message=error_msg,
                error=e
            )
    
    def _display_execution_params(self, today: bool, symbol: Optional[str], 
                                min_confidence: float, output_format: str,
                                action: str, limit: int, mock: bool, watchlist: bool):
        """显示执行参数"""
        if today:
            print("📡 获取今日交易信号...")
        else:
            print("📡 获取最新交易信号...")
        
        if symbol:
            print(f"🎯 股票筛选: {symbol.upper()}")
        elif watchlist:
            print("📋 扫描监控列表中的所有股票")
        
        print(f"📊 置信度阈值: {min_confidence:.1%}")
        print(f"🔍 信号类型: {action.upper()}")
        print(f"📋 输出格式: {output_format}")
        print(f"📈 最大显示数量: {limit}")
        
        if mock:
            print("🎭 使用模拟数据模式")
    
    def _get_symbols_to_analyze(self, symbol: Optional[str], watchlist: bool) -> List[str]:
        """获取要分析的股票列表"""
        symbols_to_analyze = []
        
        if symbol:
            # 分析指定股票
            symbols_to_analyze = [symbol.upper()]
        elif watchlist:
            # 获取监控列表中的股票
            symbols_to_analyze = self._get_watchlist_symbols()
            if not symbols_to_analyze:
                print("⚠️ 监控列表为空，使用默认股票列表")
                symbols_to_analyze = ['TSLA', 'NVDA', 'AAPL', 'MSFT', 'GOOGL']
        else:
            # 使用默认热门股票列表
            symbols_to_analyze = ['TSLA', 'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX']
        
        print(f"🔍 分析股票: {', '.join(symbols_to_analyze)}")
        return symbols_to_analyze
    
    def _get_watchlist_symbols(self) -> List[str]:
        """获取监控列表中的股票代码"""
        import os
        import yaml
        from pathlib import Path
        
        symbols = []
        
        # 从配置中获取项目根目录
        project_root = Path.cwd()  # 假设当前工作目录是项目根目录
        stocks_dir = project_root / "config" / "stocks"
        
        if not stocks_dir.exists():
            return symbols
        
        # 扫描股票配置文件
        for yaml_file in stocks_dir.glob("*.yaml"):
            try:
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
    
    def _scan_signals(self, symbols_to_analyze: List[str], mock: bool) -> Dict[str, Any]:
        """扫描信号"""
        # 获取数据获取器
        fetcher = get_fetcher(use_mock=mock)
        
        # 确保配置是字典格式
        config_dict = self.config
        if hasattr(self.config, 'to_dict'):
            config_dict = self.config.to_dict()
        elif not isinstance(self.config, dict):
            # 如果不是字典也没有to_dict方法，使用默认配置
            config_dict = {}
        
        strategy = SupportResistanceStrategy(config_dict)
        confidence_calc = ConfidenceCalculator(config_dict)
        signal_filter = SignalFilter(config_dict)
        
        # 收集所有信号
        all_signals = []
        analysis_summary = {
            'total_stocks': len(symbols_to_analyze),
            'successful_analysis': 0,
            'failed_analysis': 0,
            'total_signals': 0,
            'errors': []
        }
        
        print("\n⏳ 开始信号扫描...")
        
        for i, stock_symbol in enumerate(symbols_to_analyze, 1):
            try:
                print(f"📊 [{i}/{len(symbols_to_analyze)}] 分析 {stock_symbol}...")
                
                # 获取历史数据
                hist_data = fetcher.get_historical_data(stock_symbol, period="1mo")
                
                if len(hist_data) < 15:
                    print(f"⚠️ {stock_symbol}: 数据不足，跳过")
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
                
                print(f"✅ {stock_symbol}: 发现 {len(signals)} 个信号")
                
            except Exception as e:
                error_msg = f"{stock_symbol}: {str(e)}"
                analysis_summary['errors'].append(error_msg)
                analysis_summary['failed_analysis'] += 1
                print(f"❌ {error_msg}")
                if self.logger:
                    self.logger.warning(f"信号分析失败: {error_msg}")
        
        print(f"\n📊 扫描完成: {analysis_summary['successful_analysis']}/{analysis_summary['total_stocks']} 股票成功分析")
        print(f"🔍 发现信号总数: {analysis_summary['total_signals']}")
        
        return {
            'all_signals': all_signals,
            'analysis_summary': analysis_summary
        }
    
    def _filter_and_sort_signals(self, all_signals: List, min_confidence: float,
                                action: str, today: bool, limit: int) -> List:
        """过滤和排序信号"""
        print("⏳ 过滤和排序信号...")
        
        if not all_signals:
            return []
        
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
        
        print(f"📋 过滤后信号数量: {len(filtered_signals)}")
        
        return filtered_signals
    
    def _format_output(self, filtered_signals: List, analysis_summary: Dict[str, Any],
                      min_confidence: float, action: str, today: bool, limit: int,
                      output_format: str) -> Dict[str, Any]:
        """格式化输出"""
        date_filter = datetime.now().strftime("%Y-%m-%d") if today else "最新"
        
        if not filtered_signals:
            return self._format_empty_result(analysis_summary, min_confidence, action, 
                                           date_filter, limit, output_format)
        
        if output_format == 'json':
            return self._format_json_output(filtered_signals, analysis_summary, 
                                          min_confidence, action, date_filter, limit)
        elif output_format == 'csv':
            return self._format_csv_output(filtered_signals)
        else:  # table格式
            return self._format_table_output(filtered_signals, analysis_summary)
    
    def _format_empty_result(self, analysis_summary: Dict[str, Any], min_confidence: float,
                           action: str, date_filter: str, limit: int, output_format: str) -> Dict[str, Any]:
        """格式化空结果"""
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
            return {'json_data': result}
        elif output_format == 'csv':
            return {
                'csv_header': "股票代码,动作,价格,置信度,原因,时间,止损,止盈",
                'csv_data': ["# 无信号数据"]
            }
        else:  # table格式
            return {
                'table_data': {
                    'title': "交易信号列表",
                    'content': "📭 未发现任何交易信号",
                    'summary': analysis_summary,
                    'filter_info': {
                        'min_confidence': min_confidence,
                        'action': action
                    }
                }
            }
    
    def _format_json_output(self, filtered_signals: List, analysis_summary: Dict[str, Any],
                          min_confidence: float, action: str, date_filter: str, limit: int) -> Dict[str, Any]:
        """格式化JSON输出"""
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
        
        return {'json_data': result}
    
    def _format_csv_output(self, filtered_signals: List) -> Dict[str, Any]:
        """格式化CSV输出"""
        csv_data = []
        for signal in filtered_signals:
            symbol = getattr(signal, 'symbol', 'N/A')
            action_str = signal.signal_type.upper()
            price = signal.price
            confidence = f"{signal.confidence:.2%}"
            reason = signal.reason.replace(',', ';')  # 避免CSV分隔符冲突
            timestamp = getattr(signal, 'timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
            stop_loss = getattr(signal, 'stop_loss', '')
            take_profit = getattr(signal, 'take_profit', '')
            
            csv_data.append(f"{symbol},{action_str},{price},{confidence},{reason},{timestamp},{stop_loss},{take_profit}")
        
        return {
            'csv_header': "股票代码,动作,价格,置信度,原因,时间,止损,止盈",
            'csv_data': csv_data
        }
    
    def _format_table_output(self, filtered_signals: List, analysis_summary: Dict[str, Any]) -> Dict[str, Any]:
        """格式化表格输出"""
        # 按股票分组
        signals_by_symbol = {}
        for signal in filtered_signals:
            symbol = getattr(signal, 'symbol', 'N/A')
            if symbol not in signals_by_symbol:
                signals_by_symbol[symbol] = []
            signals_by_symbol[symbol].append(signal)
        
        # 计算统计信息
        buy_signals = [s for s in filtered_signals if s.signal_type == 'buy']
        sell_signals = [s for s in filtered_signals if s.signal_type == 'sell']
        
        statistics = {
            'buy_count': len(buy_signals),
            'sell_count': len(sell_signals),
            'total_count': len(filtered_signals)
        }
        
        if filtered_signals:
            avg_confidence = sum(s.confidence for s in filtered_signals) / len(filtered_signals)
            max_confidence = max(s.confidence for s in filtered_signals)
            min_confidence_actual = min(s.confidence for s in filtered_signals)
            
            statistics.update({
                'avg_confidence': avg_confidence,
                'max_confidence': max_confidence,
                'min_confidence': min_confidence_actual
            })
        
        return {
            'table_data': {
                'signals_by_symbol': signals_by_symbol,
                'statistics': statistics,
                'analysis_summary': analysis_summary
            }
        } 