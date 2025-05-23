# 部署指南

## 1. 部署概述

### 1.1 部署特点
- **本地部署**：个人电脑上运行，无需服务器
- **单体应用**：一个进程包含所有功能
- **零配置**：开箱即用，最小化配置
- **轻量级**：最少的依赖和资源需求

### 1.2 支持平台
- Windows 10/11
- macOS 10.15+
- Ubuntu 18.04+
- 其他Linux发行版

## 2. 系统要求

### 2.1 硬件要求

| 组件 | 最低要求 | 推荐配置 |
|------|---------|----------|
| CPU | 1核心 | 2核心+ |
| 内存 | 1GB | 2GB+ |
| 存储 | 500MB | 2GB+ |
| 网络 | 互联网连接 | 稳定宽带 |

### 2.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.9+ | 推荐3.11 |
| pip | 21.0+ | Python包管理器 |
| Git | 任意版本 | 代码版本控制 |

### 2.3 可选软件
- Visual Studio Code（代码编辑）
- DB Browser for SQLite（数据库查看）

## 3. 快速安装

### 3.1 一键安装脚本（推荐）

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/stock-trading-system/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/stock-trading-system/main/install.ps1" | Invoke-Expression
```

### 3.2 手动安装步骤

#### 步骤1：安装Python
**Windows:**
1. 访问 https://python.org/downloads/
2. 下载Python 3.11+
3. 安装时勾选"Add Python to PATH"

**macOS:**
```bash
# 使用Homebrew
brew install python@3.11

# 或直接下载安装包
# 访问 https://python.org/downloads/
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip git
```

#### 步骤2：下载项目
```bash
# 克隆项目
git clone https://github.com/your-repo/stock-trading-system.git
cd stock-trading-system

# 或下载ZIP包并解压
# curl -L https://github.com/your-repo/stock-trading-system/archive/main.zip -o trading-system.zip
# unzip trading-system.zip
# cd stock-trading-system-main
```

#### 步骤3：设置虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

#### 步骤4：安装依赖
```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 验证安装
python -c "import yfinance, pandas, talib; print('依赖安装成功')"
```

#### 步骤5：初始化配置
```bash
# 复制配置模板
cp .env.example .env

# 创建必要目录
mkdir -p data logs backups

# 初始化数据库
python scripts/init_db.py

# 验证安装
python main.py --version
```

## 4. 配置设置

### 4.1 环境变量配置

编辑 `.env` 文件：
```bash
# 基础配置
APP_NAME=US_Stock_Trading_Assistant
LOG_LEVEL=INFO
DATA_DIR=data
LOG_DIR=logs

# 数据源配置（可选）
ALPHA_VANTAGE_API_KEY=your_api_key_here
FINNHUB_API_KEY=your_api_key_here

# 通知配置（可选）
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# 风险控制
MAX_POSITION_PCT=15
MAX_DAILY_LOSS_PCT=3
STOP_LOSS_PCT=2
```

### 4.2 股票配置

编辑 `config/stocks/` 目录下的股票配置文件：

**config/stocks/TSLA.yaml 示例：**
```yaml
stock:
  symbol: "TSLA"
  name: "Tesla Inc."
  active: true

strategy:
  type: "intraday_momentum"
  
risk:
  max_position_pct: 0.15
  stop_loss_pct: 0.02
  take_profit_levels:
    - level: 0.03
      quantity_pct: 0.5
    - level: 0.05
      quantity_pct: 0.5

technical:
  lookback_days: 20
  support_resistance:
    window: 20
    min_touches: 2
    tolerance: 0.01
  indicators:
    rsi_period: 14
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
```

### 4.3 系统配置

编辑 `config/system.yaml`：
```yaml
# 系统设置
system:
  log_level: "INFO"
  cache_ttl: 300
  max_workers: 4

# 数据设置  
data:
  price_cache_ttl: 60
  history_cache_ttl: 3600
  max_api_calls_per_minute: 300

# 分析设置
analysis:
  default_lookback_days: 20
  min_volume_threshold: 1000000
  min_volatility_threshold: 0.02

# 风险设置
risk:
  max_total_exposure: 0.8
  max_single_stock: 0.15
  max_daily_trades: 10
  emergency_stop_loss: 0.05
```

## 5. 启动和使用

### 5.1 基础启动

```bash
# 确保在虚拟环境中
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 检查配置
python main.py --validate-config

# 启动系统
python main.py
```

### 5.2 常用命令

```bash
# 查看帮助
python main.py --help

# 分析特定股票
python main.py --analyze TSLA

# 查看今日信号
python main.py --today-signals

# 启动实时监控
python main.py --monitor

# 查看持仓状态
python main.py --portfolio

# 生成交易报告
python main.py --report --days 7

# 运行回测
python main.py --backtest --symbol TSLA --days 30
```

### 5.3 后台运行

**Linux/macOS (使用screen):**
```bash
# 安装screen
sudo apt install screen  # Ubuntu
brew install screen       # macOS

# 创建后台会话
screen -S trading
cd /path/to/stock-trading-system
source venv/bin/activate
python main.py --monitor

# 退出会话（保持运行）
Ctrl+A, D

# 重新连接会话
screen -r trading
```

**Windows (使用任务计划程序):**
```cmd
# 创建启动脚本 start_trading.bat
@echo off
cd /d "C:\path\to\stock-trading-system"
call venv\Scripts\activate.bat
python main.py --monitor
pause

# 然后在任务计划程序中添加这个脚本
```

## 6. Docker部署（可选）

### 6.1 Docker构建

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p data logs backups

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令
CMD ["python", "main.py", "--monitor"]
```

### 6.2 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  trading-assistant:
    build: .
    container_name: trading_assistant
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
      - ./backups:/app/backups
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - trading_network

networks:
  trading_network:
    driver: bridge
```

### 6.3 Docker运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 进入容器
docker-compose exec trading-assistant bash
```

## 7. 更新和升级

### 7.1 版本更新

```bash
# 1. 备份当前版本
./scripts/backup_full.sh

# 2. 停止服务
python main.py --stop

# 3. 更新代码
git pull origin main

# 4. 更新依赖
pip install -r requirements.txt --upgrade

# 5. 运行数据库迁移（如需要）
python scripts/migrate.py

# 6. 验证配置
python main.py --validate-config

# 7. 重启服务
python main.py --start

# 8. 验证功能
python main.py --health
```

### 7.2 依赖包更新

```bash
# 查看可更新的包
pip list --outdated

# 更新特定包
pip install yfinance --upgrade

# 更新所有包（谨慎）
pip install -r requirements.txt --upgrade

# 更新后测试
python main.py --test
```

## 8. 故障排除

### 8.1 常见问题

**问题1：Python版本不兼容**
```bash
# 检查Python版本
python --version

# 如果版本过低，安装新版本
# 参考步骤1的Python安装指南
```

**问题2：依赖安装失败**
```bash
# 升级pip
pip install --upgrade pip setuptools wheel

# 清理缓存重装
pip cache purge
pip install -r requirements.txt --no-cache-dir

# Windows系统可能需要Visual C++构建工具
# 下载安装：https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**问题3：数据获取失败**
```bash
# 检查网络连接
ping yahoo.com

# 检查API配额
python main.py --check-api

# 测试数据获取
python -c "import yfinance as yf; print(yf.Ticker('AAPL').info['currentPrice'])"
```

**问题4：数据库文件损坏**
```bash
# 检查数据库
sqlite3 data/trading_assistant.db ".schema"

# 从备份恢复
cp backups/daily/trading_assistant_latest.db data/trading_assistant.db

# 重新初始化（会丢失数据）
rm data/trading_assistant.db
python scripts/init_db.py
```

### 8.2 日志分析

```bash
# 查看错误日志
grep -i error logs/trading_assistant.log

# 查看最近1小时的日志
tail -f logs/trading_assistant.log | grep "$(date '+%Y-%m-%d %H')"

# 统计错误类型
grep -i error logs/trading_assistant.log | cut -d' ' -f4- | sort | uniq -c | sort -nr
```

### 8.3 性能问题

```bash
# 检查系统资源
python main.py --stats

# 查看内存使用
python -c "import psutil; print(f'内存使用: {psutil.virtual_memory().percent}%')"

# 清理缓存
python main.py --clear-cache

# 优化数据库
python scripts/optimize_db.py
```

## 9. 卸载指南

### 9.1 完全卸载

```bash
# 1. 停止服务
python main.py --stop

# 2. 备份重要数据（可选）
cp -r data backups/final_backup_$(date +%Y%m%d)

# 3. 退出虚拟环境
deactivate

# 4. 删除项目目录
cd ..
rm -rf stock-trading-system

# 5. 删除Python包（如果不需要）
# pip uninstall yfinance pandas numpy talib -y
```

### 9.2 保留数据卸载

```bash
# 只删除代码，保留数据
rm -rf app docs scripts tests
rm -f main.py requirements.txt

# 保留：data/ config/ logs/ backups/
```

## 10. 技术支持

### 10.1 获取帮助

- **文档**：查看 `docs/` 目录下的详细文档
- **FAQ**：常见问题解答见 `docs/faq.md`
- **示例**：参考 `examples/` 目录下的使用示例
- **问题反馈**：在GitHub项目页面提交Issue

### 10.2 社区资源

- **GitHub仓库**：https://github.com/your-repo/stock-trading-system
- **使用手册**：https://trading-assistant.readthedocs.io
- **讨论论坛**：https://github.com/your-repo/stock-trading-system/discussions

### 10.3 版本信息

```bash
# 查看详细版本信息
python main.py --version --verbose

# 检查更新
python main.py --check-update

# 查看变更日志
cat CHANGELOG.md
```
