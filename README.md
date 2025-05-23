# 美股日内套利助手

一个专注于美股市场的个人投资助手工具，通过程序化分析识别高波动股票的日内套利机会，帮助个人投资者实现高抛低吸策略。

## 🎯 项目定位

**核心理念**：利用美股市场高波动股票的价格特征，通过技术分析自动识别日内套利机会，避免情绪化交易，提高投资决策的系统性和一致性。

**目标用户**：关注美股市场的个人投资者，具备一定投资经验，偏好短期交易策略。

## ✨ 核心功能

### 🔍 智能股票筛选
- 基于波动率、成交量、技术特征筛选适合日内套利的股票
- 动态维护核心股票池（TSLA, NVDA, META, NIO等）
- 实时监控股票表现，自动调整股票池

### 📊 技术分析引擎
- **支撑阻力位识别**：自动识别关键价位
- **日内波动分析**：计算波动率、ATR等指标
- **趋势判断**：多周期趋势分析
- **成交量确认**：结合成交量验证信号强度

### 💡 智能信号生成
- **买入信号**：价格接近支撑位时的低吸机会
- **卖出信号**：价格接近阻力位时的高抛机会
- **信号强度评估**：基于多因子模型的置信度计算
- **实时提醒**：关键价位突破提醒

### 🛡️ 风险控制系统
- **止损机制**：自动设置止损价位
- **仓位管理**：控制单只股票最大仓位
- **日内限制**：限制每日最大交易次数
- **资金管理**：基于账户资金的动态调整

### 📈 投资组合追踪
- **实时P&L**：实时盈亏计算
- **交易记录**：完整的交易历史
- **绩效分析**：策略有效性统计
- **风险指标**：夏普比率、最大回撤等

## 🚀 快速开始

### 安装部署

```bash
# 克隆项目
git clone https://github.com/your-username/intraday-trading-assistant
cd intraday-trading-assistant

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加API密钥

# 初始化数据库
python scripts/init_db.py

# 启动系统
python main.py
```

### 基础使用

```bash
# 查看今日推荐股票
python main.py --command recommend

# 分析特定股票
python main.py --symbol TSLA

# 启动实时监控
python main.py --monitor --symbols TSLA,NVDA,META
```

## 📂 项目结构

```
intraday-trading-assistant/
├── app/                     # 核心应用代码
│   ├── core/               # 核心模块
│   │   ├── strategy.py    # 策略引擎
│   │   ├── risk.py        # 风险管理
│   │   └── portfolio.py   # 组合管理
│   ├── data/              # 数据模块
│   │   ├── fetcher.py     # 数据获取
│   │   └── storage.py     # 数据存储
│   ├── analysis/          # 分析模块
│   │   ├── technical.py   # 技术分析
│   │   └── signals.py     # 信号生成
│   └── api/               # API接口
├── config/                 # 配置文件
│   ├── system.yaml        # 系统配置
│   └── stocks/            # 股票配置
│       ├── TSLA.yaml     # 特斯拉配置
│       └── NVDA.yaml     # 英伟达配置
├── data/                   # 数据文件
├── logs/                   # 日志文件
├── scripts/                # 工具脚本
└── tests/                  # 测试代码
```

## ⚙️ 核心股票配置示例

```yaml
# config/stocks/TSLA.yaml
stock:
  symbol: "TSLA"
  name: "Tesla Inc."
  
strategy:
  type: "intraday_momentum"
  parameters:
    # 支撑阻力位（动态计算）
    lookback_days: 20
    level_strength: 3
    
    # 风险控制
    stop_loss_pct: 0.02      # 2% 止损
    max_position_pct: 0.15   # 最大仓位15%
    max_daily_trades: 3      # 每日最多3次交易
    
    # 信号参数
    volatility_threshold: 0.03  # 最小波动率3%
    volume_multiplier: 1.5      # 成交量倍数确认
```

## 🎯 适用股票池

### 核心股票（已配置）
- **TSLA** - Tesla（高波动，技术性强）
- **NVDA** - NVIDIA（AI龙头，成交活跃）
- **META** - Meta（大盘股，稳定波动）
- **NIO** - NIO（中概股，波动性高）
- **AMD** - AMD（半导体，跟随性强）

### 观察股票（测试中）
- AAPL, AMZN, GOOGL, NFLX, UBER

## 🚨 重要声明

⚠️ **风险提示**
- 本工具仅供个人学习和研究使用
- 所有信号仅为技术分析结果，不构成投资建议
- 股票投资存在风险，请根据自身风险承受能力谨慎投资
- 请在充分了解市场风险的前提下使用本工具

⚠️ **使用限制**
- 不提供自动交易功能，所有交易需手动执行
- 建议先使用纸上交易验证策略有效性
- 实盘使用前请充分回测和验证

## 📊 性能指标

### 目标表现（基于历史回测）
- **信号准确率**：> 60%
- **平均单次收益**：> 1%
- **最大单日亏损**：< 2%
- **月收益目标**：5-15%（视市场环境）

### 风险控制
- 单只股票最大仓位：15%
- 日内最大回撤：3%
- 连续亏损自动暂停：3次

## 🔧 技术栈

- **编程语言**：Python 3.9+
- **数据获取**：yfinance, Alpha Vantage
- **技术分析**：pandas, numpy, talib
- **数据存储**：SQLite（本地）/ PostgreSQL（生产）
- **任务调度**：APScheduler
- **部署**：Docker

## 📚 文档目录

- [项目定义](docs/project-definition.md) - 详细的项目定位和目标
- [股票筛选标准](docs/stock-selection-criteria.md) - 股票池管理策略
- [技术架构](docs/architecture.md) - 系统架构设计
- [策略开发](docs/strategy-development.md) - 自定义策略开发指南
- [部署指南](docs/deployment.md) - 生产环境部署
- [API文档](docs/api.md) - 接口说明

## 🤝 贡献指南

我们欢迎社区贡献！请参考：
- 提交Issue报告问题或建议新功能
- Fork项目并提交Pull Request
- 分享你的策略配置和使用经验

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**开始你的日内套利之旅！** 🚀

> 记住：成功的交易需要严格的纪律、风险控制和持续学习。本工具只是辅助你做出更好决策的工具，最终的投资决策权在你手中。