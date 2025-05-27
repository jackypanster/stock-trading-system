"""
信号置信度计算器模块
Signal Confidence Calculator Module

实现T4.2.1任务：提供精确的信号置信度计算和评估功能。
支持多种置信度计算方法，包括技术指标确认、市场环境评估、历史表现等。
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..utils.logger import get_analysis_logger
from ..core.config import get_config

logger = get_analysis_logger()


class ConfidenceCalculator:
    """
    信号置信度计算器
    
    提供多维度的信号置信度评估，包括：
    1. 技术指标确认强度
    2. 支撑阻力位质量
    3. 市场环境适应性
    4. 历史信号表现
    5. 风险回报比评估
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化置信度计算器
        
        Args:
            config: 配置参数，包含各种权重和阈值设置。如果为None，则使用系统配置
        """
        # 使用统一的配置读取方式
        if config is None:
            system_config = get_config()
            # 从系统配置中获取置信度相关配置
            self.config = self._get_default_config()
            confidence_config = system_config.get('signals', {}).get('confidence', {})
            if confidence_config:
                self.config.update(confidence_config)
        else:
            self.config = self._get_default_config()
            self.config.update(config)
        
        self.logger = logger
        self.logger.info("置信度计算器初始化完成")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 权重配置
            'weights': {
                'technical_indicators': 0.35,    # 技术指标权重
                'support_resistance': 0.25,      # 支撑阻力位权重
                'market_environment': 0.20,      # 市场环境权重
                'risk_reward': 0.15,             # 风险回报比权重
                'volume_confirmation': 0.05      # 成交量确认权重
            },
            
            # 技术指标阈值
            'technical_thresholds': {
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'rsi_extreme_oversold': 20,
                'rsi_extreme_overbought': 80,
                'volume_surge_threshold': 1.5,
                'volume_strong_threshold': 2.0
            },
            
            # 支撑阻力位评估
            'sr_evaluation': {
                'min_touches': 2,
                'strong_touches': 4,
                'proximity_excellent': 0.5,  # 0.5%以内
                'proximity_good': 1.0,       # 1%以内
                'proximity_fair': 2.0        # 2%以内
            },
            
            # 风险回报比评估
            'risk_reward': {
                'excellent_ratio': 3.0,
                'good_ratio': 2.5,
                'acceptable_ratio': 2.0,
                'minimum_ratio': 1.5
            },
            
            # 置信度等级
            'confidence_levels': {
                'very_high': 0.85,
                'high': 0.75,
                'medium': 0.65,
                'low': 0.50,
                'very_low': 0.35
            }
        }
    
    def calculate_signal_confidence(self, 
                                  signal_type: str,
                                  current_price: float,
                                  technical_analysis: Dict[str, Any],
                                  support_resistance: Dict[str, Any],
                                  market_data: Dict[str, Any],
                                  risk_levels: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        计算信号的综合置信度
        
        Args:
            signal_type: 信号类型 ('buy' 或 'sell')
            current_price: 当前价格
            technical_analysis: 技术分析结果
            support_resistance: 支撑阻力位分析
            market_data: 市场数据
            risk_levels: 风险水平设置
            
        Returns:
            包含置信度和详细分析的字典
        """
        try:
            # 1. 技术指标置信度
            technical_confidence = self._calculate_technical_confidence(
                signal_type, technical_analysis
            )
            
            # 2. 支撑阻力位置信度
            sr_confidence = self._calculate_sr_confidence(
                signal_type, current_price, support_resistance
            )
            
            # 3. 市场环境置信度
            market_confidence = self._calculate_market_confidence(
                signal_type, market_data, technical_analysis
            )
            
            # 4. 风险回报比置信度
            rr_confidence = self._calculate_risk_reward_confidence(
                current_price, risk_levels
            ) if risk_levels else 0.5
            
            # 5. 成交量确认置信度
            volume_confidence = self._calculate_volume_confidence(
                market_data, technical_analysis
            )
            
            # 6. 综合置信度计算
            weights = self.config['weights']
            overall_confidence = (
                technical_confidence * weights['technical_indicators'] +
                sr_confidence * weights['support_resistance'] +
                market_confidence * weights['market_environment'] +
                rr_confidence * weights['risk_reward'] +
                volume_confidence * weights['volume_confirmation']
            )
            
            # 7. 置信度调整和验证
            adjusted_confidence = self._apply_confidence_adjustments(
                overall_confidence, signal_type, technical_analysis
            )
            
            # 8. 生成详细分析报告
            confidence_analysis = {
                'overall_confidence': max(0.0, min(1.0, adjusted_confidence)),
                'confidence_level': self._get_confidence_level(adjusted_confidence),
                'components': {
                    'technical_indicators': technical_confidence,
                    'support_resistance': sr_confidence,
                    'market_environment': market_confidence,
                    'risk_reward': rr_confidence,
                    'volume_confirmation': volume_confidence
                },
                'weights_used': weights,
                'quality_score': self._calculate_quality_score(adjusted_confidence),
                'recommendation': self._get_confidence_recommendation(adjusted_confidence),
                'risk_assessment': self._assess_confidence_risk(adjusted_confidence),
                'timestamp': datetime.now()
            }
            
            self.logger.info(f"置信度计算完成: {signal_type}信号 = {adjusted_confidence:.3f}")
            return confidence_analysis
            
        except Exception as e:
            self.logger.error(f"置信度计算失败: {e}")
            return self._get_default_confidence_result()
    
    def _calculate_technical_confidence(self, 
                                      signal_type: str, 
                                      technical_analysis: Dict[str, Any]) -> float:
        """
        计算技术指标置信度
        
        Args:
            signal_type: 信号类型
            technical_analysis: 技术分析结果
            
        Returns:
            技术指标置信度 (0.0-1.0)
        """
        confidence = 0.5  # 基础置信度
        indicators = technical_analysis.get('indicators', {})
        
        try:
            # RSI确认
            rsi_data = indicators.get('rsi_14', {})
            if rsi_data and not rsi_data.get('error'):
                current_rsi = rsi_data.get('current_rsi', 50)
                confidence += self._evaluate_rsi_confirmation(signal_type, current_rsi)
            
            # MACD确认
            macd_data = indicators.get('macd', {})
            if macd_data and not macd_data.get('error'):
                confidence += self._evaluate_macd_confirmation(signal_type, macd_data)
            
            # 移动平均线确认
            price_position = technical_analysis.get('price_position', {})
            if price_position:
                confidence += self._evaluate_ma_confirmation(signal_type, price_position)
            
            # ATR波动率确认
            atr_data = indicators.get('atr', {})
            if atr_data and not atr_data.get('error'):
                confidence += self._evaluate_atr_confirmation(atr_data)
            
        except Exception as e:
            self.logger.warning(f"技术指标置信度计算失败: {e}")
        
        return max(0.0, min(1.0, confidence))
    
    def _evaluate_rsi_confirmation(self, signal_type: str, rsi_value: float) -> float:
        """评估RSI确认强度"""
        thresholds = self.config['technical_thresholds']
        
        if signal_type == 'buy':
            if rsi_value <= thresholds['rsi_extreme_oversold']:
                return 0.25  # 极度超卖，强确认
            elif rsi_value <= thresholds['rsi_oversold']:
                return 0.15  # 超卖，中等确认
            elif rsi_value <= 40:
                return 0.05  # 轻微超卖，弱确认
        else:  # sell
            if rsi_value >= thresholds['rsi_extreme_overbought']:
                return 0.25  # 极度超买，强确认
            elif rsi_value >= thresholds['rsi_overbought']:
                return 0.15  # 超买，中等确认
            elif rsi_value >= 60:
                return 0.05  # 轻微超买，弱确认
        
        return 0.0
    
    def _evaluate_macd_confirmation(self, signal_type: str, macd_data: Dict[str, Any]) -> float:
        """评估MACD确认强度"""
        signal_macd = macd_data.get('signal_type', '')
        cross_signal = macd_data.get('cross_signal', '')
        position = macd_data.get('position', '')
        histogram_trend = macd_data.get('histogram_trend', '')
        
        confirmation = 0.0
        
        if signal_type == 'buy':
            # 金叉信号
            if signal_macd == '买入信号' or cross_signal == '金叉':
                confirmation += 0.2
            # 多头区域且柱状图上升
            elif position == '多头区域' and histogram_trend == '上升':
                confirmation += 0.1
            # 即将金叉
            elif cross_signal == '即将金叉':
                confirmation += 0.05
        else:  # sell
            # 死叉信号
            if signal_macd == '卖出信号' or cross_signal == '死叉':
                confirmation += 0.2
            # 空头区域且柱状图下降
            elif position == '空头区域' and histogram_trend == '下降':
                confirmation += 0.1
            # 即将死叉
            elif cross_signal == '即将死叉':
                confirmation += 0.05
        
        return confirmation
    
    def _evaluate_ma_confirmation(self, signal_type: str, price_position: Dict[str, Any]) -> float:
        """评估移动平均线确认强度"""
        above_count = sum(1 for pos in price_position.values() if pos == 'above')
        below_count = sum(1 for pos in price_position.values() if pos == 'below')
        total_count = above_count + below_count
        
        if total_count == 0:
            return 0.0
        
        if signal_type == 'buy':
            above_ratio = above_count / total_count
            if above_ratio >= 0.8:
                return 0.15  # 强势上升趋势
            elif above_ratio >= 0.6:
                return 0.1   # 中等上升趋势
            elif above_ratio >= 0.4:
                return 0.05  # 弱上升趋势
        else:  # sell
            below_ratio = below_count / total_count
            if below_ratio >= 0.8:
                return 0.15  # 强势下降趋势
            elif below_ratio >= 0.6:
                return 0.1   # 中等下降趋势
            elif below_ratio >= 0.4:
                return 0.05  # 弱下降趋势
        
        return 0.0
    
    def _evaluate_atr_confirmation(self, atr_data: Dict[str, Any]) -> float:
        """评估ATR波动率确认"""
        atr_trend = atr_data.get('atr_trend', '')
        volatility_level = atr_data.get('volatility_level', '')
        
        confirmation = 0.0
        
        # 波动率适中有利于信号质量
        if volatility_level == '中等':
            confirmation += 0.05
        elif volatility_level == '低':
            confirmation += 0.02  # 低波动率稍有利
        
        # 波动率趋势
        if atr_trend == '稳定':
            confirmation += 0.03
        
        return confirmation
    
    def _calculate_sr_confidence(self, 
                               signal_type: str, 
                               current_price: float, 
                               support_resistance: Dict[str, Any]) -> float:
        """
        计算支撑阻力位置信度
        
        Args:
            signal_type: 信号类型
            current_price: 当前价格
            support_resistance: 支撑阻力位分析结果
            
        Returns:
            支撑阻力位置信度
        """
        confidence = 0.5
        
        try:
            if signal_type == 'buy':
                support_levels = support_resistance.get('support_levels', [])
                if support_levels:
                    nearest_support = min(support_levels, key=lambda x: abs(x['price'] - current_price))
                    confidence += self._evaluate_level_quality(nearest_support, current_price, 'support')
            else:  # sell
                resistance_levels = support_resistance.get('resistance_levels', [])
                if resistance_levels:
                    nearest_resistance = min(resistance_levels, key=lambda x: abs(x['price'] - current_price))
                    confidence += self._evaluate_level_quality(nearest_resistance, current_price, 'resistance')
        
        except Exception as e:
            self.logger.warning(f"支撑阻力位置信度计算失败: {e}")
        
        return max(0.0, min(1.0, confidence))
    
    def _evaluate_level_quality(self, level: Dict[str, Any], current_price: float, level_type: str) -> float:
        """评估支撑阻力位质量"""
        quality_score = 0.0
        sr_config = self.config['sr_evaluation']
        
        # 触及次数评估
        touch_count = level.get('touch_count', 0)
        if touch_count >= sr_config['strong_touches']:
            quality_score += 0.2  # 强支撑阻力位
        elif touch_count >= sr_config['min_touches']:
            quality_score += 0.1  # 有效支撑阻力位
        
        # 距离评估
        distance_pct = abs(level['price'] - current_price) / current_price * 100
        if distance_pct <= sr_config['proximity_excellent']:
            quality_score += 0.15  # 极近距离
        elif distance_pct <= sr_config['proximity_good']:
            quality_score += 0.1   # 良好距离
        elif distance_pct <= sr_config['proximity_fair']:
            quality_score += 0.05  # 可接受距离
        
        # 强度评级
        strength_rating = level.get('strength_rating', '弱')
        if strength_rating == '强':
            quality_score += 0.15
        elif strength_rating == '中':
            quality_score += 0.1
        elif strength_rating == '弱':
            quality_score += 0.05
        
        return quality_score
    
    def _calculate_market_confidence(self, 
                                   signal_type: str, 
                                   market_data: Dict[str, Any],
                                   technical_analysis: Dict[str, Any]) -> float:
        """计算市场环境置信度"""
        confidence = 0.5
        
        try:
            # 市场趋势评估
            trend_strength = self._assess_market_trend(technical_analysis)
            confidence += trend_strength
            
            # 波动率环境评估
            volatility_score = self._assess_volatility_environment(market_data)
            confidence += volatility_score
            
            # 流动性评估
            liquidity_score = self._assess_liquidity(market_data)
            confidence += liquidity_score
            
        except Exception as e:
            self.logger.warning(f"市场环境置信度计算失败: {e}")
        
        return max(0.0, min(1.0, confidence))
    
    def _assess_market_trend(self, technical_analysis: Dict[str, Any]) -> float:
        """评估市场趋势强度"""
        # 基于多个时间框架的趋势一致性
        price_position = technical_analysis.get('price_position', {})
        if not price_position:
            return 0.0
        
        above_count = sum(1 for pos in price_position.values() if pos == 'above')
        total_count = len([pos for pos in price_position.values() if pos in ['above', 'below']])
        
        if total_count == 0:
            return 0.0
        
        trend_consistency = abs(above_count / total_count - 0.5) * 2  # 0-1范围
        return trend_consistency * 0.1  # 最大贡献0.1
    
    def _assess_volatility_environment(self, market_data: Dict[str, Any]) -> float:
        """评估波动率环境"""
        # 适中的波动率有利于信号质量
        volatility_level = market_data.get('volatility_level', 'unknown')
        
        if volatility_level == '中等':
            return 0.05
        elif volatility_level in ['低', '高']:
            return 0.02
        else:
            return 0.0
    
    def _assess_liquidity(self, market_data: Dict[str, Any]) -> float:
        """评估流动性"""
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        if volume_ratio >= 1.5:
            return 0.05  # 高流动性
        elif volume_ratio >= 1.2:
            return 0.03  # 良好流动性
        else:
            return 0.0
    
    def _calculate_risk_reward_confidence(self, 
                                        current_price: float, 
                                        risk_levels: Dict[str, Any]) -> float:
        """计算风险回报比置信度"""
        try:
            stop_loss = risk_levels.get('stop_loss', current_price)
            take_profit = risk_levels.get('take_profit', current_price)
            
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            
            if risk <= 0:
                return 0.5
            
            rr_ratio = reward / risk
            rr_config = self.config['risk_reward']
            
            if rr_ratio >= rr_config['excellent_ratio']:
                return 1.0
            elif rr_ratio >= rr_config['good_ratio']:
                return 0.8
            elif rr_ratio >= rr_config['acceptable_ratio']:
                return 0.6
            elif rr_ratio >= rr_config['minimum_ratio']:
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            self.logger.warning(f"风险回报比置信度计算失败: {e}")
            return 0.5
    
    def _calculate_volume_confidence(self, 
                                   market_data: Dict[str, Any],
                                   technical_analysis: Dict[str, Any]) -> float:
        """计算成交量确认置信度"""
        volume_ratio = market_data.get('volume_ratio', 1.0)
        thresholds = self.config['technical_thresholds']
        
        if volume_ratio >= thresholds['volume_strong_threshold']:
            return 1.0  # 强成交量确认
        elif volume_ratio >= thresholds['volume_surge_threshold']:
            return 0.7  # 成交量放大
        elif volume_ratio >= 1.2:
            return 0.4  # 轻微放大
        else:
            return 0.2  # 成交量不足
    
    def _apply_confidence_adjustments(self, 
                                    base_confidence: float, 
                                    signal_type: str,
                                    technical_analysis: Dict[str, Any]) -> float:
        """应用置信度调整"""
        adjusted = base_confidence
        
        # 极端市场条件调整
        indicators = technical_analysis.get('indicators', {})
        rsi_data = indicators.get('rsi_14', {})
        
        if rsi_data and not rsi_data.get('error'):
            current_rsi = rsi_data.get('current_rsi', 50)
            
            # 极端RSI值增加置信度
            if signal_type == 'buy' and current_rsi <= 20:
                adjusted += 0.1  # 极度超卖奖励
            elif signal_type == 'sell' and current_rsi >= 80:
                adjusted += 0.1  # 极度超买奖励
        
        # 多重确认奖励
        confirmation_count = self._count_confirmations(technical_analysis)
        if confirmation_count >= 3:
            adjusted += 0.05  # 多重确认奖励
        
        return adjusted
    
    def _count_confirmations(self, technical_analysis: Dict[str, Any]) -> int:
        """统计确认信号数量"""
        count = 0
        indicators = technical_analysis.get('indicators', {})
        
        # RSI确认
        rsi_data = indicators.get('rsi_14', {})
        if rsi_data and not rsi_data.get('error'):
            current_rsi = rsi_data.get('current_rsi', 50)
            if current_rsi <= 30 or current_rsi >= 70:
                count += 1
        
        # MACD确认
        macd_data = indicators.get('macd', {})
        if macd_data and not macd_data.get('error'):
            signal_type = macd_data.get('signal_type', '')
            if signal_type in ['买入信号', '卖出信号']:
                count += 1
        
        # 移动平均线确认
        price_position = technical_analysis.get('price_position', {})
        if price_position:
            above_count = sum(1 for pos in price_position.values() if pos == 'above')
            total_count = len([pos for pos in price_position.values() if pos in ['above', 'below']])
            if total_count > 0:
                ratio = above_count / total_count
                if ratio >= 0.7 or ratio <= 0.3:  # 强趋势
                    count += 1
        
        return count
    
    def _get_confidence_level(self, confidence: float) -> str:
        """获取置信度等级"""
        levels = self.config['confidence_levels']
        
        if confidence >= levels['very_high']:
            return 'very_high'
        elif confidence >= levels['high']:
            return 'high'
        elif confidence >= levels['medium']:
            return 'medium'
        elif confidence >= levels['low']:
            return 'low'
        else:
            return 'very_low'
    
    def _calculate_quality_score(self, confidence: float) -> int:
        """计算质量分数 (1-10)"""
        return max(1, min(10, int(confidence * 10)))
    
    def _get_confidence_recommendation(self, confidence: float) -> str:
        """获取置信度建议"""
        if confidence >= 0.85:
            return "强烈推荐执行"
        elif confidence >= 0.75:
            return "推荐执行"
        elif confidence >= 0.65:
            return "谨慎执行"
        elif confidence >= 0.50:
            return "观望为主"
        else:
            return "不建议执行"
    
    def _assess_confidence_risk(self, confidence: float) -> str:
        """评估置信度风险"""
        if confidence >= 0.80:
            return "低风险"
        elif confidence >= 0.65:
            return "中等风险"
        elif confidence >= 0.50:
            return "较高风险"
        else:
            return "高风险"
    
    def _get_default_confidence_result(self) -> Dict[str, Any]:
        """获取默认置信度结果"""
        return {
            'overall_confidence': 0.5,
            'confidence_level': 'medium',
            'components': {
                'technical_indicators': 0.5,
                'support_resistance': 0.5,
                'market_environment': 0.5,
                'risk_reward': 0.5,
                'volume_confirmation': 0.5
            },
            'weights_used': self.config['weights'],
            'quality_score': 5,
            'recommendation': "观望为主",
            'risk_assessment': "中等风险",
            'timestamp': datetime.now(),
            'error': "计算失败，使用默认值"
        }
    
    def batch_calculate_confidence(self, 
                                 signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量计算多个信号的置信度
        
        Args:
            signals: 信号列表
            
        Returns:
            包含置信度分析的信号列表
        """
        results = []
        
        for signal in signals:
            try:
                confidence_result = self.calculate_signal_confidence(
                    signal_type=signal.get('signal_type', 'buy'),
                    current_price=signal.get('price', 0),
                    technical_analysis=signal.get('technical_analysis', {}),
                    support_resistance=signal.get('support_resistance', {}),
                    market_data=signal.get('market_data', {}),
                    risk_levels=signal.get('risk_levels', {})
                )
                
                # 将置信度结果合并到信号中
                enhanced_signal = signal.copy()
                enhanced_signal['confidence_analysis'] = confidence_result
                enhanced_signal['confidence'] = confidence_result['overall_confidence']
                
                results.append(enhanced_signal)
                
            except Exception as e:
                self.logger.error(f"批量置信度计算失败: {e}")
                # 添加默认置信度
                enhanced_signal = signal.copy()
                enhanced_signal['confidence'] = 0.5
                enhanced_signal['confidence_analysis'] = self._get_default_confidence_result()
                results.append(enhanced_signal)
        
        self.logger.info(f"批量置信度计算完成，处理了 {len(results)} 个信号")
        return results
    
    def get_confidence_statistics(self, 
                                confidence_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取置信度统计信息
        
        Args:
            confidence_results: 置信度计算结果列表
            
        Returns:
            统计信息
        """
        if not confidence_results:
            return {}
        
        confidences = [r.get('overall_confidence', 0.5) for r in confidence_results]
        
        return {
            'total_signals': len(confidence_results),
            'average_confidence': np.mean(confidences),
            'median_confidence': np.median(confidences),
            'std_confidence': np.std(confidences),
            'min_confidence': np.min(confidences),
            'max_confidence': np.max(confidences),
            'high_confidence_count': sum(1 for c in confidences if c >= 0.75),
            'medium_confidence_count': sum(1 for c in confidences if 0.5 <= c < 0.75),
            'low_confidence_count': sum(1 for c in confidences if c < 0.5),
            'confidence_distribution': {
                'very_high': sum(1 for c in confidences if c >= 0.85),
                'high': sum(1 for c in confidences if 0.75 <= c < 0.85),
                'medium': sum(1 for c in confidences if 0.65 <= c < 0.75),
                'low': sum(1 for c in confidences if 0.50 <= c < 0.65),
                'very_low': sum(1 for c in confidences if c < 0.50)
            }
        }


def create_confidence_calculator(config: Optional[Dict[str, Any]] = None) -> ConfidenceCalculator:
    """
    创建置信度计算器实例
    
    Args:
        config: 可选配置参数
        
    Returns:
        置信度计算器实例
    """
    return ConfidenceCalculator(config)


def calculate_signal_confidence(signal_data: Dict[str, Any], 
                              config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    便捷函数：计算单个信号的置信度
    
    Args:
        signal_data: 信号数据
        config: 可选配置
        
    Returns:
        置信度分析结果
    """
    calculator = create_confidence_calculator(config)
    
    return calculator.calculate_signal_confidence(
        signal_type=signal_data.get('signal_type', 'buy'),
        current_price=signal_data.get('price', 0),
        technical_analysis=signal_data.get('technical_analysis', {}),
        support_resistance=signal_data.get('support_resistance', {}),
        market_data=signal_data.get('market_data', {}),
        risk_levels=signal_data.get('risk_levels', {})
    ) 