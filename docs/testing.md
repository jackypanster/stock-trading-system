# 测试指南

## 1. 测试策略概述

### 1.1 测试理念
- **质量优先**：确保系统稳定可靠
- **自动化测试**：减少手动测试工作量
- **持续验证**：开发过程中持续测试
- **风险控制**：重点测试风险控制功能

### 1.2 测试分层
```
┌─────────────────────────────────────┐
│          用户验收测试                │
│      (端到端功能验证)                │
├─────────────────────────────────────┤
│          集成测试                    │
│    (模块间交互测试)                  │
├─────────────────────────────────────┤
│          单元测试                    │
│    (单个函数/类测试)                 │
└─────────────────────────────────────┘
```

### 1.3 测试覆盖目标
- 代码覆盖率：≥ 80%
- 核心功能覆盖率：100%
- 风险控制功能覆盖率：100%
- 性能测试覆盖：关键路径

## 2. 测试环境设置

### 2.1 测试依赖安装

```bash
# 安装测试依赖
pip install pytest pytest-cov pytest-asyncio mock requests-mock

# 安装性能测试工具
pip install pytest-benchmark memory-profiler

# 安装代码质量工具
pip install flake8 black mypy
```

### 2.2 测试目录结构

```
tests/
├── unit/                  # 单元测试
│   ├── test_market_data.py
│   ├── test_technical_analyzer.py
│   ├── test_signal_generator.py
│   └── test_risk_manager.py
├── integration/           # 集成测试
│   ├── test_trading_flow.py
│   └── test_data_pipeline.py
├── performance/           # 性能测试
│   ├── test_analysis_speed.py
│   └── test_memory_usage.py
├── fixtures/              # 测试数据
│   ├── sample_price_data.csv
│   └── mock_api_responses.json
└── conftest.py           # 测试配置
```

### 2.3 测试配置

**conftest.py：**
```python
import pytest
import pandas as pd
from unittest.mock import Mock
from app.core.trading_assistant import TradingAssistant
from app.data.market_data_manager import MarketDataManager

@pytest.fixture
def sample_price_data():
    """样本价格数据"""
    return pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='D'),
        'open': range(100, 200),
        'high': range(101, 201),
        'low': range(99, 199),
        'close': range(100, 200),
        'volume': range(1000000, 2000000, 10000)
    })

@pytest.fixture
def mock_market_data():
    """模拟市场数据管理器"""
    mock = Mock(spec=MarketDataManager)
    mock.get_current_price.return_value = 150.0
    mock.get_historical_data.return_value = pd.DataFrame({
        'close': [145, 148, 152, 149, 151],
        'volume': [1500000, 1600000, 1400000, 1700000, 1550000]
    })
    return mock

@pytest.fixture
def trading_assistant():
    """交易助手实例"""
    return TradingAssistant(config_dir="tests/fixtures/config")
```

## 3. 单元测试

### 3.1 技术分析模块测试

**tests/unit/test_technical_analyzer.py：**
```python
import pytest
import pandas as pd
import numpy as np
from app.analysis.technical_analyzer import TechnicalAnalyzer

class TestTechnicalAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        return TechnicalAnalyzer()
    
    @pytest.fixture
    def sample_data(self):
        """生成测试用的价格数据"""
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(50) * 0.5)
        return pd.DataFrame({
            'open': prices + np.random.randn(50) * 0.1,
            'high': prices + np.abs(np.random.randn(50)) * 0.5,
            'low': prices - np.abs(np.random.randn(50)) * 0.5,
            'close': prices,
            'volume': np.random.randint(1000000, 2000000, 50)
        })
    
    def test_calculate_rsi(self, analyzer, sample_data):
        """测试RSI计算"""
        config = {'indicators': {'rsi_period': 14}}
        indicators = analyzer.calculate_indicators(sample_data, config)
        
        assert 'rsi' in indicators
        assert 0 <= indicators['rsi'] <= 100
        assert not np.isnan(indicators['rsi'])
    
    def test_calculate_macd(self, analyzer, sample_data):
        """测试MACD计算"""
        config = {
            'indicators': {
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9
            }
        }
        indicators = analyzer.calculate_indicators(sample_data, config)
        
        assert 'macd' in indicators
        assert 'macd' in indicators['macd']
        assert 'signal' in indicators['macd']
        assert 'histogram' in indicators['macd']
    
    def test_support_resistance_identification(self, analyzer, sample_data):
        """测试支撑阻力位识别"""
        config = {
            'support_resistance': {
                'window': 5,
                'min_touches': 2,
                'tolerance': 0.01
            }
        }
        indicators = analyzer.calculate_indicators(sample_data, config)
        
        assert 'support_levels' in indicators
        assert 'resistance_levels' in indicators
        assert isinstance(indicators['support_levels'], list)
        assert isinstance(indicators['resistance_levels'], list)
        
        # 支撑位应该低于阻力位
        if indicators['support_levels'] and indicators['resistance_levels']:
            assert max(indicators['support_levels']) < min(indicators['resistance_levels'])
    
    def test_volatility_calculation(self, analyzer, sample_data):
        """测试波动率计算"""
        indicators = analyzer.calculate_indicators(sample_data, {})
        
        assert 'atr' in indicators
        assert 'volatility_annual' in indicators
        assert 'volatility_daily' in indicators
        assert indicators['atr'] > 0
        assert indicators['volatility_annual'] > 0
```

### 3.2 信号生成模块测试

**tests/unit/test_signal_generator.py：**
```python
import pytest
from datetime import datetime
from app.analysis.signal_generator import SignalGenerator
from app.models.signal import Signal

class TestSignalGenerator:
    
    @pytest.fixture
    def generator(self):
        return SignalGenerator()
    
    @pytest.fixture
    def sample_indicators(self):
        return {
            'current_price': 150.0,
            'support_levels': [145.0, 148.0],
            'resistance_levels': [155.0, 158.0],
            'rsi': 35.0,  # 超卖
            'macd': {
                'macd': 0.5,
                'signal': 0.3,
                'histogram': 0.2
            },
            'volume_ratio': 1.8
        }
    
    @pytest.fixture
    def sample_config(self):
        return {
            'strategy': {
                'signals': {'min_confidence': 0.6},
                'technical': {
                    'support_resistance': {'tolerance': 0.01}
                }
            },
            'risk': {'stop_loss_pct': 0.02},
            'trading': {'min_trade_amount': 1000}
        }
    
    def test_support_level_buy_signal(self, generator, sample_indicators, sample_config):
        """测试支撑位买入信号"""
        # 价格接近支撑位
        current_price = 148.2
        
        signals = generator.generate_signals(
            'TSLA', sample_indicators, current_price, sample_config
        )
        
        buy_signals = [s for s in signals if s.action == 'BUY']
        assert len(buy_signals) > 0
        
        signal = buy_signals[0]
        assert signal.symbol == 'TSLA'
        assert signal.confidence > 0.5
        assert signal.stop_loss < current_price
        assert signal.take_profit > current_price
    
    def test_resistance_level_sell_signal(self, generator, sample_config):
        """测试阻力位卖出信号"""
        indicators = {
            'resistance_levels': [155.0, 158.0],
            'rsi': 75.0,  # 超买
            'volume_ratio': 2.0
        }
        current_price = 155.1  # 接近阻力位
        
        signals = generator.generate_signals(
            'NVDA', indicators, current_price, sample_config
        )
        
        sell_signals = [s for s in signals if s.action == 'SELL']
        assert len(sell_signals) > 0
    
    def test_signal_confidence_calculation(self, generator, sample_indicators):
        """测试信号置信度计算"""
        support_level = 148.0
        current_price = 148.1
        
        confidence = generator._calculate_support_confidence(
            sample_indicators, support_level, current_price
        )
        
        assert 0.0 <= confidence <= 1.0
        
        # RSI超卖应该增加置信度
        assert confidence > 0.5  # RSI=35是超卖状态
    
    def test_minimum_confidence_filter(self, generator, sample_indicators, sample_config):
        """测试最小置信度过滤"""
        # 设置很高的最小置信度
        sample_config['strategy']['signals']['min_confidence'] = 0.9
        
        signals = generator.generate_signals(
            'AAPL', sample_indicators, 150.0, sample_config
        )
        
        # 应该过滤掉低置信度信号
        assert all(signal.confidence >= 0.9 for signal in signals)
```

### 3.3 风险管理模块测试

**tests/unit/test_risk_manager.py：**
```python
import pytest
from app.core.risk_manager import RiskManager
from app.models.signal import Signal
from app.models.portfolio import Portfolio
from datetime import datetime

class TestRiskManager:
    
    @pytest.fixture
    def risk_manager(self):
        config = {
            'risk': {
                'max_single_stock': 0.15,
                'max_total_exposure': 0.8,
                'max_daily_trades': 5,
                'emergency_stop_loss': 0.05
            }
        }
        return RiskManager(config)
    
    @pytest.fixture
    def sample_portfolio(self):
        portfolio = Portfolio()
        portfolio.add_position('TSLA', 100, 140.0)
        portfolio.add_position('NVDA', 50, 200.0)
        portfolio.cash = 10000
        return portfolio
    
    @pytest.fixture
    def buy_signal(self):
        return Signal(
            timestamp=datetime.now(),
            symbol='AAPL',
            action='BUY',
            price=150.0,
            target_shares=50,
            confidence=0.8,
            reason='Support level buy',
            stop_loss=147.0,
            take_profit=156.0
        )
    
    def test_position_size_limit(self, risk_manager, sample_portfolio, buy_signal):
        """测试仓位大小限制"""
        # 测试单只股票仓位限制
        large_signal = Signal(
            timestamp=datetime.now(),
            symbol='AAPL',
            action='BUY',
            price=150.0,
            target_shares=200,  # 过大的仓位
            confidence=0.8,
            reason='Support level buy',
            stop_loss=147.0,
            take_profit=156.0
        )
        
        is_valid = risk_manager.validate_signal(large_signal, sample_portfolio)
        assert not is_valid  # 应该被拒绝
    
    def test_total_exposure_limit(self, risk_manager, sample_portfolio, buy_signal):
        """测试总仓位暴露限制"""
        # 添加大量持仓使总暴露接近限制
        sample_portfolio.add_position('META', 100, 300.0)
        sample_portfolio.add_position('GOOGL', 80, 250.0)
        
        is_valid = risk_manager.validate_signal(buy_signal, sample_portfolio)
        # 根据总暴露情况决定是否允许
        total_value = sample_portfolio.get_total_value()
        if sample_portfolio.get_total_invested() / total_value > 0.7:
            assert not is_valid
    
    def test_stop_loss_calculation(self, risk_manager):
        """测试止损计算"""
        entry_price = 100.0
        stop_loss_pct = 0.02
        
        stop_loss = risk_manager.calculate_stop_loss(entry_price, stop_loss_pct)
        assert stop_loss == 98.0
        assert stop_loss < entry_price
    
    def test_portfolio_risk_metrics(self, risk_manager, sample_portfolio):
        """测试投资组合风险指标"""
        market_data = {
            'TSLA': {'volatility_daily': 0.03},
            'NVDA': {'volatility_daily': 0.04}
        }
        
        risk_metrics = risk_manager.calculate_portfolio_risk_metrics(
            sample_portfolio, market_data
        )
        
        assert 'concentration_risk' in risk_metrics
        assert 'var_95' in risk_metrics
        assert 'var_95_pct' in risk_metrics
        assert 'overall_risk_score' in risk_metrics
        
        assert 0 <= risk_metrics['concentration_risk'] <= 1
        assert risk_metrics['var_95'] > 0
        assert 0 <= risk_metrics['var_95_pct'] <= 1
```

## 4. 集成测试

### 4.1 数据管道测试

**tests/integration/test_data_pipeline.py：**
```python
import pytest
import asyncio
from unittest.mock import patch, Mock
from app.data.market_data_manager import MarketDataManager

class TestDataPipeline:
    
    @pytest.mark.asyncio
    async def test_data_source_failover(self):
        """测试数据源故障切换"""
        config = {'backup_data_source': True}
        manager = MarketDataManager(config)
        
        # 模拟主数据源失败
        with patch('yfinance.Ticker') as mock_yf:
            mock_yf.side_effect = Exception("API Error")
            
            # 模拟备用数据源成功
            with patch.object(manager, '_get_price_from_alpha_vantage', return_value=150.0):
                price = await manager.get_current_price('AAPL')
                assert price == 150.0
    
    @pytest.mark.asyncio
    async def test_cache_mechanism(self):
        """测试缓存机制"""
        config = {'cache': {'price_cache_ttl': 60}}
        manager = MarketDataManager(config)
        
        with patch('yfinance.Ticker') as mock_yf:
            mock_ticker = Mock()
            mock_ticker.history.return_value.empty = False
            mock_ticker.history.return_value.__getitem__.return_value.iloc = Mock()
            mock_ticker.history.return_value.__getitem__.return_value.iloc.__getitem__.return_value = 150.0
            mock_yf.return_value = mock_ticker
            
            # 第一次调用
            price1 = await manager.get_current_price('AAPL')
            
            # 第二次调用应该从缓存获取
            price2 = await manager.get_current_price('AAPL')
            
            assert price1 == price2
            # yfinance应该只被调用一次
            assert mock_yf.call_count == 1
```

### 4.2 完整交易流程测试

**tests/integration/test_trading_flow.py：**
```python
import pytest
from unittest.mock import Mock, patch
from app.core.trading_assistant import TradingAssistant

class TestTradingFlow:
    
    @pytest.mark.asyncio
    async def test_complete_analysis_flow(self):
        """测试完整的分析流程"""
        # 创建交易助手实例
        assistant = TradingAssistant()
        
        # 模拟配置
        with patch.object(assistant.config_loader, 'load_stock_config') as mock_config:
            mock_config.return_value = {
                'strategy': {
                    'technical': {'lookback_days': 20},
                    'signals': {'min_confidence': 0.6}
                },
                'risk': {'stop_loss_pct': 0.02}
            }
            
            # 模拟市场数据
            with patch.object(assistant.market_data, 'get_current_price', return_value=150.0):
                with patch.object(assistant.market_data, 'get_historical_data') as mock_history:
                    mock_history.return_value = Mock()  # 模拟历史数据
                    
                    # 执行分析
                    result = await assistant.analyze_stock('AAPL')
                    
                    # 验证结果结构
                    assert 'symbol' in result
                    assert 'current_price' in result
                    assert 'indicators' in result
                    assert 'signals' in result
                    assert result['symbol'] == 'AAPL'
                    assert result['current_price'] == 150.0
    
    @pytest.mark.asyncio
    async def test_multi_stock_analysis(self):
        """测试多股票分析"""
        assistant = TradingAssistant()
        
        symbols = ['AAPL', 'TSLA', 'NVDA']
        
        with patch.object(assistant, 'analyze_stock') as mock_analyze:
            mock_analyze.side_effect = [
                {'symbol': symbol, 'current_price': 150.0, 'signals': []}
                for symbol in symbols
            ]
            
            results = await assistant.run_analysis_cycle(symbols)
            
            assert len(results) == 3
            assert all('symbol' in result for result in results)
            assert [result['symbol'] for result in results] == symbols
```

## 5. 性能测试

### 5.1 分析速度测试

**tests/performance/test_analysis_speed.py：**
```python
import pytest
import time
import pandas as pd
import numpy as np
from app.analysis.technical_analyzer import TechnicalAnalyzer

class TestAnalysisPerformance:
    
    @pytest.fixture
    def large_dataset(self):
        """生成大量测试数据"""
        np.random.seed(42)
        size = 1000
        prices = 100 + np.cumsum(np.random.randn(size) * 0.1)
        return pd.DataFrame({
            'open': prices + np.random.randn(size) * 0.05,
            'high': prices + np.abs(np.random.randn(size)) * 0.2,
            'low': prices - np.abs(np.random.randn(size)) * 0.2,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, size)
        })
    
    def test_technical_analysis_speed(self, large_dataset):
        """测试技术分析计算速度"""
        analyzer = TechnicalAnalyzer()
        config = {
            'indicators': {'rsi_period': 14},
            'support_resistance': {'window': 20}
        }
        
        start_time = time.time()
        for _ in range(10):  # 重复10次
            indicators = analyzer.calculate_indicators(large_dataset, config)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        print(f"Average analysis time: {avg_time:.3f}s")
        
        # 单次分析应该在2秒内完成
        assert avg_time < 2.0
    
    @pytest.mark.benchmark
    def test_support_resistance_benchmark(self, benchmark, large_dataset):
        """基准测试支撑阻力位计算"""
        analyzer = TechnicalAnalyzer()
        config = {
            'support_resistance': {
                'window': 20,
                'min_touches': 2,
                'tolerance': 0.01
            }
        }
        
        result = benchmark(analyzer._calculate_support_resistance, large_dataset, config)
        
        assert 'support_levels' in result
        assert 'resistance_levels' in result
```

### 5.2 内存使用测试

**tests/performance/test_memory_usage.py：**
```python
import pytest
import psutil
import os
from memory_profiler import profile
from app.core.trading_assistant import TradingAssistant

class TestMemoryUsage:
    
    def test_memory_baseline(self):
        """测试基础内存使用"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建交易助手实例
        assistant = TradingAssistant()
        
        after_creation = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_creation - initial_memory
        
        print(f"Memory increase after creation: {memory_increase:.1f} MB")
        
        # 内存增长应该在合理范围内
        assert memory_increase < 100  # 不超过100MB
    
    @profile
    def test_analysis_memory_profile(self):
        """内存分析测试（需要手动查看输出）"""
        assistant = TradingAssistant()
        
        # 执行多次分析
        for i in range(10):
            # 这里应该有实际的分析调用
            pass
```

## 6. 回测验证

### 6.1 历史数据回测

**tests/backtest/test_strategy_backtest.py：**
```python
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.backtest.backtester import Backtester
from app.core.trading_assistant import TradingAssistant

class TestStrategyBacktest:
    
    @pytest.fixture
    def historical_data(self):
        """生成历史数据用于回测"""
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        np.random.seed(42)
        
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
        
        return pd.DataFrame({
            'date': dates,
            'open': prices + np.random.randn(len(dates)) * 0.1,
            'high': prices + np.abs(np.random.randn(len(dates))) * 0.3,
            'low': prices - np.abs(np.random.randn(len(dates))) * 0.3,
            'close': prices,
            'volume': np.random.randint(1000000, 3000000, len(dates))
        })
    
    def test_backtest_performance(self, historical_data):
        """测试策略回测性能"""
        assistant = TradingAssistant()
        backtester = Backtester(assistant, initial_capital=10000)
        
        results = backtester.run(
            historical_data, 
            start_date='2023-01-01', 
            end_date='2023-06-30'
        )
        
        assert 'total_return' in results
        assert 'max_drawdown' in results
        assert 'sharpe_ratio' in results
        assert 'win_rate' in results
        
        # 基本合理性检查
        assert -1 <= results['total_return'] <= 10  # 收益率在合理范围
        assert 0 <= results['win_rate'] <= 1  # 胜率0-100%
    
    def test_risk_metrics_calculation(self, historical_data):
        """测试风险指标计算"""
        backtester = Backtester(None, initial_capital=10000)
        
        # 模拟交易记录
        trades = [
            {'date': '2023-01-15', 'return': 0.02},
            {'date': '2023-01-20', 'return': -0.01},
            {'date': '2023-01-25', 'return': 0.03},
            {'date': '2023-01-30', 'return': -0.02},
        ]
        
        metrics = backtester.calculate_risk_metrics(trades)
        
        assert 'max_drawdown' in metrics
        assert 'volatility' in metrics
        assert 'sharpe_ratio' in metrics
        
        assert metrics['max_drawdown'] <= 0  # 最大回撤应为负数或0
        assert metrics['volatility'] >= 0   # 波动率应为正数
```

## 7. 运行测试

### 7.1 测试执行命令

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_technical_analyzer.py

# 运行特定测试类
pytest tests/unit/test_signal_generator.py::TestSignalGenerator

# 运行特定测试方法
pytest tests/unit/test_risk_manager.py::TestRiskManager::test_position_size_limit

# 显示详细输出
pytest -v

# 显示测试覆盖率
pytest --cov=app --cov-report=html

# 运行性能测试
pytest tests/performance/ --benchmark-only
```

### 7.2 持续集成配置

**.github/workflows/test.yml：**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 7.3 测试报告

```bash
# 生成HTML测试报告
pytest --html=reports/test_report.html --self-contained-html

# 生成覆盖率报告
pytest --cov=app --cov-report=html --cov-report=term

# 生成性能报告
pytest --benchmark-only --benchmark-json=reports/benchmark.json
```

## 8. 测试最佳实践

### 8.1 测试编写原则

1. **测试独立性**：每个测试应该独立运行
2. **可重复性**：测试结果应该稳定可重复
3. **清晰命名**：测试名称应该描述测试场景
4. **单一职责**：每个测试只验证一个功能点

### 8.2 Mock使用指南

```python
# 好的Mock使用示例
@patch('app.data.market_data_manager.yfinance.Ticker')
def test_price_fetching(self, mock_ticker):
    """正确的Mock使用"""
    # 设置Mock行为
    mock_ticker.return_value.history.return_value = pd.DataFrame({
        'Close': [150.0]
    })
    
    # 执行测试
    manager = MarketDataManager()
    price = manager.get_current_price('AAPL')
    
    # 验证结果
    assert price == 150.0
    mock_ticker.assert_called_once_with('AAPL')
```

### 8.3 测试数据管理

```python
# 使用fixtures管理测试数据
@pytest.fixture
def sample_stock_config():
    return {
        'symbol': 'AAPL',
        'strategy': {'type': 'intraday_momentum'},
        'risk': {'stop_loss_pct': 0.02}
    }

# 参数化测试
@pytest.mark.parametrize("symbol,expected_result", [
    ("AAPL", True),
    ("INVALID", False),
])
def test_symbol_validation(symbol, expected_result):
    assert validate_symbol(symbol) == expected_result
```

### 8.4 异步测试

```python
@pytest.mark.asyncio
async def test_async_data_fetching():
    """异步函数测试"""
    manager = MarketDataManager()
    price = await manager.get_current_price('AAPL')
    assert isinstance(price, (int, float))
    assert price > 0
```
