"""
交易信号扫描命令处理器

处理多股票的信号扫描、过滤和显示功能。
"""

from typing import Dict, Any, Optional, List
import click
from datetime import datetime, date

from .base import AnalysisCommandHandler, CommandResult


class SignalsCommandHandler(AnalysisCommandHandler):
    """交易信号扫描命令处理器"""
    
    @property
    def command_name(self) -> str:
        return "signals"
    
    @property
    def command_description(self) -> str:
        return "扫描多只股票的交易信号"
    
    def validate_params(self, **kwargs) -> CommandResult:
        """验证signals命令参数"""
        symbols = kwargs.get('symbols', [])
        if symbols and not isinstance(symbols, list):
            return CommandResult(success=False, message="股票代码列表格式错误")
        
        confidence_threshold = kwargs.get('confidence_threshold', 0.7)
        if not isinstance(confidence_threshold, (int, float)) or not (0 <= confidence_threshold <= 1):
            return CommandResult(success=False, message="置信度阈值必须在0-1之间")
        
        signal_type = kwargs.get('signal_type', 'all')
        if signal_type not in ['all', 'buy', 'sell']:
            return CommandResult(success=False, message="信号类型必须为 all、buy 或 sell")
        
        output_format = kwargs.get('output_format', 'table')
        if output_format not in ['table', 'json', 'csv']:
            return CommandResult(success=False, message="输出格式必须为 table、json 或 csv")
        
        return CommandResult(success=True, message="参数验证通过")
    
    def execute(self, **kwargs) -> CommandResult:
        """执行信号扫描"""
        symbols = kwargs.get('symbols', [])
        today = kwargs.get('today', False)
        confidence_threshold = kwargs.get('confidence_threshold', 0.7)
        signal_type = kwargs.get('signal_type', 'all')
        mock = kwargs.get('mock', False)
        use_watchlist = kwargs.get('use_watchlist', False)
        
        try:
            # 1. 确定要扫描的股票列表
            self.log_info("开始信号扫描...")
            
            if use_watchlist or not symbols:
                # 使用监控列表
                watchlist = self._get_watchlist()
                if not watchlist:
                    return CommandResult(
                        success=False,
                        message="监控列表为空，请在配置中设置监控股票或手动指定股票代码"
                    )
                symbols = watchlist
                self.log_info(f"使用监控列表: {symbols}")
            else:
                self.log_info(f"扫描指定股票: {symbols}")
            
            # 2. 扫描每只股票的信号
            all_signals = []
            scan_results = {}
            
            for symbol in symbols:
                self.log_info(f"扫描股票: {symbol}")
                symbol_result = self._scan_symbol_signals(
                    symbol, mock=mock, confidence_threshold=confidence_threshold
                )
                
                if symbol_result['success']:
                    signals = symbol_result['signals']
                    all_signals.extend(signals)
                    scan_results[symbol] = {
                        'success': True,
                        'signals': signals,
                        'signal_count': len(signals),
                        'analysis_time': symbol_result.get('analysis_time')
                    }
                else:
                    scan_results[symbol] = {
                        'success': False,
                        'error': symbol_result.get('error', '未知错误'),
                        'signal_count': 0
                    }
                    self.log_warning(f"扫描 {symbol} 失败: {symbol_result.get('error')}")
            
            # 3. 过滤信号
            filtered_signals = self._filter_signals(all_signals, signal_type, confidence_threshold)
            
            # 4. 排序信号（按置信度降序）
            sorted_signals = sorted(filtered_signals, key=lambda x: x.confidence, reverse=True)
            
            # 5. 组装结果
            result_data = {
                'scan_date': datetime.now().isoformat(),
                'scanned_symbols': symbols,
                'scan_results': scan_results,
                'total_signals': len(all_signals),
                'filtered_signals': len(filtered_signals),
                'signals': [self._signal_to_dict(signal) for signal in sorted_signals],
                'filters': {
                    'confidence_threshold': confidence_threshold,
                    'signal_type': signal_type,
                    'today_only': today
                },
                'statistics': self._calculate_statistics(scan_results, all_signals, filtered_signals)
            }
            
            self.log_info(f"信号扫描完成: {len(symbols)}只股票, {len(all_signals)}个原始信号, {len(filtered_signals)}个高质量信号")
            
            return CommandResult(
                success=True,
                data=result_data,
                message=f"扫描完成，发现 {len(filtered_signals)} 个高质量信号"
            )
            
        except Exception as e:
            return self.handle_error(e, symbols=symbols)
    
    def _get_watchlist(self) -> List[str]:
        """获取监控股票列表"""
        try:
            # 从配置中获取监控列表
            scheduler_config = self.config.get('scheduler', {})
            watchlist = scheduler_config.get('symbols', [])
            
            if not watchlist:
                # 如果没有配置监控列表，使用默认列表
                watchlist = ['AMD', 'PONY']
                self.log_info("使用默认监控列表: AMD, PONY")
            
            return watchlist
        except Exception as e:
            self.log_warning(f"获取监控列表失败: {e}")
            return []
    
    def _scan_symbol_signals(self, symbol: str, mock: bool = False, 
                           confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """扫描单只股票的信号"""
        try:
            start_time = datetime.now()
            
            # 获取股票数据
            data_result = self.get_stock_data(symbol, period="1mo", use_mock=mock)
            if not data_result:
                return {
                    'success': False,
                    'error': data_result.message,
                    'signals': []
                }
            
            hist_data = data_result.data
            
            # 进行技术分析
            from app.analysis.indicators import analyze_stock_technical
            analysis_result = analyze_stock_technical(hist_data)
            
            # 生成信号
            config_dict = self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config
            all_signals = self.strategy.analyze(hist_data, analysis_result=analysis_result)
            
            # 为信号添加股票代码
            for signal in all_signals:
                signal.metadata['symbol'] = symbol
                signal.metadata['current_price'] = analysis_result.get('current_price', 0)
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'signals': all_signals,
                'analysis_time': analysis_time,
                'data_points': len(hist_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'signals': []
            }
    
    def _filter_signals(self, signals: List, signal_type: str, 
                       confidence_threshold: float) -> List:
        """过滤信号"""
        filtered = []
        
        for signal in signals:
            # 置信度过滤
            if signal.confidence < confidence_threshold:
                continue
            
            # 信号类型过滤
            if signal_type != 'all' and signal.signal_type != signal_type:
                continue
            
            filtered.append(signal)
        
        return filtered
    
    def _signal_to_dict(self, signal) -> Dict[str, Any]:
        """将信号对象转换为字典"""
        signal_dict = signal.to_dict()
        # 添加股票代码到顶层
        signal_dict['symbol'] = signal.metadata.get('symbol', 'UNKNOWN')
        signal_dict['current_price'] = signal.metadata.get('current_price', 0)
        return signal_dict
    
    def _calculate_statistics(self, scan_results: Dict[str, Any], 
                            all_signals: List, filtered_signals: List) -> Dict[str, Any]:
        """计算扫描统计信息"""
        successful_scans = sum(1 for result in scan_results.values() if result['success'])
        failed_scans = len(scan_results) - successful_scans
        
        # 按信号类型统计
        buy_signals = [s for s in filtered_signals if s.signal_type == 'buy']
        sell_signals = [s for s in filtered_signals if s.signal_type == 'sell']
        
        # 按置信度统计
        high_confidence = [s for s in filtered_signals if s.confidence >= 0.8]
        medium_confidence = [s for s in filtered_signals if 0.6 <= s.confidence < 0.8]
        low_confidence = [s for s in filtered_signals if s.confidence < 0.6]
        
        return {
            'scan_summary': {
                'total_symbols': len(scan_results),
                'successful_scans': successful_scans,
                'failed_scans': failed_scans,
                'success_rate': successful_scans / len(scan_results) if scan_results else 0
            },
            'signal_summary': {
                'total_signals': len(all_signals),
                'filtered_signals': len(filtered_signals),
                'filter_rate': len(filtered_signals) / len(all_signals) if all_signals else 0,
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals)
            },
            'confidence_distribution': {
                'high_confidence': len(high_confidence),
                'medium_confidence': len(medium_confidence),
                'low_confidence': len(low_confidence)
            }
        }
    
    def format_output(self, result: CommandResult, output_format: str = 'table') -> str:
        """格式化signals命令的输出"""
        if not result.success:
            return f"❌ 信号扫描失败: {result.message}"
        
        data = result.data
        if not data:
            return result.message
        
        if output_format == 'json':
            return self.formatter.format_json(data)
        elif output_format == 'csv':
            return self._format_csv_output(data)
        else:  # table
            return self._format_table_output(data)
    
    def _format_table_output(self, data: Dict[str, Any]) -> str:
        """格式化为表格输出"""
        lines = []
        
        # 扫描概要
        lines.append(f"\n📡 交易信号扫描结果:")
        lines.append("=" * 60)
        lines.append(f"扫描时间: {data['scan_date']}")
        lines.append(f"扫描股票: {', '.join(data['scanned_symbols'])}")
        
        # 统计信息
        stats = data['statistics']
        scan_summary = stats['scan_summary']
        signal_summary = stats['signal_summary']
        
        lines.append(f"\n📊 扫描统计:")
        lines.append(f"  成功扫描: {scan_summary['successful_scans']}/{scan_summary['total_symbols']} ({scan_summary['success_rate']:.1%})")
        lines.append(f"  原始信号: {signal_summary['total_signals']} 个")
        lines.append(f"  高质量信号: {signal_summary['filtered_signals']} 个")
        lines.append(f"  买入信号: {signal_summary['buy_signals']} 个")
        lines.append(f"  卖出信号: {signal_summary['sell_signals']} 个")
        
        # 信号详情
        signals = data['signals']
        if signals:
            lines.append(f"\n⭐ 高质量信号详情:")
            lines.append("-" * 60)
            
            for i, signal in enumerate(signals[:10], 1):  # 最多显示10个信号
                action_emoji = "🟢" if signal['signal_type'] == 'buy' else "🔴"
                lines.append(f"{i:2d}. {action_emoji} {signal['symbol']} - {signal['action'].upper()}")
                lines.append(f"     价格: ${signal['price']:.2f} | 置信度: {signal['confidence']:.1%}")
                lines.append(f"     原因: {signal['reason']}")
                if signal.get('stop_loss'):
                    lines.append(f"     止损: ${signal['stop_loss']:.2f} | 止盈: ${signal.get('take_profit', 0):.2f}")
                lines.append("")
            
            if len(signals) > 10:
                lines.append(f"... 还有 {len(signals) - 10} 个信号未显示")
        else:
            lines.append(f"\n💡 未发现符合条件的交易信号")
            lines.append(f"   建议降低置信度阈值或检查市场条件")
        
        # 失败的扫描
        failed_scans = [symbol for symbol, result in data['scan_results'].items() if not result['success']]
        if failed_scans:
            lines.append(f"\n⚠️ 扫描失败的股票:")
            for symbol in failed_scans:
                error = data['scan_results'][symbol]['error']
                lines.append(f"  • {symbol}: {error}")
        
        lines.append(f"\n✅ 信号扫描完成！")
        return "\n".join(lines)
    
    def _format_csv_output(self, data: Dict[str, Any]) -> str:
        """格式化为CSV输出"""
        lines = ["股票代码,信号类型,动作,价格,置信度,原因,止损,止盈"]
        
        for signal in data['signals']:
            lines.append(
                f"{signal['symbol']},"
                f"{signal['signal_type']},"
                f"{signal['action']},"
                f"{signal['price']:.2f},"
                f"{signal['confidence']:.3f},"
                f"\"{signal['reason']}\","
                f"{signal.get('stop_loss', ''):.2f},"
                f"{signal.get('take_profit', ''):.2f}"
            )
        
        return "\n".join(lines) 