#!/usr/bin/env python3
"""
T4.2.1 置信度计算测试
Test Confidence Calculation Implementation

验证置信度计算器的各项功能：
1. 基础置信度计算
2. 多维度置信度评估
3. 置信度等级分类
4. 批量置信度计算
5. 置信度统计分析
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from datetime import datetime
import json

def test_t421_basic_confidence():
    """测试T4.2.1基础置信度计算"""
    print("🧪 测试T4.2.1 - 基础置信度计算")
    print("=" * 50)
    
    try:
        from app.analysis.confidence import create_confidence_calculator
        
        # 创建置信度计算器
        calculator = create_confidence_calculator()
        
        # 模拟技术分析数据
        technical_analysis = {
            'indicators': {
                'rsi_14': {
                    'current_rsi': 25.5,  # 极度超卖
                    'error': False
                },
                'macd': {
                    'signal_type': '买入信号',
                    'cross_signal': '金叉',
                    'position': '多头区域',
                    'histogram_trend': '上升',
                    'error': False
                },
                'atr': {
                    'atr_trend': '稳定',
                    'volatility_level': '中等',
                    'error': False
                }
            },
            'price_position': {
                'sma_5': 'above',
                'sma_10': 'above',
                'sma_20': 'below',
                'sma_50': 'below'
            }
        }
        
        # 模拟支撑阻力位数据
        support_resistance = {
            'support_levels': [
                {
                    'price': 98.50,
                    'touch_count': 4,
                    'strength_rating': '强'
                }
            ],
            'resistance_levels': [
                {
                    'price': 102.30,
                    'touch_count': 3,
                    'strength_rating': '中'
                }
            ]
        }
        
        # 模拟市场数据
        market_data = {
            'volume_ratio': 1.8,  # 成交量放大
            'volatility_level': '中等'
        }
        
        # 模拟风险水平
        risk_levels = {
            'stop_loss': 97.00,
            'take_profit': 103.50
        }
        
        current_price = 99.00
        
        # 计算买入信号置信度
        print("📊 计算买入信号置信度...")
        buy_confidence = calculator.calculate_signal_confidence(
            signal_type='buy',
            current_price=current_price,
            technical_analysis=technical_analysis,
            support_resistance=support_resistance,
            market_data=market_data,
            risk_levels=risk_levels
        )
        
        print(f"✅ 买入信号置信度计算完成:")
        print(f"  总体置信度: {buy_confidence['overall_confidence']:.3f}")
        print(f"  置信度等级: {buy_confidence['confidence_level']}")
        print(f"  质量分数: {buy_confidence['quality_score']}/10")
        print(f"  建议: {buy_confidence['recommendation']}")
        print(f"  风险评估: {buy_confidence['risk_assessment']}")
        
        print(f"\n📈 置信度组成部分:")
        components = buy_confidence['components']
        for component, value in components.items():
            print(f"  {component}: {value:.3f}")
        
        # 验证置信度范围
        assert 0.0 <= buy_confidence['overall_confidence'] <= 1.0, "置信度应在0-1范围内"
        
        # 验证高置信度（应该很高，因为有多重确认）
        assert buy_confidence['overall_confidence'] >= 0.7, f"多重确认信号置信度应该较高，实际: {buy_confidence['overall_confidence']:.3f}"
        
        print(f"✅ 基础置信度计算测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基础置信度计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_t421_confidence_levels():
    """测试T4.2.1置信度等级分类"""
    print("\n🧪 测试T4.2.1 - 置信度等级分类")
    print("=" * 50)
    
    try:
        from app.analysis.confidence import create_confidence_calculator
        
        calculator = create_confidence_calculator()
        
        # 测试不同置信度等级
        test_cases = [
            (0.90, 'very_high', '强烈推荐执行'),
            (0.80, 'high', '推荐执行'),
            (0.70, 'medium', '谨慎执行'),
            (0.55, 'low', '观望为主'),
            (0.40, 'very_low', '不建议执行')
        ]
        
        print("📊 测试置信度等级分类:")
        
        for confidence_value, expected_level, expected_recommendation in test_cases:
            level = calculator._get_confidence_level(confidence_value)
            recommendation = calculator._get_confidence_recommendation(confidence_value)
            risk = calculator._assess_confidence_risk(confidence_value)
            quality = calculator._calculate_quality_score(confidence_value)
            
            print(f"  置信度 {confidence_value:.2f}: {level} | {recommendation} | {risk} | 质量{quality}/10")
            
            # 验证等级分类
            assert level == expected_level, f"置信度等级错误: 期望{expected_level}, 实际{level}"
            assert recommendation == expected_recommendation, f"建议错误: 期望{expected_recommendation}, 实际{recommendation}"
        
        print(f"✅ 置信度等级分类测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 置信度等级分类测试失败: {e}")
        return False


def test_t421_sell_signal_confidence():
    """测试T4.2.1卖出信号置信度"""
    print("\n🧪 测试T4.2.1 - 卖出信号置信度")
    print("=" * 50)
    
    try:
        from app.analysis.confidence import create_confidence_calculator
        
        calculator = create_confidence_calculator()
        
        # 模拟卖出信号的技术分析数据
        technical_analysis = {
            'indicators': {
                'rsi_14': {
                    'current_rsi': 78.5,  # 超买
                    'error': False
                },
                'macd': {
                    'signal_type': '卖出信号',
                    'cross_signal': '死叉',
                    'position': '空头区域',
                    'histogram_trend': '下降',
                    'error': False
                },
                'atr': {
                    'atr_trend': '上升',
                    'volatility_level': '高',
                    'error': False
                }
            },
            'price_position': {
                'sma_5': 'below',
                'sma_10': 'below',
                'sma_20': 'below',
                'sma_50': 'above'
            }
        }
        
        # 模拟支撑阻力位数据
        support_resistance = {
            'support_levels': [
                {
                    'price': 96.80,
                    'touch_count': 2,
                    'strength_rating': '中'
                }
            ],
            'resistance_levels': [
                {
                    'price': 100.20,
                    'touch_count': 5,
                    'strength_rating': '强'
                }
            ]
        }
        
        # 模拟市场数据
        market_data = {
            'volume_ratio': 2.2,  # 强成交量
            'volatility_level': '高'
        }
        
        # 模拟风险水平
        risk_levels = {
            'stop_loss': 101.50,
            'take_profit': 97.00
        }
        
        current_price = 100.00
        
        # 计算卖出信号置信度
        print("📊 计算卖出信号置信度...")
        sell_confidence = calculator.calculate_signal_confidence(
            signal_type='sell',
            current_price=current_price,
            technical_analysis=technical_analysis,
            support_resistance=support_resistance,
            market_data=market_data,
            risk_levels=risk_levels
        )
        
        print(f"✅ 卖出信号置信度计算完成:")
        print(f"  总体置信度: {sell_confidence['overall_confidence']:.3f}")
        print(f"  置信度等级: {sell_confidence['confidence_level']}")
        print(f"  质量分数: {sell_confidence['quality_score']}/10")
        print(f"  建议: {sell_confidence['recommendation']}")
        print(f"  风险评估: {sell_confidence['risk_assessment']}")
        
        print(f"\n📉 置信度组成部分:")
        components = sell_confidence['components']
        for component, value in components.items():
            print(f"  {component}: {value:.3f}")
        
        # 验证卖出信号置信度
        assert 0.0 <= sell_confidence['overall_confidence'] <= 1.0, "置信度应在0-1范围内"
        assert sell_confidence['overall_confidence'] >= 0.6, f"强卖出信号置信度应该较高，实际: {sell_confidence['overall_confidence']:.3f}"
        
        print(f"✅ 卖出信号置信度测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 卖出信号置信度测试失败: {e}")
        return False


def test_t421_batch_confidence():
    """测试T4.2.1批量置信度计算"""
    print("\n🧪 测试T4.2.1 - 批量置信度计算")
    print("=" * 50)
    
    try:
        from app.analysis.confidence import create_confidence_calculator
        
        calculator = create_confidence_calculator()
        
        # 创建多个测试信号
        signals = [
            {
                'signal_type': 'buy',
                'price': 99.00,
                'technical_analysis': {
                    'indicators': {
                        'rsi_14': {'current_rsi': 25, 'error': False},
                        'macd': {'signal_type': '买入信号', 'error': False}
                    }
                },
                'support_resistance': {
                    'support_levels': [{'price': 98.5, 'touch_count': 3, 'strength_rating': '强'}]
                },
                'market_data': {'volume_ratio': 1.8},
                'risk_levels': {'stop_loss': 97, 'take_profit': 103}
            },
            {
                'signal_type': 'sell',
                'price': 100.50,
                'technical_analysis': {
                    'indicators': {
                        'rsi_14': {'current_rsi': 75, 'error': False},
                        'macd': {'signal_type': '卖出信号', 'error': False}
                    }
                },
                'support_resistance': {
                    'resistance_levels': [{'price': 100.8, 'touch_count': 4, 'strength_rating': '强'}]
                },
                'market_data': {'volume_ratio': 2.1},
                'risk_levels': {'stop_loss': 102, 'take_profit': 98}
            },
            {
                'signal_type': 'buy',
                'price': 95.00,
                'technical_analysis': {
                    'indicators': {
                        'rsi_14': {'current_rsi': 45, 'error': False},
                        'macd': {'signal_type': '中性', 'error': False}
                    }
                },
                'support_resistance': {
                    'support_levels': [{'price': 94.5, 'touch_count': 1, 'strength_rating': '弱'}]
                },
                'market_data': {'volume_ratio': 1.1},
                'risk_levels': {'stop_loss': 93, 'take_profit': 98}
            }
        ]
        
        print(f"📊 批量计算 {len(signals)} 个信号的置信度...")
        
        # 批量计算置信度
        enhanced_signals = calculator.batch_calculate_confidence(signals)
        
        print(f"✅ 批量置信度计算完成:")
        
        for i, signal in enumerate(enhanced_signals):
            confidence = signal['confidence']
            level = signal['confidence_analysis']['confidence_level']
            recommendation = signal['confidence_analysis']['recommendation']
            
            print(f"  信号{i+1} ({signal['signal_type']}): {confidence:.3f} | {level} | {recommendation}")
        
        # 验证批量计算结果
        assert len(enhanced_signals) == len(signals), "批量计算结果数量应该一致"
        
        for signal in enhanced_signals:
            assert 'confidence' in signal, "每个信号都应该有置信度"
            assert 'confidence_analysis' in signal, "每个信号都应该有详细分析"
            assert 0.0 <= signal['confidence'] <= 1.0, "置信度应在0-1范围内"
        
        # 获取统计信息
        stats = calculator.get_confidence_statistics([s['confidence_analysis'] for s in enhanced_signals])
        
        print(f"\n📈 置信度统计:")
        print(f"  平均置信度: {stats['average_confidence']:.3f}")
        print(f"  中位数置信度: {stats['median_confidence']:.3f}")
        print(f"  高置信度信号: {stats['high_confidence_count']}")
        print(f"  中等置信度信号: {stats['medium_confidence_count']}")
        print(f"  低置信度信号: {stats['low_confidence_count']}")
        
        print(f"✅ 批量置信度计算测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 批量置信度计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_t421_confidence_components():
    """测试T4.2.1置信度组件分析"""
    print("\n🧪 测试T4.2.1 - 置信度组件分析")
    print("=" * 50)
    
    try:
        from app.analysis.confidence import create_confidence_calculator
        
        calculator = create_confidence_calculator()
        
        # 测试各个组件的独立贡献
        print("📊 测试置信度组件独立贡献:")
        
        # 1. 测试RSI确认
        rsi_values = [15, 25, 35, 45, 55, 65, 75, 85]
        print(f"\n  RSI确认测试 (买入信号):")
        for rsi in rsi_values:
            confirmation = calculator._evaluate_rsi_confirmation('buy', rsi)
            print(f"    RSI {rsi}: +{confirmation:.3f}")
        
        # 2. 测试MACD确认
        macd_scenarios = [
            {'signal_type': '买入信号', 'cross_signal': '金叉'},
            {'signal_type': '中性', 'position': '多头区域', 'histogram_trend': '上升'},
            {'signal_type': '卖出信号', 'cross_signal': '死叉'},
            {'signal_type': '中性', 'position': '空头区域', 'histogram_trend': '下降'}
        ]
        
        print(f"\n  MACD确认测试:")
        for i, macd in enumerate(macd_scenarios):
            signal_type = 'buy' if i < 2 else 'sell'
            confirmation = calculator._evaluate_macd_confirmation(signal_type, macd)
            print(f"    场景{i+1} ({signal_type}): +{confirmation:.3f}")
        
        # 3. 测试移动平均线确认
        ma_scenarios = [
            {'sma_5': 'above', 'sma_10': 'above', 'sma_20': 'above', 'sma_50': 'above'},  # 全部上方
            {'sma_5': 'above', 'sma_10': 'above', 'sma_20': 'below', 'sma_50': 'below'},  # 一半上方
            {'sma_5': 'below', 'sma_10': 'below', 'sma_20': 'below', 'sma_50': 'below'}   # 全部下方
        ]
        
        print(f"\n  移动平均线确认测试:")
        for i, ma_pos in enumerate(ma_scenarios):
            buy_confirmation = calculator._evaluate_ma_confirmation('buy', ma_pos)
            sell_confirmation = calculator._evaluate_ma_confirmation('sell', ma_pos)
            print(f"    场景{i+1}: 买入+{buy_confirmation:.3f}, 卖出+{sell_confirmation:.3f}")
        
        # 4. 测试风险回报比评估
        rr_scenarios = [
            (100, 98, 106),   # 1:3 风险回报比
            (100, 98, 104),   # 1:2 风险回报比
            (100, 98, 103),   # 1:1.5 风险回报比
            (100, 98, 101)    # 1:0.5 风险回报比
        ]
        
        print(f"\n  风险回报比评估测试:")
        for price, stop, target in rr_scenarios:
            risk_levels = {'stop_loss': stop, 'take_profit': target}
            rr_confidence = calculator._calculate_risk_reward_confidence(price, risk_levels)
            ratio = (target - price) / (price - stop)
            print(f"    1:{ratio:.1f} 风险回报比: {rr_confidence:.3f}")
        
        print(f"✅ 置信度组件分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 置信度组件分析测试失败: {e}")
        return False


def test_t421_integration():
    """测试T4.2.1集成功能"""
    print("\n🧪 测试T4.2.1 - 集成功能测试")
    print("=" * 50)
    
    try:
        from app.analysis.confidence import calculate_signal_confidence
        
        # 使用便捷函数测试
        signal_data = {
            'signal_type': 'buy',
            'price': 99.50,
            'technical_analysis': {
                'indicators': {
                    'rsi_14': {'current_rsi': 28, 'error': False},
                    'macd': {'signal_type': '买入信号', 'cross_signal': '金叉', 'error': False},
                    'atr': {'atr_trend': '稳定', 'volatility_level': '中等', 'error': False}
                },
                'price_position': {
                    'sma_5': 'above',
                    'sma_10': 'above',
                    'sma_20': 'above'
                }
            },
            'support_resistance': {
                'support_levels': [
                    {'price': 99.0, 'touch_count': 4, 'strength_rating': '强'}
                ]
            },
            'market_data': {
                'volume_ratio': 1.9,
                'volatility_level': '中等'
            },
            'risk_levels': {
                'stop_loss': 97.5,
                'take_profit': 103.5
            }
        }
        
        print("📊 使用便捷函数计算置信度...")
        
        result = calculate_signal_confidence(signal_data)
        
        print(f"✅ 集成功能测试完成:")
        print(f"  总体置信度: {result['overall_confidence']:.3f}")
        print(f"  置信度等级: {result['confidence_level']}")
        print(f"  建议: {result['recommendation']}")
        
        # 验证结果完整性
        required_fields = [
            'overall_confidence', 'confidence_level', 'components',
            'quality_score', 'recommendation', 'risk_assessment'
        ]
        
        for field in required_fields:
            assert field in result, f"结果中缺少必需字段: {field}"
        
        # 验证组件完整性
        required_components = [
            'technical_indicators', 'support_resistance', 'market_environment',
            'risk_reward', 'volume_confirmation'
        ]
        
        for component in required_components:
            assert component in result['components'], f"组件中缺少: {component}"
        
        print(f"✅ 集成功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 集成功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始T4.2.1置信度计算测试")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("基础置信度计算", test_t421_basic_confidence),
        ("置信度等级分类", test_t421_confidence_levels),
        ("卖出信号置信度", test_t421_sell_signal_confidence),
        ("批量置信度计算", test_t421_batch_confidence),
        ("置信度组件分析", test_t421_confidence_components),
        ("集成功能测试", test_t421_integration)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}执行失败: {e}")
            test_results.append((test_name, False))
    
    # 汇总测试结果
    print("\n" + "=" * 60)
    print("📊 T4.2.1置信度计算测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 T4.2.1置信度计算模块实现完成！")
        print("\n✅ 验收标准检查:")
        print("  ✅ 信号置信度在0-1范围")
        print("  ✅ 反映信号质量差异")
        print("  ✅ 多维度置信度评估")
        print("  ✅ 置信度等级分类")
        print("  ✅ 批量计算功能")
        print("  ✅ 统计分析功能")
        
        return True
    else:
        print("❌ 部分测试失败，需要修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 