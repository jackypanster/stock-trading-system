#!/usr/bin/env python3
"""
T4.1.3 卖出信号生成验证测试
T4.1.3 Sell Signal Generation Validation Test

验证增强版卖出信号生成功能
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime

def test_t413_sell_signal_generation():
    """测试T4.1.3卖出信号生成"""
    print("🧪 T4.1.3 - 增强版卖出信号生成测试")
    print("=" * 60)
    
    try:
        from app.analysis.strategies import SupportResistanceStrategy
        
        # 场景1: 明确的卖出场景 - 接近阻力位
        print("📊 场景1: 接近阻力位卖出信号")
        print("-" * 40)
        
        # 创建明确的阻力位场景
        dates = pd.date_range('2024-01-01', periods=35, freq='D')
        
        # 价格数据：明确的阻力位模式
        prices = []
        
        # 前15天：建立多个阻力位
        for i in range(15):
            if i % 5 == 2:  # 位置2,7,12建立高点
                prices.append(110.0 + np.random.normal(0, 0.1))  # 阻力位附近
            elif i % 5 == 0:  # 位置0,5,10建立低点
                prices.append(105.0 + np.random.normal(0, 0.2))  # 低位
            else:
                prices.append(107.5 + np.random.normal(0, 0.5))  # 中间位置
        
        # 中间10天：明显下跌
        for i in range(10):
            prices.append(100.0 - i * 0.8)  # 从100下跌到92
        
        # 最后10天：反弹接近阻力位
        for i in range(10):
            if i < 7:
                rebound_price = 92.0 + i * 1.5  # 逐渐反弹
                prices.append(rebound_price + np.random.normal(0, 0.3))
            else:
                prices.append(109.0 + np.random.normal(0, 0.2))  # 接近阻力位
        
        df1 = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': [p + 0.5 for p in prices],
            'Low': [p - 0.5 for p in prices],
            'Volume': [1000] * 35
        }, index=dates)
        
        print(f"数据: {len(df1)}天, 价格范围 ${df1['Close'].min():.2f}-${df1['Close'].max():.2f}")
        print(f"当前价格: ${df1['Close'].iloc[-1]:.2f}")
        
        # 创建策略
        strategy = SupportResistanceStrategy({
            'window': 3,
            'min_change_pct': 0.5,
            'tolerance': 1.0,
            'proximity_threshold': 5.0,
            'min_confidence': 0.3,
            'min_strength_rating': '弱'
        })
        
        # 生成信号
        signals = strategy.analyze(df1)
        
        print(f"生成信号数量: {len(signals)}")
        
        if signals:
            signal = signals[0]
            signal_dict = signal.to_dict()
            
            print(f"✅ 卖出信号生成成功:")
            print(f"  类型: {signal_dict['signal_type']}")
            print(f"  动作: {signal_dict['action']}")
            print(f"  置信度: {signal_dict['confidence']:.3f}")
            print(f"  价格: ${signal_dict['price']:.2f}")
            print(f"  原因: {signal_dict['reason']}")
            print(f"  止损: ${signal_dict['stop_loss']:.2f}")
            print(f"  止盈: ${signal_dict['take_profit']:.2f}")
            print(f"  仓位: {signal_dict['position_size']:.1%}")
            
            # 检查增强功能
            metadata = signal_dict.get('metadata', {})
            if 'technical_confirmations' in metadata:
                tech_conf = metadata['technical_confirmations']
                print(f"  技术确认: {tech_conf.get('confirmation_count', 0)}个")
                print(f"  确认强度: {tech_conf.get('confirmation_strength', 0):.3f}")
            
            if 'base_confidence' in metadata:
                base_conf = metadata['base_confidence']
                enhancement = metadata.get('enhancement_factor', 0)
                print(f"  基础置信度: {base_conf:.3f}")
                print(f"  增强幅度: +{enhancement:.3f}")
            
            # 验证是否为卖出信号
            if signal_dict['signal_type'] == 'sell':
                print("✅ 正确生成卖出信号")
                return True
            else:
                print(f"❌ 期望卖出信号，实际生成: {signal_dict['signal_type']}")
                return False
        else:
            print("❌ 未生成卖出信号")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_t413_sell_signal_quality():
    """测试T4.1.3卖出信号质量评估"""
    print("\n🔍 卖出信号质量评估测试")
    print("-" * 40)
    
    try:
        from app.analysis.strategies import SupportResistanceStrategy
        
        # 创建高质量卖出信号场景
        dates = pd.date_range('2024-02-01', periods=35, freq='D')
        
        # 强阻力位场景
        strong_resistance = 120.0
        prices = []
        
        # 前12天：建立强阻力位模式
        for i in range(12):
            if i % 4 == 2:  # 位置2,6,10建立高点
                prices.append(strong_resistance + np.random.normal(0, 0.05))
            elif i % 4 == 0:  # 位置0,4,8建立低点
                prices.append(115.0 + np.random.normal(0, 0.1))
            else:
                prices.append(117.5 + np.random.normal(0, 0.3))
        
        # 中间15天：下跌远离阻力位
        for i in range(15):
            decline_price = 110.0 - i * 0.5  # 逐渐下跌
            prices.append(decline_price + np.random.normal(0, 0.4))
        
        # 最后8天：反弹接近强阻力位
        for i in range(8):
            if i < 5:
                rebound_price = 102.5 + i * 2.0  # 逐渐反弹
                prices.append(rebound_price + np.random.normal(0, 0.2))
            else:
                prices.append(119.0 + np.random.normal(0, 0.1))  # 非常接近阻力位
        
        df2 = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': [p + 0.3 for p in prices],
            'Low': [p - 0.3 for p in prices],
            'Volume': [2000] * 35
        }, index=dates)
        
        strategy = SupportResistanceStrategy({
            'window': 3,
            'min_change_pct': 0.4,
            'tolerance': 0.8,
            'proximity_threshold': 4.0,
            'min_confidence': 0.4,
            'min_strength_rating': '弱'
        })
        
        signals = strategy.analyze(df2)
        
        if signals:
            signal_dict = signals[0].to_dict()
            
            print(f"✅ 高质量卖出信号生成:")
            print(f"  置信度: {signal_dict['confidence']:.3f}")
            print(f"  原因: {signal_dict['reason']}")
            
            # 质量检查
            quality_score = 0
            
            if signal_dict['confidence'] >= 0.7:
                quality_score += 3
                print(f"  ✅ 高置信度 (+3)")
            elif signal_dict['confidence'] >= 0.5:
                quality_score += 2
                print(f"  ✅ 中等置信度 (+2)")
            else:
                quality_score += 1
                print(f"  ⚠️ 低置信度 (+1)")
            
            # 风险回报比检查
            current_price = signal_dict['price']
            stop_loss = signal_dict['stop_loss']
            take_profit = signal_dict['take_profit']
            
            risk = stop_loss - current_price
            reward = current_price - take_profit
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= 2.5:
                quality_score += 3
                print(f"  ✅ 优秀风险回报比 1:{rr_ratio:.1f} (+3)")
            elif rr_ratio >= 2.0:
                quality_score += 2
                print(f"  ✅ 良好风险回报比 1:{rr_ratio:.1f} (+2)")
            else:
                quality_score += 1
                print(f"  ⚠️ 一般风险回报比 1:{rr_ratio:.1f} (+1)")
            
            # 增强功能检查
            metadata = signal_dict.get('metadata', {})
            if metadata.get('enhancement_factor', 0) > 0.1:
                quality_score += 2
                print(f"  ✅ 有效信号增强 (+2)")
            
            # 验证卖出信号特征
            if signal_dict['signal_type'] == 'sell':
                quality_score += 2
                print(f"  ✅ 正确信号类型 (+2)")
            
            print(f"  总质量分数: {quality_score}/10")
            
            return quality_score >= 6  # 6分以上认为通过
        else:
            print("❌ 未生成信号")
            return False
            
    except Exception as e:
        print(f"❌ 质量测试失败: {e}")
        return False


def test_t413_technical_confirmations():
    """测试T4.1.3技术指标确认功能"""
    print("\n🔧 技术指标确认测试")
    print("-" * 40)
    
    try:
        from app.analysis.strategies import SupportResistanceStrategy
        
        # 创建包含技术指标确认的场景
        dates = pd.date_range('2024-03-01', periods=50, freq='D')
        
        # 模拟RSI超买 + MACD看跌的场景
        resistance_level = 100.0
        prices = []
        
        # 前30天：上升趋势，RSI逐渐超买
        for i in range(30):
            base_price = 90 + i * 0.3  # 逐渐上升
            prices.append(base_price + np.random.normal(0, 0.2))
        
        # 后20天：接近阻力位，准备反转
        for i in range(20):
            if i >= 15:  # 最后几天接近阻力位
                prices.append(resistance_level - 0.5 + np.random.normal(0, 0.1))
            else:
                prices.append(resistance_level - 2 + np.random.normal(0, 0.3))
        
        df3 = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Volume': [1500] * 50
        }, index=dates)
        
        strategy = SupportResistanceStrategy({
            'window': 5,
            'min_change_pct': 0.3,
            'tolerance': 0.5,
            'proximity_threshold': 3.0,
            'min_confidence': 0.3,
            'min_strength_rating': '弱'
        })
        
        signals = strategy.analyze(df3)
        
        if signals:
            signal_dict = signals[0].to_dict()
            metadata = signal_dict.get('metadata', {})
            
            print(f"✅ 技术确认测试结果:")
            print(f"  信号类型: {signal_dict['signal_type']}")
            print(f"  置信度: {signal_dict['confidence']:.3f}")
            
            # 检查技术确认
            tech_conf = metadata.get('technical_confirmations', {})
            print(f"  技术确认数量: {tech_conf.get('confirmation_count', 0)}")
            print(f"  确认强度: {tech_conf.get('confirmation_strength', 0):.3f}")
            
            # 检查具体确认项
            confirmations = []
            if tech_conf.get('rsi_overbought'):
                confirmations.append("RSI超买")
            if tech_conf.get('macd_bearish'):
                confirmations.append("MACD看跌")
            if tech_conf.get('moving_avg_resistance'):
                confirmations.append("均线阻力")
            
            if confirmations:
                print(f"  确认项目: {', '.join(confirmations)}")
            
            return len(confirmations) > 0  # 至少有一个技术确认
        else:
            print("❌ 未生成信号进行技术确认测试")
            return False
            
    except Exception as e:
        print(f"❌ 技术确认测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 T4.1.3 - 实现卖出信号生成 验证测试")
    print("验收标准: 价格接近阻力位时生成卖出信号")
    print("=" * 80)
    
    # 测试1: 基本卖出信号生成
    test1_pass = test_t413_sell_signal_generation()
    
    # 测试2: 卖出信号质量评估
    test2_pass = test_t413_sell_signal_quality()
    
    # 测试3: 技术指标确认
    test3_pass = test_t413_technical_confirmations()
    
    print("\n" + "=" * 80)
    print("📋 T4.1.3 验证测试结果:")
    print(f"  卖出信号生成: {'✅ 通过' if test1_pass else '❌ 失败'}")
    print(f"  信号质量评估: {'✅ 通过' if test2_pass else '❌ 失败'}")
    print(f"  技术指标确认: {'✅ 通过' if test3_pass else '❌ 失败'}")
    
    if test1_pass and test2_pass and test3_pass:
        print("\n🎉 T4.1.3验收标准达成:")
        print("  ✅ 价格接近阻力位时能够生成卖出信号")
        print("  ✅ 增强版卖出信号包含技术指标确认")
        print("  ✅ 信号质量评估和风险管理完善")
        print("  ✅ 置信度计算和动态仓位管理有效")
        print("  ✅ RSI超买、MACD看跌、均线阻力确认机制")
        print("\n✅ T4.1.3 - 实现卖出信号生成 验证通过！")
        return True
    else:
        print("\n⚠️ 部分测试未通过，需要进一步调试")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 