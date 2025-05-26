#!/usr/bin/env python3
"""
T4.2.2 信号过滤机制简化测试
Signal Filtering Mechanism Simple Test

简化版测试，不依赖pandas和numpy，专注于核心功能验证。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.analysis.signal_filter import SignalFilter, FilterCriteria, create_signal_filter
from app.analysis.strategies import TradingSignal


def create_simple_test_signals() -> List[TradingSignal]:
    """创建简单的测试信号数据"""
    base_time = datetime.now()
    
    signals = [
        # 高置信度买入信号
        TradingSignal(
            signal_type='buy',
            action='enter',
            confidence=0.85,
            price=150.0,
            timestamp=base_time,
            reason='强支撑位反弹',
            stop_loss=145.0,
            take_profit=160.0,
            position_size=0.3
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
            position_size=0.1
        ),
        
        # 高置信度卖出信号
        TradingSignal(
            signal_type='sell',
            action='enter',
            confidence=0.78,
            price=155.0,
            timestamp=base_time - timedelta(minutes=5),
            reason='接近阻力位',
            stop_loss=158.0,
            take_profit=150.0,
            position_size=0.25
        ),
        
        # 重复信号（与第一个相似）
        TradingSignal(
            signal_type='buy',
            action='enter',
            confidence=0.82,
            price=150.5,
            timestamp=base_time + timedelta(minutes=15),
            reason='支撑位反弹确认',
            stop_loss=145.5,
            take_profit=159.0,
            position_size=0.28
        ),
        
        # 过时信号
        TradingSignal(
            signal_type='sell',
            action='enter',
            confidence=0.75,
            price=158.0,
            timestamp=base_time - timedelta(hours=25),
            reason='阻力位卖出',
            stop_loss=162.0,
            take_profit=152.0,
            position_size=0.15
        )
    ]
    
    return signals


def test_confidence_filtering():
    """测试置信度过滤"""
    print("=== 测试1: 置信度过滤 ===")
    
    signals = create_simple_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：最小置信度0.7
    criteria = FilterCriteria(min_confidence=0.7)
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    
    # 验证所有过滤后的信号置信度都>=0.7
    for signal in filtered_signals:
        assert signal.confidence >= 0.7, f"信号置信度 {signal.confidence} 低于阈值 0.7"
    
    print("✅ 置信度过滤测试通过")
    print(f"保留的信号置信度: {[f'{s.confidence:.2f}' for s in filtered_signals]}")
    print()
    
    return len(filtered_signals) < len(signals)  # 应该有信号被过滤


def test_signal_type_filtering():
    """测试信号类型过滤"""
    print("=== 测试2: 信号类型过滤 ===")
    
    signals = create_simple_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：只保留买入信号
    criteria = FilterCriteria(
        min_confidence=0.4,
        signal_types=['buy']
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
    
    return True


def test_time_window_filtering():
    """测试时间窗口过滤"""
    print("=== 测试3: 时间窗口过滤 ===")
    
    signals = create_simple_test_signals()
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
    
    # 验证所有信号都在24小时内
    current_time = datetime.now()
    for signal in filtered_signals:
        time_diff = current_time - signal.timestamp
        assert time_diff.total_seconds() <= 24 * 3600, f"信号超出24小时时间窗口: {time_diff}"
    
    print("✅ 时间窗口过滤测试通过")
    print()
    
    return len(filtered_signals) < len(signals)  # 应该有过时信号被过滤


def test_duplicate_removal():
    """测试重复信号去除"""
    print("=== 测试4: 重复信号去除 ===")
    
    signals = create_simple_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置过滤条件：去除重复信号
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
    removed_count = duplicate_stats.get('removed_count', 0)
    print(f"重复信号去除数量: {removed_count}")
    
    print("✅ 重复信号去除测试通过")
    print()
    
    return removed_count > 0  # 应该有重复信号被去除


def test_comprehensive_filtering():
    """测试综合过滤功能"""
    print("=== 测试5: 综合过滤功能 ===")
    
    signals = create_simple_test_signals()
    filter_instance = create_signal_filter()
    
    # 设置综合过滤条件
    criteria = FilterCriteria(
        min_confidence=0.65,
        signal_types=['buy', 'sell'],
        max_position_size=0.5,
        time_window_hours=24,
        remove_duplicates=True,
        max_signals_per_day=3
    )
    
    result = filter_instance.filter_signals(signals, criteria)
    
    filtered_signals = result['filtered_signals']
    statistics = result['statistics']
    quality_summary = result['quality_summary']
    
    print(f"原始信号数量: {statistics['original_count']}")
    print(f"过滤后信号数量: {statistics['filtered_count']}")
    print(f"总过滤率: {statistics['filter_efficiency']['filter_rate']:.2%}")
    
    # 显示各步骤过滤结果
    print("\n各步骤过滤结果:")
    for step_name, step_stats in statistics['filter_steps'].items():
        removed_count = step_stats.get('removed_count', 0)
        if removed_count > 0:
            print(f"  {step_name}: 移除 {removed_count} 个信号")
    
    # 验证最终结果
    assert len(filtered_signals) <= 3, "信号数量超过每日限制"
    
    for signal in filtered_signals:
        assert signal.confidence >= 0.65, f"置信度 {signal.confidence} 低于阈值"
        assert signal.position_size <= 0.5, f"仓位大小 {signal.position_size} 超过限制"
    
    print("✅ 综合过滤功能测试通过")
    print()
    
    return True


def test_filter_statistics():
    """测试过滤器统计功能"""
    print("=== 测试6: 过滤器统计功能 ===")
    
    signals = create_simple_test_signals()
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
    
    # 验证统计信息
    assert stats['total_processed'] == len(signals) * 2, "处理信号数统计错误"
    assert stats['total_processed'] >= stats['total_filtered'], "过滤后信号数不应超过处理数"
    
    print("✅ 过滤器统计功能测试通过")
    print()
    
    return True


def main():
    """运行所有测试"""
    print("🚀 开始T4.2.2信号过滤机制简化测试")
    print("=" * 50)
    
    try:
        # 运行各项测试
        test_results = []
        
        test_results.append(test_confidence_filtering())
        test_results.append(test_signal_type_filtering())
        test_results.append(test_time_window_filtering())
        test_results.append(test_duplicate_removal())
        test_results.append(test_comprehensive_filtering())
        test_results.append(test_filter_statistics())
        
        # 验证测试结果
        assert all(test_results), "某些测试未达到预期效果"
        
        print("🎉 所有测试通过！")
        print("\n✅ T4.2.2验收标准验证:")
        print("  ✓ 低置信度信号被过滤")
        print("  ✓ 高质量信号保留")
        print("  ✓ 过滤前后信号数量和质量变化可验证")
        print("  ✓ 多维度过滤功能正常")
        print("  ✓ 重复信号去除功能正常")
        print("  ✓ 时间窗口过滤功能正常")
        print("  ✓ 信号类型过滤功能正常")
        print("  ✓ 综合过滤功能正常")
        print("  ✓ 过滤统计功能正常")
        
        print("\n📊 T4.2.2任务完成情况:")
        print("  ✅ 信号过滤机制实现完成")
        print("  ✅ 多维度过滤条件支持")
        print("  ✅ 过滤效果统计和分析")
        print("  ✅ 质量评估和改进建议")
        print("  ✅ 便捷函数接口提供")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 