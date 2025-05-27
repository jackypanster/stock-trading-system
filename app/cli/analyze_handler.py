"""
股票分析命令处理器

处理股票技术分析、信号生成和风险管理的完整分析流程。
"""

from typing import Dict, Any, Optional
import click
from datetime import datetime

from .base import AnalysisCommandHandler, CommandResult


class AnalyzeCommandHandler(AnalysisCommandHandler):
    """股票分析命令处理器"""
    
    @property
    def command_name(self) -> str:
        return "analyze"
    
    @property
    def command_description(self) -> str:
        return "分析指定股票的技术指标和交易信号"
    
    def validate_params(self, **kwargs) -> CommandResult:
        """验证analyze命令参数"""
        symbol = kwargs.get('symbol')
        if not symbol:
            return CommandResult(success=False, message="股票代码不能为空")
        
        days = kwargs.get('days', 20)
        if not isinstance(days, int) or days <= 0:
            return CommandResult(success=False, message="数据天数必须为正整数")
        
        output_format = kwargs.get('output_format', 'table')
        if output_format not in ['table', 'json', 'csv']:
            return CommandResult(success=False, message="输出格式必须为 table、json 或 csv")
        
        portfolio_value = kwargs.get('portfolio_value', 100000)
        if not isinstance(portfolio_value, (int, float)) or portfolio_value <= 0:
            return CommandResult(success=False, message="投资组合价值必须为正数")
        
        return CommandResult(success=True, message="参数验证通过")
    
    def execute(self, **kwargs) -> CommandResult:
        """执行股票分析"""
        symbol = kwargs['symbol'].upper()
        days = kwargs.get('days', 20)
        mock = kwargs.get('mock', False)
        with_signals = kwargs.get('with_signals', False)
        with_risk = kwargs.get('with_risk', False)
        portfolio_value = kwargs.get('portfolio_value', 100000)
        
        try:
            # 1. 获取股票数据
            self.log_info(f"开始分析股票: {symbol}")
            
            # 确定数据周期
            period_map = {
                5: "5d", 10: "10d", 20: "1mo", 30: "1mo", 
                60: "2mo", 90: "3mo", 180: "6mo", 365: "1y"
            }
            period = period_map.get(days, "1mo")
            
            # 获取历史数据
            data_result = self.get_stock_data(symbol, period, mock)
            if not data_result:
                return data_result
            
            hist_data = data_result.data
            self.log_info(f"获取到 {len(hist_data)} 条历史数据")
            
            # 2. 进行技术分析
            self.log_info("计算技术指标...")
            analysis_result = self._perform_technical_analysis(hist_data)
            
            # 3. 信号生成分析（可选）
            signals_result = None
            if with_signals:
                self.log_info("生成交易信号...")
                signals_result = self._perform_signal_analysis(hist_data, analysis_result)
            
            # 4. 风险管理分析（可选）
            risk_result = None
            if with_risk:
                self.log_info("计算风险管理指标...")
                risk_result = self._perform_risk_analysis(
                    symbol, analysis_result, portfolio_value
                )
            
            # 5. 组装完整结果
            complete_result = {
                'symbol': symbol,
                'analysis_date': datetime.now().isoformat(),
                'data_points': len(hist_data),
                'technical_analysis': analysis_result,
                'signals': signals_result,
                'risk_management': risk_result,
                'parameters': {
                    'days': days,
                    'period': period,
                    'mock_data': mock,
                    'with_signals': with_signals,
                    'with_risk': with_risk,
                    'portfolio_value': portfolio_value
                }
            }
            
            self.log_info(f"股票分析完成: {symbol}")
            return CommandResult(
                success=True,
                data=complete_result,
                message=f"股票 {symbol} 分析完成"
            )
            
        except Exception as e:
            return self.handle_error(e, symbol=symbol)
    
    def _perform_technical_analysis(self, hist_data) -> Dict[str, Any]:
        """执行技术分析"""
        from app.analysis.indicators import analyze_stock_technical
        return analyze_stock_technical(hist_data)
    
    def _perform_signal_analysis(self, hist_data, analysis_result) -> Optional[Dict[str, Any]]:
        """执行信号分析"""
        try:
            from app.analysis.confidence import ConfidenceCalculator
            from app.analysis.signal_filter import SignalFilter
            
            # 创建分析器实例，传递配置字典
            config_dict = self.config.to_dict() if hasattr(self.config, 'to_dict') else self.config
            confidence_calc = ConfidenceCalculator(config_dict)
            signal_filter = SignalFilter(config_dict)
            
            # 生成信号
            all_signals = self.strategy.analyze(hist_data, analysis_result=analysis_result)
            
            # 分离买入和卖出信号
            buy_signals = [s for s in all_signals if s.signal_type == 'buy']
            sell_signals = [s for s in all_signals if s.signal_type == 'sell']
            
            # 过滤信号
            filter_result = signal_filter.filter_signals(all_signals)
            filtered_signals = filter_result.get('filtered_signals', [])
            
            self.log_info(f"信号生成完成: {len(buy_signals)}个买入信号, {len(sell_signals)}个卖出信号")
            self.log_info(f"信号过滤: {len(all_signals)}个原始信号 → {len(filtered_signals)}个高质量信号")
            
            return {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'filtered_signals': filtered_signals,
                'filter_stats': filter_result.get('statistics', {}),
                'total_signals': len(all_signals),
                'high_quality_signals': len(filtered_signals)
            }
            
        except Exception as e:
            self.log_warning(f"信号生成失败: {e}")
            return None
    
    def _perform_risk_analysis(self, symbol: str, analysis_result: Dict[str, Any], 
                              portfolio_value: float) -> Optional[Dict[str, Any]]:
        """执行风险管理分析"""
        try:
            # 获取当前价格
            current_price = analysis_result['current_price']
            
            # 获取股票配置
            stock_config = self.config.get('stocks', {}).get(symbol, {})
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
            buy_stop_loss, buy_take_profit = self.risk_manager.calculate_stop_loss_take_profit(
                current_price, "BUY", stock_config
            )
            buy_position_size = self.risk_manager.calculate_position_size(
                current_price, buy_stop_loss, portfolio_value * 0.8, stock_config
            )
            buy_risk_metrics = self.risk_manager.calculate_risk_metrics(
                current_price, buy_stop_loss, buy_take_profit, buy_position_size, portfolio_value
            )
            
            # 计算卖出场景的风险指标
            sell_stop_loss, sell_take_profit = self.risk_manager.calculate_stop_loss_take_profit(
                current_price, "SELL", stock_config
            )
            sell_position_size = self.risk_manager.calculate_position_size(
                current_price, sell_stop_loss, portfolio_value * 0.8, stock_config
            )
            sell_risk_metrics = self.risk_manager.calculate_risk_metrics(
                current_price, sell_stop_loss, sell_take_profit, sell_position_size, portfolio_value
            )
            
            # 评估投资组合风险（假设当前无持仓）
            portfolio_risk = self.risk_manager.assess_portfolio_risk([], portfolio_value)
            
            self.log_info("风险管理分析完成")
            
            return {
                'current_price': current_price,
                'portfolio_value': portfolio_value,
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
            
        except Exception as e:
            self.log_warning(f"风险管理分析失败: {e}")
            return None
    
    def format_output(self, result: CommandResult, output_format: str = 'table') -> str:
        """格式化analyze命令的输出"""
        if not result.success:
            return f"❌ 分析失败: {result.message}"
        
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
        
        # 基本信息
        lines.append(f"\n📈 技术分析结果:")
        lines.append("=" * 60)
        lines.append(f"股票代码: {data['symbol']}")
        lines.append(f"分析时间: {data['analysis_date']}")
        lines.append(f"数据点数: {data['data_points']}")
        
        # 技术分析结果
        tech_analysis = data['technical_analysis']
        if tech_analysis:
            lines.append(f"当前价格: ${tech_analysis['current_price']}")
            
            # RSI分析
            rsi_data = tech_analysis['indicators']['rsi_14']
            lines.append(f"\n📊 RSI (14) 分析:")
            lines.append(f"  当前RSI: {rsi_data['current_rsi']}")
            lines.append(f"  状态: {rsi_data['status']}")
            lines.append(f"  信号: {rsi_data['signal']}")
            
            # MACD分析
            macd_data = tech_analysis['indicators']['macd']
            lines.append(f"\n📈 MACD (12,26,9) 分析:")
            if 'error' not in macd_data:
                lines.append(f"  MACD线: {macd_data['current_macd']}")
                lines.append(f"  信号线: {macd_data['current_signal']}")
                lines.append(f"  交叉信号: {macd_data['cross_signal']}")
                lines.append(f"  位置: {macd_data['position']}")
            else:
                lines.append(f"  错误: {macd_data['error']}")
            
            # ATR分析
            atr_data = tech_analysis['indicators']['atr']
            lines.append(f"\n📊 ATR (14) 波动率分析:")
            if 'error' not in atr_data:
                lines.append(f"  当前ATR: {atr_data['current_atr']}")
                lines.append(f"  波动率水平: {atr_data['volatility_level']}")
                lines.append(f"  波动率信号: {atr_data['volatility_signal']}")
            else:
                lines.append(f"  错误: {atr_data['error']}")
            
            # 支撑阻力位分析
            if 'support_resistance' in tech_analysis:
                sr_data = tech_analysis['support_resistance']
                lines.append(f"\n🎯 支撑阻力位分析:")
                summary = sr_data.get('summary', {})
                lines.append(f"  识别高点: {summary.get('identified_highs', 0)}")
                lines.append(f"  识别低点: {summary.get('identified_lows', 0)}")
                lines.append(f"  支撑位: {summary.get('support_levels', 0)}")
                lines.append(f"  阻力位: {summary.get('resistance_levels', 0)}")
        
        # 信号分析结果
        signals = data.get('signals')
        if signals:
            lines.append(f"\n📡 交易信号分析:")
            lines.append("=" * 60)
            
            buy_signals = signals.get('buy_signals', [])
            sell_signals = signals.get('sell_signals', [])
            filtered_signals = signals.get('filtered_signals', [])
            
            lines.append(f"🟢 买入信号: {len(buy_signals)}个")
            lines.append(f"🔴 卖出信号: {len(sell_signals)}个")
            lines.append(f"⭐ 高质量信号: {len(filtered_signals)}个")
            
            # 显示高质量信号详情
            if filtered_signals:
                lines.append(f"\n⭐ 高质量信号详情:")
                for i, signal in enumerate(filtered_signals[:3], 1):
                    action_emoji = "🟢" if signal.action == "BUY" else "🔴"
                    lines.append(f"  {i}. {action_emoji} {signal.action} @ ${signal.price:.2f}")
                    lines.append(f"     置信度: {signal.confidence:.2%}")
                    lines.append(f"     原因: {signal.reason}")
        
        # 风险管理结果
        risk = data.get('risk_management')
        if risk:
            lines.append(f"\n🛡️ 风险管理分析:")
            lines.append("=" * 60)
            
            portfolio_risk = risk['portfolio_risk']
            lines.append(f"投资组合价值: ${portfolio_risk.total_value:,.2f}")
            lines.append(f"风险级别: {portfolio_risk.risk_level}")
            
            buy_scenario = risk['buy_scenario']
            lines.append(f"\n🟢 买入场景:")
            lines.append(f"  建议仓位: {buy_scenario['position_size']} 股")
            lines.append(f"  止损价位: ${buy_scenario['stop_loss']:.2f}")
            lines.append(f"  止盈价位: ${buy_scenario['take_profit']:.2f}")
            
            sell_scenario = risk['sell_scenario']
            lines.append(f"\n🔴 卖出场景:")
            lines.append(f"  建议仓位: {sell_scenario['position_size']} 股")
            lines.append(f"  止损价位: ${sell_scenario['stop_loss']:.2f}")
            lines.append(f"  止盈价位: ${sell_scenario['take_profit']:.2f}")
        
        lines.append(f"\n✅ 分析完成！")
        return "\n".join(lines)
    
    def _format_csv_output(self, data: Dict[str, Any]) -> str:
        """格式化为CSV输出"""
        lines = ["指标,数值,状态"]
        
        # 基本信息
        lines.append(f"股票代码,{data['symbol']},--")
        
        # 技术分析
        tech_analysis = data['technical_analysis']
        if tech_analysis:
            lines.append(f"当前价格,{tech_analysis['current_price']},--")
            
            # RSI
            rsi_data = tech_analysis['indicators']['rsi_14']
            lines.append(f"RSI(14),{rsi_data['current_rsi']},{rsi_data['status']}")
            
            # MACD
            macd_data = tech_analysis['indicators']['macd']
            if 'error' not in macd_data:
                lines.append(f"MACD线,{macd_data['current_macd']},{macd_data['cross_signal']}")
            
            # ATR
            atr_data = tech_analysis['indicators']['atr']
            if 'error' not in atr_data:
                lines.append(f"ATR(14),{atr_data['current_atr']},{atr_data['volatility_level']}")
        
        # 信号统计
        signals = data.get('signals')
        if signals:
            lines.append(f"买入信号数量,{len(signals.get('buy_signals', []))},个")
            lines.append(f"卖出信号数量,{len(signals.get('sell_signals', []))},个")
            lines.append(f"高质量信号数量,{len(signals.get('filtered_signals', []))},个")
        
        # 风险管理
        risk = data.get('risk_management')
        if risk:
            portfolio_risk = risk['portfolio_risk']
            buy_scenario = risk['buy_scenario']
            lines.append(f"投资组合价值,${portfolio_risk.total_value:,.2f},--")
            lines.append(f"风险级别,{portfolio_risk.risk_level},--")
            lines.append(f"买入建议仓位,{buy_scenario['position_size']},股")
        
        return "\n".join(lines) 