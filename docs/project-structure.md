# 项目结构规范

## 1. 目录结构设计

### 1.1 整体项目布局

```
intraday-trading-assistant/
├── README.md                  # 项目说明
├── requirements.txt           # Python依赖
├── setup.py                   # 安装脚本
├── .env.example              # 环境变量模板
├── .gitignore                # Git忽略文件
├── LICENSE                   # 开源许可证
│
├── main.py                   # 主入口文件
├── cli.py                    # 命令行界面
│
├── app/                      # 核心应用代码
│   ├── __init__.py
│   ├── core/                 # 核心模块
│   │   ├── __init__.py
│   │   ├── assistant.py      # 主应用控制器
│   │   ├── market_data.py    # 市场数据管理
│   │   ├── technical.py      # 技术分析
│   │   ├── signals.py        # 信号生成
│   │   ├── risk.py          # 风险管理
│   │   └── portfolio.py     # 组合管理
│   │
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── signal.py        # 信号模型
│   │   ├── position.py      # 持仓模型
│   │   └── config.py        # 配置模型
│   │
│   ├── services/            # 业务服务
│   │   ├── __init__.py
│   │   ├── data_service.py  # 数据服务
│   │   ├── analysis_service.py # 分析服务
│   │   └── notification_service.py # 通知服务
│   │
│   ├── utils/               # 工具函数
│   │   ├── __init__.py
│   │   ├── helpers.py       # 通用帮助函数
│   │   ├── validators.py    # 数据验证
│   │   └── formatters.py    # 格式化工具
│   │
│   └── web/                 # Web界面 (可选)
│       ├── __init__.py
│       ├── app.py           # Flask应用
│       ├── routes.py        # 路由定义
│       └── templates/       # 模板文件
│
├── config/                  # 配置文件目录
│   ├── system.yaml          # 系统级配置
│   ├── stocks/              # 股票配置目录
│   │   ├── TSLA.yaml       # Tesla配置
│   │   ├── NVDA.yaml       # NVIDIA配置
│   │   ├── META.yaml       # Meta配置
│   │   ├── NIO.yaml        # NIO配置
│   │   └── template.yaml   # 配置模板
│   └── strategies/          # 策略配置目录
│       ├── intraday_momentum.yaml
│       └── support_resistance.yaml
│
├── data/                    # 数据文件目录
│   ├── database/           # 数据库文件
│   │   └── trading.db      # SQLite数据库
│   ├── cache/              # 缓存文件
│   ├── backups/            # 备份文件
│   └── exports/            # 导出文件
│
├── logs/                   # 日志文件目录
│   ├── app.log             # 应用日志
│   ├── trading.log         # 交易日志
│   └── error.log           # 错误日志
│
├── scripts/                # 工具脚本
│   ├── init_db.py          # 数据库初始化
│   ├── backup.py           # 备份脚本
│   ├── stock_screener.py   # 股票筛选
│   └── performance_report.py # 性能报告
│
├── tests/                  # 测试代码
│   ├── __init__.py
│   ├── unit/               # 单元测试
│   │   ├── test_core/
│   │   ├── test_models/
│   │   └── test_utils/
│   ├── integration/        # 集成测试
│   ├── fixtures/           # 测试数据
│   └── conftest.py         # 测试配置
│
├── docs/                   # 文档目录
│   ├── project-definition.md
│   ├── stock-selection-criteria.md
│   ├── simplified-architecture.md
│   ├── project-structure.md (本文件)
│   ├── configuration.md
│   ├── api.md
│   ├── deployment.md
│   └── user-guide.md
│
└── docker/                 # Docker相关文件
    ├── Dockerfile
    ├── docker-compose.yml
    └── .dockerignore
```

## 2. 配置体系设计

### 2.1 配置文件层次结构

```
配置优先级（高到低）：
1. 环境变量
2. 命令行参数  
3. 股票特定配置 (config/stocks/SYMBOL.yaml)
4. 策略配置 (config/strategies/STRATEGY.yaml)
5. 系统默认配置 (config/system.yaml)
```

### 2.2 系统配置 (config/system.yaml)

```yaml
# 系统级默认配置
app:
  name: "Intraday Trading Assistant"
  version: "1.0.0"
  debug: false
  log_level: "INFO"

# 数据源配置
data_sources:
  primary:
    name: "yfinance"
    timeout: 30
    retry_times: 3
  
  fallback:
    name: "alpha_vantage"
    api_key: "${ALPHA_VANTAGE_API_KEY}"
    timeout: 30

# 数据库配置
database:
  type: "sqlite"
  path: "data/database/trading.db"
  backup_interval: 24  # hours
  
# 缓存配置
cache:
  price_cache_ttl: 60  # seconds
  indicator_cache_ttl: 300  # seconds
  
# 风险管理默认参数
risk_management:
  max_portfolio_risk: 0.20        # 最大组合风险20%
  max_single_position: 0.15       # 单只股票最大仓位15%
  max_daily_trades: 5             # 每日最大交易次数
  stop_loss_default: 0.02         # 默认止损2%
  
# 通知配置
notifications:
  enabled: true
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    from_email: "${EMAIL_FROM}"
    to_email: "${EMAIL_TO}"
    password: "${EMAIL_PASSWORD}"
    
# 调度配置
scheduler:
  market_data_interval: 60        # 市场数据更新间隔(秒)
  analysis_interval: 300          # 分析执行间隔(秒)
  
# 市场时间配置
market_hours:
  timezone: "US/Eastern"
  open_time: "09:30"
  close_time: "16:00"
  
# 日志配置
logging:
  level: "INFO"
  file_path: "logs/app.log"
  max_size: "10MB"
  backup_count: 5
```

### 2.3 股票配置模板 (config/stocks/template.yaml)

```yaml
# 股票配置模板
stock:
  symbol: "SYMBOL"              # 股票代码
  name: "Company Name"          # 公司名称
  exchange: "NASDAQ"            # 交易所
  currency: "USD"               # 货币
  active: true                  # 是否激活监控

# 策略配置
strategy:
  type: "intraday_momentum"     # 策略类型
  
  # 技术分析参数
  technical:
    lookback_days: 20           # 历史数据回看天数
    support_resistance:
      window: 20                # 支撑阻力位计算窗口
      min_touches: 2            # 最小触及次数
      tolerance: 0.01           # 价位容差1%
    
    indicators:
      rsi_period: 14            # RSI周期
      macd_fast: 12             # MACD快线
      macd_slow: 26             # MACD慢线
      macd_signal: 9            # MACD信号线
      
  # 信号生成参数  
  signals:
    min_confidence: 0.6         # 最小信号置信度
    volume_confirmation: true    # 是否需要成交量确认
    volume_multiplier: 1.5      # 成交量倍数
    
# 风险控制参数
risk:
  max_position_pct: 0.10        # 最大仓位10%
  stop_loss_pct: 0.02           # 止损2%
  take_profit_levels:           # 分层止盈
    - level: 0.03               # 3%止盈
      portion: 0.3              # 减仓30%
    - level: 0.05               # 5%止盈  
      portion: 0.5              # 减仓50%
    - level: 0.08               # 8%止盈
      portion: 1.0              # 全部减仓
      
  max_daily_trades: 3           # 每日最大交易次数
  max_consecutive_losses: 2     # 最大连续亏损次数
  
# 交易参数
trading:
  min_trade_amount: 100         # 最小交易金额
  position_sizing: "fixed"      # 仓位计算方式: fixed/percentage/risk_based
  commission: 0.005             # 手续费率
  
# 监控参数
monitoring:
  price_alert_threshold: 0.02   # 价格提醒阈值2%
  volume_alert_threshold: 2.0   # 成交量提醒阈值
  
# 回测参数
backtest:
  enabled: true
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  initial_capital: 10000
```

### 2.4 具体股票配置示例 (config/stocks/TSLA.yaml)

```yaml
# Tesla股票配置
stock:
  symbol: "TSLA"
  name: "Tesla Inc."
  exchange: "NASDAQ"
  currency: "USD"
  active: true

strategy:
  type: "intraday_momentum"
  
  technical:
    lookback_days: 30           # Tesla波动大，需要更多历史数据
    support_resistance:
      window: 25                # 更大的计算窗口
      min_touches: 3            # 更严格的确认
      tolerance: 0.015          # 1.5%容差
      
  signals:
    min_confidence: 0.7         # 更高的信号要求
    volume_confirmation: true
    volume_multiplier: 2.0      # Tesla成交量要求更高

risk:
  max_position_pct: 0.08        # Tesla风险大，仓位控制更严格
  stop_loss_pct: 0.025          # 2.5%止损
  take_profit_levels:
    - level: 0.04               # 4%第一止盈
      portion: 0.4
    - level: 0.07               # 7%第二止盈
      portion: 0.6
      
  max_daily_trades: 2           # 限制日内交易次数
  
trading:
  min_trade_amount: 200         # Tesla单价高，最小交易额提高
  position_sizing: "risk_based" # 基于风险的仓位管理

monitoring:
  price_alert_threshold: 0.03   # 3%价格提醒
  
# Tesla特有参数
tesla_specific:
  earnings_sensitive: true      # 对财报敏感
  news_impact_multiplier: 1.5   # 新闻影响系数
  elon_tweet_factor: true       # 考虑马斯克推特影响
```

## 3. 代码组织规范

### 3.1 模块导入规范

```python
# 标准库导入
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union

# 第三方库导入
import pandas as pd
import numpy as np
import yfinance as yf
from sqlalchemy import create_engine

# 本地模块导入
from app.core.assistant import TradingAssistant
from app.models.signal import Signal
from app.utils.helpers import format_price
```

### 3.2 类和函数命名规范

```python
# 类名：PascalCase
class TradingAssistant:
    pass

class MarketDataManager:
    pass

# 函数名：snake_case  
def get_current_price():
    pass

def calculate_support_resistance():
    pass

# 常量：UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30
MAX_RETRY_TIMES = 3

# 配置键：lower_snake_case
config = {
    'data_source': 'yfinance',
    'cache_ttl': 300,
    'risk_management': {
        'max_position': 0.15
    }
}
```

### 3.3 文档字符串规范

```python
def calculate_technical_indicators(data: pd.DataFrame, config: Dict) -> Dict:
    """
    计算技术指标
    
    Args:
        data: 价格数据DataFrame，包含OHLCV列
        config: 技术指标配置参数
        
    Returns:
        Dict: 包含各种技术指标的字典
        {
            'rsi': float,
            'macd': Dict,
            'support_levels': List[float],
            'resistance_levels': List[float]
        }
        
    Raises:
        ValueError: 当数据不足时抛出异常
        
    Example:
        >>> data = get_price_data('TSLA', 30)
        >>> config = {'rsi_period': 14, 'macd_fast': 12}
        >>> indicators = calculate_technical_indicators(data, config)
        >>> print(indicators['rsi'])
        65.4
    """
    pass
```

### 3.4 配置加载规范

```python
# app/utils/config_loader.py
import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.system_config = self._load_system_config()
        
    def load_stock_config(self, symbol: str) -> Dict[str, Any]:
        """加载股票配置"""
        config_file = os.path.join(self.config_dir, "stocks", f"{symbol}.yaml")
        
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Stock config not found: {config_file}")
            
        with open(config_file, 'r') as f:
            stock_config = yaml.safe_load(f)
            
        # 合并系统默认配置
        merged_config = self._merge_configs(self.system_config, stock_config)
        
        # 环境变量替换
        merged_config = self._substitute_env_vars(merged_config)
        
        return merged_config
        
    def _merge_configs(self, system: Dict, stock: Dict) -> Dict:
        """合并配置，股票配置覆盖系统配置"""
        # 深度合并逻辑
        pass
        
    def _substitute_env_vars(self, config: Dict) -> Dict:
        """替换环境变量"""
        # ${VAR_NAME} 格式的环境变量替换
        pass
```

## 4. 开发规范

### 4.1 Git提交规范

```bash
# 提交格式：<type>(<scope>): <description>

# 类型说明：
feat:     新功能
fix:      Bug修复
docs:     文档更新
style:    代码格式修改
refactor: 代码重构
test:     测试相关
chore:    构建过程或辅助工具变动

# 示例：
git commit -m "feat(signals): add MACD signal generation"
git commit -m "fix(data): handle API timeout gracefully"
git commit -m "docs(config): update stock configuration guide"
```

### 4.2 代码质量标准

```python
# 使用类型提示
def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    pass

# 异常处理
try:
    price = data_source.get_price(symbol)
except APIError as e:
    logger.error(f"Failed to get price for {symbol}: {e}")
    return None
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise

# 日志记录
import logging
logger = logging.getLogger(__name__)

logger.info(f"Starting analysis for {symbol}")
logger.warning(f"Low confidence signal: {confidence}")
logger.error(f"API call failed: {error}")
```

### 4.3 测试规范

```python
# tests/unit/test_core/test_signals.py
import pytest
from app.core.signals import SignalGenerator
from app.models.signal import Signal

class TestSignalGenerator:
    
    @pytest.fixture
    def signal_generator(self):
        return SignalGenerator()
        
    def test_generate_buy_signal(self, signal_generator):
        """测试买入信号生成"""
        # Given
        indicators = {
            'rsi': 25,  # 超卖
            'price': 100,
            'support': 98
        }
        
        # When
        signals = signal_generator.generate_signals('TSLA', indicators)
        
        # Then
        assert len(signals) == 1
        assert signals[0].action == 'BUY'
        assert signals[0].confidence > 0.6
```

## 5. 部署配置

### 5.1 环境变量配置 (.env)

```bash
# API密钥
ALPHA_VANTAGE_API_KEY=your_api_key_here
POLYGON_API_KEY=your_polygon_key

# 邮件配置
EMAIL_FROM=trading@example.com
EMAIL_TO=user@example.com  
EMAIL_PASSWORD=your_app_password

# 数据库配置（生产环境）
DATABASE_URL=postgresql://user:pass@localhost:5432/trading

# 应用配置
APP_ENV=development
LOG_LEVEL=DEBUG
CACHE_TTL=300

# 风险控制
MAX_PORTFOLIO_RISK=0.15
MAX_DAILY_TRADES=3
```

### 5.2 Docker配置

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/database logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV APP_ENV=production

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from app.core.assistant import TradingAssistant; print('OK')"

# 启动命令
CMD ["python", "main.py", "--mode", "daemon"]
```

这个项目结构设计提供了：

1. **清晰的目录组织**：按功能模块划分，便于维护
2. **灵活的配置体系**：支持多层配置合并和环境变量
3. **标准的代码规范**：统一的命名和文档规范
4. **完整的开发流程**：从开发到测试到部署的完整规范

你觉得这个第二步的架构设计如何？我们是否可以继续进入第三步？ 