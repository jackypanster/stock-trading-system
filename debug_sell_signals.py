#!/usr/bin/env python3
"""
调试卖出信号生成问题
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime

def debug_resistance_detection():
    """调试阻力位检测"""
    print("🔍 调试阻力位检测逻辑")
    print("=" * 50)
    
    try:
        from app.analysis.support_resistance import SupportResistanceAnalyzer
        
        # 创建简单明确的阻力位场景
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        resistance_level = 100.0
        
        # 简单的阻力位模式 - 明确的高低点
        prices = [95.0, 98.0, 100.5, 98.0, 95.0,  # 明确的高点在位置2
                  92.0, 89.0, 86.0, 89.0, 92.0,   # 明确的低点在位置7
                  95.0, 98.0, 100.2, 98.0, 95.0,  # 另一个高点在位置12
                  92.0, 89.0, 87.0, 91.0, 99.0]   # 最后反弹接近阻力位
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 20
        }, index=dates)
        
        print(f"数据: {len(df)}天")
        print(f"价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
        print(f"当前价格: ${df['Close'].iloc[-1]:.2f}")
        print(f"预期阻力位: ${resistance_level:.2f}")
        
        # 分析支撑阻力位
        analyzer = SupportResistanceAnalyzer()
        result = analyzer.analyze_price_action(df, window=3, min_change_pct=0.5, tolerance=1.0)
        
        print("\n📊 分析结果:")
        print(f"识别的高点数: {result['local_extrema']['total_highs']}")
        print(f"识别的低点数: {result['local_extrema']['total_lows']}")
        print(f"阻力位数量: {result['support_resistance']['total_resistance']}")
        print(f"支撑位数量: {result['support_resistance']['total_support']}")
        
        # 详细查看阻力位
        resistance_levels = result['support_resistance']['resistance_levels']
        print(f"\n🔴 阻力位详情:")
        for i, level in enumerate(resistance_levels):
            print(f"  阻力位{i+1}: ${level['price']:.2f}, 强度:{level['strength_rating']}, 触及次数:{level['touch_count']}")
        
        # 详细查看支撑位
        support_levels = result['support_resistance']['support_levels']
        print(f"\n🟢 支撑位详情:")
        for i, level in enumerate(support_levels):
            print(f"  支撑位{i+1}: ${level['price']:.2f}, 强度:{level['strength_rating']}, 触及次数:{level['touch_count']}")
        
        # 当前位置分析
        current_position = result['support_resistance'].get('current_position')
        if current_position:
            print(f"\n📍 当前位置分析:")
            print(f"  位置描述: {current_position['position_description']}")
            print(f"  当前价格: ${current_position['current_price']:.2f}")
            
            if current_position['nearest_resistance']:
                res_dist = current_position['resistance_distance']
                print(f"  最近阻力位: ${current_position['nearest_resistance']['price']:.2f}")
                print(f"  阻力位距离: ${res_dist['price_diff']:.2f} ({res_dist['percentage']:.2f}%)")
            
            if current_position['nearest_support']:
                sup_dist = current_position['support_distance']
                print(f"  最近支撑位: ${current_position['nearest_support']['price']:.2f}")
                print(f"  支撑位距离: ${sup_dist['price_diff']:.2f} ({sup_dist['percentage']:.2f}%)")
        else:
            print("\n❌ 无法确定当前位置")
        
        return result
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def debug_strategy_analysis():
    """调试策略分析"""
    print("\n🔍 调试策略分析逻辑")
    print("=" * 50)
    
    try:
        from app.analysis.strategies import SupportResistanceStrategy
        
        # 使用相同的测试数据 - 明确的高低点模式
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        prices = [95.0, 98.0, 100.5, 98.0, 95.0,  # 明确的高点在位置2
                  92.0, 89.0, 86.0, 89.0, 92.0,   # 明确的低点在位置7
                  95.0, 98.0, 100.2, 98.0, 95.0,  # 另一个高点在位置12
                  92.0, 89.0, 87.0, 91.0, 99.0]   # 最后反弹接近阻力位
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1000] * 20
        }, index=dates)
        
        print(f"当前价格: ${df['Close'].iloc[-1]:.2f}")
        
        # 创建策略
        strategy = SupportResistanceStrategy({
            'window': 3,
            'min_change_pct': 0.5,
            'tolerance': 1.0,
            'proximity_threshold': 5.0,  # 5%接近阈值
            'min_confidence': 0.3,
            'min_strength_rating': '弱'
        })
        
        # 生成信号
        signals = strategy.analyze(df)
        
        print(f"生成信号数量: {len(signals)}")
        
        if signals:
            for i, signal in enumerate(signals):
                signal_dict = signal.to_dict()
                print(f"\n信号{i+1}:")
                print(f"  类型: {signal_dict['signal_type']}")
                print(f"  置信度: {signal_dict['confidence']:.3f}")
                print(f"  价格: ${signal_dict['price']:.2f}")
                print(f"  原因: {signal_dict['reason']}")
        else:
            print("❌ 未生成任何信号")
        
        return signals
        
    except Exception as e:
        print(f"❌ 策略调试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主调试函数"""
    print("🐛 T4.1.3 卖出信号生成调试")
    print("=" * 60)
    
    # 调试1: 支撑阻力位检测
    sr_result = debug_resistance_detection()
    
    # 调试2: 策略分析
    strategy_result = debug_strategy_analysis()
    
    print("\n" + "=" * 60)
    print("📋 调试总结:")
    print(f"  支撑阻力位检测: {'✅ 成功' if sr_result else '❌ 失败'}")
    print(f"  策略信号生成: {'✅ 成功' if strategy_result else '❌ 失败'}")


if __name__ == "__main__":
    main() 