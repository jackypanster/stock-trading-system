# CLI接口文档

## 1. 接口概述

### 1.1 设计理念
- **CLI优先**：命令行界面是主要交互方式
- **简单直观**：命令和参数清晰易懂
- **批处理友好**：支持脚本化操作
- **输出格式化**：支持JSON、表格等多种输出格式

### 1.2 命令结构
```
python main.py [COMMAND] [OPTIONS] [ARGUMENTS]
```

**通用选项：**
- `--config`: 指定配置文件路径
- `--format`: 输出格式 (table/json/csv)
- `--verbose`: 详细输出
- `--help`: 显示帮助信息

## 2. 核心命令

### 2.1 分析命令

#### 单股票分析
```bash
python main.py analyze SYMBOL [OPTIONS]
```

**参数：**
- `SYMBOL`: 股票代码（如 TSLA, AAPL）

**选项：**
- `--days N`: 分析天数（默认20）
- `--indicators LIST`: 指定技术指标
- `--signals`: 包含信号生成
- `--detail`: 详细分析报告

**示例：**
```bash
# 基础分析
python main.py analyze TSLA

# 详细分析含信号
python main.py analyze TSLA --signals --detail

# 指定分析天数
python main.py analyze NVDA --days 30

# JSON格式输出
python main.py analyze AAPL --format json
```

**输出示例：**
```
股票分析报告 - TSLA
==================
基础信息:
  当前价格: $248.50
  日涨跌幅: +2.45% (+$5.95)
  成交量: 125,678,900

技术指标:
  RSI(14): 65.4 (中性)
  MACD: 上升趋势
  支撑位: $245.20, $242.80
  阻力位: $252.10, $256.40

风险评估:
  波动率: 3.2% (高)
  流动性: 优秀
  趋势强度: 中等

信号总结:
  当前建议: 观望
  信号强度: 中等 (6.5/10)
```

#### 多股票批量分析
```bash
python main.py batch SYMBOLS [OPTIONS]
```

**参数：**
- `SYMBOLS`: 股票列表，逗号分隔

**示例：**
```bash
# 分析多只股票
python main.py batch TSLA,NVDA,AAPL,META

# 输出为CSV格式
python main.py batch TSLA,NVDA,AAPL --format csv > analysis.csv
```

### 2.2 监控命令

#### 实时监控
```bash
python main.py monitor [SYMBOLS] [OPTIONS]
```

**选项：**
- `--interval SECONDS`: 监控间隔（默认300秒）
- `--alert-level LEVEL`: 告警级别 (low/medium/high)
- `--daemon`: 后台运行模式

**示例：**
```bash
# 监控默认股票池
python main.py monitor

# 监控特定股票
python main.py monitor TSLA,NVDA

# 后台监控
python main.py monitor --daemon --interval 60
```

#### 今日信号查看
```bash
python main.py signals [OPTIONS]
```

**选项：**
- `--today`: 仅显示今日信号
- `--symbol SYMBOL`: 特定股票信号
- `--min-confidence FLOAT`: 最小置信度过滤

**示例：**
```bash
# 查看今日所有信号
python main.py signals --today

# 查看特定股票信号
python main.py signals --symbol TSLA

# 高置信度信号
python main.py signals --min-confidence 0.8
```

### 2.3 投资组合命令

#### 持仓查看
```bash
python main.py portfolio [OPTIONS]
```

**选项：**
- `--summary`: 仅显示汇总信息
- `--pnl`: 显示盈亏分析
- `--risk`: 显示风险指标

**示例：**
```bash
# 查看完整持仓
python main.py portfolio

# 仅显示汇总
python main.py portfolio --summary

# 盈亏分析
python main.py portfolio --pnl
```

**输出示例：**
```
投资组合状况
============
总资产: $52,450.00
持仓市值: $42,450.00
现金余额: $10,000.00
总收益: +$4,500.00 (+9.4%)

持仓明细:
股票     数量    成本      当前价格   市值       盈亏       比例
TSLA     100    $240.00   $248.50   $24,850   +$850     47.4%
NVDA     50     $180.00   $195.20   $9,760    +$760     18.6%
AAPL     80     $150.00   $155.00   $12,400   +$400     23.6%

风险指标:
单股最大仓位: 47.4% (TSLA)
总仓位比例: 80.9%
组合波动率: 2.8%
```

#### 交易记录
```bash
python main.py trades [OPTIONS]
```

**选项：**
- `--days N`: 查看N天内的交易
- `--symbol SYMBOL`: 特定股票交易
- `--stats`: 显示交易统计

**示例：**
```bash
# 查看最近7天交易
python main.py trades --days 7

# 查看交易统计
python main.py trades --stats
```

### 2.4 配置命令

#### 配置查看和修改
```bash
python main.py config [ACTION] [OPTIONS]
```

**动作：**
- `show`: 显示当前配置
- `set KEY VALUE`: 设置配置项
- `get KEY`: 获取配置项
- `reset`: 重置为默认配置

**示例：**
```bash
# 查看所有配置
python main.py config show

# 设置风险参数
python main.py config set risk.max_position_pct 0.20

# 查看特定配置
python main.py config get risk.stop_loss_pct

# 重置配置
python main.py config reset
```

#### 股票池管理
```bash
python main.py stocks [ACTION] [SYMBOL] [OPTIONS]
```

**动作：**
- `list`: 显示当前股票池
- `add SYMBOL`: 添加股票
- `remove SYMBOL`: 移除股票
- `activate SYMBOL`: 激活股票
- `deactivate SYMBOL`: 停用股票

**示例：**
```bash
# 查看股票池
python main.py stocks list

# 添加新股票
python main.py stocks add GOOGL

# 移除股票
python main.py stocks remove SNAP

# 停用股票（不删除配置）
python main.py stocks deactivate AMD
```

### 2.5 报告命令

#### 生成报告
```bash
python main.py report [TYPE] [OPTIONS]
```

**报告类型：**
- `daily`: 日报
- `weekly`: 周报
- `monthly`: 月报
- `custom`: 自定义时间范围

**选项：**
- `--start DATE`: 开始日期
- `--end DATE`: 结束日期
- `--output FILE`: 输出文件
- `--email`: 发送邮件

**示例：**
```bash
# 生成日报
python main.py report daily

# 生成周报并保存
python main.py report weekly --output weekly_report.pdf

# 自定义时间范围
python main.py report custom --start 2024-01-01 --end 2024-01-31

# 发送邮件报告
python main.py report daily --email
```

### 2.6 回测命令

#### 策略回测
```bash
python main.py backtest [OPTIONS]
```

**选项：**
- `--symbol SYMBOL`: 回测股票
- `--start DATE`: 开始日期
- `--end DATE`: 结束日期
- `--capital AMOUNT`: 初始资金
- `--strategy NAME`: 策略名称

**示例：**
```bash
# 回测TSLA策略
python main.py backtest --symbol TSLA --start 2023-01-01 --end 2023-12-31

# 指定初始资金
python main.py backtest --symbol NVDA --capital 50000

# 回测多只股票
python main.py backtest --start 2023-06-01 --end 2023-12-31
```

### 2.7 系统命令

#### 系统状态
```bash
python main.py status [OPTIONS]
```

**选项：**
- `--health`: 健康检查
- `--performance`: 性能指标
- `--api`: API连接状态

**示例：**
```bash
# 系统状态概览
python main.py status

# 详细健康检查
python main.py status --health

# 性能监控
python main.py status --performance
```

#### 系统管理
```bash
python main.py system [ACTION] [OPTIONS]
```

**动作：**
- `start`: 启动服务
- `stop`: 停止服务
- `restart`: 重启服务
- `cleanup`: 清理缓存和临时文件

**示例：**
```bash
# 启动服务
python main.py system start

# 清理系统
python main.py system cleanup

# 重启
python main.py system restart
```

## 3. 输出格式

### 3.1 表格格式（默认）
```
股票     当前价格    涨跌幅      信号      置信度    建议
TSLA     $248.50    +2.45%     买入      85%       建议买入
NVDA     $195.20    -1.20%     观望      45%       持有观望
AAPL     $155.00    +0.80%     卖出      75%       部分获利
```

### 3.2 JSON格式
```json
{
  "timestamp": "2024-12-19T15:30:00Z",
  "stocks": [
    {
      "symbol": "TSLA",
      "current_price": 248.50,
      "price_change": 5.95,
      "price_change_pct": 0.0245,
      "signal": "BUY",
      "confidence": 0.85,
      "recommendation": "建议买入",
      "indicators": {
        "rsi": 65.4,
        "macd": "上升",
        "support_levels": [245.20, 242.80],
        "resistance_levels": [252.10, 256.40]
      }
    }
  ]
}
```

### 3.3 CSV格式
```csv
symbol,current_price,price_change_pct,signal,confidence,recommendation
TSLA,248.50,0.0245,BUY,0.85,建议买入
NVDA,195.20,-0.0120,HOLD,0.45,持有观望
AAPL,155.00,0.0080,SELL,0.75,部分获利
```

## 4. 错误处理

### 4.1 常见错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| E001 | 股票代码无效 | 检查股票代码拼写 |
| E002 | 网络连接失败 | 检查网络连接 |
| E003 | API配额超限 | 等待配额重置或升级账户 |
| E004 | 配置文件错误 | 检查配置文件格式 |
| E005 | 数据库错误 | 检查数据库文件权限 |

### 4.2 错误输出示例
```bash
$ python main.py analyze INVALID_SYMBOL

错误: 股票代码无效 (E001)
描述: 找不到股票代码 'INVALID_SYMBOL'
建议: 请检查股票代码拼写，或使用以下命令查看支持的股票:
      python main.py stocks list
```

## 5. 高级用法

### 5.1 管道操作
```bash
# 分析结果保存到文件
python main.py analyze TSLA --format json > tsla_analysis.json

# 批量分析并筛选信号
python main.py batch TSLA,NVDA,AAPL --format csv | grep BUY

# 结合其他工具
python main.py signals --today --format json | jq '.[] | select(.confidence > 0.8)'
```

### 5.2 脚本化操作
```bash
#!/bin/bash
# daily_check.sh - 每日检查脚本

echo "执行每日分析..."
python main.py batch TSLA,NVDA,AAPL,META,GOOGL

echo "检查高置信度信号..."
python main.py signals --today --min-confidence 0.8

echo "查看投资组合状况..."
python main.py portfolio --summary

echo "生成日报..."
python main.py report daily --email
```

### 5.3 环境变量配置
```bash
# 设置API密钥
export ALPHA_VANTAGE_API_KEY="your_api_key"

# 设置默认输出格式
export TRADING_OUTPUT_FORMAT="json"

# 设置日志级别
export TRADING_LOG_LEVEL="DEBUG"

# 运行命令
python main.py analyze TSLA
```

## 6. API扩展（可选）

### 6.1 HTTP API（简化版）
如果需要Web界面或第三方集成，可以启用简化的HTTP API：

```bash
# 启动Web服务
python main.py serve --port 8080

# API端点
GET /api/status          # 系统状态
GET /api/stocks          # 股票列表
GET /api/stocks/{symbol} # 单股票分析
GET /api/portfolio       # 投资组合
GET /api/signals         # 交易信号
```

### 6.2 WebHook通知
```bash
# 配置WebHook
python main.py config set notifications.webhook_url "https://your-webhook.com/trading"

# 测试通知
python main.py system test-notification
```

## 7. 开发者接口

### 7.1 插件系统
```python
# 自定义指标插件示例
from app.plugins.base import IndicatorPlugin

class CustomRSI(IndicatorPlugin):
    def calculate(self, data, config):
        # 自定义RSI计算逻辑
        return rsi_value

# 注册插件
python main.py plugins register custom_rsi.py
```

### 7.2 策略接口
```python
# 自定义策略示例
from app.strategies.base import BaseStrategy

class CustomStrategy(BaseStrategy):
    def generate_signals(self, data, indicators):
        # 自定义信号生成逻辑
        return signals

# 使用自定义策略
python main.py config set strategy.type "custom_strategy"
```

这个重写的API文档现在完全聚焦于CLI接口，去掉了复杂的RESTful API设计，符合简化架构的理念！
