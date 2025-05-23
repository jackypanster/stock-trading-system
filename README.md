# 通用股票交易策略系统

一个灵活可配置的股票自动交易策略系统，支持多种股票和自定义策略。

## 📋 项目概述

本系统旨在提供一个通用的股票交易策略框架，通过配置文件即可适配不同的股票和交易策略，避免情绪化交易，实现系统化投资。

### 主要特性

- 🔄 **多股票支持**：通过配置文件支持任意股票
- 📊 **策略可插拔**：支持自定义交易策略
- 📈 **技术分析**：内置多种技术指标
- 🛡️ **风险控制**：自动止损止盈，仓位管理
- 📱 **实时监控**：价格提醒，交易通知
- 📝 **交易记录**：完整的交易历史追踪
- 🔍 **策略回测**：历史数据验证策略效果

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/your-username/stock-trading-system.git
cd stock-trading-system

# 安装依赖
pip install -r requirements.txt

# 配置股票（以PONY为例）
cp config/stocks/example.yaml config/stocks/PONY.yaml
# 编辑配置文件

# 运行系统
python main.py --stock PONY
```

## 📁 项目文档

### 开发文档
- [需求文档](docs/requirements.md) - 系统需求和功能说明
- [架构设计](docs/architecture.md) - 系统架构和技术选型
- [API文档](docs/api.md) - 接口定义和使用说明
- [数据库设计](docs/database.md) - 数据模型和表结构

### 使用文档
- [安装指南](docs/installation.md) - 详细安装步骤
- [配置说明](docs/configuration.md) - 配置文件详解
- [策略开发](docs/strategy-development.md) - 如何开发自定义策略
- [使用教程](docs/user-guide.md) - 日常使用指南

### 运维文档
- [部署文档](docs/deployment.md) - 生产环境部署
- [监控指南](docs/monitoring.md) - 系统监控和告警
- [故障处理](docs/troubleshooting.md) - 常见问题解决
- [备份恢复](docs/backup.md) - 数据备份和恢复

### 开发文档
- [开发指南](docs/development.md) - 开发环境搭建
- [测试文档](docs/testing.md) - 测试策略和用例
- [贡献指南](docs/contributing.md) - 如何贡献代码

## 🏗️ 项目结构

```
stock-trading-system/
├── src/                      # 源代码
│   ├── core/                # 核心模块
│   │   ├── engine.py       # 策略引擎
│   │   ├── portfolio.py    # 组合管理
│   │   └── risk.py         # 风险控制
│   ├── strategies/          # 策略实现
│   │   ├── base.py        # 策略基类
│   │   ├── ma_cross.py    # 均线策略
│   │   └── support_resistance.py  # 支撑阻力策略
│   ├── data/               # 数据处理
│   │   ├── fetcher.py     # 数据获取
│   │   └── validator.py   # 数据验证
│   └── utils/              # 工具函数
├── config/                  # 配置文件
│   ├── stocks/             # 股票配置
│   │   ├── example.yaml   # 示例配置
│   │   └── PONY.yaml      # PONY股票配置
│   └── system.yaml         # 系统配置
├── tests/                   # 测试代码
├── docs/                    # 文档目录
├── scripts/                 # 脚本工具
└── requirements.txt         # 依赖列表
```

## ⚙️ 配置示例

### 股票配置文件 (config/stocks/AAPL.yaml)
```yaml
stock:
  symbol: "AAPL"
  name: "Apple Inc."
  exchange: "NASDAQ"
  
strategy:
  type: "support_resistance"
  parameters:
    support_levels: [150, 155, 160]
    resistance_levels: [170, 175, 180]
    stop_loss_pct: 0.05
    
trading:
  initial_capital: 10000
  max_position_pct: 0.3
  min_trade_amount: 100
```

## 🔧 支持的策略

1. **支撑阻力策略** - 基于关键价位的交易
2. **均线交叉策略** - MA/EMA交叉信号
3. **RSI策略** - 超买超卖指标
4. **MACD策略** - 趋势跟踪
5. **自定义策略** - 支持扩展

## 📊 数据源

- **实时数据**: Alpaca, Interactive Brokers
- **延迟数据**: Yahoo Finance, Alpha Vantage
- **历史数据**: 本地缓存，数据库存储

## 🤝 贡献

欢迎贡献代码！请查看[贡献指南](docs/contributing.md)。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢所有贡献者
- 使用的开源库列表见 [CREDITS](CREDITS.md)

## 📞 联系方式

- Issue: [GitHub Issues](https://github.com/your-username/stock-trading-system/issues)