#!/usr/bin/env python3
"""
调试局部极值识别
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np

def debug_extrema_detection():
    """调试局部极值识别"""
    print("🔍 调试局部极值识别")
    print("=" * 50)
    
    # 创建简单的测试数据 - 明确的高低点模式
    prices = [95.0, 98.0, 100.5, 98.0, 95.0,  # 明确的高点在位置2
              92.0, 89.0, 86.0, 89.0, 92.0,   # 明确的低点在位置7
              95.0, 98.0, 100.2, 98.0, 95.0,  # 另一个高点在位置12
              92.0, 89.0, 87.0, 91.0, 99.0]   # 最后反弹
    
    dates = pd.date_range('2024-01-01', periods=len(prices), freq='D')
    price_series = pd.Series(prices, index=dates)
    
    print(f"价格数据: {prices}")
    print(f"数据长度: {len(prices)}")
    print(f"价格范围: ${min(prices):.2f} - ${max(prices):.2f}")
    
    # 手动检查局部极值
    window = 3
    min_change_pct = 0.5
    
    print(f"\n使用窗口={window}, 最小变化={min_change_pct}%")
    print("手动检查每个位置:")
    
    for i in range(window, len(prices) - window):
        current_price = prices[i]
        window_prices = prices[i-window:i+window+1]
        
        is_max = current_price == max(window_prices)
        is_min = current_price == min(window_prices)
        
        if is_max:
            min_in_window = min(window_prices)
            change_pct = ((current_price - min_in_window) / min_in_window) * 100
            print(f"  位置{i}: ${current_price:.2f} 是局部最大值, 变化幅度={change_pct:.2f}%")
            if change_pct >= min_change_pct:
                print(f"    ✅ 符合高点条件")
            else:
                print(f"    ❌ 变化幅度不足")
        
        if is_min:
            max_in_window = max(window_prices)
            change_pct = ((max_in_window - current_price) / current_price) * 100
            print(f"  位置{i}: ${current_price:.2f} 是局部最小值, 变化幅度={change_pct:.2f}%")
            if change_pct >= min_change_pct:
                print(f"    ✅ 符合低点条件")
            else:
                print(f"    ❌ 变化幅度不足")
    
    # 使用实际的分析器
    print(f"\n使用SupportResistanceAnalyzer:")
    try:
        from app.analysis.support_resistance import SupportResistanceAnalyzer
        
        analyzer = SupportResistanceAnalyzer()
        result = analyzer.find_local_extrema(price_series, window=window, min_change_pct=min_change_pct)
        
        print(f"识别的高点: {len(result['highs'])}")
        for i, high in enumerate(result['highs']):
            print(f"  高点{i+1}: 位置{high['index']}, ${high['price']:.2f}, 强度{high['strength']:.2f}%")
        
        print(f"识别的低点: {len(result['lows'])}")
        for i, low in enumerate(result['lows']):
            print(f"  低点{i+1}: 位置{low['index']}, ${low['price']:.2f}, 强度{low['strength']:.2f}%")
        
    except Exception as e:
        print(f"❌ 分析器测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_extrema_detection() 