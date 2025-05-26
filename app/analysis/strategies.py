"""
交易信号生成策略模块
Trading Signal Generation Strategies Module

实现各种交易策略的信号生成逻辑，包括支撑阻力位策略、技术指标策略等。
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
import logging

from ..utils.logger import get_analysis_logger

logger = get_analysis_logger()


class TradingSignal:
    """
    交易信号数据类
    """
    
    def __init__(self, 
                 signal_type: str, 
                 action: str, 
                 confidence: float,
                 price: float,
                 timestamp: datetime,
                 reason: str,
                 stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None,
                 position_size: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        初始化交易信号
        
        Args:
            signal_type: 信号类型 ('buy', 'sell', 'hold')
            action: 具体动作 ('enter', 'exit', 'hold')
            confidence: 信号置信度 (0.0-1.0)
            price: 信号触发价格
            timestamp: 信号生成时间
            reason: 信号生成原因
            stop_loss: 止损价位
            take_profit: 止盈价位
            position_size: 建议仓位大小 (0.0-1.0)
            metadata: 附加信息
        """
        self.signal_type = signal_type
        self.action = action
        self.confidence = max(0.0, min(1.0, confidence))  # 确保在0-1范围内
        self.price = price
        self.timestamp = timestamp
        self.reason = reason
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.position_size = position_size or 0.0
        self.metadata = metadata or {}
        
        # 验证信号有效性
        self._validate()
    
    def _validate(self):
        """验证信号参数有效性"""
        if self.signal_type not in ['buy', 'sell', 'hold']:
            raise ValueError(f"无效的信号类型: {self.signal_type}")
        
        if self.action not in ['enter', 'exit', 'hold']:
            raise ValueError(f"无效的动作类型: {self.action}")
        
        if self.price <= 0:
            raise ValueError("价格必须大于0")
        
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise ValueError("止损价位必须大于0")
        
        if self.take_profit is not None and self.take_profit <= 0:
            raise ValueError("止盈价位必须大于0")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'signal_type': self.signal_type,
            'action': self.action,
            'confidence': round(self.confidence, 3),
            'price': round(self.price, 2),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'reason': self.reason,
            'stop_loss': round(self.stop_loss, 2) if self.stop_loss else None,
            'take_profit': round(self.take_profit, 2) if self.take_profit else None,
            'position_size': round(self.position_size, 3),
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"TradingSignal({self.signal_type.upper()} {self.action.upper()} "
                f"@${self.price:.2f}, confidence={self.confidence:.2f}, "
                f"reason='{self.reason}')")


class BaseStrategy(ABC):
    """
    交易策略基类
    
    所有具体策略都应该继承此基类并实现必要的抽象方法。
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            config: 策略配置参数
        """
        self.name = name
        self.config = config or {}
        self.signals_generated = []  # 历史信号记录
        self.last_signal = None      # 最近一次信号
        self.logger = get_analysis_logger()
        
        self.logger.info(f"策略初始化: {self.name}")
    
    @abstractmethod
    def analyze(self, df: pd.DataFrame, **kwargs) -> List[TradingSignal]:
        """
        分析数据并生成交易信号
        
        Args:
            df: 股票数据DataFrame，包含OHLCV数据
            **kwargs: 额外的分析参数
            
        Returns:
            交易信号列表
        """
        pass
    
    @abstractmethod
    def get_strategy_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            策略的详细描述
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """获取策略配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新策略配置"""
        self.config.update(new_config)
        self.logger.info(f"策略配置已更新: {self.name}")
    
    def get_signal_history(self) -> List[Dict[str, Any]]:
        """获取历史信号记录"""
        return [signal.to_dict() for signal in self.signals_generated]
    
    def get_last_signal(self) -> Optional[Dict[str, Any]]:
        """获取最近一次信号"""
        return self.last_signal.to_dict() if self.last_signal else None
    
    def clear_signals(self):
        """清空信号历史"""
        self.signals_generated = []
        self.last_signal = None
        self.logger.info(f"策略信号历史已清空: {self.name}")
    
    def _add_signal(self, signal: TradingSignal):
        """添加信号到历史记录"""
        self.signals_generated.append(signal)
        self.last_signal = signal
        self.logger.info(f"生成新信号: {signal}")
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证输入数据的有效性
        
        Args:
            df: 输入的股票数据
            
        Returns:
            数据是否有效
        """
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            self.logger.error(f"缺少必要的数据列: {missing_columns}")
            return False
        
        if len(df) == 0:
            self.logger.error("数据为空")
            return False
        
        # 检查数据中是否有NaN值
        if df[required_columns].isnull().any().any():
            self.logger.warning("数据中包含NaN值")
        
        return True


class SupportResistanceStrategy(BaseStrategy):
    """
    支撑阻力位交易策略
    
    基于支撑阻力位识别的交易信号生成策略。
    当价格接近支撑位时生成买入信号，接近阻力位时生成卖出信号。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化支撑阻力位策略
        
        Args:
            config: 策略配置，包含以下可选参数:
                - window: 局部极值搜索窗口，默认5
                - min_change_pct: 最小变化百分比，默认1.0
                - tolerance: 支撑阻力位聚类容忍度，默认0.5
                - proximity_threshold: 接近支撑阻力位的阈值，默认2.0%
                - min_confidence: 最小信号置信度，默认0.6
                - atr_multiplier: ATR止损倍数，默认2.0
        """
        default_config = {
            'window': 5,
            'min_change_pct': 1.0,
            'tolerance': 0.5,
            'proximity_threshold': 2.0,  # 接近阈值百分比
            'min_confidence': 0.6,
            'atr_multiplier': 2.0,
            'min_strength_rating': '弱'  # 最小强度要求
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("SupportResistanceStrategy", default_config)
    
    def analyze(self, df: pd.DataFrame, **kwargs) -> List[TradingSignal]:
        """
        分析数据并生成基于支撑阻力位的交易信号
        
        Args:
            df: 股票数据DataFrame
            **kwargs: 额外参数
            
        Returns:
            交易信号列表
        """
        if not self.validate_data(df):
            return []
        
        signals = []
        
        try:
            # 导入支撑阻力位分析模块
            from .support_resistance import SupportResistanceAnalyzer
            from .indicators import TechnicalIndicators
            
            # 进行支撑阻力位分析
            sr_analyzer = SupportResistanceAnalyzer()
            analysis = sr_analyzer.analyze_price_action(
                df, 
                window=self.config['window'],
                min_change_pct=self.config['min_change_pct'],
                tolerance=self.config['tolerance']
            )
            
            # 手动调整当前位置分析以使用策略的proximity_threshold
            sr_levels = analysis.get('support_resistance', {})
            if sr_levels.get('current_position'):
                current_position = self._adjust_position_analysis_with_proximity_threshold(
                    sr_levels['current_position'], 
                    self.config['proximity_threshold']
                )
                analysis['support_resistance']['current_position'] = current_position
            
            # 计算ATR用于止损计算
            tech_indicators = TechnicalIndicators()
            atr = tech_indicators.calculate_atr(df, 14)
            current_atr = atr.iloc[-1] if len(atr) > 0 else 0
            
            # 获取完整技术分析结果（为增强版买入信号提供技术指标确认）
            try:
                technical_summary = tech_indicators.get_technical_summary(df)
                # 将技术分析结果合并到完整分析中
                analysis.update(technical_summary)
            except Exception as e:
                self.logger.warning(f"获取技术分析摘要失败: {e}")
            
            current_price = df['Close'].iloc[-1]
            current_time = datetime.now()
            
            # 获取支撑阻力位信息
            sr_levels = analysis.get('support_resistance', {})
            current_position = sr_levels.get('current_position')
            
            if not current_position:
                self.logger.info("无法确定当前价格位置，跳过信号生成")
                return []
            
            # 生成交易信号
            signal = self._generate_signal_from_position(
                current_position, current_price, current_time, current_atr, analysis
            )
            
            if signal:
                signals.append(signal)
                self._add_signal(signal)
            
        except Exception as e:
            self.logger.error(f"支撑阻力位策略分析失败: {e}")
        
        return signals
    
    def _generate_signal_from_position(self, 
                                     position_info: Dict[str, Any], 
                                     current_price: float, 
                                     current_time: datetime,
                                     current_atr: float,
                                     full_analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        根据当前位置信息生成交易信号
        
        Args:
            position_info: 当前位置信息
            current_price: 当前价格
            current_time: 当前时间
            current_atr: 当前ATR值
            full_analysis: 完整分析结果
            
        Returns:
            交易信号或None
        """
        position_desc = position_info.get('position_description', '')
        resistance_distance = position_info.get('resistance_distance')
        support_distance = position_info.get('support_distance')
        nearest_resistance = position_info.get('nearest_resistance')
        nearest_support = position_info.get('nearest_support')
        
        proximity_threshold = self.config['proximity_threshold']
        min_confidence = self.config['min_confidence']
        atr_multiplier = self.config['atr_multiplier']
        min_strength = self.config['min_strength_rating']
        
        # 检查是否接近支撑位（买入机会）- 增强版买入信号生成
        if (position_desc == "接近支撑位" or 
            (support_distance and support_distance['percentage'] <= proximity_threshold)):
            
            if nearest_support and self._is_level_strong_enough(nearest_support, min_strength):
                # 生成增强版买入信号
                buy_signal = self._generate_enhanced_buy_signal(
                    current_price, current_time, current_atr, 
                    nearest_support, support_distance, full_analysis
                )
                if buy_signal:
                    return buy_signal
        
        # 检查是否接近阻力位（卖出机会）- 增强版卖出信号生成
        elif (position_desc == "接近阻力位" or 
              (resistance_distance and resistance_distance['percentage'] <= proximity_threshold)):
            
            if nearest_resistance and self._is_level_strong_enough(nearest_resistance, min_strength):
                # 生成增强版卖出信号
                sell_signal = self._generate_enhanced_sell_signal(
                    current_price, current_time, current_atr, 
                    nearest_resistance, resistance_distance, full_analysis
                )
                if sell_signal:
                    return sell_signal
        
        return None
    
    def _generate_enhanced_buy_signal(self,
                                    current_price: float,
                                    current_time: datetime,
                                    current_atr: float,
                                    nearest_support: Dict[str, Any],
                                    support_distance: Optional[Dict[str, Any]],
                                    full_analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        生成增强版买入信号（T4.1.2核心功能）
        
        包含多重技术指标确认和高级信号质量评估
        
        Args:
            current_price: 当前价格
            current_time: 当前时间
            current_atr: 当前ATR值
            nearest_support: 最近支撑位信息
            support_distance: 支撑位距离信息
            full_analysis: 完整分析结果
            
        Returns:
            增强版买入信号或None
        """
        try:
            # 1. 基础置信度计算
            base_confidence = self._calculate_confidence(
                signal_type='buy',
                distance_info=support_distance,
                level_info=nearest_support,
                full_analysis=full_analysis
            )
            
            # 2. 技术指标确认分析
            technical_confirmations = self._analyze_technical_confirmations_for_buy(full_analysis)
            
            # 3. 成交量确认
            volume_confirmation = self._analyze_volume_for_buy(full_analysis)
            
            # 4. 趋势确认
            trend_confirmation = self._analyze_trend_for_buy(full_analysis)
            
            # 5. 综合置信度计算
            enhanced_confidence = self._calculate_enhanced_buy_confidence(
                base_confidence,
                technical_confirmations,
                volume_confirmation,
                trend_confirmation
            )
            
            # 6. 检查最小置信度要求
            if enhanced_confidence < self.config['min_confidence']:
                self.logger.debug(f"买入信号置信度不足: {enhanced_confidence:.3f} < {self.config['min_confidence']}")
                return None
            
            # 7. 计算增强版止损止盈
            stop_loss, take_profit = self._calculate_enhanced_risk_levels(
                current_price, current_atr, nearest_support, technical_confirmations
            )
            
            # 8. 生成信号原因描述
            reason = self._generate_buy_signal_reason(
                nearest_support, technical_confirmations, volume_confirmation, trend_confirmation
            )
            
            # 9. 计算动态仓位大小
            position_size = self._calculate_dynamic_position_size(enhanced_confidence, technical_confirmations)
            
            # 10. 生成增强版买入信号
            return TradingSignal(
                signal_type='buy',
                action='enter',
                confidence=enhanced_confidence,
                price=current_price,
                timestamp=current_time,
                reason=reason,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                metadata={
                    'support_level': nearest_support['price'],
                    'support_strength': nearest_support['strength_rating'],
                    'distance_pct': support_distance['percentage'] if support_distance else None,
                    'atr_value': current_atr,
                    'technical_confirmations': technical_confirmations,
                    'volume_confirmation': volume_confirmation,
                    'trend_confirmation': trend_confirmation,
                    'base_confidence': base_confidence,
                    'enhancement_factor': enhanced_confidence - base_confidence
                }
            )
            
        except Exception as e:
            self.logger.error(f"增强版买入信号生成失败: {e}")
            return None
    
    def _generate_enhanced_sell_signal(self,
                                     current_price: float,
                                     current_time: datetime,
                                     current_atr: float,
                                     nearest_resistance: Dict[str, Any],
                                     resistance_distance: Optional[Dict[str, Any]],
                                     full_analysis: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        生成增强版卖出信号（T4.1.3核心功能）
        
        包含多重技术指标确认和高级信号质量评估
        
        Args:
            current_price: 当前价格
            current_time: 当前时间
            current_atr: 当前ATR值
            nearest_resistance: 最近阻力位信息
            resistance_distance: 阻力位距离信息
            full_analysis: 完整分析结果
            
        Returns:
            增强版卖出信号或None
        """
        try:
            # 1. 基础置信度计算
            base_confidence = self._calculate_confidence(
                signal_type='sell',
                distance_info=resistance_distance,
                level_info=nearest_resistance,
                full_analysis=full_analysis
            )
            
            # 2. 技术指标确认分析
            technical_confirmations = self._analyze_technical_confirmations_for_sell(full_analysis)
            
            # 3. 成交量确认
            volume_confirmation = self._analyze_volume_for_sell(full_analysis)
            
            # 4. 趋势确认
            trend_confirmation = self._analyze_trend_for_sell(full_analysis)
            
            # 5. 综合置信度计算
            enhanced_confidence = self._calculate_enhanced_sell_confidence(
                base_confidence,
                technical_confirmations,
                volume_confirmation,
                trend_confirmation
            )
            
            # 6. 检查最小置信度要求
            if enhanced_confidence < self.config['min_confidence']:
                self.logger.debug(f"卖出信号置信度不足: {enhanced_confidence:.3f} < {self.config['min_confidence']}")
                return None
            
            # 7. 计算增强版止损止盈
            stop_loss, take_profit = self._calculate_enhanced_sell_risk_levels(
                current_price, current_atr, nearest_resistance, technical_confirmations
            )
            
            # 8. 生成信号原因描述
            reason = self._generate_sell_signal_reason(
                nearest_resistance, technical_confirmations, volume_confirmation, trend_confirmation
            )
            
            # 9. 计算动态仓位大小
            position_size = self._calculate_dynamic_position_size(enhanced_confidence, technical_confirmations)
            
            # 10. 生成增强版卖出信号
            return TradingSignal(
                signal_type='sell',
                action='enter',
                confidence=enhanced_confidence,
                price=current_price,
                timestamp=current_time,
                reason=reason,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                metadata={
                    'resistance_level': nearest_resistance['price'],
                    'resistance_strength': nearest_resistance['strength_rating'],
                    'distance_pct': resistance_distance['percentage'] if resistance_distance else None,
                    'atr_value': current_atr,
                    'technical_confirmations': technical_confirmations,
                    'volume_confirmation': volume_confirmation,
                    'trend_confirmation': trend_confirmation,
                    'base_confidence': base_confidence,
                    'enhancement_factor': enhanced_confidence - base_confidence
                }
            )
            
        except Exception as e:
            self.logger.error(f"增强版卖出信号生成失败: {e}")
            return None
    
    def _analyze_technical_confirmations_for_buy(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析技术指标对买入信号的确认
        
        Args:
            full_analysis: 完整分析结果
            
        Returns:
            技术确认信息
        """
        confirmations = {
            'rsi_oversold': False,
            'macd_bullish': False,
            'moving_avg_support': False,
            'confirmation_count': 0,
            'confirmation_strength': 0.0
        }
        
        try:
            # 从完整分析中获取技术指标数据（如果可用）
            # 注意：这里需要在调用analyze时传入技术分析结果
            indicators = full_analysis.get('indicators', {})
            
            # RSI超卖确认
            rsi_data = indicators.get('rsi_14', {})
            if rsi_data and not rsi_data.get('error'):
                current_rsi = rsi_data.get('current_rsi', 50)
                if current_rsi is not None and current_rsi <= 35:  # 更严格的超卖条件
                    confirmations['rsi_oversold'] = True
                    confirmations['confirmation_count'] += 1
                    confirmations['confirmation_strength'] += 0.2
                    if current_rsi <= 25:  # 极度超卖
                        confirmations['confirmation_strength'] += 0.1
            
            # MACD看涨确认
            macd_data = indicators.get('macd', {})
            if macd_data and not macd_data.get('error'):
                signal_type = macd_data.get('signal_type', '')
                cross_signal = macd_data.get('cross_signal', '')
                position = macd_data.get('position', '')
                
                # 金叉或即将金叉
                if signal_type == '买入信号' or cross_signal == '金叉':
                    confirmations['macd_bullish'] = True
                    confirmations['confirmation_count'] += 1
                    confirmations['confirmation_strength'] += 0.25
                # MACD在零轴上方且柱状图上升
                elif position == '多头区域' and macd_data.get('histogram_trend') == '上升':
                    confirmations['macd_bullish'] = True
                    confirmations['confirmation_count'] += 1
                    confirmations['confirmation_strength'] += 0.15
            
            # 移动平均线支撑确认
            price_position = full_analysis.get('price_position', {})
            if price_position:
                above_count = sum(1 for pos in price_position.values() if pos == 'above')
                total_count = len([pos for pos in price_position.values() if pos in ['above', 'below']])
                
                if total_count > 0:
                    above_ratio = above_count / total_count
                    if above_ratio >= 0.5:  # 至少一半均线上方
                        confirmations['moving_avg_support'] = True
                        confirmations['confirmation_count'] += 1
                        confirmations['confirmation_strength'] += 0.1 + (above_ratio - 0.5) * 0.2
            
        except Exception as e:
            self.logger.warning(f"技术指标确认分析失败: {e}")
        
        return confirmations
    
    def _analyze_volume_for_buy(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析成交量对买入信号的确认
        
        Args:
            full_analysis: 完整分析结果
            
        Returns:
            成交量确认信息
        """
        volume_confirmation = {
            'increasing_volume': False,
            'above_average': False,
            'confirmation_strength': 0.0
        }
        
        try:
            # 这里可以添加成交量分析逻辑
            # 由于当前数据结构中没有成交量分析，先提供基础框架
            volume_confirmation['confirmation_strength'] = 0.05  # 基础分值
            
        except Exception as e:
            self.logger.warning(f"成交量分析失败: {e}")
        
        return volume_confirmation
    
    def _analyze_trend_for_buy(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析趋势对买入信号的确认
        
        Args:
            full_analysis: 完整分析结果
            
        Returns:
            趋势确认信息
        """
        trend_confirmation = {
            'uptrend': False,
            'trend_strength': 'neutral',
            'confirmation_strength': 0.0
        }
        
        try:
            # 基于价格相对均线位置判断趋势
            price_position = full_analysis.get('price_position', {})
            if price_position:
                above_count = sum(1 for pos in price_position.values() if pos == 'above')
                total_count = len([pos for pos in price_position.values() if pos in ['above', 'below']])
                
                if total_count > 0:
                    above_ratio = above_count / total_count
                    if above_ratio >= 0.6:
                        trend_confirmation['uptrend'] = True
                        trend_confirmation['trend_strength'] = 'strong'
                        trend_confirmation['confirmation_strength'] = 0.15
                    elif above_ratio >= 0.4:
                        trend_confirmation['trend_strength'] = 'weak_up'
                        trend_confirmation['confirmation_strength'] = 0.05
            
            # 检查ATR趋势（波动率变化）
            indicators = full_analysis.get('indicators', {})
            atr_data = indicators.get('atr', {})
            if atr_data and not atr_data.get('error'):
                atr_trend = atr_data.get('atr_trend', '')
                if atr_trend == '下降':  # 波动率下降有利于趋势延续
                    trend_confirmation['confirmation_strength'] += 0.05
            
        except Exception as e:
            self.logger.warning(f"趋势分析失败: {e}")
        
        return trend_confirmation
    
    def _calculate_enhanced_buy_confidence(self,
                                         base_confidence: float,
                                         technical_confirmations: Dict[str, Any],
                                         volume_confirmation: Dict[str, Any],
                                         trend_confirmation: Dict[str, Any]) -> float:
        """
        计算增强版买入信号置信度
        
        Args:
            base_confidence: 基础置信度
            technical_confirmations: 技术确认信息
            volume_confirmation: 成交量确认信息
            trend_confirmation: 趋势确认信息
            
        Returns:
            增强版置信度
        """
        enhanced_confidence = base_confidence
        
        # 技术指标确认加成
        enhanced_confidence += technical_confirmations.get('confirmation_strength', 0.0)
        
        # 成交量确认加成
        enhanced_confidence += volume_confirmation.get('confirmation_strength', 0.0)
        
        # 趋势确认加成
        enhanced_confidence += trend_confirmation.get('confirmation_strength', 0.0)
        
        # 多重确认奖励
        confirmation_count = technical_confirmations.get('confirmation_count', 0)
        if confirmation_count >= 2:
            enhanced_confidence += 0.1  # 2个以上确认信号奖励
        if confirmation_count >= 3:
            enhanced_confidence += 0.05  # 3个确认信号额外奖励
        
        # 确保在合理范围内
        return max(0.0, min(1.0, enhanced_confidence))
    
    def _calculate_enhanced_risk_levels(self,
                                      current_price: float,
                                      current_atr: float,
                                      nearest_support: Dict[str, Any],
                                      technical_confirmations: Dict[str, Any]) -> Tuple[float, float]:
        """
        计算增强版风险管理水平
        
        Args:
            current_price: 当前价格
            current_atr: 当前ATR值
            nearest_support: 最近支撑位
            technical_confirmations: 技术确认信息
            
        Returns:
            (止损价位, 止盈价位)
        """
        atr_multiplier = self.config['atr_multiplier']
        
        # 基础止损：支撑位下方或ATR止损，取较近者
        support_stop = nearest_support['price'] * 0.98  # 支撑位下方2%
        atr_stop = current_price - (current_atr * atr_multiplier)
        stop_loss = max(support_stop, atr_stop)  # 取较高者，减少风险
        
        # 根据技术确认强度调整风险回报比
        confirmation_strength = technical_confirmations.get('confirmation_strength', 0.0)
        
        if confirmation_strength >= 0.3:
            # 强确认：使用3:1风险回报比
            risk_distance = current_price - stop_loss
            take_profit = current_price + (risk_distance * 3)
        elif confirmation_strength >= 0.15:
            # 中等确认：使用2.5:1风险回报比
            risk_distance = current_price - stop_loss
            take_profit = current_price + (risk_distance * 2.5)
        else:
            # 弱确认：使用2:1风险回报比
            risk_distance = current_price - stop_loss
            take_profit = current_price + (risk_distance * 2)
        
        return stop_loss, take_profit
    
    def _generate_buy_signal_reason(self,
                                  nearest_support: Dict[str, Any],
                                  technical_confirmations: Dict[str, Any],
                                  volume_confirmation: Dict[str, Any],
                                  trend_confirmation: Dict[str, Any]) -> str:
        """
        生成买入信号的详细原因描述
        
        Args:
            nearest_support: 最近支撑位
            technical_confirmations: 技术确认
            volume_confirmation: 成交量确认
            trend_confirmation: 趋势确认
            
        Returns:
            信号原因描述
        """
        reason_parts = []
        
        # 主要原因：接近支撑位
        support_price = nearest_support['price']
        support_strength = nearest_support['strength_rating']
        reason_parts.append(f"接近{support_strength}支撑位${support_price:.2f}")
        
        # 技术指标确认
        confirmations = []
        if technical_confirmations.get('rsi_oversold'):
            confirmations.append("RSI超卖")
        if technical_confirmations.get('macd_bullish'):
            confirmations.append("MACD看涨")
        if technical_confirmations.get('moving_avg_support'):
            confirmations.append("均线支撑")
        
        if confirmations:
            reason_parts.append(f"技术确认: {'/'.join(confirmations)}")
        
        # 趋势确认
        if trend_confirmation.get('uptrend'):
            trend_strength = trend_confirmation.get('trend_strength', 'weak')
            if trend_strength == 'strong':
                reason_parts.append("强上升趋势")
            else:
                reason_parts.append("上升趋势")
        
        return "，".join(reason_parts)
    
    def _calculate_dynamic_position_size(self,
                                       confidence: float,
                                       technical_confirmations: Dict[str, Any]) -> float:
        """
        基于信号质量计算动态仓位大小
        
        Args:
            confidence: 信号置信度
            technical_confirmations: 技术确认信息
            
        Returns:
            建议仓位大小 (0.0-1.0)
        """
        # 基础仓位：基于置信度
        base_position = confidence * 0.5  # 最大50%仓位
        
        # 根据技术确认数量调整
        confirmation_count = technical_confirmations.get('confirmation_count', 0)
        if confirmation_count >= 3:
            position_multiplier = 1.2
        elif confirmation_count >= 2:
            position_multiplier = 1.1
        else:
            position_multiplier = 1.0
        
        dynamic_position = base_position * position_multiplier
        
        # 确保在合理范围内
        return max(0.05, min(0.6, dynamic_position))  # 最小5%，最大60%
    
    def _is_level_strong_enough(self, level_info: Dict[str, Any], min_strength: str) -> bool:
        """
        检查支撑阻力位强度是否足够
        
        Args:
            level_info: 支撑阻力位信息
            min_strength: 最小强度要求
            
        Returns:
            强度是否足够
        """
        strength_order = {'弱': 1, '中': 2, '强': 3}
        level_strength = level_info.get('strength_rating', '弱')
        
        return strength_order.get(level_strength, 0) >= strength_order.get(min_strength, 1)
    
    def _calculate_confidence(self, 
                            signal_type: str,
                            distance_info: Optional[Dict[str, Any]],
                            level_info: Dict[str, Any],
                            full_analysis: Dict[str, Any]) -> float:
        """
        计算信号置信度
        
        Args:
            signal_type: 信号类型
            distance_info: 距离信息
            level_info: 支撑阻力位信息
            full_analysis: 完整分析结果
            
        Returns:
            置信度 (0.0-1.0)
        """
        confidence = 0.5  # 基础置信度
        
        # 基于支撑阻力位强度调整
        strength_rating = level_info.get('strength_rating', '弱')
        if strength_rating == '强':
            confidence += 0.2
        elif strength_rating == '中':
            confidence += 0.1
        
        # 基于触及次数调整
        touch_count = level_info.get('touch_count', 0)
        confidence += min(0.15, touch_count * 0.05)
        
        # 基于距离调整（越近置信度越高）
        if distance_info:
            distance_pct = distance_info.get('percentage', 100)
            if distance_pct <= 1.0:
                confidence += 0.15
            elif distance_pct <= 2.0:
                confidence += 0.1
            elif distance_pct <= 3.0:
                confidence += 0.05
        
        # 基于其他技术指标确认（如果有的话）
        # 这里可以添加RSI、MACD等确认逻辑
        
        # 确保在0-1范围内
        return max(0.0, min(1.0, confidence))
    
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        return """
支撑阻力位交易策略:

该策略基于技术分析中的支撑阻力位理论，通过识别价格历史中的关键支撑位和阻力位，
在价格接近这些关键位置时生成交易信号。

核心逻辑:
1. 识别历史价格中的局部高低点
2. 聚类相近的价格水平形成支撑阻力位
3. 评估支撑阻力位的强度（基于触及次数和价格反应幅度）
4. 当价格接近强支撑位时生成买入信号
5. 当价格接近强阻力位时生成卖出信号

风险控制:
- 使用ATR计算止损位
- 采用2:1的风险回报比设置止盈位
- 基于信号置信度调整仓位大小
- 只有满足最小置信度要求的信号才会生成

适用场景:
- 趋势震荡或横盘整理的市场
- 有明显支撑阻力位的股票
- 中短期交易策略
"""

    def _adjust_position_analysis_with_proximity_threshold(self, 
                                                         current_position: Dict[str, Any], 
                                                         proximity_threshold: float) -> Dict[str, Any]:
        """
        根据策略的proximity_threshold调整当前位置分析
        
        Args:
            current_position: 原始位置分析结果
            proximity_threshold: 策略的接近阈值(百分比)
            
        Returns:
            调整后的位置分析结果
        """
        # 复制原始数据
        adjusted_position = current_position.copy()
        
        # 重新判断位置描述
        resistance_distance = current_position.get('resistance_distance')
        support_distance = current_position.get('support_distance')
        
        position_desc = "中性区域"
        
        # 使用策略配置的proximity_threshold重新判断
        if resistance_distance and resistance_distance['percentage'] <= proximity_threshold:
            position_desc = "接近阻力位"
        elif support_distance and support_distance['percentage'] <= proximity_threshold:
            position_desc = "接近支撑位"
        elif resistance_distance and support_distance:
            if resistance_distance['percentage'] < support_distance['percentage']:
                position_desc = "偏向阻力位"
            else:
                position_desc = "偏向支撑位"
        
        adjusted_position['position_description'] = position_desc
        
        return adjusted_position

    def _analyze_technical_confirmations_for_sell(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析技术指标对卖出信号的确认
        
        Args:
            full_analysis: 完整分析结果
            
        Returns:
            技术确认信息
        """
        confirmations = {
            'rsi_overbought': False,
            'macd_bearish': False,
            'moving_avg_resistance': False,
            'confirmation_count': 0,
            'confirmation_strength': 0.0
        }
        
        try:
            # 从完整分析中获取技术指标数据
            indicators = full_analysis.get('indicators', {})
            
            # RSI超买确认
            rsi_data = indicators.get('rsi_14', {})
            if rsi_data and not rsi_data.get('error'):
                current_rsi = rsi_data.get('current_rsi', 50)
                if current_rsi is not None and current_rsi >= 65:  # 更严格的超买条件
                    confirmations['rsi_overbought'] = True
                    confirmations['confirmation_count'] += 1
                    confirmations['confirmation_strength'] += 0.2
                    if current_rsi >= 75:  # 极度超买
                        confirmations['confirmation_strength'] += 0.1
            
            # MACD看跌确认
            macd_data = indicators.get('macd', {})
            if macd_data and not macd_data.get('error'):
                signal_type = macd_data.get('signal_type', '')
                cross_signal = macd_data.get('cross_signal', '')
                position = macd_data.get('position', '')
                
                # 死叉或即将死叉
                if signal_type == '卖出信号' or cross_signal == '死叉':
                    confirmations['macd_bearish'] = True
                    confirmations['confirmation_count'] += 1
                    confirmations['confirmation_strength'] += 0.25
                # MACD在零轴下方且柱状图下降
                elif position == '空头区域' and macd_data.get('histogram_trend') == '下降':
                    confirmations['macd_bearish'] = True
                    confirmations['confirmation_count'] += 1
                    confirmations['confirmation_strength'] += 0.15
            
            # 移动平均线阻力确认
            price_position = full_analysis.get('price_position', {})
            if price_position:
                below_count = sum(1 for pos in price_position.values() if pos == 'below')
                total_count = len([pos for pos in price_position.values() if pos in ['above', 'below']])
                
                if total_count > 0:
                    below_ratio = below_count / total_count
                    if below_ratio >= 0.5:  # 至少一半均线下方
                        confirmations['moving_avg_resistance'] = True
                        confirmations['confirmation_count'] += 1
                        confirmations['confirmation_strength'] += 0.1 + (below_ratio - 0.5) * 0.2
            
        except Exception as e:
            self.logger.warning(f"卖出技术指标确认分析失败: {e}")
        
        return confirmations

    def _analyze_volume_for_sell(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析成交量对卖出信号的确认
        
        Args:
            full_analysis: 完整分析结果
            
        Returns:
            成交量确认信息
        """
        volume_confirmation = {
            'increasing_volume': False,
            'above_average': False,
            'confirmation_strength': 0.0
        }
        
        try:
            # 这里可以添加成交量分析逻辑
            # 由于当前数据结构中没有成交量分析，先提供基础框架
            volume_confirmation['confirmation_strength'] = 0.05  # 基础分值
            
        except Exception as e:
            self.logger.warning(f"卖出成交量分析失败: {e}")
        
        return volume_confirmation
    
    def _analyze_trend_for_sell(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析趋势对卖出信号的确认
        
        Args:
            full_analysis: 完整分析结果
            
        Returns:
            趋势确认信息
        """
        trend_confirmation = {
            'downtrend': False,
            'trend_strength': 'neutral',
            'confirmation_strength': 0.0
        }
        
        try:
            # 基于价格相对均线位置判断趋势
            price_position = full_analysis.get('price_position', {})
            if price_position:
                below_count = sum(1 for pos in price_position.values() if pos == 'below')
                total_count = len([pos for pos in price_position.values() if pos in ['above', 'below']])
                
                if total_count > 0:
                    below_ratio = below_count / total_count
                    if below_ratio >= 0.6:
                        trend_confirmation['downtrend'] = True
                        trend_confirmation['trend_strength'] = 'strong'
                        trend_confirmation['confirmation_strength'] = 0.15
                    elif below_ratio >= 0.4:
                        trend_confirmation['trend_strength'] = 'weak_down'
                        trend_confirmation['confirmation_strength'] = 0.05
            
            # 检查ATR趋势（波动率变化）
            indicators = full_analysis.get('indicators', {})
            atr_data = indicators.get('atr', {})
            if atr_data and not atr_data.get('error'):
                atr_trend = atr_data.get('atr_trend', '')
                if atr_trend == '上升':  # 波动率上升有利于卖出信号
                    trend_confirmation['confirmation_strength'] += 0.05
            
        except Exception as e:
            self.logger.warning(f"卖出趋势分析失败: {e}")
        
        return trend_confirmation

    def _calculate_enhanced_sell_confidence(self,
                                          base_confidence: float,
                                          technical_confirmations: Dict[str, Any],
                                          volume_confirmation: Dict[str, Any],
                                          trend_confirmation: Dict[str, Any]) -> float:
        """
        计算增强版卖出信号置信度
        
        Args:
            base_confidence: 基础置信度
            technical_confirmations: 技术确认信息
            volume_confirmation: 成交量确认信息
            trend_confirmation: 趋势确认信息
            
        Returns:
            增强版置信度
        """
        enhanced_confidence = base_confidence
        
        # 技术指标确认加成
        enhanced_confidence += technical_confirmations.get('confirmation_strength', 0.0)
        
        # 成交量确认加成
        enhanced_confidence += volume_confirmation.get('confirmation_strength', 0.0)
        
        # 趋势确认加成
        enhanced_confidence += trend_confirmation.get('confirmation_strength', 0.0)
        
        # 多重确认奖励
        confirmation_count = technical_confirmations.get('confirmation_count', 0)
        if confirmation_count >= 2:
            enhanced_confidence += 0.1  # 2个以上确认信号奖励
        if confirmation_count >= 3:
            enhanced_confidence += 0.05  # 3个确认信号额外奖励
        
        # 确保在合理范围内
        return max(0.0, min(1.0, enhanced_confidence))

    def _calculate_enhanced_sell_risk_levels(self,
                                           current_price: float,
                                           current_atr: float,
                                           nearest_resistance: Dict[str, Any],
                                           technical_confirmations: Dict[str, Any]) -> Tuple[float, float]:
        """
        计算增强版卖出信号风险管理水平
        
        Args:
            current_price: 当前价格
            current_atr: 当前ATR值
            nearest_resistance: 最近阻力位
            technical_confirmations: 技术确认信息
            
        Returns:
            (止损价位, 止盈价位)
        """
        atr_multiplier = self.config['atr_multiplier']
        
        # 基础止损：阻力位上方或ATR止损，取较近者
        resistance_stop = nearest_resistance['price'] * 1.02  # 阻力位上方2%
        atr_stop = current_price + (current_atr * atr_multiplier)
        stop_loss = min(resistance_stop, atr_stop)  # 取较低者，减少风险
        
        # 根据技术确认强度调整风险回报比
        confirmation_strength = technical_confirmations.get('confirmation_strength', 0.0)
        
        if confirmation_strength >= 0.3:
            # 强确认：使用3:1风险回报比
            risk_distance = stop_loss - current_price
            take_profit = current_price - (risk_distance * 3)
        elif confirmation_strength >= 0.15:
            # 中等确认：使用2.5:1风险回报比
            risk_distance = stop_loss - current_price
            take_profit = current_price - (risk_distance * 2.5)
        else:
            # 弱确认：使用2:1风险回报比
            risk_distance = stop_loss - current_price
            take_profit = current_price - (risk_distance * 2)
        
        return stop_loss, take_profit

    def _generate_sell_signal_reason(self,
                                   nearest_resistance: Dict[str, Any],
                                   technical_confirmations: Dict[str, Any],
                                   volume_confirmation: Dict[str, Any],
                                   trend_confirmation: Dict[str, Any]) -> str:
        """
        生成卖出信号的详细原因描述
        
        Args:
            nearest_resistance: 最近阻力位
            technical_confirmations: 技术确认
            volume_confirmation: 成交量确认
            trend_confirmation: 趋势确认
            
        Returns:
            信号原因描述
        """
        reason_parts = []
        
        # 主要原因：接近阻力位
        resistance_price = nearest_resistance['price']
        resistance_strength = nearest_resistance['strength_rating']
        reason_parts.append(f"接近{resistance_strength}阻力位${resistance_price:.2f}")
        
        # 技术指标确认
        confirmations = []
        if technical_confirmations.get('rsi_overbought'):
            confirmations.append("RSI超买")
        if technical_confirmations.get('macd_bearish'):
            confirmations.append("MACD看跌")
        if technical_confirmations.get('moving_avg_resistance'):
            confirmations.append("均线阻力")
        
        if confirmations:
            reason_parts.append(f"技术确认: {'/'.join(confirmations)}")
        
        # 趋势确认
        if trend_confirmation.get('downtrend'):
            trend_strength = trend_confirmation.get('trend_strength', 'weak')
            if trend_strength == 'strong':
                reason_parts.append("强下降趋势")
            else:
                reason_parts.append("下降趋势")
        
        return "，".join(reason_parts)


# 便捷函数
def create_support_resistance_strategy(config: Optional[Dict[str, Any]] = None) -> SupportResistanceStrategy:
    """
    创建支撑阻力位策略的便捷函数
    
    Args:
        config: 策略配置参数
        
    Returns:
        支撑阻力位策略实例
    """
    return SupportResistanceStrategy(config)


def analyze_with_strategy(df: pd.DataFrame, 
                         strategy: BaseStrategy,
                         **kwargs) -> List[Dict[str, Any]]:
    """
    使用指定策略分析股票数据的便捷函数
    
    Args:
        df: 股票数据DataFrame
        strategy: 交易策略实例
        **kwargs: 额外的分析参数
        
    Returns:
        交易信号字典列表
    """
    signals = strategy.analyze(df, **kwargs)
    return [signal.to_dict() for signal in signals] 