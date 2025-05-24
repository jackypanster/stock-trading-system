"""
支撑阻力位分析模块
Support and Resistance Analysis Module

实现局部高低点识别、支撑阻力位计算和强度分析。
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
from datetime import datetime

from ..utils.logger import get_analysis_logger

logger = get_analysis_logger()


class SupportResistanceAnalyzer:
    """
    支撑阻力位分析器
    
    提供局部高低点识别、支撑阻力位计算和强度分析功能。
    """
    
    def __init__(self):
        """初始化支撑阻力位分析器"""
        logger.info("支撑阻力位分析器初始化完成")
    
    def find_local_extrema(self, prices: pd.Series, 
                          window: int = 5, 
                          min_change_pct: float = 1.0) -> Dict[str, Any]:
        """
        识别局部高低点
        
        Args:
            prices: 价格序列（通常是收盘价）
            window: 搜索窗口大小，默认5（左右各5个点）
            min_change_pct: 最小变化百分比，用于过滤噪音，默认1%
            
        Returns:
            包含高点、低点信息的字典
            
        Raises:
            ValueError: 输入数据无效
        """
        if len(prices) < window * 2 + 1:
            raise ValueError(f"数据长度不足，至少需要{window * 2 + 1}个数据点")
        
        if window <= 0:
            raise ValueError("窗口大小必须大于0")
        
        if min_change_pct < 0:
            raise ValueError("最小变化百分比必须为非负数")
        
        logger.debug(f"识别局部高低点，窗口={window}，最小变化={min_change_pct}%，数据点={len(prices)}")
        
        highs = []  # 局部高点
        lows = []   # 局部低点
        
        # 遍历价格序列，寻找局部极值
        for i in range(window, len(prices) - window):
            current_price = prices.iloc[i]
            
            # 获取窗口内的价格
            window_prices = prices.iloc[i-window:i+window+1]
            
            # 检查是否为局部高点
            if current_price == window_prices.max():
                # 计算与窗口内其他价格的变化幅度
                min_price_in_window = window_prices.min()
                change_pct = ((current_price - min_price_in_window) / min_price_in_window) * 100
                
                if change_pct >= min_change_pct:
                    highs.append({
                        'index': i,
                        'date': prices.index[i] if hasattr(prices.index[i], 'strftime') else i,
                        'price': round(current_price, 2),
                        'strength': round(change_pct, 2)  # 强度用变化幅度表示
                    })
            
            # 检查是否为局部低点
            elif current_price == window_prices.min():
                # 计算与窗口内其他价格的变化幅度
                max_price_in_window = window_prices.max()
                change_pct = ((max_price_in_window - current_price) / current_price) * 100
                
                if change_pct >= min_change_pct:
                    lows.append({
                        'index': i,
                        'date': prices.index[i] if hasattr(prices.index[i], 'strftime') else i,
                        'price': round(current_price, 2),
                        'strength': round(change_pct, 2)  # 强度用变化幅度表示
                    })
        
        # 按强度排序
        highs.sort(key=lambda x: x['strength'], reverse=True)
        lows.sort(key=lambda x: x['strength'], reverse=True)
        
        result = {
            'highs': highs,
            'lows': lows,
            'total_highs': len(highs),
            'total_lows': len(lows),
            'analysis_params': {
                'window': window,
                'min_change_pct': min_change_pct,
                'data_points': len(prices)
            }
        }
        
        logger.info(f"局部高低点识别完成: {len(highs)}个高点, {len(lows)}个低点")
        
        return result
    
    def identify_support_resistance_levels(self, extrema: Dict[str, Any], 
                                         tolerance: float = 0.5) -> Dict[str, Any]:
        """
        基于局部高低点识别支撑阻力位
        
        Args:
            extrema: 局部高低点数据（来自find_local_extrema）
            tolerance: 价格容忍度百分比，用于聚类相近的价位，默认0.5%
            
        Returns:
            支撑阻力位分析结果
        """
        if not extrema or 'highs' not in extrema or 'lows' not in extrema:
            raise ValueError("无效的极值数据")
        
        logger.debug(f"识别支撑阻力位，容忍度={tolerance}%")
        
        # 提取价格列表
        high_prices = [h['price'] for h in extrema['highs']]
        low_prices = [l['price'] for l in extrema['lows']]
        
        # 聚类相近的阻力位（高点）
        resistance_levels = self._cluster_price_levels(
            extrema['highs'], tolerance, level_type='resistance'
        )
        
        # 聚类相近的支撑位（低点）
        support_levels = self._cluster_price_levels(
            extrema['lows'], tolerance, level_type='support'
        )
        
        # 计算当前价格位置（如果有价格数据）
        current_position = None
        if high_prices or low_prices:
            all_prices = high_prices + low_prices
            if all_prices:
                recent_price = max(all_prices)  # 简化处理，使用最高价作为参考
                current_position = self._analyze_current_position(
                    recent_price, resistance_levels, support_levels
                )
        
        result = {
            'resistance_levels': resistance_levels,
            'support_levels': support_levels,
            'total_resistance': len(resistance_levels),
            'total_support': len(support_levels),
            'current_position': current_position,
            'analysis_params': {
                'tolerance': tolerance,
                'source_highs': len(extrema['highs']),
                'source_lows': len(extrema['lows'])
            }
        }
        
        logger.info(f"支撑阻力位识别完成: {len(resistance_levels)}个阻力位, {len(support_levels)}个支撑位")
        
        return result
    
    def _cluster_price_levels(self, extrema_list: List[Dict], 
                            tolerance: float, 
                            level_type: str) -> List[Dict[str, Any]]:
        """
        聚类相近的价格水平
        
        Args:
            extrema_list: 极值点列表
            tolerance: 价格容忍度百分比
            level_type: 水平类型（'resistance' 或 'support'）
            
        Returns:
            聚类后的价格水平列表
        """
        if not extrema_list:
            return []
        
        # 按价格排序
        sorted_extrema = sorted(extrema_list, key=lambda x: x['price'])
        
        clusters = []
        current_cluster = [sorted_extrema[0]]
        
        for i in range(1, len(sorted_extrema)):
            current_price = sorted_extrema[i]['price']
            cluster_avg_price = sum(p['price'] for p in current_cluster) / len(current_cluster)
            
            # 计算价格差异百分比
            price_diff_pct = abs((current_price - cluster_avg_price) / cluster_avg_price) * 100
            
            if price_diff_pct <= tolerance:
                # 加入当前聚类
                current_cluster.append(sorted_extrema[i])
            else:
                # 创建新聚类
                if current_cluster:
                    clusters.append(current_cluster)
                current_cluster = [sorted_extrema[i]]
        
        # 添加最后一个聚类
        if current_cluster:
            clusters.append(current_cluster)
        
        # 转换为支撑阻力位格式
        levels = []
        for cluster in clusters:
            # 计算聚类的平均价格
            avg_price = sum(p['price'] for p in cluster) / len(cluster)
            
            # 计算聚类强度（触及次数和平均强度）
            touch_count = len(cluster)
            avg_strength = sum(p['strength'] for p in cluster) / len(cluster)
            
            # 计算强度评级
            if touch_count >= 3 and avg_strength >= 3.0:
                strength_rating = "强"
            elif touch_count >= 2 and avg_strength >= 2.0:
                strength_rating = "中"
            else:
                strength_rating = "弱"
            
            # 获取最近触及时间
            latest_touch = max(cluster, key=lambda x: x['index'])
            
            level = {
                'price': round(avg_price, 2),
                'touch_count': touch_count,
                'avg_strength': round(avg_strength, 2),
                'strength_rating': strength_rating,
                'level_type': level_type,
                'latest_touch_index': latest_touch['index'],
                'latest_touch_date': latest_touch['date'],
                'price_range': {
                    'min': round(min(p['price'] for p in cluster), 2),
                    'max': round(max(p['price'] for p in cluster), 2)
                },
                'individual_touches': cluster
            }
            
            levels.append(level)
        
        # 按强度排序（触及次数优先，然后是强度）
        levels.sort(key=lambda x: (x['touch_count'], x['avg_strength']), reverse=True)
        
        return levels
    
    def _analyze_current_position(self, current_price: float, 
                                resistance_levels: List[Dict], 
                                support_levels: List[Dict]) -> Dict[str, Any]:
        """
        分析当前价格相对于支撑阻力位的位置
        
        Args:
            current_price: 当前价格
            resistance_levels: 阻力位列表
            support_levels: 支撑位列表
            
        Returns:
            位置分析结果
        """
        # 找到最近的支撑位和阻力位
        nearest_resistance = None
        nearest_support = None
        
        # 找到上方最近的阻力位
        above_resistances = [r for r in resistance_levels if r['price'] > current_price]
        if above_resistances:
            nearest_resistance = min(above_resistances, key=lambda x: x['price'] - current_price)
        
        # 找到下方最近的支撑位
        below_supports = [s for s in support_levels if s['price'] < current_price]
        if below_supports:
            nearest_support = max(below_supports, key=lambda x: x['price'])
        
        # 计算距离
        resistance_distance = None
        support_distance = None
        
        if nearest_resistance:
            resistance_distance = {
                'price_diff': round(nearest_resistance['price'] - current_price, 2),
                'percentage': round(((nearest_resistance['price'] - current_price) / current_price) * 100, 2)
            }
        
        if nearest_support:
            support_distance = {
                'price_diff': round(current_price - nearest_support['price'], 2),
                'percentage': round(((current_price - nearest_support['price']) / current_price) * 100, 2)
            }
        
        # 判断当前位置
        position_desc = "中性区域"
        if resistance_distance and resistance_distance['percentage'] <= 1.0:
            position_desc = "接近阻力位"
        elif support_distance and support_distance['percentage'] <= 1.0:
            position_desc = "接近支撑位"
        elif resistance_distance and support_distance:
            if resistance_distance['percentage'] < support_distance['percentage']:
                position_desc = "偏向阻力位"
            else:
                position_desc = "偏向支撑位"
        
        return {
            'current_price': current_price,
            'position_description': position_desc,
            'nearest_resistance': nearest_resistance,
            'nearest_support': nearest_support,
            'resistance_distance': resistance_distance,
            'support_distance': support_distance
        }
    
    def analyze_price_action(self, df: pd.DataFrame, 
                           price_column: str = 'Close',
                           window: int = 5,
                           min_change_pct: float = 1.0,
                           tolerance: float = 0.5) -> Dict[str, Any]:
        """
        完整的价格行为分析
        
        Args:
            df: 包含价格数据的DataFrame
            price_column: 价格列名
            window: 局部极值搜索窗口
            min_change_pct: 最小变化百分比
            tolerance: 支撑阻力位聚类容忍度
            
        Returns:
            完整的价格行为分析结果
        """
        if price_column not in df.columns:
            raise ValueError(f"数据中没有找到价格列: {price_column}")
        
        prices = df[price_column]
        current_price = prices.iloc[-1]
        
        logger.info(f"开始价格行为分析: {len(prices)}个数据点")
        
        # 1. 识别局部高低点
        extrema = self.find_local_extrema(prices, window, min_change_pct)
        
        # 2. 识别支撑阻力位
        levels = self.identify_support_resistance_levels(extrema, tolerance)
        
        # 3. 更新当前价格位置分析
        if levels['resistance_levels'] or levels['support_levels']:
            current_position = self._analyze_current_position(
                current_price, 
                levels['resistance_levels'], 
                levels['support_levels']
            )
            levels['current_position'] = current_position
        
        # 4. 生成交易建议
        trading_signals = self._generate_trading_signals(levels, current_price)
        
        # 组合最终结果
        result = {
            'symbol': df.get('Symbol', pd.Series([None])).iloc[-1] if 'Symbol' in df.columns else "Unknown",
            'current_price': round(current_price, 2),
            'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'local_extrema': extrema,
            'support_resistance': levels,
            'trading_signals': trading_signals,
            'summary': {
                'total_analysis_points': len(prices),
                'identified_highs': extrema['total_highs'],
                'identified_lows': extrema['total_lows'],
                'resistance_levels': levels['total_resistance'],
                'support_levels': levels['total_support']
            }
        }
        
        logger.info(f"价格行为分析完成: {extrema['total_highs']}高点, {extrema['total_lows']}低点, "
                   f"{levels['total_resistance']}阻力位, {levels['total_support']}支撑位")
        
        return result
    
    def _generate_trading_signals(self, levels: Dict[str, Any], 
                                current_price: float) -> Dict[str, Any]:
        """
        基于支撑阻力位生成交易信号
        
        Args:
            levels: 支撑阻力位数据
            current_price: 当前价格
            
        Returns:
            交易信号字典
        """
        signals = {
            'signals': [],
            'risk_levels': {},
            'key_levels': {}
        }
        
        current_pos = levels.get('current_position')
        if not current_pos:
            return signals
        
        # 识别关键价位
        if current_pos['nearest_resistance']:
            signals['key_levels']['next_resistance'] = current_pos['nearest_resistance']['price']
        
        if current_pos['nearest_support']:
            signals['key_levels']['next_support'] = current_pos['nearest_support']['price']
        
        # 生成交易信号
        position_desc = current_pos['position_description']
        
        if position_desc == "接近阻力位":
            signals['signals'].append({
                'type': 'warning',
                'signal': '接近阻力位',
                'description': '价格接近重要阻力位，注意可能的回调',
                'action': '考虑减仓或设置止盈'
            })
        elif position_desc == "接近支撑位":
            signals['signals'].append({
                'type': 'opportunity',
                'signal': '接近支撑位',
                'description': '价格接近重要支撑位，可能出现反弹',
                'action': '考虑逢低买入或加仓'
            })
        
        # 风险水平评估
        resistance_risk = "低"
        support_risk = "低"
        
        if current_pos['resistance_distance'] and current_pos['resistance_distance']['percentage'] <= 2.0:
            resistance_risk = "高"
        elif current_pos['resistance_distance'] and current_pos['resistance_distance']['percentage'] <= 5.0:
            resistance_risk = "中"
        
        if current_pos['support_distance'] and current_pos['support_distance']['percentage'] <= 2.0:
            support_risk = "高"
        elif current_pos['support_distance'] and current_pos['support_distance']['percentage'] <= 5.0:
            support_risk = "中"
        
        signals['risk_levels'] = {
            'resistance_risk': resistance_risk,
            'support_risk': support_risk,
            'overall_risk': 'high' if resistance_risk == "高" or support_risk == "高" else 'medium' if resistance_risk == "中" or support_risk == "中" else 'low'
        }
        
        return signals


# 便捷函数
def find_support_resistance(df: pd.DataFrame, 
                          price_column: str = 'Close',
                          window: int = 5,
                          min_change_pct: float = 1.0,
                          tolerance: float = 0.5) -> Dict[str, Any]:
    """
    寻找支撑阻力位的便捷函数
    
    Args:
        df: 包含价格数据的DataFrame
        price_column: 价格列名
        window: 局部极值搜索窗口
        min_change_pct: 最小变化百分比
        tolerance: 支撑阻力位聚类容忍度
        
    Returns:
        支撑阻力位分析结果
    """
    analyzer = SupportResistanceAnalyzer()
    return analyzer.analyze_price_action(df, price_column, window, min_change_pct, tolerance) 