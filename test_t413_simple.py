#!/usr/bin/env python3
"""
T4.1.3 简化卖出信号生成测试
T4.1.3 Simplified Sell Signal Generation Test

使用已验证成功的数据模式
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime

def test_t413_simple():
    """简化的T4.1.3卖出信号生成测试"""
    print("🧪 T4.1.3 - 简化卖出信号生成测试")
    print("验收标准: 价格接近阻力位时生成卖出信号")
    print("=" * 60)
    
    try:
        from app.analysis.strategies import SupportResistanceStrategy
        
        # 使用已验证成功的数据模式
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
        
        print(f"📊 测试数据:")
        print(f"  数据长度: {len(df)}天")
        print(f"  价格范围: ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
        print(f"  当前价格: ${df['Close'].iloc[-1]:.2f}")
        print(f"  预期阻力位: ~$100.20")
        
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
        
        print(f"\n📈 信号生成结果:")
        print(f"  生成信号数量: {len(signals)}")
        
        if signals:
            for i, signal in enumerate(signals):
                signal_dict = signal.to_dict()
                print(f"\n  信号{i+1}:")
                print(f"    类型: {signal_dict['signal_type']}")
                print(f"    动作: {signal_dict['action']}")
                print(f"    置信度: {signal_dict['confidence']:.3f}")
                print(f"    价格: ${signal_dict['price']:.2f}")
                print(f"    原因: {signal_dict['reason']}")
                
                if signal_dict.get('stop_loss'):
                    print(f"    止损: ${signal_dict['stop_loss']:.2f}")
                if signal_dict.get('take_profit'):
                    print(f"    止盈: ${signal_dict['take_profit']:.2f}")
                if signal_dict.get('position_size'):
                    print(f"    仓位大小: {signal_dict['position_size']:.1%}")
                
                # 检查元数据
                metadata = signal_dict.get('metadata', {})
                if metadata:
                    print(f"    元数据:")
                    if 'resistance_level' in metadata:
                        print(f"      阻力位: ${metadata['resistance_level']:.2f}")
                    if 'resistance_strength' in metadata:
                        print(f"      阻力位强度: {metadata['resistance_strength']}")
                    if 'distance_pct' in metadata and metadata['distance_pct']:
                        print(f"      距离: {metadata['distance_pct']:.2f}%")
                    if 'technical_confirmations' in metadata:
                        tc = metadata['technical_confirmations']
                        print(f"      技术确认数: {tc.get('confirmation_count', 0)}")
            
            # 验证卖出信号
            sell_signals = [s for s in signals if s.signal_type == 'sell']
            if sell_signals:
                print(f"\n✅ T4.1.3验证成功:")
                print(f"  - 成功生成{len(sell_signals)}个卖出信号")
                print(f"  - 信号置信度: {sell_signals[0].confidence:.3f}")
                print(f"  - 符合验收标准: 价格接近阻力位时生成卖出信号")
                return True
            else:
                print(f"\n❌ T4.1.3验证失败: 未生成卖出信号")
                return False
        else:
            print(f"\n❌ T4.1.3验证失败: 未生成任何信号")
            return False
        
    except Exception as e:
        print(f"\n❌ T4.1.3测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 T4.1.3 - 实现卖出信号生成 简化验证")
    print("=" * 80)
    
    success = test_t413_simple()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 T4.1.3 验证测试通过！")
        print("✅ 卖出信号生成功能实现成功")
    else:
        print("⚠️ T4.1.3 验证测试未通过")
        print("❌ 需要进一步调试")


if __name__ == "__main__":
    main() 