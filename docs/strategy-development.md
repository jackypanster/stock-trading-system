# 策略开发指南

## 1. 策略开发概述

### 1.1 设计理念
美股日内套利助手支持自定义策略开发，让用户能够基于自己的投资理念创建专属的交易策略。

**核心特点：**
- **模块化设计**：策略、指标、信号生成完全解耦
- **日内聚焦**：专为美股日内交易优化
- **风险优先**：内置风险控制和回测验证
- **简单易用**：最小化配置，最大化效果

### 1.2 策略分类

**内置策略类型：**
- **支撑阻力策略**：基于关键价位的反转交易
- **动量策略**：捕捉价格突破和趋势跟随
- **均值回归策略**：利用价格偏离均值的回归机会
- **成交量确认策略**：结合成交量分析的信号增强

**适用场景：**
- 高波动美股（TSLA, NVDA, META等）
- 日内套利（开盘到收盘）
- 个人投资者资金规模
- 非高频交易策略

## 2. 策略架构

### 2.1 核心接口设计

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

class BaseStrategy(ABC):
    """策略基类 - 所有自定义策略的父类"""
    
    def __init__(self, symbol: str, config: Dict):
        self.symbol = symbol
        self.config = config
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        
    @abstractmethod
    def analyze(self, market_data: pd.DataFrame) -> Dict:
        """
        核心分析方法
        
        Args:
            market_data: 包含OHLCV数据的DataFrame
            
        Returns:
            分析结果字典，包含指标和信号
        """
        pass
        
    @abstractmethod
    def get_required_history_days(self) -> int:
        """返回策略需要的历史数据天数"""
        pass
        
    def validate_config(self) -> tuple[bool, str]:
        """
        验证策略配置
        
        Returns:
            (是否有效, 错误信息)
        """
        required_fields = ['risk', 'technical']
        for field in required_fields:
            if field not in self.config:
                return False, f"缺少必需配置项: {field}"
        return True, ""
        
    def get_risk_parameters(self) -> Dict:
        """获取风险控制参数"""
        return {
            'max_position_pct': self.config.get('risk', {}).get('max_position_pct', 0.15),
            'stop_loss_pct': self.config.get('risk', {}).get('stop_loss_pct', 0.02),
            'take_profit_pct': self.config.get('risk', {}).get('take_profit_pct', 0.05),
            'max_daily_trades': self.config.get('risk', {}).get('max_daily_trades', 3)
        }
```

### 2.2 信号数据结构

```python
from dataclasses import dataclass
from enum import Enum

class SignalAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalStrength(Enum):
    WEAK = "WEAK"        # 置信度 < 0.6
    MODERATE = "MODERATE" # 置信度 0.6-0.8
    STRONG = "STRONG"     # 置信度 > 0.8

@dataclass
class TradingSignal:
    """交易信号标准格式"""
    timestamp: datetime
    symbol: str
    action: SignalAction
    entry_price: float
    target_shares: int
    confidence: float  # 0.0 - 1.0
    strength: SignalStrength
    reason: str
    strategy_name: str
    
    # 风险控制
    stop_loss: float
    take_profit: float
    
    # 元数据
    indicators: Dict = None
    market_condition: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'action': self.action.value,
            'entry_price': self.entry_price,
            'target_shares': self.target_shares,
            'confidence': self.confidence,
            'strength': self.strength.value,
            'reason': self.reason,
            'strategy_name': self.strategy_name,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'indicators': self.indicators or {},
            'market_condition': self.market_condition
        }
```

## 3. 策略开发实例

### 3.1 简单支撑阻力策略

```python
class SupportResistanceStrategy(BaseStrategy):
    """
    支撑阻力位策略 - 适合日内交易
    
    策略逻辑：
    1. 识别近期支撑阻力位
    2. 价格接近支撑位时寻找买入机会
    3. 价格接近阻力位时寻找卖出机会
    4. 结合RSI和成交量确认
    """
    
    def __init__(self, symbol: str, config: Dict):
        super().__init__(symbol, config)
        self.lookback_days = config.get('technical', {}).get('lookback_days', 20)
        self.level_tolerance = config.get('technical', {}).get('level_tolerance', 0.01)
        self.rsi_period = config.get('technical', {}).get('rsi_period', 14)
        
    def get_required_history_days(self) -> int:
        return max(self.lookback_days, self.rsi_period) + 5
        
    def analyze(self, market_data: pd.DataFrame) -> Dict:
        """执行支撑阻力分析"""
        
        # 1. 计算技术指标
        indicators = self._calculate_indicators(market_data)
        
        # 2. 识别支撑阻力位
        levels = self._identify_support_resistance(market_data)
        
        # 3. 生成交易信号
        signals = self._generate_signals(market_data, indicators, levels)
        
        # 4. 市场状态评估
        market_condition = self._assess_market_condition(indicators)
        
        return {
            'indicators': indicators,
            'support_resistance': levels,
            'signals': [signal.to_dict() for signal in signals],
            'market_condition': market_condition,
            'analysis_time': datetime.now().isoformat()
        }
        
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """计算技术指标"""
        # RSI计算
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # ATR计算（平均真实范围）
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean()
        
        # 成交量分析
        volume_sma = data['volume'].rolling(window=20).mean()
        volume_ratio = data['volume'].iloc[-1] / volume_sma.iloc[-1]
        
        return {
            'current_price': data['close'].iloc[-1],
            'rsi': rsi.iloc[-1],
            'atr': atr.iloc[-1],
            'volume_ratio': volume_ratio,
            'price_change_pct': (data['close'].iloc[-1] - data['close'].iloc[-2]) / data['close'].iloc[-2],
            'intraday_range_pct': (data['high'].iloc[-1] - data['low'].iloc[-1]) / data['open'].iloc[-1]
        }
        
    def _identify_support_resistance(self, data: pd.DataFrame) -> Dict:
        """识别支撑阻力位"""
        recent_data = data.tail(self.lookback_days)
        
        # 寻找局部高点和低点
        highs = []
        lows = []
        
        for i in range(2, len(recent_data) - 2):
            # 局部高点
            if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and 
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1] and
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i-2] and
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+2]):
                highs.append(recent_data['high'].iloc[i])
                
            # 局部低点
            if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and 
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1] and
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i-2] and
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+2]):
                lows.append(recent_data['low'].iloc[i])
        
        # 聚类相近的价位
        resistance_levels = self._cluster_levels(highs)
        support_levels = self._cluster_levels(lows)
        
        current_price = data['close'].iloc[-1]
        
        return {
            'support_levels': sorted([level for level in support_levels if level < current_price]),
            'resistance_levels': sorted([level for level in resistance_levels if level > current_price]),
            'nearest_support': max([level for level in support_levels if level < current_price], default=None),
            'nearest_resistance': min([level for level in resistance_levels if level > current_price], default=None)
        }
        
    def _cluster_levels(self, levels: List[float]) -> List[float]:
        """聚类相近的价位"""
        if not levels:
            return []
            
        levels = sorted(levels)
        clustered = [levels[0]]
        
        for level in levels[1:]:
            # 如果与最近的聚类中心距离超过阈值，创建新聚类
            if abs(level - clustered[-1]) / clustered[-1] > self.level_tolerance:
                clustered.append(level)
            else:
                # 否则更新聚类中心为平均值
                clustered[-1] = (clustered[-1] + level) / 2
                
        return clustered
        
    def _generate_signals(self, data: pd.DataFrame, indicators: Dict, levels: Dict) -> List[TradingSignal]:
        """生成交易信号"""
        signals = []
        current_price = indicators['current_price']
        risk_params = self.get_risk_parameters()
        
        # 支撑位买入信号
        if levels['nearest_support']:
            distance_to_support = (current_price - levels['nearest_support']) / current_price
            
            if distance_to_support <= 0.01:  # 接近支撑位（1%以内）
                # 多重确认
                rsi_oversold = indicators['rsi'] < 35
                volume_confirmation = indicators['volume_ratio'] > 1.2
                
                confidence = 0.5  # 基础置信度
                if rsi_oversold:
                    confidence += 0.2
                if volume_confirmation:
                    confidence += 0.15
                    
                reason_parts = ["接近支撑位"]
                if rsi_oversold:
                    reason_parts.append("RSI超卖")
                if volume_confirmation:
                    reason_parts.append("成交量放大")
                    
                if confidence >= 0.6:  # 最小置信度
                    signals.append(TradingSignal(
                        timestamp=datetime.now(),
                        symbol=self.symbol,
                        action=SignalAction.BUY,
                        entry_price=current_price,
                        target_shares=self._calculate_position_size(current_price),
                        confidence=min(confidence, 0.95),
                        strength=self._get_signal_strength(confidence),
                        reason=" + ".join(reason_parts),
                        strategy_name=self.name,
                        stop_loss=current_price * (1 - risk_params['stop_loss_pct']),
                        take_profit=current_price * (1 + risk_params['take_profit_pct']),
                        indicators=indicators,
                        market_condition=self._assess_market_condition(indicators)
                    ))
        
        # 阻力位卖出信号
        if levels['nearest_resistance']:
            distance_to_resistance = (levels['nearest_resistance'] - current_price) / current_price
            
            if distance_to_resistance <= 0.01:  # 接近阻力位
                rsi_overbought = indicators['rsi'] > 70
                volume_confirmation = indicators['volume_ratio'] > 1.2
                
                confidence = 0.5
                if rsi_overbought:
                    confidence += 0.2
                if volume_confirmation:
                    confidence += 0.15
                    
                reason_parts = ["接近阻力位"]
                if rsi_overbought:
                    reason_parts.append("RSI超买")
                if volume_confirmation:
                    reason_parts.append("成交量放大")
                    
                if confidence >= 0.6:
                    signals.append(TradingSignal(
                        timestamp=datetime.now(),
                        symbol=self.symbol,
                        action=SignalAction.SELL,
                        entry_price=current_price,
                        target_shares=0,  # 卖出信号不指定数量
                        confidence=min(confidence, 0.95),
                        strength=self._get_signal_strength(confidence),
                        reason=" + ".join(reason_parts),
                        strategy_name=self.name,
                        stop_loss=current_price * (1 + risk_params['stop_loss_pct']),
                        take_profit=current_price * (1 - risk_params['take_profit_pct']),
                        indicators=indicators,
                        market_condition=self._assess_market_condition(indicators)
                    ))
                    
        return signals
        
    def _calculate_position_size(self, price: float) -> int:
        """计算建议仓位大小"""
        risk_params = self.get_risk_parameters()
        max_investment = 10000 * risk_params['max_position_pct']  # 假设总资金10万
        shares = int(max_investment / price)
        return max(shares, 1)  # 至少1股
        
    def _get_signal_strength(self, confidence: float) -> SignalStrength:
        """根据置信度确定信号强度"""
        if confidence < 0.6:
            return SignalStrength.WEAK
        elif confidence < 0.8:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.STRONG
            
    def _assess_market_condition(self, indicators: Dict) -> str:
        """评估市场状态"""
        rsi = indicators['rsi']
        volume_ratio = indicators['volume_ratio']
        price_change = indicators['price_change_pct']
        
        conditions = []
        
        if rsi > 70:
            conditions.append("超买")
        elif rsi < 30:
            conditions.append("超卖")
        else:
            conditions.append("中性")
            
        if volume_ratio > 1.5:
            conditions.append("成交活跃")
        elif volume_ratio < 0.7:
            conditions.append("成交清淡")
            
        if abs(price_change) > 0.02:
            conditions.append("高波动")
            
        return " | ".join(conditions)
```

### 3.2 动量突破策略

```python
class MomentumBreakoutStrategy(BaseStrategy):
    """
    动量突破策略 - 捕捉价格突破
    
    策略逻辑：
    1. 监控价格突破关键阻力位
    2. 成交量确认突破有效性
    3. 动量指标确认趋势强度
    4. 快速止盈止损
    """
    
    def __init__(self, symbol: str, config: Dict):
        super().__init__(symbol, config)
        self.breakout_period = config.get('technical', {}).get('breakout_period', 10)
        self.volume_threshold = config.get('technical', {}).get('volume_threshold', 1.5)
        
    def get_required_history_days(self) -> int:
        return self.breakout_period + 10
        
    def analyze(self, market_data: pd.DataFrame) -> Dict:
        """执行动量突破分析"""
        
        # 计算突破位
        breakout_high = market_data['high'].rolling(window=self.breakout_period).max().iloc[-2]  # 前一天的最高点
        breakout_low = market_data['low'].rolling(window=self.breakout_period).min().iloc[-2]   # 前一天的最低点
        
        current_price = market_data['close'].iloc[-1]
        current_volume = market_data['volume'].iloc[-1]
        avg_volume = market_data['volume'].rolling(window=20).mean().iloc[-1]
        
        # 突破检测
        upward_breakout = current_price > breakout_high
        downward_breakout = current_price < breakout_low
        volume_confirmed = current_volume > avg_volume * self.volume_threshold
        
        signals = []
        
        if upward_breakout and volume_confirmed:
            risk_params = self.get_risk_parameters()
            signals.append(TradingSignal(
                timestamp=datetime.now(),
                symbol=self.symbol,
                action=SignalAction.BUY,
                entry_price=current_price,
                target_shares=self._calculate_position_size(current_price),
                confidence=0.8,
                strength=SignalStrength.STRONG,
                reason=f"向上突破 {breakout_high:.2f}，成交量确认",
                strategy_name=self.name,
                stop_loss=breakout_high * 0.98,  # 突破位下方2%止损
                take_profit=current_price * (1 + risk_params['take_profit_pct'] * 1.5),  # 更大止盈
                market_condition="突破上涨"
            ))
            
        return {
            'breakout_levels': {
                'resistance': breakout_high,
                'support': breakout_low
            },
            'volume_analysis': {
                'current': current_volume,
                'average': avg_volume,
                'ratio': current_volume / avg_volume
            },
            'signals': [signal.to_dict() for signal in signals],
            'market_condition': "突破" if (upward_breakout or downward_breakout) else "整理"
        }
        
    def _calculate_position_size(self, price: float) -> int:
        """动量策略使用较小仓位"""
        risk_params = self.get_risk_parameters()
        max_investment = 10000 * risk_params['max_position_pct'] * 0.8  # 80%的正常仓位
        shares = int(max_investment / price)
        return max(shares, 1)
```

## 4. 策略配置

### 4.1 配置文件结构

每个策略都需要对应的YAML配置文件，放置在 `config/strategies/` 目录下：

```yaml
# config/strategies/support_resistance_TSLA.yaml
strategy:
  name: "SupportResistanceStrategy"
  symbol: "TSLA"
  active: true
  
  # 技术参数
  technical:
    lookback_days: 20
    level_tolerance: 0.01
    rsi_period: 14
    volume_confirmation: true
    
  # 信号参数
  signals:
    min_confidence: 0.6
    max_signals_per_day: 3
    
  # 风险控制
  risk:
    max_position_pct: 0.15
    stop_loss_pct: 0.02
    take_profit_pct: 0.05
    max_daily_trades: 3
    max_consecutive_losses: 2
    
  # 回测参数
  backtest:
    start_date: "2023-01-01"
    initial_capital: 10000
    commission_rate: 0.001
```

### 4.2 策略管理命令

```bash
# 查看所有策略
python main.py strategies list

# 激活策略
python main.py strategies activate support_resistance_TSLA

# 停用策略
python main.py strategies deactivate momentum_breakout_NVDA

# 测试策略配置
python main.py strategies test support_resistance_TSLA

# 策略回测
python main.py strategies backtest support_resistance_TSLA --days 30
```

## 5. 策略测试

### 5.1 单元测试

```python
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class TestSupportResistanceStrategy(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        self.config = {
            'technical': {
                'lookback_days': 10,
                'level_tolerance': 0.01,
                'rsi_period': 14
            },
            'risk': {
                'max_position_pct': 0.15,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.05
            }
        }
        self.strategy = SupportResistanceStrategy('TEST', self.config)
        
        # 创建测试数据
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(30) * 0.5)
        
        self.test_data = pd.DataFrame({
            'open': prices + np.random.randn(30) * 0.1,
            'high': prices + np.abs(np.random.randn(30)) * 0.5,
            'low': prices - np.abs(np.random.randn(30)) * 0.5,
            'close': prices,
            'volume': np.random.randint(1000000, 2000000, 30)
        }, index=dates)
        
    def test_indicator_calculation(self):
        """测试指标计算"""
        indicators = self.strategy._calculate_indicators(self.test_data)
        
        self.assertIn('current_price', indicators)
        self.assertIn('rsi', indicators)
        self.assertIn('atr', indicators)
        self.assertTrue(0 <= indicators['rsi'] <= 100)
        self.assertTrue(indicators['atr'] > 0)
        
    def test_support_resistance_identification(self):
        """测试支撑阻力位识别"""
        levels = self.strategy._identify_support_resistance(self.test_data)
        
        self.assertIn('support_levels', levels)
        self.assertIn('resistance_levels', levels)
        self.assertIsInstance(levels['support_levels'], list)
        self.assertIsInstance(levels['resistance_levels'], list)
        
    def test_signal_generation(self):
        """测试信号生成"""
        result = self.strategy.analyze(self.test_data)
        
        self.assertIn('signals', result)
        self.assertIn('indicators', result)
        self.assertIn('market_condition', result)
        
        # 检查信号格式
        for signal_dict in result['signals']:
            self.assertIn('action', signal_dict)
            self.assertIn('confidence', signal_dict)
            self.assertIn('stop_loss', signal_dict)
            self.assertTrue(0 <= signal_dict['confidence'] <= 1)

if __name__ == '__main__':
    unittest.main()
```

### 5.2 回测验证

```python
class StrategyBacktester:
    """策略回测工具"""
    
    def __init__(self, strategy: BaseStrategy, initial_capital: float = 10000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        
    def run_backtest(self, historical_data: pd.DataFrame) -> Dict:
        """运行回测"""
        daily_returns = []
        
        for i in range(self.strategy.get_required_history_days(), len(historical_data)):
            # 获取当前分析需要的数据
            current_data = historical_data.iloc[:i+1]
            
            # 执行策略分析
            analysis_result = self.strategy.analyze(current_data)
            
            # 处理信号
            for signal_dict in analysis_result['signals']:
                signal = TradingSignal(**signal_dict)
                self._execute_signal(signal, current_data.iloc[i])
                
            # 计算当日收益
            daily_return = self._calculate_daily_return(current_data.iloc[i])
            daily_returns.append(daily_return)
            
        # 计算回测指标
        return self._calculate_backtest_metrics(daily_returns)
        
    def _execute_signal(self, signal: TradingSignal, market_data: pd.Series):
        """执行交易信号"""
        if signal.action == SignalAction.BUY and signal.symbol not in self.positions:
            cost = signal.target_shares * signal.entry_price
            if cost <= self.current_capital * 0.95:  # 保留5%现金
                self.positions[signal.symbol] = {
                    'shares': signal.target_shares,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit
                }
                self.current_capital -= cost
                self.trades.append({
                    'action': 'BUY',
                    'symbol': signal.symbol,
                    'shares': signal.target_shares,
                    'price': signal.entry_price,
                    'timestamp': signal.timestamp
                })
                
    def _calculate_backtest_metrics(self, daily_returns: List[float]) -> Dict:
        """计算回测指标"""
        total_return = (self.current_capital / self.initial_capital) - 1
        
        if len(daily_returns) > 0:
            avg_daily_return = np.mean(daily_returns)
            volatility = np.std(daily_returns)
            sharpe_ratio = avg_daily_return / volatility if volatility > 0 else 0
        else:
            avg_daily_return = volatility = sharpe_ratio = 0
            
        return {
            'total_return': total_return,
            'avg_daily_return': avg_daily_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(self.trades),
            'final_capital': self.current_capital
        }
```

## 6. 策略部署

### 6.1 策略注册

```python
# app/strategies/registry.py
class StrategyRegistry:
    """策略注册表"""
    
    _strategies = {}
    
    @classmethod
    def register(cls, strategy_class: type):
        """注册策略"""
        cls._strategies[strategy_class.__name__] = strategy_class
        
    @classmethod
    def get_strategy(cls, name: str) -> type:
        """获取策略类"""
        return cls._strategies.get(name)
        
    @classmethod
    def list_strategies(cls) -> List[str]:
        """列出所有已注册策略"""
        return list(cls._strategies.keys())

# 注册内置策略
StrategyRegistry.register(SupportResistanceStrategy)
StrategyRegistry.register(MomentumBreakoutStrategy)
```

### 6.2 生产环境使用

```bash
# 部署新策略
python main.py strategies deploy custom_strategy.py

# 验证策略
python main.py strategies validate custom_strategy

# 生产运行
python main.py --strategy custom_strategy --symbol TSLA --monitor
```

## 7. 最佳实践

### 7.1 策略设计原则

1. **简单有效**：避免过度复杂化
2. **风险优先**：先考虑风险控制，再考虑收益
3. **参数化**：关键参数可配置
4. **可测试**：支持回测和单元测试
5. **可解释**：信号生成逻辑清晰

### 7.2 性能优化

```python
# 使用缓存避免重复计算
from functools import lru_cache

class OptimizedStrategy(BaseStrategy):
    
    @lru_cache(maxsize=100)
    def _calculate_rsi(self, close_data_hash: int, period: int) -> float:
        """缓存RSI计算结果"""
        # RSI计算逻辑
        pass
        
    def _get_data_hash(self, data: pd.Series) -> int:
        """生成数据哈希用于缓存"""
        return hash(tuple(data.values))
```

### 7.3 错误处理

```python
class RobustStrategy(BaseStrategy):
    
    def analyze(self, market_data: pd.DataFrame) -> Dict:
        try:
            # 数据验证
            if len(market_data) < self.get_required_history_days():
                raise ValueError("历史数据不足")
                
            # 策略分析
            result = self._perform_analysis(market_data)
            
            # 结果验证
            self._validate_result(result)
            
            return result
            
        except Exception as e:
            # 记录错误并返回安全的默认值
            logger.error(f"策略分析失败: {e}")
            return {
                'signals': [],
                'error': str(e),
                'market_condition': 'ERROR'
            }
            
    def _validate_result(self, result: Dict):
        """验证分析结果"""
        required_keys = ['signals', 'indicators', 'market_condition']
        for key in required_keys:
            if key not in result:
                raise ValueError(f"缺少必需结果项: {key}")
```

## 8. 常见问题

### 8.1 Q&A

**Q: 如何处理股票停牌或数据缺失？**
A: 在策略中检查数据完整性，缺失数据时返回空信号：

```python
def analyze(self, market_data: pd.DataFrame) -> Dict:
    # 检查数据完整性
    if market_data.isnull().any().any():
        return {'signals': [], 'error': '数据缺失'}
    
    # 检查是否有交易
    if market_data['volume'].iloc[-1] == 0:
        return {'signals': [], 'error': '无交易量'}
```

**Q: 如何避免过拟合？**
A: 使用滚动窗口回测，避免使用未来数据：

```python
# 错误：使用了未来数据
resistance = data['high'].max()  # 包含未来最高价

# 正确：只使用历史数据
resistance = data['high'].iloc[:-1].rolling(window=20).max().iloc[-1]
```

**Q: 如何处理盘前盘后交易？**
A: 配置交易时间窗口，过滤非交易时段信号：

```python
def _is_trading_hours(self, timestamp: datetime) -> bool:
    """检查是否在交易时间"""
    trading_start = timestamp.replace(hour=9, minute=30, second=0)
    trading_end = timestamp.replace(hour=16, minute=0, second=0)
    return trading_start <= timestamp <= trading_end
```

通过这个完整的策略开发指南，用户可以基于美股日内套利的特点开发个性化的交易策略，同时确保代码质量和风险控制！