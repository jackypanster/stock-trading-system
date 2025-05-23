# 简化架构设计

## 1. 架构设计理念

### 1.1 设计原则
- **简单优先**：单体应用，避免过度工程化
- **本地部署**：个人使用，本地运行为主
- **快速迭代**：MVP优先，逐步完善
- **易于维护**：代码结构清晰，依赖关系简单

### 1.2 架构特点
- 单进程应用，多线程/异步处理
- 本地SQLite数据库，可选升级PostgreSQL
- 内存缓存，无需Redis
- 命令行界面 + 简单Web界面

## 2. 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        用户接口层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  CLI命令行  │  │  Web界面    │  │  配置文件管理        │  │
│  │  快速执行   │  │  监控面板   │  │  stock configs       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                      应用核心层                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 主应用控制器                         │   │
│  │              (TradingAssistant)                     │   │
│  │  • 协调各模块工作                                     │   │
│  │  • 定时任务调度                                       │   │
│  │  • 事件处理                                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────┐ │
│  │ 市场数据  │ │ 技术分析  │ │ 信号生成  │ │  风险管理   │ │
│  │   模块    │ │   模块    │ │   模块    │ │    模块     │ │
│  │MarketData │ │Technical  │ │ Signal    │ │ RiskManager │ │
│  │Manager    │ │Analyzer   │ │Generator  │ │             │ │
│  └───────────┘ └───────────┘ └───────────┘ └─────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                      数据存储层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ SQLite数据库 │  │ 本地缓存    │  │ 配置文件存储         │  │
│  │ • 交易记录   │  │ • 价格数据  │  │ • 股票配置           │  │
│  │ • 历史信号   │  │ • 指标计算  │  │ • 系统参数           │  │
│  │ • 持仓信息   │  │ • 临时状态  │  │ • 用户设置           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

外部依赖：
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Yahoo Finance│    │Alpha Vantage│    │  邮件服务   │
│  API        │    │    API      │    │ (可选通知)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 3. 核心模块设计

### 3.1 主应用控制器 (TradingAssistant)

```python
class TradingAssistant:
    """
    主应用控制器，协调所有模块
    职责：
    - 启动和停止应用
    - 调度定时任务
    - 协调各模块工作
    - 处理用户命令
    """
    
    def __init__(self):
        self.market_data = MarketDataManager()
        self.analyzer = TechnicalAnalyzer()
        self.signal_gen = SignalGenerator()
        self.risk_mgr = RiskManager()
        self.portfolio = Portfolio()
        
    async def run_analysis_cycle(self):
        """运行一次完整的分析周期"""
        # 1. 获取市场数据
        # 2. 技术分析
        # 3. 生成信号
        # 4. 风险检查
        # 5. 输出建议
        
    def start_monitoring(self):
        """开始实时监控"""
        
    def get_recommendation(self, symbol):
        """获取特定股票建议"""
```

### 3.2 市场数据模块 (MarketDataManager)

```python
class MarketDataManager:
    """
    市场数据管理
    职责：
    - 从多个数据源获取价格数据
    - 数据验证和清洗
    - 本地缓存管理
    - 数据源切换
    """
    
    def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        
    def get_historical_data(self, symbol: str, days: int) -> pd.DataFrame:
        """获取历史数据"""
        
    def get_intraday_data(self, symbol: str) -> pd.DataFrame:
        """获取日内分钟级数据"""
```

### 3.3 技术分析模块 (TechnicalAnalyzer)

```python
class TechnicalAnalyzer:
    """
    技术分析计算
    职责：
    - 计算技术指标（SMA, RSI, MACD等）
    - 识别支撑阻力位
    - 分析价格形态
    - 计算波动率指标
    """
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Dict:
        """计算支撑阻力位"""
        
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """计算所有技术指标"""
        
    def analyze_volatility(self, data: pd.DataFrame) -> Dict:
        """分析波动率特征"""
```

### 3.4 信号生成模块 (SignalGenerator)

```python
class SignalGenerator:
    """
    交易信号生成
    职责：
    - 基于技术分析生成买卖信号
    - 计算信号强度和置信度
    - 结合多个因素综合判断
    - 过滤低质量信号
    """
    
    def generate_signals(self, symbol: str, indicators: Dict) -> List[Signal]:
        """生成交易信号"""
        
    def calculate_confidence(self, signal: Signal, market_context: Dict) -> float:
        """计算信号置信度"""
```

### 3.5 风险管理模块 (RiskManager)

```python
class RiskManager:
    """
    风险控制管理
    职责：
    - 仓位管理
    - 止损止盈设置
    - 风险度量
    - 信号过滤
    """
    
    def validate_signal(self, signal: Signal, portfolio: Portfolio) -> bool:
        """验证信号是否符合风险要求"""
        
    def calculate_position_size(self, signal: Signal, portfolio: Portfolio) -> int:
        """计算建议仓位大小"""
        
    def check_risk_limits(self, portfolio: Portfolio) -> Dict:
        """检查风险限制"""
```

## 4. 数据模型设计

### 4.1 核心数据结构

```python
@dataclass
class Signal:
    """交易信号"""
    timestamp: datetime
    symbol: str
    action: str  # BUY/SELL/HOLD
    price: float
    target_shares: int
    confidence: float
    reason: str
    stop_loss: float
    take_profit: float

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    
@dataclass
class StockConfig:
    """股票配置"""
    symbol: str
    name: str
    strategy_type: str
    risk_params: Dict
    technical_params: Dict
```

### 4.2 数据库设计（SQLite）

```sql
-- 简化的数据库表结构

-- 持仓表
CREATE TABLE positions (
    symbol TEXT PRIMARY KEY,
    shares INTEGER NOT NULL,
    avg_cost REAL NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易记录表
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL, -- BUY/SELL
    shares INTEGER NOT NULL,
    price REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    strategy TEXT,
    notes TEXT
);

-- 信号历史表
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    price REAL NOT NULL,
    confidence REAL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE
);

-- 股票监控表
CREATE TABLE watchlist (
    symbol TEXT PRIMARY KEY,
    active BOOLEAN DEFAULT TRUE,
    last_analyzed TIMESTAMP,
    avg_daily_volume REAL,
    avg_volatility REAL
);
```

## 5. 技术栈选择

### 5.1 核心技术栈

| 组件 | 技术选择 | 理由 |
|------|---------|------|
| 编程语言 | Python 3.9+ | 金融库丰富，开发效率高 |
| 数据获取 | yfinance | 免费，稳定，数据质量好 |
| 数据存储 | SQLite | 轻量，无需配置，适合个人使用 |
| 数据处理 | pandas, numpy | 标准金融数据处理库 |
| 技术分析 | TA-Lib, pandas-ta | 成熟的技术指标库 |
| 任务调度 | APScheduler | 简单的定时任务 |
| 命令行 | Click | 优雅的CLI框架 |
| Web界面 | Flask (可选) | 轻量级Web框架 |
| 配置管理 | PyYAML | 人类可读的配置格式 |

### 5.2 可选组件

| 组件 | 技术选择 | 使用场景 |
|------|---------|----------|
| 数据库升级 | PostgreSQL | 数据量大时升级 |
| 缓存 | Redis | 高频交易时使用 |
| 消息通知 | SMTP, Webhook | 重要信号通知 |
| 前端 | Vue.js | 需要更丰富界面时 |

## 6. 部署架构

### 6.1 本地开发/个人使用

```
┌─────────────────────────────────────┐
│          本地机器                    │
│  ┌─────────────────────────────────┐ │
│  │     Trading Assistant App       │ │
│  │  ┌─────────┐  ┌─────────────┐   │ │
│  │  │   CLI   │  │   Web UI    │   │ │
│  │  └─────────┘  └─────────────┘   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │      Core Engine            │ │ │
│  │  └─────────────────────────────┘ │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │      SQLite Database            │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │       Config Files              │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
            ↕ Internet
┌─────────────────────────────────────┐
│        外部数据源                    │
│  • Yahoo Finance API               │
│  • Alpha Vantage API               │
└─────────────────────────────────────┘
```

### 6.2 Docker容器化（可选）

```dockerfile
# 简化的Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py", "--mode", "daemon"]
```

## 7. 关键设计决策

### 7.1 为什么选择单体应用？
- **个人使用**：不需要复杂的分布式架构
- **快速开发**：减少跨服务通信复杂性
- **易于调试**：所有逻辑在一个进程中
- **部署简单**：一个可执行文件即可

### 7.2 为什么选择SQLite？
- **零配置**：无需单独安装数据库服务
- **高性能**：对于个人使用量完全够用
- **可移植**：数据库文件可以轻松备份迁移
- **可升级**：后续可以无缝升级到PostgreSQL

### 7.3 为什么使用配置文件？
- **灵活性**：无需修改代码即可调整参数
- **可版本控制**：配置变更可以追踪
- **易于分享**：可以分享成功的股票配置
- **动态调整**：运行时可以重新加载配置

## 8. 扩展性考虑

### 8.1 未来可能的扩展
- **多用户支持**：添加用户认证和权限管理
- **云端部署**：Docker + 云服务器部署
- **移动端**：开发移动应用
- **社区功能**：用户分享策略和配置

### 8.2 架构演进路径
1. **阶段一**：单机版CLI应用
2. **阶段二**：添加Web界面
3. **阶段三**：Docker化部署
4. **阶段四**：云端多用户版本 