#!/usr/bin/env python3
"""
通用股票交易策略系统 - 核心实现
支持多股票、多策略的自动化交易系统
"""

import os
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """交易信号"""
    timestamp: datetime
    symbol: str
    action: str  # BUY/SELL/HOLD
    price: float
    shares: int
    confidence: float
    reason: str
    strategy_name: str


class TradingSystem:
    """通用交易系统主类"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.system_config = self._load_system_config()
        self.stocks = {}
        self.strategies = {}
        self.data_manager = DataManager(self.system_config['data_sources'])
        self.risk_manager = RiskManager(self.system_config['risk_management'])
        self.portfolio = Portfolio()
        
    def _load_system_config(self) -> Dict:
        """加载系统配置"""
        config_path = os.path.join(self.config_dir, "system.yaml")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def add_stock(self, symbol: str, config_file: Optional[str] = None):
        """添加股票到监控列表"""
        if config_file:
            config_path = os.path.join(self.config_dir, "stocks", config_file)
        else:
            config_path = os.path.join(self.config_dir, "stocks", f"{symbol}.yaml")
            
        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            return False
            
        with open(config_path, 'r') as f:
            stock_config = yaml.safe_load(f)
            
        # 创建策略实例
        strategy_type = stock_config['strategy']['type']
        strategy_class = self._get_strategy_class(strategy_type)
        
        if not strategy_class:
            logger.error(f"Unknown strategy type: {strategy_type}")
            return False
            
        strategy = strategy_class(symbol, stock_config['strategy']['parameters'])
        
        self.stocks[symbol] = stock_config
        self.strategies[symbol] = strategy
        
        logger.info(f"Added stock {symbol} with strategy {strategy_type}")
        return True
    
    def _get_strategy_class(self, strategy_type: str):
        """获取策略类"""
        from strategies import STRATEGY_REGISTRY
        return STRATEGY_REGISTRY.get(strategy_type)
    
    def run_analysis(self, symbol: str) -> Dict:
        """运行单个股票的分析"""
        if symbol not in self.stocks:
            logger.error(f"Stock {symbol} not configured")
            return {}
            
        # 获取市场数据
        current_price = self.data_manager.get_current_price(symbol)
        historical_data = self.data_manager.get_historical_data(
            symbol, 
            self.strategies[symbol].get_required_history()
        )
        
        # 执行策略
        strategy = self.strategies[symbol]
        indicators = strategy.calculate_indicators(historical_data)
        signals = strategy.generate_signals(indicators, current_price)
        
        # 风险检查
        validated_signals = []
        for signal in signals:
            if self.risk_manager.validate_signal(signal, self.portfolio):
                validated_signals.append(signal)
            else:
                logger.warning(f"Signal rejected by risk manager: {signal}")
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'indicators': indicators,
            'signals': validated_signals,
            'timestamp': datetime.now()
        }
    
    def run_all(self) -> List[Dict]:
        """运行所有股票的分析"""
        results = []
        for symbol in self.stocks:
            try:
                result = self.run_analysis(symbol)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
        return results
    
    def execute_signal(self, signal: Signal) -> bool:
        """执行交易信号（模拟）"""
        logger.info(f"Executing signal: {signal}")
        
        if signal.action == 'BUY':
            success = self.portfolio.buy(
                signal.symbol, 
                signal.shares, 
                signal.price
            )
        elif signal.action == 'SELL':
            success = self.portfolio.sell(
                signal.symbol, 
                signal.shares, 
                signal.price
            )
        else:
            success = True  # HOLD
            
        if success:
            logger.info(f"Signal executed successfully")
        else:
            logger.error(f"Failed to execute signal")
            
        return success


class DataManager:
    """数据管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache = {}
        
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        # 这里应该接入实际的数据源
        # 示例：使用yfinance
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            return float(data['Close'].iloc[-1])
        except:
            # 模拟数据
            logger.warning(f"Using mock price for {symbol}")
            return 100.0 + (hash(symbol) % 50)
    
    def get_historical_data(self, symbol: str, days: int) -> pd.DataFrame:
        """获取历史数据"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f'{days}d')
            return data
        except:
            # 模拟数据
            logger.warning(f"Using mock data for {symbol}")
            dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
            prices = [100 + i + (hash(f"{symbol}{i}") % 10) for i in range(days)]
            
            return pd.DataFrame({
                'date': dates,
                'open': prices,
                'high': [p * 1.02 for p in prices],
                'low': [p * 0.98 for p in prices],
                'close': prices,
                'volume': [1000000] * days
            })


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.20)
        self.max_single_position = config.get('max_single_position', 0.15)
        self.max_daily_loss = config.get('max_daily_loss', 0.05)
        
    def validate_signal(self, signal: Signal, portfolio) -> bool:
        """验证信号是否符合风险控制要求"""
        if signal.action == 'BUY':
            # 检查单个仓位限制
            position_value = signal.shares * signal.price
            total_value = portfolio.get_total_value()
            
            if total_value > 0:
                position_pct = position_value / total_value
                if position_pct > self.max_single_position:
                    logger.warning(f"Position size {position_pct:.2%} exceeds limit")
                    return False
                    
        return True


class Portfolio:
    """投资组合管理"""
    
    def __init__(self, initial_cash: float = 100000):
        self.cash = initial_cash
        self.positions = {}  # {symbol: {'shares': x, 'avg_cost': y}}
        self.trades = []
        
    def buy(self, symbol: str, shares: int, price: float) -> bool:
        """买入股票"""
        cost = shares * price
        
        if cost > self.cash:
            logger.error(f"Insufficient cash: need {cost}, have {self.cash}")
            return False
            
        self.cash -= cost
        
        if symbol in self.positions:
            # 更新平均成本
            pos = self.positions[symbol]
            total_shares = pos['shares'] + shares
            total_cost = pos['shares'] * pos['avg_cost'] + cost
            pos['shares'] = total_shares
            pos['avg_cost'] = total_cost / total_shares
        else:
            self.positions[symbol] = {
                'shares': shares,
                'avg_cost': price
            }
            
        self.trades.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': 'BUY',
            'shares': shares,
            'price': price
        })
        
        logger.info(f"Bought {shares} shares of {symbol} at {price}")
        return True
    
    def sell(self, symbol: str, shares: int, price: float) -> bool:
        """卖出股票"""
        if symbol not in self.positions:
            logger.error(f"No position in {symbol}")
            return False
            
        pos = self.positions[symbol]
        if shares > pos['shares']:
            logger.error(f"Insufficient shares: have {pos['shares']}, selling {shares}")
            return False
            
        self.cash += shares * price
        pos['shares'] -= shares
        
        if pos['shares'] == 0:
            del self.positions[symbol]
            
        self.trades.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': 'SELL',
            'shares': shares,
            'price': price
        })
        
        logger.info(f"Sold {shares} shares of {symbol} at {price}")
        return True
    
    def get_total_value(self) -> float:
        """计算总价值"""
        total = self.cash
        # 这里应该用实时价格，简化起见先不实现
        return total


# 策略基类
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, symbol: str, config: Dict):
        self.symbol = symbol
        self.config = config
        
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """计算指标"""
        pass
        
    @abstractmethod
    def generate_signals(self, indicators: Dict, current_price: float) -> List[Signal]:
        """生成信号"""
        pass
        
    @abstractmethod
    def get_required_history(self) -> int:
        """需要的历史数据天数"""
        pass


# 简单均线策略示例
class SimpleMAStrategy(BaseStrategy):
    """简单均线策略"""
    
    def get_required_history(self) -> int:
        return self.config.get('slow_period', 30) + 10
        
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        fast_period = self.config.get('fast_period', 10)
        slow_period = self.config.get('slow_period', 30)
        
        data['ma_fast'] = data['close'].rolling(window=fast_period).mean()
        data['ma_slow'] = data['close'].rolling(window=slow_period).mean()
        
        return {
            'ma_fast': data['ma_fast'].iloc[-1],
            'ma_slow': data['ma_slow'].iloc[-1],
            'trend': 'up' if data['ma_fast'].iloc[-1] > data['ma_slow'].iloc[-1] else 'down'
        }
        
    def generate_signals(self, indicators: Dict, current_price: float) -> List[Signal]:
        signals = []
        
        # 简单的交叉逻辑
        if indicators['trend'] == 'up':
            signals.append(Signal(
                timestamp=datetime.now(),
                symbol=self.symbol,
                action='BUY',
                price=current_price,
                shares=100,  # 简化处理
                confidence=0.7,
                reason="MA cross up",
                strategy_name="SimpleMA"
            ))
            
        return signals


# 策略注册表
STRATEGY_REGISTRY = {
    'simple_ma': SimpleMAStrategy,
    # 在这里添加更多策略
}


# 主程序入口
def main():
    """主函数"""
    # 创建交易系统
    system = TradingSystem()
    
    # 添加股票（确保配置文件存在）
    system.add_stock('AAPL')  # 需要 config/stocks/AAPL.yaml
    system.add_stock('PONY')  # 需要 config/stocks/PONY.yaml
    
    # 运行分析
    results = system.run_all()
    
    # 显示结果
    for result in results:
        print(f"\n=== {result['symbol']} ===")
        print(f"Current Price: ${result['current_price']:.2f}")
        print(f"Indicators: {result['indicators']}")
        
        if result['signals']:
            print("Signals:")
            for signal in result['signals']:
                print(f"  - {signal.action} {signal.shares} shares at ${signal.price:.2f}")
                print(f"    Reason: {signal.reason}")
                print(f"    Confidence: {signal.confidence:.2%}")
        else:
            print("No signals generated")
    
    # 显示组合状态
    print(f"\nPortfolio:")
    print(f"Cash: ${system.portfolio.cash:,.2f}")
    print(f"Positions: {system.portfolio.positions}")


if __name__ == "__main__":
    main()