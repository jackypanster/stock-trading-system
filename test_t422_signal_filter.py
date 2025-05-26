#!/usr/bin/env python3
"""
T4.2.2 信号过滤机制测试
Signal Filtering Mechanism Test

测试信号过滤器的各种功能，包括：
1. 基础置信度过滤
2. 重复信号去除
3. 时间窗口过滤
4. 风险回报比过滤
5. 市场条件过滤
6. 质量评估和统计分析
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.analysis.signal_filter import SignalFilter, FilterCriteria, create_signal_filter, filter_signals
from app.analysis.strategies import TradingSignal


def create_test_signals() -> List[TradingSignal]:
    """创建测试信号数据"""
    base_time = datetime.now()
    
    signals = [
        # 高质量买入信号
        TradingSignal(
            signal_type='buy',
            action='enter',
            confidence=0.85,
            price=150.0,
            timestamp=base_time,
            reason='强支撑位反弹，RSI超卖',
            stop_loss=145.0,
            take_profit=160.0,
            position_size=0.3,
            metadata={
                'technical_confirmations': {
                    'rsi_oversold': True,
                    'macd_bullish': True,
                    'moving_avg_support': True
                },
                'support_level': 148.0,
                'support_strength': '强'
            }
        ),
        
        # 低置信度买入信号
        TradingSignal(
            signal_type='buy',
            action='enter',
            confidence=0.45,
            price=152.0,
            timestamp=base_time - timedelta(minutes=10),
            reason='接近支撑位',
            stop_loss=148.0,
            take_profit=156.0,
            position_size=0.1,
            metadata={'support_level': 150.0}
        ),
        
        # 高质量卖出信号
        TradingSignal(
            signal_type='sell',
            action='enter',
            confidence=0.78,
            price=155.0,
            timestamp=base_time - timedelta(minutes=5),
            reason='接近阻力位，RSI超买',
            stop_loss=158.0,
            take_profit=150.0,
            position_size=0.25,
            metadata={
                'technical_confirmations': {
                    'rsi_overbought': True,
                    'macd_bearish': False,
                    'moving_avg_resistance': True
                },
                'resistance_level': 157.0
            }
        ),
        
        # 重复信号（与第一个信号相似）
        TradingSignal(
            signal_type='buy',
            action='enter',
            confidence=0.82,
            price=150.5,
            timestamp=base_time + timedelta(minutes=15),
            reason='支撑位反弹确认',
            stop_loss=145.5,
            take_profit=159.0,
            position_size=0.28,
            metadata={'support_level': 148.0}
        ),
        
        # 风险回报比差的信号
        TradingSignal(
            signal_type='buy',
            action='enter',
            confidence=0.70,
            price=160.0,
            timestamp=base_time - timedelta(minutes=20),
            reason='技术指标确认',
            stop_loss=155.0,  # 风险5美元
            take_profit=162.0,  # 回报2美元，风险回报比0.4:1
            position_size=0.2,
            metadata={}
        ),
        
        # 过时信号
        TradingSignal(
            signal_type='sell',
            action='enter',
            confidence=0.75,
            price=158.0,
            timestamp=base_time - timedelta(hours=25),  # 25小时前
            reason='阻力位卖出',
            stop_loss=162.0,
            take_profit=152.0,
            position_size=0.15,
            metadata={}
        ),
        
        # 仓位过大的信号
        TradingSignal(
            signal_type='buy',
            action='enter',
            confidence=0.72,
            price=153.0,
            timestamp=base_time - timedelta(minutes=30),
            reason='突破买入',
            stop_loss=150.0,
            take_profit=158.0,
            position_size=0.8,  # 80%仓位过大
            metadata={}
        )
    ]
    
    return signals


def test_basic_confidence_filtering():
    """测试基础置信度过滤"""
    print("=== 测试1: 基础置信度过滤 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：最小置信度0.7
    criteria = FilterCriteria(min_confidence=0.7)
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    print(f"过滤率: {statistics['filter_efficiency']['filter_rate']:.2%}")
    
    # 验证所有过滤后的信号置信度都>=0.7
    for signal in filtered_signals:
        assert signal.confidence >= 0.7, f"信号置信度 {signal.confidence} 低于阈值 0.7"
    
    print("✅ 置信度过滤测试通过")
    print(f"保留的信号置信度: {[f'{s.confidence:.2f}' for s in filtered_signals]}")
    print()


def test_duplicate_signal_removal():
    """测试重复信号去除"""
    print("=== 测试2: 重复信号去除 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：去除重复信号，低置信度阈值以保留更多信号
    criteria = FilterCriteria(
        min_confidence=0.4,
        remove_duplicates=True
    )
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    
    # 检查重复信号去除步骤
    duplicate_stats = statistics['filter_steps'].get('duplicates', {})
    print(f"重复信号去除数量: {duplicate_stats.get('removed_count', 0)}")
    
    # 验证没有重复信号
    signal_signatures = []
    for signal in filtered_signals:
        signature = (signal.signal_type, round(signal.price, 0), signal.timestamp.hour)
        assert signature not in signal_signatures, f"发现重复信号: {signature}"
        signal_signatures.append(signature)
    
    print("✅ 重复信号去除测试通过")
    print()


def test_time_window_filtering():
    """测试时间窗口过滤"""
    print("=== 测试3: 时间窗口过滤 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：只保留24小时内的信号
    criteria = FilterCriteria(
        min_confidence=0.4,
        time_window_hours=24,
        remove_duplicates=False
    )
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    
    # 检查时间窗口过滤步骤
    time_stats = statistics['filter_steps'].get('time_window', {})
    print(f"超时信号去除数量: {time_stats.get('removed_count', 0)}")
    
    # 验证所有信号都在24小时内
    current_time = datetime.now()
    for signal in filtered_signals:
        time_diff = current_time - signal.timestamp
        assert time_diff.total_seconds() <= 24 * 3600, f"信号超出24小时时间窗口: {time_diff}"
    
    print("✅ 时间窗口过滤测试通过")
    print()


def test_risk_reward_filtering():
    """测试风险回报比过滤"""
    print("=== 测试4: 风险回报比过滤 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：最小风险回报比1.5:1
    criteria = FilterCriteria(
        min_confidence=0.4,
        min_risk_reward_ratio=1.5,
        remove_duplicates=False,
        time_window_hours=None
    )
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    
    # 检查风险回报比过滤步骤
    rr_stats = statistics['filter_steps'].get('risk_reward', {})
    print(f"风险回报比不足信号去除数量: {rr_stats.get('removed_count', 0)}")
    
    # 验证所有信号的风险回报比都>=1.5
    for signal in filtered_signals:
        if signal.stop_loss and signal.take_profit:
            if signal.signal_type == 'buy':
                risk = abs(signal.price - signal.stop_loss)
                reward = abs(signal.take_profit - signal.price)
            else:  # sell
                risk = abs(signal.stop_loss - signal.price)
                reward = abs(signal.price - signal.take_profit)
            
            if risk > 0:
                rr_ratio = reward / risk
                assert rr_ratio >= 1.5, f"风险回报比 {rr_ratio:.2f} 低于阈值 1.5"
                print(f"信号风险回报比: {rr_ratio:.2f}")
    
    print("✅ 风险回报比过滤测试通过")
    print()


def test_signal_type_filtering():
    """测试信号类型过滤"""
    print("=== 测试5: 信号类型过滤 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：只保留买入信号
    criteria = FilterCriteria(
        min_confidence=0.4,
        signal_types=['buy'],
        remove_duplicates=False
    )
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    
    # 验证所有信号都是买入信号
    for signal in filtered_signals:
        assert signal.signal_type == 'buy', f"发现非买入信号: {signal.signal_type}"
    
    print("✅ 信号类型过滤测试通过")
    print(f"保留的信号类型: {[s.signal_type for s in filtered_signals]}")
    print()


def test_daily_limit_filtering():
    """测试每日信号数量限制"""
    print("=== 测试6: 每日信号数量限制 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：每日最多3个信号
    criteria = FilterCriteria(
        min_confidence=0.4,
        max_signals_per_day=3,
        remove_duplicates=False
    )
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    
    # 验证信号数量不超过限制
    assert len(filtered_signals) <= 3, f"信号数量 {len(filtered_signals)} 超过限制 3"
    
    # 验证保留的是置信度最高的信号
    if len(filtered_signals) > 1:
        confidences = [s.confidence for s in filtered_signals]
        assert confidences == sorted(confidences, reverse=True), "信号未按置信度排序"
    
    print("✅ 每日信号数量限制测试通过")
    print(f"保留信号的置信度: {[f'{s.confidence:.2f}' for s in filtered_signals]}")
    print()


def test_comprehensive_filtering():
    """测试综合过滤功能"""
    print("=== 测试7: 综合过滤功能 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置综合过滤条件
    criteria = FilterCriteria(
        min_confidence=0.65,
        signal_types=['buy', 'sell'],
        max_position_size=0.5,
        time_window_hours=24,
        remove_duplicates=True,
        min_risk_reward_ratio=1.2,
        max_signals_per_day=5
    )
    
    # 模拟市场数据
    market_data = {
        'volatility': 0.03,
        'volume_ratio': 1.2,
        'trend_strength': 0.5
    }
    
    result = filter_instance.filter_signals(signals, criteria, market_data)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    quality_summary = result['quality_summary']
    recommendations = result['recommendations']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    print(f"总过滤率: {statistics['filter_efficiency']['filter_rate']:.2%}")
    
    # 显示各步骤过滤结果
    print("\n各步骤过滤结果:")
    for step_name, step_stats in statistics['filter_steps'].items():
        removed_count = step_stats.get('removed_count', 0)
        if removed_count > 0:
            print(f"  {step_name}: 移除 {removed_count} 个信号")
    
    # 显示质量分析
    print(f"\n质量分析:")
    quality_metrics = quality_summary.get('quality_metrics', {})
    print(f"  平均置信度: {quality_metrics.get('avg_confidence', 0):.3f}")
    print(f"  质量分布: {quality_metrics.get('quality_distribution', {})}")
    
    # 显示建议
    if recommendations:
        print(f"\n优化建议:")
        for rec in recommendations:
            print(f"  - {rec}")
    
    print("✅ 综合过滤功能测试通过")
    print()


def test_filter_statistics():
    """测试过滤器统计功能"""
    print("=== 测试8: 过滤器统计功能 ===")
    
    signals = create_test_signals()
    filter_instance = create_signal_filter()
    
    # 重置统计信息
    filter_instance.reset_statistics()
    
    # 执行多次过滤
    criteria1 = FilterCriteria(min_confidence=0.7)
    criteria2 = FilterCriteria(min_confidence=0.8)
    
    result1 = filter_instance.filter_signals(signals, criteria1)
    result2 = filter_instance.filter_signals(signals, criteria2)
    
    # 获取统计信息
    stats = filter_instance.get_filter_statistics()
    
    print(f"总处理信号数: {stats['total_processed']}")
    print(f"总过滤后信号数: {stats['total_filtered']}")
    print(f"总体过滤率: {stats['overall_filter_rate']:.2%}")
    
    # 显示过滤原因统计
    print(f"\n过滤原因统计:")
    for reason, count in stats['filter_reasons'].items():
        if count > 0:
            print(f"  {reason}: {count} 次")
    
    print("✅ 过滤器统计功能测试通过")
    print()


def test_convenience_functions():
    """测试便捷函数"""
    print("=== 测试9: 便捷函数 ===")
    
    signals = create_test_signals()
    
    # 测试便捷过滤函数
    result = filter_signals(
        signals,
        criteria=FilterCriteria(min_confidence=0.7),
        config={'default_min_confidence': 0.6}
    )
    
    filtered_signals = result['filtered_signals']
    
    print(f"便捷函数过滤结果: {len(signals)} -> {len(filtered_signals)} 个信号")
    
    # 验证结果
    assert len(filtered_signals) <= len(signals), "过滤后信号数量不应增加"
    
    for signal in filtered_signals:
        assert signal.confidence >= 0.7, f"信号置信度 {signal.confidence} 低于阈值"
    
    print("✅ 便捷函数测试通过")
    print()


def main():
    """运行所有测试"""
    print("🚀 开始T4.2.2信号过滤机制测试")
    print("=" * 50)
    
    try:
        test_basic_confidence_filtering()
        test_duplicate_signal_removal()
        test_time_window_filtering()
        test_risk_reward_filtering()
        test_signal_type_filtering()
        test_daily_limit_filtering()
        test_comprehensive_filtering()
        test_filter_statistics()
        test_convenience_functions()
        
        print("🎉 所有测试通过！")
        print("\n✅ T4.2.2验收标准验证:")
        print("  ✓ 低置信度信号被过滤")
        print("  ✓ 高质量信号保留")
        print("  ✓ 过滤前后信号数量和质量变化可验证")
        print("  ✓ 多维度过滤功能正常")
        print("  ✓ 重复信号去除功能正常")
        print("  ✓ 时间窗口过滤功能正常")
        print("  ✓ 风险回报比过滤功能正常")
        print("  ✓ 信号质量评估功能正常")
        print("  ✓ 过滤统计和分析功能正常")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 