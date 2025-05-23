# 配置指南

## 1. 配置概述

### 1.1 配置体系
美股日内套利助手采用分层配置体系，支持灵活的参数调整：

```
配置层次结构
├── 系统配置 (config/system.yaml)        # 全局系统设置
├── 股票配置 (config/stocks/*.yaml)      # 个股专属配置
├── 策略配置 (config/strategies/*.yaml)  # 自定义策略配置
└── 环境变量 (.env)                      # 敏感信息配置
```

### 1.2 配置优先级
1. **命令行参数** - 最高优先级
2. **环境变量** - 覆盖配置文件
3. **个股配置** - 覆盖系统默认值
4. **系统配置** - 基础默认值

### 1.3 配置管理原则
- **安全第一**：敏感信息存储在环境变量
- **个性化**：每只股票可独立配置
- **向后兼容**：版本升级不破坏现有配置
- **验证机制**：配置错误时提供明确提示

## 2. 系统配置

### 2.1 主配置文件

**config/system.yaml：**
```yaml
# 美股日内套利助手 - 系统配置
version: "1.0.0"
updated: "2024-12-19"

# 应用基础设置
app:
  name: "US Stock Intraday Arbitrage Assistant"
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  timezone: "America/New_York"  # 美东时间
  language: "zh_CN"
  
# 数据源配置
data:
  # 主数据源
  primary_source: "yfinance"
  
  # 备用数据源
  fallback_sources:
    - "alpha_vantage"
    - "finnhub"
  
  # 缓存设置
  cache:
    price_ttl: 60          # 价格数据缓存时间（秒）
    history_ttl: 3600      # 历史数据缓存时间（秒）
    indicators_ttl: 300    # 技术指标缓存时间（秒）
  
  # API限制
  rate_limits:
    requests_per_minute: 300
    requests_per_hour: 5000
    
# 分析参数
analysis:
  # 默认技术分析参数
  default_lookback_days: 20
  min_volume_threshold: 1000000      # 最小成交量
  min_volatility_threshold: 0.02    # 最小波动率
  
  # 支撑阻力位识别
  support_resistance:
    window: 20
    min_touches: 2
    tolerance: 0.01
  
  # 技术指标参数
  indicators:
    rsi_period: 14
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    atr_period: 14
    volume_ma_period: 20

# 风险控制全局设置
risk:
  # 总仓位控制
  max_total_exposure: 0.80           # 最大总仓位比例
  emergency_cash_reserve: 0.05       # 紧急现金储备
  
  # 单股票风险
  default_max_position_pct: 0.15     # 默认单股票最大仓位
  default_stop_loss_pct: 0.02       # 默认止损比例
  default_take_profit_pct: 0.05     # 默认止盈比例
  
  # 交易频率控制
  max_daily_trades: 10               # 每日最大交易次数
  max_trades_per_stock: 3            # 单股票每日最大交易次数
  
  # 连续亏损控制
  max_consecutive_losses: 3          # 最大连续亏损次数
  loss_pause_hours: 2                # 连续亏损后暂停时间

# 信号生成设置
signals:
  min_confidence: 0.60               # 最小信号置信度
  max_signals_per_analysis: 5        # 单次分析最大信号数
  signal_expiry_minutes: 30          # 信号有效期
  
  # 信号过滤
  filters:
    volume_confirmation: true        # 需要成交量确认
    trend_confirmation: true         # 需要趋势确认
    rsi_bounds: [20, 80]            # RSI有效范围

# 监控设置
monitoring:
  # 实时监控
  update_interval: 300               # 更新间隔（秒）
  market_hours_only: true           # 仅在交易时间监控
  
  # 交易时间（美东时间）
  trading_hours:
    start: "09:30"
    end: "16:00"
    timezone: "America/New_York"
  
  # 盘前盘后
  extended_hours:
    enabled: false
    premarket_start: "04:00"
    aftermarket_end: "20:00"

# 通知设置
notifications:
  enabled: true
  
  # 通知类型
  types:
    - "high_confidence_signals"      # 高置信度信号
    - "stop_loss_triggered"         # 止损触发
    - "daily_summary"               # 日度总结
    - "system_errors"               # 系统错误
  
  # 通知渠道
  channels:
    console: true                    # 控制台输出
    file: true                      # 文件记录
    email: false                    # 邮件通知
    webhook: false                  # Webhook通知

# 数据库设置
database:
  type: "sqlite"
  path: "data/trading_assistant.db"
  
  # 备份设置
  backup:
    enabled: true
    frequency: "daily"
    retention_days: 30
    path: "backups/"

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # 日志文件
  files:
    main: "logs/trading_assistant.log"
    errors: "logs/errors.log"
    trades: "logs/trades.log"
  
  # 日志轮转
  rotation:
    max_size: "10MB"
    backup_count: 5

# 性能设置
performance:
  max_workers: 4                     # 最大工作线程数
  memory_limit: "500MB"              # 内存限制
  
  # 并发控制
  concurrent_analysis: 3             # 并发分析股票数
  batch_size: 10                     # 批处理大小
```

### 2.2 环境变量配置

**.env 文件：**
```bash
# 应用基础配置
APP_NAME="US Stock Intraday Arbitrage Assistant"
LOG_LEVEL=INFO
DEBUG=false

# 数据源API密钥
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FINNHUB_API_KEY=your_finnhub_key_here
POLYGON_API_KEY=your_polygon_key_here

# 邮件通知配置
EMAIL_ENABLED=false
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=trader@example.com

# Webhook通知
WEBHOOK_URL=https://your-webhook-url.com/trading-alerts
WEBHOOK_SECRET=your_webhook_secret

# 交易配置
INITIAL_CAPITAL=100000
PAPER_TRADING=true

# 数据库配置
DATABASE_PATH=data/trading_assistant.db
BACKUP_ENABLED=true

# 安全设置
SECRET_KEY=your_secret_key_here
```

## 3. 股票配置

### 3.1 个股配置模板

**config/stocks/TSLA.yaml：**
```yaml
# 特斯拉 (TSLA) 个股配置
stock:
  symbol: "TSLA"
  name: "Tesla Inc."
  active: true
  market: "NASDAQ"
  sector: "Automotive"
  
# 策略配置
strategy:
  type: "support_resistance"        # 主要策略类型
  
  # 技术分析参数
  technical:
    lookback_days: 20               # 历史数据回望天数
    support_resistance:
      window: 15                    # 支撑阻力位识别窗口
      min_touches: 2                # 最小触及次数
      tolerance: 0.015              # 价位容忍度 (1.5%)
    
    indicators:
      rsi_period: 14
      rsi_oversold: 30              # RSI超卖阈值
      rsi_overbought: 70            # RSI超买阈值
      
      macd_fast: 12
      macd_slow: 26
      macd_signal: 9
      
      volume_threshold: 1.5         # 成交量放大倍数

# 风险控制
risk:
  # 仓位管理
  max_position_pct: 0.15            # 最大仓位比例 (15%)
  max_position_value: 15000         # 最大仓位金额
  
  # 止损止盈
  stop_loss_pct: 0.025              # 止损比例 (2.5%)
  take_profit_levels:               # 分层止盈
    - level: 0.03                   # 3% 止盈一半
      quantity_pct: 0.5
    - level: 0.06                   # 6% 全部止盈
      quantity_pct: 1.0
  
  # 交易频率
  max_daily_trades: 3               # 每日最大交易次数
  min_trade_interval: 1800          # 最小交易间隔（秒）
  
  # 资金管理
  min_trade_amount: 1000            # 最小交易金额
  position_sizing: "fixed_percent"  # 仓位计算方式

# 信号参数
signals:
  min_confidence: 0.65              # 最小信号置信度
  
  # 买入信号条件
  buy_conditions:
    near_support: 0.01              # 接近支撑位距离
    rsi_oversold: true              # 需要RSI超卖确认
    volume_confirmation: true       # 需要成交量确认
    
  # 卖出信号条件  
  sell_conditions:
    near_resistance: 0.01           # 接近阻力位距离
    rsi_overbought: true            # 需要RSI超买确认
    volume_confirmation: true
    
  # 信号有效期
  signal_expiry: 1800               # 信号有效期（秒）

# 监控设置
monitoring:
  enabled: true
  priority: "high"                  # 监控优先级
  alert_threshold: 0.8              # 告警阈值

# 特殊设置
special:
  earnings_pause: true              # 财报期间暂停交易
  news_sensitivity: "medium"        # 新闻敏感度
  volatility_filter: 0.025          # 最小波动率过滤

# 回测设置
backtest:
  enabled: true
  start_date: "2023-01-01"
  commission_rate: 0.001            # 手续费率
  slippage: 0.0005                  # 滑点
```

### 3.2 其他股票配置示例

**config/stocks/NVDA.yaml：**
```yaml
stock:
  symbol: "NVDA"
  name: "NVIDIA Corporation"
  active: true
  
strategy:
  type: "momentum_breakout"         # 突破策略
  
  technical:
    breakout_period: 10
    volume_threshold: 2.0           # 更高的成交量要求
    
risk:
  max_position_pct: 0.12            # 相对保守的仓位
  stop_loss_pct: 0.02
  take_profit_pct: 0.04
  
signals:
  min_confidence: 0.70              # 更高的置信度要求
```

**config/stocks/AAPL.yaml：**
```yaml
stock:
  symbol: "AAPL"
  name: "Apple Inc."
  active: true
  
strategy:
  type: "mean_reversion"            # 均值回归策略
  
  technical:
    lookback_days: 30               # 更长的历史数据
    bollinger_period: 20
    bollinger_std: 2
    
risk:
  max_position_pct: 0.20            # 较大仓位（稳定股票）
  stop_loss_pct: 0.015              # 较小止损
  
signals:
  min_confidence: 0.60              # 较低置信度要求
```

## 4. 策略配置

### 4.1 策略配置文件

**config/strategies/custom_intraday.yaml：**
```yaml
# 自定义日内策略配置
strategy:
  name: "CustomIntradayStrategy"
  version: "1.0.0"
  description: "个性化日内交易策略"
  
  # 策略参数
  parameters:
    # 时间参数
    analysis_window: 30             # 分析时间窗口（天）
    signal_cooldown: 1800           # 信号冷却时间（秒）
    
    # 技术指标权重
    indicator_weights:
      support_resistance: 0.4       # 支撑阻力位权重
      rsi: 0.3                     # RSI权重
      volume: 0.2                  # 成交量权重
      trend: 0.1                   # 趋势权重
    
    # 阈值设置
    thresholds:
      strong_signal: 0.8           # 强信号阈值
      moderate_signal: 0.6         # 中等信号阈值
      weak_signal: 0.4             # 弱信号阈值
  
  # 适用股票
  applicable_stocks:
    - "TSLA"
    - "NVDA"
    - "META"
    - "GOOGL"
  
  # 市场条件过滤
  market_filters:
    min_volume: 5000000            # 最小成交量
    max_spread_pct: 0.005          # 最大买卖价差
    min_price: 10                  # 最小股价
    max_price: 1000                # 最大股价
```

### 4.2 组合策略配置

**config/strategies/portfolio_strategy.yaml：**
```yaml
# 投资组合策略配置
portfolio:
  name: "Balanced Intraday Portfolio"
  
  # 资金分配
  allocation:
    aggressive: 0.4               # 激进策略配置40%
    moderate: 0.4                 # 温和策略配置40%
    conservative: 0.2             # 保守策略配置20%
  
  # 股票分组
  stock_groups:
    high_volatility:              # 高波动组
      stocks: ["TSLA", "NIO"]
      max_allocation: 0.3
      strategy: "momentum_breakout"
      
    tech_giants:                  # 科技巨头组
      stocks: ["AAPL", "GOOGL", "META"]
      max_allocation: 0.5
      strategy: "support_resistance"
      
    growth_stocks:                # 成长股组
      stocks: ["NVDA", "AMD"]
      max_allocation: 0.2
      strategy: "trend_following"
  
  # 相关性控制
  correlation_limits:
    max_sector_exposure: 0.6      # 单行业最大暴露
    max_correlation: 0.7          # 最大相关性
  
  # 再平衡设置
  rebalancing:
    frequency: "daily"
    threshold: 0.05               # 偏离阈值
    max_trades_per_rebalance: 5
```

## 5. 配置管理

### 5.1 配置验证

**配置验证规则：**
```python
# 配置验证示例
VALIDATION_RULES = {
    'risk.max_position_pct': {
        'type': float,
        'min': 0.01,
        'max': 0.5,
        'default': 0.15
    },
    'risk.stop_loss_pct': {
        'type': float,
        'min': 0.005,
        'max': 0.1,
        'default': 0.02
    },
    'signals.min_confidence': {
        'type': float,
        'min': 0.1,
        'max': 1.0,
        'default': 0.6
    }
}
```

### 5.2 配置命令

```bash
# 验证所有配置
python main.py config validate

# 查看配置概览
python main.py config show

# 设置配置项
python main.py config set risk.max_position_pct 0.20

# 获取配置项
python main.py config get risk.stop_loss_pct

# 重置为默认值
python main.py config reset risk

# 导出配置
python main.py config export --format yaml > my_config.yaml

# 导入配置
python main.py config import my_config.yaml
```

### 5.3 配置模板

**生成配置模板：**
```bash
# 为新股票生成配置模板
python main.py config template --symbol AMZN --strategy support_resistance

# 生成完整系统配置模板
python main.py config template --type system

# 生成策略配置模板
python main.py config template --type strategy --name custom_momentum
```

## 6. 配置最佳实践

### 6.1 安全配置

```yaml
# 敏感信息处理
security:
  # 永远不要在配置文件中硬编码API密钥
  api_keys:
    alpha_vantage: "${ALPHA_VANTAGE_API_KEY}"  # 使用环境变量
    
  # 密码和令牌
  tokens:
    webhook_secret: "${WEBHOOK_SECRET}"
    
  # 文件权限
  file_permissions:
    config_files: "600"           # 配置文件权限
    log_files: "644"              # 日志文件权限
```

### 6.2 性能配置

```yaml
# 性能优化配置
performance:
  # 缓存策略
  cache_strategy: "aggressive"    # conservative, moderate, aggressive
  
  # 并发设置
  concurrency:
    analysis_workers: 4           # 分析工作线程
    io_workers: 8                 # IO工作线程
    
  # 内存管理
  memory:
    max_cache_size: "100MB"       # 最大缓存大小
    gc_threshold: 0.8             # 垃圾回收阈值
    
  # 网络优化
  network:
    connection_pool_size: 10      # 连接池大小
    request_timeout: 30           # 请求超时时间
    retry_attempts: 3             # 重试次数
```

### 6.3 监控配置

```yaml
# 监控告警配置
monitoring:
  # 性能指标
  performance_metrics:
    - "response_time"
    - "memory_usage"
    - "cache_hit_rate"
    - "api_call_rate"
    
  # 告警阈值
  alerts:
    high_memory_usage: 0.85       # 内存使用率告警
    slow_response: 5.0            # 响应时间告警（秒）
    api_error_rate: 0.1           # API错误率告警
    
  # 健康检查
  health_check:
    interval: 300                 # 检查间隔（秒）
    timeout: 10                   # 检查超时
    retries: 3                    # 重试次数
```

## 7. 环境配置

### 7.1 开发环境

**config/environments/development.yaml：**
```yaml
environment: "development"

app:
  debug: true
  log_level: "DEBUG"
  
data:
  cache:
    price_ttl: 10                 # 更短的缓存时间
    
risk:
  paper_trading: true             # 模拟交易
  
notifications:
  console: true
  email: false
```

### 7.2 生产环境

**config/environments/production.yaml：**
```yaml
environment: "production"

app:
  debug: false
  log_level: "INFO"
  
risk:
  paper_trading: false            # 实盘交易
  max_total_exposure: 0.7         # 更保守的仓位
  
notifications:
  console: false
  email: true
  webhook: true
```

### 7.3 测试环境

**config/environments/test.yaml：**
```yaml
environment: "test"

database:
  path: ":memory:"               # 内存数据库
  
data:
  primary_source: "mock"         # 模拟数据源
  
risk:
  paper_trading: true
  initial_capital: 10000
```

## 8. 配置故障排除

### 8.1 常见配置错误

**1. 格式错误**
```yaml
# 错误：缩进不正确
risk:
max_position_pct: 0.15

# 正确：正确的缩进
risk:
  max_position_pct: 0.15
```

**2. 类型错误**
```yaml
# 错误：字符串值
risk:
  max_position_pct: "0.15"

# 正确：数值类型
risk:
  max_position_pct: 0.15
```

**3. 范围错误**
```yaml
# 错误：超出有效范围
risk:
  max_position_pct: 1.5          # 150%仓位

# 正确：合理范围
risk:
  max_position_pct: 0.15         # 15%仓位
```

### 8.2 配置诊断

```bash
# 配置文件语法检查
python main.py config lint

# 配置完整性检查
python main.py config check --comprehensive

# 配置性能分析
python main.py config benchmark

# 配置兼容性检查
python main.py config compatibility --version 1.0.0
```

### 8.3 配置恢复

```bash
# 备份当前配置
python main.py config backup --name manual_backup_$(date +%Y%m%d)

# 恢复默认配置
python main.py config restore --default

# 从备份恢复
python main.py config restore --backup manual_backup_20241219

# 配置回滚
python main.py config rollback --steps 1
```

通过这个完整的配置指南，用户可以精确控制美股日内套利助手的每个方面，实现个性化的投资策略！
