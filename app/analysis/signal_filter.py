"""
信号过滤机制模块
Signal Filtering Mechanism Module

实现T4.2.2任务：提供多维度的信号过滤功能，确保只有高质量的信号被保留。
支持置信度过滤、重复信号去除、时间窗口过滤、市场条件过滤等功能。
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from .strategies import TradingSignal
from .confidence import ConfidenceCalculator
from ..utils.logger import get_analysis_logger

logger = get_analysis_logger()


@dataclass
class FilterCriteria:
    """过滤条件数据类"""
    min_confidence: float = 0.5
    max_confidence: float = 1.0
    signal_types: Optional[List[str]] = None  # ['buy', 'sell', 'hold']
    min_position_size: float = 0.0
    max_position_size: float = 1.0
    time_window_hours: Optional[int] = None
    remove_duplicates: bool = True
    market_conditions: Optional[List[str]] = None
    min_risk_reward_ratio: Optional[float] = None
    max_signals_per_day: Optional[int] = None


class SignalFilter:
    """
    信号过滤器
    
    提供多维度的信号过滤功能，包括：
    1. 置信度过滤
    2. 重复信号去除
    3. 时间窗口过滤
    4. 市场条件过滤
    5. 风险回报比过滤
    6. 信号质量评估
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化信号过滤器
        
        Args:
            config: 过滤器配置参数
        """
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        self.confidence_calculator = ConfidenceCalculator(
            self.config.get('confidence_config', {})
        )
        
        self.logger = logger
        self.filter_statistics = {
            'total_processed': 0,
            'total_filtered': 0,
            'filter_reasons': {},
            'quality_distribution': {}
        }
        
        self.logger.info("信号过滤器初始化完成")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 基础过滤配置
            'default_min_confidence': 0.65,
            'default_max_signals_per_day': 10,
            'duplicate_time_window_minutes': 30,
            'min_signal_interval_minutes': 15,
            
            # 质量评估配置
            'quality_thresholds': {
                'excellent': 0.85,
                'good': 0.75,
                'fair': 0.65,
                'poor': 0.50
            },
            
            # 风险管理配置
            'risk_filters': {
                'min_risk_reward_ratio': 1.5,
                'max_position_size': 0.3,
                'max_daily_risk': 0.05
            },
            
            # 市场条件过滤
            'market_filters': {
                'allowed_conditions': ['normal', 'bullish', 'bearish'],
                'blocked_conditions': ['extreme_volatility', 'low_liquidity']
            },
            
            # 高级过滤配置
            'advanced_filters': {
                'enable_correlation_filter': True,
                'enable_momentum_filter': True,
                'enable_volume_filter': True,
                'correlation_threshold': 0.8
            }
        }
    
    def filter_signals(self, 
                      signals: List[TradingSignal], 
                      criteria: Optional[FilterCriteria] = None,
                      market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        过滤信号列表
        
        Args:
            signals: 原始信号列表
            criteria: 过滤条件
            market_data: 市场数据（用于高级过滤）
            
        Returns:
            包含过滤结果和统计信息的字典
        """
        if not signals:
            return self._get_empty_filter_result()
        
        # 使用默认条件或提供的条件
        if criteria is None:
            criteria = FilterCriteria(
                min_confidence=self.config['default_min_confidence'],
                max_signals_per_day=self.config['default_max_signals_per_day']
            )
        
        self.logger.info(f"开始过滤 {len(signals)} 个信号")
        
        # 初始化过滤统计
        filter_stats = {
            'original_count': len(signals),
            'filtered_count': 0,
            'filter_steps': {},
            'quality_analysis': {},
            'removed_signals': []
        }
        
        # 转换为可处理的格式
        signal_data = [self._signal_to_dict(signal) for signal in signals]
        
        # 执行多步过滤
        filtered_signals = signal_data.copy()
        
        # 1. 置信度过滤
        filtered_signals, step_stats = self._filter_by_confidence(
            filtered_signals, criteria, filter_stats
        )
        filter_stats['filter_steps']['confidence'] = step_stats
        
        # 2. 信号类型过滤
        if criteria.signal_types:
            filtered_signals, step_stats = self._filter_by_signal_type(
                filtered_signals, criteria, filter_stats
            )
            filter_stats['filter_steps']['signal_type'] = step_stats
        
        # 3. 仓位大小过滤
        filtered_signals, step_stats = self._filter_by_position_size(
            filtered_signals, criteria, filter_stats
        )
        filter_stats['filter_steps']['position_size'] = step_stats
        
        # 4. 时间窗口过滤
        if criteria.time_window_hours:
            filtered_signals, step_stats = self._filter_by_time_window(
                filtered_signals, criteria, filter_stats
            )
            filter_stats['filter_steps']['time_window'] = step_stats
        
        # 5. 重复信号去除
        if criteria.remove_duplicates:
            filtered_signals, step_stats = self._remove_duplicate_signals(
                filtered_signals, filter_stats
            )
            filter_stats['filter_steps']['duplicates'] = step_stats
        
        # 6. 风险回报比过滤
        if criteria.min_risk_reward_ratio:
            filtered_signals, step_stats = self._filter_by_risk_reward(
                filtered_signals, criteria, filter_stats
            )
            filter_stats['filter_steps']['risk_reward'] = step_stats
        
        # 7. 市场条件过滤
        if criteria.market_conditions and market_data:
            filtered_signals, step_stats = self._filter_by_market_conditions(
                filtered_signals, criteria, market_data, filter_stats
            )
            filter_stats['filter_steps']['market_conditions'] = step_stats
        
        # 8. 每日信号数量限制
        if criteria.max_signals_per_day:
            filtered_signals, step_stats = self._limit_daily_signals(
                filtered_signals, criteria, filter_stats
            )
            filter_stats['filter_steps']['daily_limit'] = step_stats
        
        # 9. 高级质量过滤
        filtered_signals, step_stats = self._apply_advanced_quality_filters(
            filtered_signals, market_data, filter_stats
        )
        filter_stats['filter_steps']['advanced_quality'] = step_stats
        
        # 10. 最终质量评估
        quality_analysis = self._analyze_signal_quality(filtered_signals)
        filter_stats['quality_analysis'] = quality_analysis
        
        # 转换回TradingSignal对象
        final_signals = [self._dict_to_signal(signal_dict) for signal_dict in filtered_signals]
        
        # 更新统计信息
        filter_stats['filtered_count'] = len(final_signals)
        filter_stats['filter_efficiency'] = self._calculate_filter_efficiency(filter_stats)
        
        # 更新全局统计
        self._update_global_statistics(filter_stats)
        
        result = {
            'filtered_signals': final_signals,
            'statistics': filter_stats,
            'quality_summary': self._generate_quality_summary(final_signals, filter_stats),
            'recommendations': self._generate_filter_recommendations(filter_stats)
        }
        
        self.logger.info(f"过滤完成: {len(signals)} -> {len(final_signals)} 个信号")
        return result
    
    def _filter_by_confidence(self, 
                             signals: List[Dict[str, Any]], 
                             criteria: FilterCriteria,
                             filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """按置信度过滤信号"""
        original_count = len(signals)
        
        filtered = []
        removed = []
        
        for signal in signals:
            confidence = signal.get('confidence', 0.0)
            if criteria.min_confidence <= confidence <= criteria.max_confidence:
                filtered.append(signal)
            else:
                removed.append({
                    'signal': signal,
                    'reason': f"置信度 {confidence:.3f} 不在范围 [{criteria.min_confidence:.3f}, {criteria.max_confidence:.3f}]"
                })
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _filter_by_signal_type(self, 
                              signals: List[Dict[str, Any]], 
                              criteria: FilterCriteria,
                              filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """按信号类型过滤"""
        original_count = len(signals)
        
        filtered = []
        removed = []
        
        for signal in signals:
            signal_type = signal.get('signal_type', '')
            if signal_type in criteria.signal_types:
                filtered.append(signal)
            else:
                removed.append({
                    'signal': signal,
                    'reason': f"信号类型 '{signal_type}' 不在允许列表 {criteria.signal_types}"
                })
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _filter_by_position_size(self, 
                                signals: List[Dict[str, Any]], 
                                criteria: FilterCriteria,
                                filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """按仓位大小过滤"""
        original_count = len(signals)
        
        filtered = []
        removed = []
        
        for signal in signals:
            position_size = signal.get('position_size', 0.0)
            if criteria.min_position_size <= position_size <= criteria.max_position_size:
                filtered.append(signal)
            else:
                removed.append({
                    'signal': signal,
                    'reason': f"仓位大小 {position_size:.3f} 不在范围 [{criteria.min_position_size:.3f}, {criteria.max_position_size:.3f}]"
                })
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _filter_by_time_window(self, 
                              signals: List[Dict[str, Any]], 
                              criteria: FilterCriteria,
                              filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """按时间窗口过滤信号"""
        original_count = len(signals)
        
        if not criteria.time_window_hours:
            return signals, {'original_count': original_count, 'filtered_count': original_count, 'removed_count': 0}
        
        current_time = datetime.now()
        time_threshold = current_time - timedelta(hours=criteria.time_window_hours)
        
        filtered = []
        removed = []
        
        for signal in signals:
            signal_time = self._parse_timestamp(signal.get('timestamp'))
            if signal_time and signal_time >= time_threshold:
                filtered.append(signal)
            else:
                removed.append({
                    'signal': signal,
                    'reason': f"信号时间 {signal_time} 超出时间窗口 {criteria.time_window_hours}小时"
                })
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _remove_duplicate_signals(self, 
                                 signals: List[Dict[str, Any]],
                                 filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """去除重复信号"""
        original_count = len(signals)
        
        if original_count <= 1:
            return signals, {'original_count': original_count, 'filtered_count': original_count, 'removed_count': 0}
        
        # 按时间排序
        sorted_signals = sorted(signals, key=lambda x: self._parse_timestamp(x.get('timestamp', '')))
        
        filtered = []
        removed = []
        duplicate_window = timedelta(minutes=self.config['duplicate_time_window_minutes'])
        
        for signal in sorted_signals:
            is_duplicate = False
            signal_time = self._parse_timestamp(signal.get('timestamp'))
            signal_type = signal.get('signal_type')
            signal_price = signal.get('price', 0)
            
            # 检查是否与已有信号重复
            for existing in filtered:
                existing_time = self._parse_timestamp(existing.get('timestamp'))
                existing_type = existing.get('signal_type')
                existing_price = existing.get('price', 0)
                
                # 检查时间、类型和价格相似性
                if (signal_time and existing_time and 
                    abs(signal_time - existing_time) <= duplicate_window and
                    signal_type == existing_type and
                    abs(signal_price - existing_price) / existing_price < 0.01):  # 价格差异小于1%
                    
                    is_duplicate = True
                    removed.append({
                        'signal': signal,
                        'reason': f"与 {existing_time} 的信号重复"
                    })
                    break
            
            if not is_duplicate:
                filtered.append(signal)
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _filter_by_risk_reward(self, 
                              signals: List[Dict[str, Any]], 
                              criteria: FilterCriteria,
                              filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """按风险回报比过滤"""
        original_count = len(signals)
        
        filtered = []
        removed = []
        
        for signal in signals:
            risk_reward_ratio = self._calculate_risk_reward_ratio(signal)
            
            if risk_reward_ratio is None or risk_reward_ratio >= criteria.min_risk_reward_ratio:
                filtered.append(signal)
            else:
                removed.append({
                    'signal': signal,
                    'reason': f"风险回报比 {risk_reward_ratio:.2f} 低于最小要求 {criteria.min_risk_reward_ratio:.2f}"
                })
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _filter_by_market_conditions(self, 
                                   signals: List[Dict[str, Any]], 
                                   criteria: FilterCriteria,
                                   market_data: Dict[str, Any],
                                   filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """按市场条件过滤"""
        original_count = len(signals)
        
        current_market_condition = self._assess_current_market_condition(market_data)
        
        filtered = []
        removed = []
        
        for signal in signals:
            if current_market_condition in criteria.market_conditions:
                filtered.append(signal)
            else:
                removed.append({
                    'signal': signal,
                    'reason': f"当前市场条件 '{current_market_condition}' 不在允许列表 {criteria.market_conditions}"
                })
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed,
            'market_condition': current_market_condition
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _limit_daily_signals(self, 
                           signals: List[Dict[str, Any]], 
                           criteria: FilterCriteria,
                           filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """限制每日信号数量"""
        original_count = len(signals)
        
        if original_count <= criteria.max_signals_per_day:
            return signals, {'original_count': original_count, 'filtered_count': original_count, 'removed_count': 0}
        
        # 按置信度排序，保留最高置信度的信号
        sorted_signals = sorted(signals, key=lambda x: x.get('confidence', 0), reverse=True)
        
        filtered = sorted_signals[:criteria.max_signals_per_day]
        removed_signals = sorted_signals[criteria.max_signals_per_day:]
        
        removed = [{
            'signal': signal,
            'reason': f"超出每日信号数量限制 {criteria.max_signals_per_day}"
        } for signal in removed_signals]
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _apply_advanced_quality_filters(self, 
                                      signals: List[Dict[str, Any]], 
                                      market_data: Optional[Dict[str, Any]],
                                      filter_stats: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """应用高级质量过滤"""
        original_count = len(signals)
        
        filtered = []
        removed = []
        
        for signal in signals:
            quality_score = self._calculate_signal_quality_score(signal, market_data)
            
            # 质量阈值检查
            min_quality = self.config['quality_thresholds']['poor']
            if quality_score >= min_quality:
                # 添加质量评级到信号元数据
                if 'metadata' not in signal:
                    signal['metadata'] = {}
                signal['metadata']['quality_score'] = quality_score
                signal['metadata']['quality_grade'] = self._get_quality_grade(quality_score)
                
                filtered.append(signal)
            else:
                removed.append({
                    'signal': signal,
                    'reason': f"质量评分 {quality_score:.3f} 低于最小要求 {min_quality:.3f}"
                })
        
        step_stats = {
            'original_count': original_count,
            'filtered_count': len(filtered),
            'removed_count': len(removed),
            'removal_rate': len(removed) / original_count if original_count > 0 else 0,
            'removed_signals': removed
        }
        
        filter_stats['removed_signals'].extend(removed)
        return filtered, step_stats
    
    def _calculate_signal_quality_score(self, 
                                      signal: Dict[str, Any], 
                                      market_data: Optional[Dict[str, Any]]) -> float:
        """计算信号质量评分"""
        score = 0.0
        
        # 基础置信度权重 (40%)
        confidence = signal.get('confidence', 0.0)
        score += confidence * 0.4
        
        # 风险回报比权重 (25%)
        risk_reward = self._calculate_risk_reward_ratio(signal)
        if risk_reward:
            # 将风险回报比转换为0-1分数
            rr_score = min(1.0, (risk_reward - 1.0) / 2.0)  # 1:1比例=0分，3:1比例=1分
            score += rr_score * 0.25
        
        # 技术指标确认权重 (20%)
        metadata = signal.get('metadata', {})
        technical_confirmations = metadata.get('technical_confirmations', {})
        if technical_confirmations:
            confirmation_count = sum(1 for v in technical_confirmations.values() if v)
            max_confirmations = len(technical_confirmations)
            if max_confirmations > 0:
                score += (confirmation_count / max_confirmations) * 0.2
        
        # 市场环境适应性权重 (10%)
        if market_data:
            market_score = self._assess_market_compatibility(signal, market_data)
            score += market_score * 0.1
        
        # 信号新鲜度权重 (5%)
        freshness_score = self._calculate_signal_freshness(signal)
        score += freshness_score * 0.05
        
        return min(1.0, max(0.0, score))
    
    def _get_quality_grade(self, quality_score: float) -> str:
        """获取质量等级"""
        thresholds = self.config['quality_thresholds']
        
        if quality_score >= thresholds['excellent']:
            return 'excellent'
        elif quality_score >= thresholds['good']:
            return 'good'
        elif quality_score >= thresholds['fair']:
            return 'fair'
        else:
            return 'poor'
    
    def _calculate_risk_reward_ratio(self, signal: Dict[str, Any]) -> Optional[float]:
        """计算风险回报比"""
        price = signal.get('price', 0)
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        
        if not all([price, stop_loss, take_profit]) or price <= 0:
            return None
        
        signal_type = signal.get('signal_type', '')
        
        if signal_type == 'buy':
            risk = abs(price - stop_loss)
            reward = abs(take_profit - price)
        elif signal_type == 'sell':
            risk = abs(stop_loss - price)
            reward = abs(price - take_profit)
        else:
            return None
        
        if risk <= 0:
            return None
        
        return reward / risk
    
    def _assess_current_market_condition(self, market_data: Dict[str, Any]) -> str:
        """评估当前市场条件"""
        # 简化的市场条件评估
        volatility = market_data.get('volatility', 0.0)
        volume_ratio = market_data.get('volume_ratio', 1.0)
        trend_strength = market_data.get('trend_strength', 0.0)
        
        if volatility > 0.05:  # 高波动
            return 'high_volatility'
        elif volume_ratio < 0.5:  # 低成交量
            return 'low_liquidity'
        elif trend_strength > 0.7:
            return 'strong_trend'
        elif trend_strength < -0.7:
            return 'strong_downtrend'
        else:
            return 'normal'
    
    def _assess_market_compatibility(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """评估信号与市场环境的兼容性"""
        signal_type = signal.get('signal_type', '')
        market_condition = self._assess_current_market_condition(market_data)
        
        # 兼容性评分矩阵
        compatibility_matrix = {
            'buy': {
                'normal': 0.8,
                'strong_trend': 0.9,
                'strong_downtrend': 0.3,
                'high_volatility': 0.6,
                'low_liquidity': 0.4
            },
            'sell': {
                'normal': 0.8,
                'strong_trend': 0.3,
                'strong_downtrend': 0.9,
                'high_volatility': 0.6,
                'low_liquidity': 0.4
            }
        }
        
        return compatibility_matrix.get(signal_type, {}).get(market_condition, 0.5)
    
    def _calculate_signal_freshness(self, signal: Dict[str, Any]) -> float:
        """计算信号新鲜度"""
        signal_time = self._parse_timestamp(signal.get('timestamp'))
        if not signal_time:
            return 0.0
        
        current_time = datetime.now()
        time_diff = current_time - signal_time
        
        # 1小时内的信号得满分，24小时后得0分
        hours_old = time_diff.total_seconds() / 3600
        freshness = max(0.0, 1.0 - hours_old / 24.0)
        
        return freshness
    
    def _parse_timestamp(self, timestamp: Union[str, datetime]) -> Optional[datetime]:
        """解析时间戳"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    return None
        return None
    
    def _analyze_signal_quality(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析信号质量分布"""
        if not signals:
            return {'total_signals': 0}
        
        confidences = [s.get('confidence', 0.0) for s in signals]
        quality_scores = [s.get('metadata', {}).get('quality_score', 0.0) for s in signals]
        
        quality_distribution = {}
        for signal in signals:
            grade = signal.get('metadata', {}).get('quality_grade', 'unknown')
            quality_distribution[grade] = quality_distribution.get(grade, 0) + 1
        
        # 计算统计值（不使用numpy）
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        min_confidence = min(confidences) if confidences else 0.0
        max_confidence = max(confidences) if confidences else 0.0
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # 计算标准差
        if confidences and len(confidences) > 1:
            mean_conf = avg_confidence
            variance = sum((x - mean_conf) ** 2 for x in confidences) / len(confidences)
            confidence_std = variance ** 0.5
        else:
            confidence_std = 0.0
        
        return {
            'total_signals': len(signals),
            'avg_confidence': avg_confidence,
            'min_confidence': min_confidence,
            'max_confidence': max_confidence,
            'avg_quality_score': avg_quality_score,
            'quality_distribution': quality_distribution,
            'confidence_std': confidence_std
        }
    
    def _calculate_filter_efficiency(self, filter_stats: Dict[str, Any]) -> Dict[str, Any]:
        """计算过滤效率"""
        original = filter_stats['original_count']
        filtered = filter_stats['filtered_count']
        
        if original == 0:
            return {'filter_rate': 0.0, 'retention_rate': 0.0}
        
        filter_rate = (original - filtered) / original
        retention_rate = filtered / original
        
        return {
            'filter_rate': filter_rate,
            'retention_rate': retention_rate,
            'signals_removed': original - filtered,
            'signals_retained': filtered
        }
    
    def _generate_quality_summary(self, 
                                signals: List[TradingSignal], 
                                filter_stats: Dict[str, Any]) -> Dict[str, Any]:
        """生成质量摘要"""
        if not signals:
            return {'message': '没有信号通过过滤'}
        
        # 转换为字典格式进行分析
        signal_dicts = [self._signal_to_dict(signal) for signal in signals]
        quality_analysis = self._analyze_signal_quality(signal_dicts)
        
        # 生成摘要
        summary = {
            'total_signals': len(signals),
            'quality_metrics': quality_analysis,
            'filter_efficiency': filter_stats.get('filter_efficiency', {}),
            'top_signals': self._get_top_signals(signals, 3),
            'quality_recommendations': self._generate_quality_recommendations(quality_analysis)
        }
        
        return summary
    
    def _get_top_signals(self, signals: List[TradingSignal], count: int) -> List[Dict[str, Any]]:
        """获取置信度最高的信号"""
        sorted_signals = sorted(signals, key=lambda x: x.confidence, reverse=True)
        return [self._signal_to_dict(signal) for signal in sorted_signals[:count]]
    
    def _generate_quality_recommendations(self, quality_analysis: Dict[str, Any]) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        avg_confidence = quality_analysis.get('avg_confidence', 0.0)
        if avg_confidence < 0.7:
            recommendations.append("建议提高信号生成的置信度阈值")
        
        quality_dist = quality_analysis.get('quality_distribution', {})
        poor_signals = quality_dist.get('poor', 0)
        total_signals = quality_analysis.get('total_signals', 1)
        
        if poor_signals / total_signals > 0.3:
            recommendations.append("建议加强信号质量控制，减少低质量信号")
        
        if quality_analysis.get('confidence_std', 0) > 0.2:
            recommendations.append("信号置信度差异较大，建议优化信号生成算法")
        
        return recommendations
    
    def _generate_filter_recommendations(self, filter_stats: Dict[str, Any]) -> List[str]:
        """生成过滤器优化建议"""
        recommendations = []
        
        efficiency = filter_stats.get('filter_efficiency', {})
        filter_rate = efficiency.get('filter_rate', 0.0)
        
        if filter_rate > 0.8:
            recommendations.append("过滤率过高，建议放宽过滤条件")
        elif filter_rate < 0.2:
            recommendations.append("过滤率较低，建议加强质量控制")
        
        # 分析各步骤的过滤效果
        filter_steps = filter_stats.get('filter_steps', {})
        for step_name, step_stats in filter_steps.items():
            removal_rate = step_stats.get('removal_rate', 0.0)
            if removal_rate > 0.5:
                recommendations.append(f"{step_name}过滤步骤移除了过多信号，建议调整参数")
        
        return recommendations
    
    def _signal_to_dict(self, signal: TradingSignal) -> Dict[str, Any]:
        """将TradingSignal转换为字典"""
        return signal.to_dict()
    
    def _dict_to_signal(self, signal_dict: Dict[str, Any]) -> TradingSignal:
        """将字典转换为TradingSignal"""
        timestamp_str = signal_dict.get('timestamp', '')
        timestamp = self._parse_timestamp(timestamp_str) or datetime.now()
        
        return TradingSignal(
            signal_type=signal_dict.get('signal_type', 'hold'),
            action=signal_dict.get('action', 'hold'),
            confidence=signal_dict.get('confidence', 0.0),
            price=signal_dict.get('price', 0.0),
            timestamp=timestamp,
            reason=signal_dict.get('reason', ''),
            stop_loss=signal_dict.get('stop_loss'),
            take_profit=signal_dict.get('take_profit'),
            position_size=signal_dict.get('position_size', 0.0),
            metadata=signal_dict.get('metadata', {})
        )
    
    def _get_empty_filter_result(self) -> Dict[str, Any]:
        """获取空的过滤结果"""
        return {
            'filtered_signals': [],
            'statistics': {
                'original_count': 0,
                'filtered_count': 0,
                'filter_steps': {},
                'quality_analysis': {'total_signals': 0},
                'removed_signals': []
            },
            'quality_summary': {'message': '没有输入信号'},
            'recommendations': []
        }
    
    def _update_global_statistics(self, filter_stats: Dict[str, Any]):
        """更新全局统计信息"""
        self.filter_statistics['total_processed'] += filter_stats['original_count']
        self.filter_statistics['total_filtered'] += filter_stats['filtered_count']
        
        # 更新过滤原因统计
        for removed_signal in filter_stats.get('removed_signals', []):
            reason = removed_signal.get('reason', 'unknown')
            self.filter_statistics['filter_reasons'][reason] = \
                self.filter_statistics['filter_reasons'].get(reason, 0) + 1
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """获取过滤器统计信息"""
        total_processed = self.filter_statistics['total_processed']
        total_filtered = self.filter_statistics['total_filtered']
        
        return {
            'total_processed': total_processed,
            'total_filtered': total_filtered,
            'overall_filter_rate': (total_processed - total_filtered) / total_processed if total_processed > 0 else 0,
            'filter_reasons': self.filter_statistics['filter_reasons'],
            'quality_distribution': self.filter_statistics['quality_distribution']
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.filter_statistics = {
            'total_processed': 0,
            'total_filtered': 0,
            'filter_reasons': {},
            'quality_distribution': {}
        }
        self.logger.info("过滤器统计信息已重置")


# 便捷函数
def create_signal_filter(config: Optional[Dict[str, Any]] = None) -> SignalFilter:
    """
    创建信号过滤器实例
    
    Args:
        config: 过滤器配置
        
    Returns:
        信号过滤器实例
    """
    return SignalFilter(config)


def filter_signals(signals: List[TradingSignal], 
                  criteria: Optional[FilterCriteria] = None,
                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    过滤信号的便捷函数
    
    Args:
        signals: 信号列表
        criteria: 过滤条件
        config: 过滤器配置
        
    Returns:
        过滤结果
    """
    filter_instance = create_signal_filter(config)
    return filter_instance.filter_signals(signals, criteria)


def create_filter_criteria(min_confidence: float = 0.65,
                          signal_types: Optional[List[str]] = None,
                          max_signals_per_day: int = 10,
                          remove_duplicates: bool = True,
                          **kwargs) -> FilterCriteria:
    """
    创建过滤条件的便捷函数
    
    Args:
        min_confidence: 最小置信度
        signal_types: 允许的信号类型
        max_signals_per_day: 每日最大信号数
        remove_duplicates: 是否去除重复信号
        **kwargs: 其他过滤条件参数
        
    Returns:
        过滤条件实例
    """
    return FilterCriteria(
        min_confidence=min_confidence,
        signal_types=signal_types,
        max_signals_per_day=max_signals_per_day,
        remove_duplicates=remove_duplicates,
        **kwargs
    ) 