# 详细设计文档

## 1. 设计概述

本文档基于[简化架构设计](simplified-architecture.md)，详细描述美股日内套利助手的具体实现设计，包括核心类设计、算法实现、数据模型等。

## 2. 核心类设计

### 2.1 主应用控制器

```python
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import logging

class TradingAssistant:
    """
    主应用控制器
    负责协调所有模块，提供统一的应用入口
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_loader = ConfigLoader(config_dir)
        self.market_data = MarketDataManager(self.config_loader.system_config)
        self.analyzer = TechnicalAnalyzer()
        self.signal_gen = SignalGenerator()
        self.risk_mgr = RiskManager(self.config_loader.system_config)
        self.portfolio = Portfolio()
        self.logger = logging.getLogger(__name__)
        
    async def analyze_stock(self, symbol: str) -> Dict:
        """分析单只股票"""
        try:
            # 加载股票配置
            config = self.config_loader.load_stock_config(symbol)
            
            # 获取市场数据
            current_price = await self.market_data.get_current_price(symbol)
            historical_data = await self.market_data.get_historical_data(
                symbol, config['strategy']['technical']['lookback_days']
            )
            
            # 技术分析
            indicators = self.analyzer.calculate_indicators(historical_data, config)
            
            # 生成信号
            signals = self.signal_gen.generate_signals(symbol, indicators, current_price, config)
            
            # 风险检查
            validated_signals = []
            for signal in signals:
                if self.risk_mgr.validate_signal(signal, self.portfolio, config):
                    validated_signals.append(signal)
                    
            return {
                'symbol': symbol,
                'current_price': current_price,
                'indicators': indicators,
                'signals': validated_signals,
                'timestamp': datetime.now(),
                'config': config
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def run_analysis_cycle(self, symbols: List[str]) -> List[Dict]:
        """运行完整分析周期"""
        results = []
        for symbol in symbols:
            result = await self.analyze_stock(symbol)
            results.append(result)
        return results
        
    def start_monitoring(self, symbols: List[str], interval: int = 300):
        """开始实时监控"""
        async def monitor_loop():
            while True:
                results = await self.run_analysis_cycle(symbols)
                self._process_results(results)
                await asyncio.sleep(interval)
                
        asyncio.run(monitor_loop())
```

### 2.2 市场数据管理器

```python
import yfinance as yf
import pandas as pd
from typing import Dict, Optional
import aiohttp
import asyncio

class MarketDataManager:
    """
    市场数据管理器
    支持多数据源，自动切换和缓存
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}
        self.cache_ttl = config.get('cache', {}).get('price_cache_ttl', 60)
        
    async def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        # 检查缓存
        cache_key = f"price_{symbol}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
            
        try:
            # 主数据源：yfinance
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            if not data.empty:
                price = float(data['Close'].iloc[-1])
                self._cache_data(cache_key, price)
                return price
                
        except Exception as e:
            logging.warning(f"Primary data source failed for {symbol}: {e}")
            
        try:
            # 备用数据源：Alpha Vantage
            price = await self._get_price_from_alpha_vantage(symbol)
            if price:
                self._cache_data(cache_key, price)
                return price
                
        except Exception as e:
            logging.error(f"Backup data source failed for {symbol}: {e}")
            
        raise Exception(f"Failed to get price for {symbol}")
        
    async def get_historical_data(self, symbol: str, days: int) -> pd.DataFrame:
        """获取历史数据"""
        cache_key = f"history_{symbol}_{days}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
            
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f'{days}d')
            
            if not data.empty:
                # 标准化列名
                data = data.rename(columns={
                    'Open': 'open',
                    'High': 'high', 
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                
                self._cache_data(cache_key, data, ttl=300)  # 5分钟缓存
                return data
                
        except Exception as e:
            logging.error(f"Failed to get historical data for {symbol}: {e}")
            
        return pd.DataFrame()
        
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        return (datetime.now() - self.cache[key]['timestamp']).seconds < self.cache_ttl
        
    def _cache_data(self, key: str, data, ttl: Optional[int] = None):
        """缓存数据"""
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now(),
            'ttl': ttl or self.cache_ttl
        }
```

### 2.3 技术分析器

```python
import pandas as pd
import numpy as np
from typing import Dict, List
import talib

class TechnicalAnalyzer:
    """
    技术分析器
    计算各种技术指标和支撑阻力位
    """
    
    def calculate_indicators(self, data: pd.DataFrame, config: Dict) -> Dict:
        """计算所有技术指标"""
        if data.empty or len(data) < 20:
            return {}
            
        indicators = {}
        tech_config = config.get('strategy', {}).get('technical', {})
        
        # 基础价格指标
        indicators.update(self._calculate_price_indicators(data))
        
        # 技术指标
        indicators.update(self._calculate_technical_indicators(data, tech_config))
        
        # 支撑阻力位
        indicators.update(self._calculate_support_resistance(data, tech_config))
        
        # 波动率指标
        indicators.update(self._calculate_volatility_indicators(data))
        
        return indicators
        
    def _calculate_price_indicators(self, data: pd.DataFrame) -> Dict:
        """计算价格相关指标"""
        current_price = data['close'].iloc[-1]
        prev_close = data['close'].iloc[-2] if len(data) > 1 else current_price
        
        return {
            'current_price': current_price,
            'prev_close': prev_close,
            'price_change': current_price - prev_close,
            'price_change_pct': (current_price - prev_close) / prev_close,
            'high_24h': data['high'].tail(24).max() if len(data) >= 24 else data['high'].max(),
            'low_24h': data['low'].tail(24).min() if len(data) >= 24 else data['low'].min(),
        }
        
    def _calculate_technical_indicators(self, data: pd.DataFrame, config: Dict) -> Dict:
        """计算技术指标"""
        indicators = {}
        
        # RSI
        rsi_period = config.get('indicators', {}).get('rsi_period', 14)
        if len(data) >= rsi_period:
            indicators['rsi'] = talib.RSI(data['close'], timeperiod=rsi_period).iloc[-1]
            
        # MACD
        macd_config = config.get('indicators', {})
        fast = macd_config.get('macd_fast', 12)
        slow = macd_config.get('macd_slow', 26)
        signal = macd_config.get('macd_signal', 9)
        
        if len(data) >= slow:
            macd, macd_signal, macd_hist = talib.MACD(
                data['close'], fastperiod=fast, slowperiod=slow, signalperiod=signal
            )
            indicators['macd'] = {
                'macd': macd.iloc[-1],
                'signal': macd_signal.iloc[-1],
                'histogram': macd_hist.iloc[-1]
            }
            
        # 移动平均线
        for period in [5, 10, 20, 50]:
            if len(data) >= period:
                indicators[f'sma_{period}'] = data['close'].rolling(window=period).mean().iloc[-1]
                
        return indicators
        
    def _calculate_support_resistance(self, data: pd.DataFrame, config: Dict) -> Dict:
        """计算支撑阻力位"""
        sr_config = config.get('support_resistance', {})
        window = sr_config.get('window', 20)
        min_touches = sr_config.get('min_touches', 2)
        tolerance = sr_config.get('tolerance', 0.01)
        
        if len(data) < window * 2:
            return {'support_levels': [], 'resistance_levels': []}
            
        # 使用局部极值方法
        highs = data['high'].values
        lows = data['low'].values
        
        # 找局部最大值（阻力位）
        resistance_indices = []
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i-window:i+window+1]):
                resistance_indices.append(i)
                
        # 找局部最小值（支撑位）
        support_indices = []
        for i in range(window, len(lows) - window):
            if lows[i] == min(lows[i-window:i+window+1]):
                support_indices.append(i)
                
        # 聚类相近的价位
        resistance_levels = self._cluster_levels(
            [highs[i] for i in resistance_indices], tolerance
        )
        support_levels = self._cluster_levels(
            [lows[i] for i in support_indices], tolerance
        )
        
        return {
            'support_levels': sorted(support_levels)[-3:],  # 最近的3个支撑位
            'resistance_levels': sorted(resistance_levels)[:3]  # 最近的3个阻力位
        }
        
    def _cluster_levels(self, levels: List[float], tolerance: float) -> List[float]:
        """聚类相近的价位"""
        if not levels:
            return []
            
        clustered = []
        sorted_levels = sorted(levels)
        
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                current_cluster.append(level)
            else:
                # 完成当前聚类，取平均值
                clustered.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]
                
        # 添加最后一个聚类
        if current_cluster:
            clustered.append(sum(current_cluster) / len(current_cluster))
            
        return clustered
        
    def _calculate_volatility_indicators(self, data: pd.DataFrame) -> Dict:
        """计算波动率指标"""
        if len(data) < 20:
            return {}
            
        # ATR (Average True Range)
        atr = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
        
        # 历史波动率
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        
        return {
            'atr': atr.iloc[-1] if not atr.empty else 0,
            'volatility_annual': volatility,
            'volatility_daily': returns.std()
        }
```

### 2.4 信号生成器

```python
from typing import List, Dict
from datetime import datetime
from app.models.signal import Signal

class SignalGenerator:
    """
    信号生成器
    基于技术分析结果生成买卖信号
    """
    
    def generate_signals(self, symbol: str, indicators: Dict, current_price: float, config: Dict) -> List[Signal]:
        """生成交易信号"""
        signals = []
        signal_config = config.get('strategy', {}).get('signals', {})
        
        # 支撑阻力位信号
        sr_signals = self._generate_support_resistance_signals(
            symbol, indicators, current_price, config
        )
        signals.extend(sr_signals)
        
        # RSI信号
        rsi_signals = self._generate_rsi_signals(
            symbol, indicators, current_price, config
        )
        signals.extend(rsi_signals)
        
        # MACD信号
        macd_signals = self._generate_macd_signals(
            symbol, indicators, current_price, config
        )
        signals.extend(macd_signals)
        
        # 过滤低置信度信号
        min_confidence = signal_config.get('min_confidence', 0.6)
        filtered_signals = [s for s in signals if s.confidence >= min_confidence]
        
        return filtered_signals
        
    def _generate_support_resistance_signals(self, symbol: str, indicators: Dict, 
                                           current_price: float, config: Dict) -> List[Signal]:
        """基于支撑阻力位生成信号"""
        signals = []
        support_levels = indicators.get('support_levels', [])
        resistance_levels = indicators.get('resistance_levels', [])
        
        tolerance = config.get('strategy', {}).get('technical', {}).get('support_resistance', {}).get('tolerance', 0.01)
        
        # 检查是否接近支撑位（买入机会）
        for support in support_levels:
            distance = abs(current_price - support) / support
            if distance <= tolerance and current_price >= support * 0.99:  # 略高于支撑位
                confidence = self._calculate_support_confidence(indicators, support, current_price)
                
                signals.append(Signal(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    action='BUY',
                    price=current_price,
                    target_shares=self._calculate_shares(current_price, config),
                    confidence=confidence,
                    reason=f"Price near support level ${support:.2f}",
                    stop_loss=support * 0.98,  # 支撑位下方2%止损
                    take_profit=self._calculate_take_profit(current_price, config)
                ))
                
        # 检查是否接近阻力位（卖出机会）
        for resistance in resistance_levels:
            distance = abs(current_price - resistance) / resistance
            if distance <= tolerance and current_price <= resistance * 1.01:  # 略低于阻力位
                confidence = self._calculate_resistance_confidence(indicators, resistance, current_price)
                
                signals.append(Signal(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    action='SELL',
                    price=current_price,
                    target_shares=0,  # 卖出信号，具体数量由风险管理决定
                    confidence=confidence,
                    reason=f"Price near resistance level ${resistance:.2f}",
                    stop_loss=resistance * 1.02,  # 阻力位上方2%止损
                    take_profit=0  # 卖出信号不设止盈
                ))
                
        return signals
        
    def _calculate_support_confidence(self, indicators: Dict, support: float, current_price: float) -> float:
        """计算支撑位信号置信度"""
        confidence = 0.5  # 基础置信度
        
        # RSI超卖加分
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            confidence += 0.2
        elif rsi < 40:
            confidence += 0.1
            
        # 成交量确认
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            confidence += 0.15
            
        # 距离支撑位越近，置信度越高
        distance = abs(current_price - support) / support
        confidence += (0.01 - distance) * 10  # 距离越近加分越多
        
        return min(confidence, 1.0)
        
    def _calculate_shares(self, price: float, config: Dict) -> int:
        """计算建议买入数量"""
        # 这里简化处理，实际应该由风险管理模块计算
        min_amount = config.get('trading', {}).get('min_trade_amount', 100)
        return max(1, int(min_amount / price))
        
    def _calculate_take_profit(self, entry_price: float, config: Dict) -> float:
        """计算止盈价位"""
        take_profit_levels = config.get('risk', {}).get('take_profit_levels', [])
        if take_profit_levels:
            first_level = take_profit_levels[0].get('level', 0.03)
            return entry_price * (1 + first_level)
        return entry_price * 1.03  # 默认3%止盈
```

## 3. 数据模型设计

### 3.1 核心数据类

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Signal:
    """交易信号数据模型"""
    timestamp: datetime
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    price: float
    target_shares: int
    confidence: float  # 0.0 - 1.0
    reason: str
    stop_loss: float
    take_profit: float
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'action': self.action,
            'price': self.price,
            'target_shares': self.target_shares,
            'confidence': self.confidence,
            'reason': self.reason,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'metadata': self.metadata or {}
        }

@dataclass  
class Position:
    """持仓数据模型"""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    last_updated: datetime
    
    @classmethod
    def calculate_from_trades(cls, symbol: str, trades: List[Dict], current_price: float):
        """从交易记录计算持仓"""
        total_shares = 0
        total_cost = 0
        
        for trade in trades:
            if trade['action'] == 'BUY':
                total_shares += trade['shares']
                total_cost += trade['shares'] * trade['price']
            elif trade['action'] == 'SELL':
                total_shares -= trade['shares']
                # 按比例减少成本
                if total_shares > 0:
                    total_cost *= (total_shares + trade['shares']) / total_shares
                    
        avg_cost = total_cost / total_shares if total_shares > 0 else 0
        market_value = total_shares * current_price
        unrealized_pnl = market_value - total_cost
        unrealized_pnl_pct = unrealized_pnl / total_cost if total_cost > 0 else 0
        
        return cls(
            symbol=symbol,
            shares=total_shares,
            avg_cost=avg_cost,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            last_updated=datetime.now()
        )

@dataclass
class StockConfig:
    """股票配置数据模型"""
    symbol: str
    name: str
    exchange: str
    active: bool
    strategy_type: str
    technical_params: Dict
    risk_params: Dict
    trading_params: Dict
    
    @classmethod
    def from_yaml(cls, config_dict: Dict):
        """从YAML配置创建实例"""
        stock_info = config_dict.get('stock', {})
        strategy_info = config_dict.get('strategy', {})
        
        return cls(
            symbol=stock_info.get('symbol'),
            name=stock_info.get('name'),
            exchange=stock_info.get('exchange', 'NASDAQ'),
            active=stock_info.get('active', True),
            strategy_type=strategy_info.get('type', 'intraday_momentum'),
            technical_params=strategy_info.get('technical', {}),
            risk_params=config_dict.get('risk', {}),
            trading_params=config_dict.get('trading', {})
        )
```

## 4. 算法实现细节

### 4.1 支撑阻力位识别算法

```python
def identify_support_resistance_levels(data: pd.DataFrame, window: int = 20, 
                                     min_touches: int = 2, tolerance: float = 0.01) -> Dict:
    """
    识别支撑阻力位的改进算法
    
    Args:
        data: OHLCV数据
        window: 局部极值检测窗口
        min_touches: 最小触及次数
        tolerance: 价位聚类容差
        
    Returns:
        包含支撑阻力位的字典
    """
    
    # 1. 识别局部极值
    local_maxima = []
    local_minima = []
    
    highs = data['high'].values
    lows = data['low'].values
    
    for i in range(window, len(data) - window):
        # 局部最大值（潜在阻力位）
        if highs[i] == max(highs[i-window:i+window+1]):
            local_maxima.append((i, highs[i]))
            
        # 局部最小值（潜在支撑位）  
        if lows[i] == min(lows[i-window:i+window+1]):
            local_minima.append((i, lows[i]))
    
    # 2. 聚类相近价位
    resistance_clusters = cluster_price_levels([price for _, price in local_maxima], tolerance)
    support_clusters = cluster_price_levels([price for _, price in local_minima], tolerance)
    
    # 3. 验证有效性（检查触及次数）
    valid_resistance = []
    for level in resistance_clusters:
        touches = count_level_touches(data, level, tolerance, 'resistance')
        if touches >= min_touches:
            valid_resistance.append({
                'level': level,
                'touches': touches,
                'strength': calculate_level_strength(data, level, tolerance)
            })
    
    valid_support = []
    for level in support_clusters:
        touches = count_level_touches(data, level, tolerance, 'support')
        if touches >= min_touches:
            valid_support.append({
                'level': level,
                'touches': touches,
                'strength': calculate_level_strength(data, level, tolerance)
            })
    
    # 4. 按强度排序
    valid_resistance.sort(key=lambda x: x['strength'], reverse=True)
    valid_support.sort(key=lambda x: x['strength'], reverse=True)
    
    return {
        'resistance_levels': [item['level'] for item in valid_resistance[:3]],
        'support_levels': [item['level'] for item in valid_support[:3]],
        'resistance_details': valid_resistance[:3],
        'support_details': valid_support[:3]
    }

def calculate_level_strength(data: pd.DataFrame, level: float, tolerance: float) -> float:
    """
    计算支撑阻力位强度
    考虑因素：触及次数、成交量、时间跨度等
    """
    touches = 0
    volume_at_touches = []
    time_span = 0
    
    for i, row in data.iterrows():
        high, low, volume = row['high'], row['low'], row['volume']
        
        # 检查是否触及该价位
        if abs(high - level) / level <= tolerance or abs(low - level) / level <= tolerance:
            touches += 1
            volume_at_touches.append(volume)
            if time_span == 0:
                first_touch = i
            last_touch = i
    
    if touches == 0:
        return 0
        
    # 计算强度分数
    touch_score = min(touches / 5.0, 1.0)  # 触及次数，最多5次满分
    volume_score = np.mean(volume_at_touches) / data['volume'].mean()  # 相对成交量
    time_score = (last_touch - first_touch) / len(data)  # 时间跨度
    
    strength = (touch_score * 0.4 + volume_score * 0.4 + time_score * 0.2)
    return min(strength, 1.0)
```

### 4.2 风险评估算法

```python
def calculate_portfolio_risk_metrics(portfolio: Portfolio, market_data: Dict) -> Dict:
    """
    计算投资组合风险指标
    """
    total_value = portfolio.get_total_value()
    positions = portfolio.get_all_positions()
    
    # 1. 仓位集中度风险
    concentration_risk = 0
    for position in positions:
        weight = position.market_value / total_value
        concentration_risk += weight ** 2  # Herfindahl指数
    
    # 2. 单日VaR (Value at Risk)
    daily_returns = []
    for position in positions:
        symbol = position.symbol
        volatility = market_data.get(symbol, {}).get('volatility_daily', 0.02)
        weight = position.market_value / total_value
        daily_returns.append(weight * volatility)
    
    portfolio_volatility = np.sqrt(np.sum(np.array(daily_returns) ** 2))
    var_95 = total_value * portfolio_volatility * 1.645  # 95%置信度
    
    # 3. 最大回撤风险
    max_drawdown = calculate_max_drawdown_risk(portfolio)
    
    # 4. 流动性风险
    liquidity_risk = calculate_liquidity_risk(positions, market_data)
    
    return {
        'total_value': total_value,
        'concentration_risk': concentration_risk,
        'var_95': var_95,
        'var_95_pct': var_95 / total_value,
        'max_drawdown_risk': max_drawdown,
        'liquidity_risk': liquidity_risk,
        'overall_risk_score': calculate_overall_risk_score({
            'concentration': concentration_risk,
            'var': var_95 / total_value,
            'drawdown': max_drawdown,
            'liquidity': liquidity_risk
        })
    }
```

这个重新设计的 `design.md` 文档：

1. **与简化架构保持一致**：基于新的单体应用架构设计
2. **去除了旧的复杂性**：删除了微服务相关的复杂设计
3. **聚焦日内套利**：专门针对日内交易的算法和逻辑
4. **通用化设计**：不再专门针对PONY股票，而是通用的股票分析
5. **实现细节完整**：提供了具体的类设计和算法实现

现在文档体系更加一致和清晰了！
