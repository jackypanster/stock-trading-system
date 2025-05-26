# 美股日内套利助手 - 用户使用教程

本教程将详细介绍如何使用美股日内套利助手的各项功能，帮助您快速上手并充分利用系统的分析能力。

## 📚 目录

1. [快速开始](#快速开始)
2. [基础功能](#基础功能)
3. [高级功能](#高级功能)
4. [配置管理](#配置管理)
5. [实战案例](#实战案例)
6. [最佳实践](#最佳实践)
7. [故障排除](#故障排除)

## 🚀 快速开始

### 第一次使用

确保您已经按照 [安装指南](installation-guide.md) 完成了系统安装。

#### 1. 验证安装
```bash
# 检查系统版本
python main.py --version

# 查看帮助信息
python main.py --help
```

#### 2. 测试基础功能
```bash
# 测试数据获取（使用模拟数据）
python main.py test-data AAPL --mock

# 分析一只股票
python main.py analyze TSLA
```

#### 3. 查看系统状态
```bash
# 检查系统状态
python main.py status
```

## 📊 基础功能

### 1. 股票分析 (analyze)

`analyze` 命令是系统的核心功能，提供全面的技术分析。

#### 基础用法
```bash
# 分析特斯拉股票
python main.py analyze TSLA

# 分析苹果股票，指定分析天数
python main.py analyze AAPL --days 30

# 使用JSON格式输出
python main.py analyze NVDA --format json
```

#### 输出格式选项
```bash
# 表格格式（默认）
python main.py analyze TSLA --format table

# JSON格式（便于程序处理）
python main.py analyze TSLA --format json

# CSV格式（便于Excel处理）
python main.py analyze TSLA --format csv
```

#### 分析结果解读

**RSI分析**：
- `当前RSI`: 相对强弱指标值（0-100）
- `状态`: 超买(>70)、超卖(<30)、正常(30-70)
- `信号`: 买入信号、卖出信号、无信号

**MACD分析**：
- `MACD线`: 快速EMA与慢速EMA的差值
- `信号线`: MACD的9期EMA
- `交叉信号`: 金叉（买入）、死叉（卖出）
- `位置`: 多头区域、空头区域、过渡区域

**ATR分析**：
- `当前ATR`: 平均真实范围，衡量波动率
- `波动率水平`: 高波动、正常波动、低波动
- `建议止损位`: 基于ATR倍数的止损建议

**支撑阻力位**：
- `支撑位`: 价格可能反弹的关键位置
- `阻力位`: 价格可能回调的关键位置
- `强度评级`: 强、中、弱

### 2. 信号扫描 (signals)

`signals` 命令用于扫描多只股票的交易信号。

#### 基础用法
```bash
# 扫描默认股票池的信号
python main.py signals

# 扫描指定股票的信号
python main.py signals --symbol TSLA

# 只显示今日信号
python main.py signals --today
```

#### 信号过滤
```bash
# 只显示高置信度信号（≥0.7）
python main.py signals --min-confidence 0.7

# 只显示买入信号
python main.py signals --action buy

# 只显示卖出信号
python main.py signals --action sell

# 限制信号数量
python main.py signals --limit 5
```

#### 高级过滤
```bash
# 组合过滤条件
python main.py signals --min-confidence 0.6 --action buy --limit 3

# 使用监控列表模式
python main.py signals --watchlist --min-confidence 0.65
```

#### 信号结果解读

**信号类型**：
- `buy`: 买入信号
- `sell`: 卖出信号
- `hold`: 持有信号

**置信度**：
- `0.8-1.0`: 高置信度，强烈推荐
- `0.6-0.8`: 中等置信度，谨慎考虑
- `0.4-0.6`: 低置信度，观望为主
- `<0.4`: 极低置信度，不建议操作

**风险指标**：
- `止损价`: 建议的止损位置
- `止盈价`: 建议的止盈位置
- `风险回报比`: 预期收益与风险的比例

### 3. 配置管理 (config)

`config` 命令用于管理系统配置。

#### 查看配置
```bash
# 查看所有配置
python main.py config show

# 查看特定配置节
python main.py config show --section app
python main.py config show --section data
python main.py config show --section risk

# 查看股票配置
python main.py config show --section stocks

# 查看策略配置
python main.py config show --section strategies
```

#### 设置配置
```bash
# 设置应用配置
python main.py config set app.debug true

# 设置数据源配置
python main.py config set data.cache_ttl 600

# 设置风险参数
python main.py config set risk.max_position_pct 0.2
```

#### 配置验证
```bash
# 验证所有配置
python main.py config validate

# 验证特定配置节
python main.py config validate --section data
```

#### 配置备份和恢复
```bash
# 备份当前配置
python main.py config backup

# 恢复配置
python main.py config restore --backup-file config_backup_20250526.yaml

# 重置为默认配置
python main.py config reset --section app
```

### 4. 系统状态 (status)

检查系统运行状态和健康度。

```bash
# 查看系统状态
python main.py status

# 详细状态信息
python main.py status --verbose

# 检查数据源连接
python main.py status --check-data

# 检查配置完整性
python main.py status --check-config
```

### 5. 数据测试功能

#### 测试数据获取
```bash
# 测试真实数据获取
python main.py test-data AAPL

# 测试模拟数据
python main.py test-data AAPL --mock

# 指定获取天数
python main.py test-data TSLA --days 10

# 测试多只股票（需要分别执行）
python main.py test-data AAPL --mock
python main.py test-data TSLA --mock
python main.py test-data NVDA --mock
```

#### 测试备用数据源
```bash
# 测试备用数据源切换
python main.py test-backup AAPL

# 指定测试次数
python main.py test-backup TSLA --calls 5

# 强制触发备用源
python main.py test-backup NVDA --force-backup
```

## 🎯 高级功能

### 1. 批量分析

#### 分析多只股票
```bash
# 创建股票列表文件
echo "TSLA\nNVDA\nAAPL\nMETA\nAMD" > my_stocks.txt

# 批量分析（需要脚本支持）
for symbol in $(cat my_stocks.txt); do
    echo "分析 $symbol..."
    python main.py analyze $symbol --format json > "analysis_${symbol}.json"
done
```

#### 定时分析
```bash
# 使用cron定时执行（Linux/macOS）
# 编辑crontab
crontab -e

# 添加定时任务（每小时执行一次）
0 * * * * cd /path/to/stock-trading-system && python main.py signals --min-confidence 0.7 >> daily_signals.log
```

### 2. 数据导出和处理

#### 导出分析结果
```bash
# 导出为JSON格式
python main.py analyze TSLA --format json > tsla_analysis.json

# 导出为CSV格式
python main.py analyze TSLA --format csv > tsla_analysis.csv

# 导出信号数据
python main.py signals --format json > daily_signals.json
```

#### 处理导出数据
```python
# Python脚本示例：处理JSON数据
import json

# 读取分析结果
with open('tsla_analysis.json', 'r') as f:
    data = json.load(f)

# 提取关键信息
current_price = data['current_price']
rsi = data['indicators']['rsi_14']['current_rsi']
signal = data['indicators']['rsi_14']['signal']

print(f"TSLA当前价格: ${current_price}")
print(f"RSI: {rsi}")
print(f"信号: {signal}")
```

### 3. 自定义配置

#### 创建自定义股票配置
```bash
# 创建新股票配置文件
mkdir -p config/stocks
cat > config/stocks/AMZN.yaml << EOF
stock:
  symbol: "AMZN"
  name: "Amazon.com Inc."
  active: true

strategy:
  type: "support_resistance"
  parameters:
    lookback_days: 20
    min_touches: 2
    tolerance: 0.5

risk:
  stop_loss_pct: 0.025
  take_profit_pct: 0.05
  max_position_pct: 0.1
  max_daily_trades: 2
EOF
```

#### 创建自定义策略配置
```bash
# 创建策略配置文件
mkdir -p config/strategies
cat > config/strategies/aggressive.yaml << EOF
strategy:
  name: "aggressive"
  description: "激进交易策略"

parameters:
  min_confidence: 0.6
  max_signals_per_day: 10
  risk_tolerance: "high"

risk:
  stop_loss_pct: 0.03
  take_profit_pct: 0.06
  max_position_pct: 0.2
EOF
```

## ⚙️ 配置管理

### 1. 系统配置文件

#### config/system.yaml
```yaml
app:
  name: "美股日内套利助手"
  version: "1.0.0"
  debug: false

data:
  source: "yfinance"
  cache_enabled: true
  cache_ttl: 300
  backup_enabled: true

logging:
  level: "INFO"
  file_enabled: true
  max_file_size: "10MB"
  backup_count: 5

risk:
  default_stop_loss_pct: 0.02
  default_take_profit_pct: 0.04
  max_position_pct: 0.15
  max_daily_trades: 3
```

### 2. 环境变量配置

#### .env 文件
```bash
# 应用配置
APP_NAME=美股日内套利助手
DEBUG=false

# 数据源配置
DATA_SOURCE=yfinance
CACHE_ENABLED=true
CACHE_TTL=300

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=true

# API密钥（可选）
ALPHA_VANTAGE_API_KEY=your_key_here
```

### 3. 配置优先级

配置的优先级从高到低：
1. 命令行参数
2. 环境变量
3. .env 文件
4. 配置文件 (config/*.yaml)
5. 默认值

## 📈 实战案例

### 案例1：日内交易信号识别

**目标**：识别TSLA的日内交易机会

```bash
# 1. 分析当前技术状态
python main.py analyze TSLA --format table

# 2. 查看交易信号
python main.py signals --symbol TSLA --min-confidence 0.6

# 3. 监控关键价位
python main.py analyze TSLA --format json | jq '.support_resistance'
```

**分析步骤**：
1. 查看RSI是否接近超买/超卖区域
2. 确认MACD是否有交叉信号
3. 检查价格是否接近支撑/阻力位
4. 评估ATR判断波动率水平
5. 综合置信度做出交易决策

### 案例2：多股票组合监控

**目标**：监控科技股组合的交易机会

```bash
# 1. 定义股票池并批量分析
TECH_STOCKS=("TSLA" "NVDA" "AAPL" "META" "GOOGL" "AMZN")

# 2. 批量分析
for symbol in "${TECH_STOCKS[@]}"; do
    python main.py signals --symbol $symbol --min-confidence 0.65
done

# 3. 筛选高质量信号
python main.py signals --watchlist --min-confidence 0.75 --limit 3

# 4. 导出结果
python main.py signals --watchlist --format json > tech_signals.json
```

### 案例3：风险控制实践

**目标**：为NVDA设置合理的风险参数

```bash
# 1. 分析NVDA的波动特征
python main.py analyze NVDA --days 30

# 2. 查看ATR建议的止损位
python main.py analyze NVDA --format json | jq '.indicators.atr.stop_loss_levels'

# 3. 配置个性化风险参数
python main.py config set stocks.NVDA.risk.stop_loss_pct 0.025
python main.py config set stocks.NVDA.risk.max_position_pct 0.12

# 4. 验证配置
python main.py config show --section stocks.NVDA
```

## 💡 最佳实践

### 1. 交易信号使用建议

#### 信号确认原则
- **多重确认**：至少2-3个技术指标同时确认
- **置信度筛选**：优先考虑置信度>0.7的信号
- **市场环境**：考虑整体市场趋势和波动率
- **风险回报比**：确保风险回报比≥2:1

#### 信号执行时机
```bash
# 1. 盘前分析
python main.py signals --min-confidence 0.7 --format table

# 2. 盘中监控
python main.py analyze TSLA  # 关注关键价位

# 3. 盘后复盘
python main.py signals --today --format json > daily_review.json
```

### 2. 风险管理实践

#### 仓位管理
- 单只股票最大仓位：10-15%
- 总仓位控制：不超过80%
- 止损严格执行：2-3%止损
- 分批建仓：避免一次性满仓

#### 风险监控
```bash
# 每日风险检查
python main.py status --check-risk

# 配置风险警报
python main.py config set risk.max_daily_loss 0.05
```

### 3. 数据管理

#### 缓存优化
```bash
# 定期清理缓存
python main.py config clear-cache

# 调整缓存时间
python main.py config set data.cache_ttl 600  # 10分钟
```

#### 日志管理
```bash
# 查看错误日志
tail -f logs/error.log

# 调整日志级别
python main.py config set logging.level DEBUG
```

### 4. 性能优化

#### 提高分析速度
- 使用缓存：启用数据缓存
- 限制历史数据：使用合适的天数
- 批量处理：避免频繁单次调用

#### 资源管理
```bash
# 监控系统资源
python main.py status --verbose

# 优化内存使用
python main.py config set data.max_history_days 30
```

## 🔧 故障排除

### 常见问题解决

#### 1. 数据获取失败
```bash
# 检查网络连接
ping google.com

# 测试数据源
python main.py test-data AAPL --mock

# 检查API限制
python main.py status --check-data
```

#### 2. 分析结果异常
```bash
# 检查数据质量
python main.py analyze TSLA --debug

# 验证配置
python main.py config validate

# 查看详细日志
tail -f logs/analysis.log
```

#### 3. 配置问题
```bash
# 重置配置
python main.py config reset --section app

# 恢复备份
python main.py config restore

# 验证配置
python main.py config validate --verbose
```

#### 4. 性能问题
```bash
# 清理缓存
python main.py config clear-cache

# 检查系统状态
python main.py status --verbose

# 调整配置
python main.py config set data.cache_ttl 300
```

### 调试技巧

#### 启用调试模式
```bash
# 临时启用调试
python main.py --debug analyze TSLA

# 永久启用调试
python main.py config set app.debug true
```

#### 查看详细日志
```bash
# 实时查看日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log

# 查看特定模块日志
grep "analysis" logs/app.log
```

## 📞 获取帮助

### 内置帮助
```bash
# 查看命令帮助
python main.py --help
python main.py analyze --help
python main.py signals --help
python main.py config --help
```

### 系统诊断
```bash
# 运行系统诊断
python main.py status --verbose

# 检查配置完整性
python main.py config validate --all

# 测试核心功能
python main.py test-data AAPL --mock
```

### 社区支持
- GitHub Issues：报告问题和建议
- 文档中心：查看详细文档
- 示例代码：参考实际使用案例

## 🎯 下一步学习

完成本教程后，建议您：

1. **深入学习**：
   - 阅读 [策略开发指南](strategy-development.md)
   - 了解 [技术分析原理](technical-analysis.md)
   - 学习 [风险管理](risk-management.md)

2. **实践应用**：
   - 使用模拟数据练习
   - 建立个人股票池
   - 制定交易计划

3. **高级功能**：
   - 自定义策略开发
   - API集成使用
   - 自动化交易脚本

4. **持续改进**：
   - 记录交易日志
   - 分析策略效果
   - 优化参数设置

恭喜您完成了用户教程！现在您已经掌握了美股日内套利助手的核心功能。开始您的智能投资之旅吧！🚀

---

**重要提醒**：
- 本工具仅供学习和研究使用
- 所有信号仅为技术分析结果，不构成投资建议
- 请根据自身风险承受能力谨慎投资
- 建议先使用模拟交易验证策略有效性 