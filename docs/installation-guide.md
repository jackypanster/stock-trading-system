# 美股日内套利助手 - 安装指南

本指南将帮助您在不同操作系统上成功安装和配置美股日内套利助手。

## 📋 系统要求

### 最低系统要求
- **操作系统**：Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python版本**：Python 3.7 或更高版本
- **内存**：至少 4GB RAM
- **存储空间**：至少 1GB 可用空间
- **网络**：稳定的互联网连接（用于获取股票数据）

### 推荐系统配置
- **操作系统**：Windows 11, macOS 12+, Ubuntu 20.04+
- **Python版本**：Python 3.9+
- **内存**：8GB+ RAM
- **存储空间**：5GB+ 可用空间
- **网络**：高速宽带连接

## 🔧 安装步骤

### 步骤1：检查Python环境

首先确认您的系统已安装Python 3.7+：

```bash
# 检查Python版本
python --version
# 或者
python3 --version
```

如果没有安装Python，请访问 [Python官网](https://www.python.org/downloads/) 下载安装。

### 步骤2：获取项目代码

#### 方法1：Git克隆（推荐）
```bash
# 克隆项目仓库
git clone https://github.com/your-username/stock-trading-system.git
cd stock-trading-system
```

#### 方法2：下载ZIP包
1. 访问项目GitHub页面
2. 点击"Code" -> "Download ZIP"
3. 解压到目标目录
4. 进入项目目录

### 步骤3：创建虚拟环境

强烈建议使用虚拟环境来隔离项目依赖：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

激活成功后，命令行前缀会显示 `(venv)`。

### 步骤4：安装项目依赖

```bash
# 升级pip到最新版本
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 步骤5：环境配置

#### 创建配置文件
```bash
# 复制环境变量模板
cp .env.example .env
```

#### 编辑配置文件
使用文本编辑器打开 `.env` 文件，根据需要修改配置：

```bash
# 基础配置
APP_NAME=美股日内套利助手
APP_VERSION=1.0.0
DEBUG=false

# 数据源配置
DATA_SOURCE=yfinance
CACHE_ENABLED=true
CACHE_TTL=300

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=true

# API配置（可选）
# ALPHA_VANTAGE_API_KEY=your_api_key_here
# FINNHUB_API_KEY=your_api_key_here
```

### 步骤6：验证安装

运行以下命令验证安装是否成功：

```bash
# 检查版本信息
python main.py --version

# 查看帮助信息
python main.py --help

# 测试数据获取功能
python main.py test-data AAPL --mock
```

如果看到类似以下输出，说明安装成功：

```
美股日内套利助手 v1.0.0
数据获取测试成功！
```

## 🎯 快速验证

### 基础功能测试

```bash
# 1. 测试股票分析功能
python main.py analyze TSLA --format table

# 2. 测试信号生成功能
python main.py signals --symbols AAPL,TSLA --format table

# 3. 测试配置管理功能
python main.py config show --section app
```

### 高级功能测试

```bash
# 1. 测试技术分析
python main.py analyze NVDA --format json

# 2. 测试信号过滤
python main.py signals --min-confidence 0.7 --format table

# 3. 测试备用数据源
python main.py test-backup AAPL --calls 3
```

## 🔧 平台特定安装说明

### Windows 安装

#### 使用PowerShell（推荐）
```powershell
# 1. 检查Python
python --version

# 2. 克隆项目
git clone https://github.com/your-username/stock-trading-system.git
cd stock-trading-system

# 3. 创建虚拟环境
python -m venv venv
venv\Scripts\Activate.ps1

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置环境
copy .env.example .env
notepad .env

# 6. 测试安装
python main.py --version
```

#### 使用命令提示符
```cmd
# 激活虚拟环境
venv\Scripts\activate.bat

# 其他步骤相同
```

### macOS 安装

#### 使用Homebrew（推荐）
```bash
# 1. 安装Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装Python
brew install python

# 3. 克隆项目
git clone https://github.com/your-username/stock-trading-system.git
cd stock-trading-system

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 配置环境
cp .env.example .env
nano .env

# 7. 测试安装
python main.py --version
```

### Ubuntu/Debian 安装

```bash
# 1. 更新系统包
sudo apt update
sudo apt upgrade -y

# 2. 安装Python和相关工具
sudo apt install python3 python3-pip python3-venv git -y

# 3. 克隆项目
git clone https://github.com/your-username/stock-trading-system.git
cd stock-trading-system

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装依赖
pip install -r requirements.txt

# 6. 配置环境
cp .env.example .env
nano .env

# 7. 测试安装
python main.py --version
```

### CentOS/RHEL 安装

```bash
# 1. 安装EPEL仓库
sudo yum install epel-release -y

# 2. 安装Python和Git
sudo yum install python3 python3-pip git -y

# 3. 其他步骤与Ubuntu相同
```

## 🐳 Docker 安装（可选）

如果您熟悉Docker，可以使用容器化部署：

### 构建Docker镜像
```bash
# 构建镜像
docker build -t stock-trading-system .

# 运行容器
docker run -it --rm stock-trading-system python main.py --help
```

### 使用Docker Compose
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## ⚠️ 常见问题解决

### 问题1：Python版本不兼容
**错误信息**：`SyntaxError` 或版本相关错误

**解决方案**：
```bash
# 检查Python版本
python --version

# 如果版本低于3.7，请升级Python
# Windows: 从官网下载最新版本
# macOS: brew upgrade python
# Ubuntu: sudo apt install python3.9
```

### 问题2：pip安装失败
**错误信息**：`pip: command not found` 或权限错误

**解决方案**：
```bash
# 安装pip
# Ubuntu/Debian:
sudo apt install python3-pip

# CentOS/RHEL:
sudo yum install python3-pip

# 升级pip
python -m pip install --upgrade pip
```

### 问题3：依赖包安装失败
**错误信息**：编译错误或网络超时

**解决方案**：
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或者使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 问题4：虚拟环境激活失败
**错误信息**：`cannot be loaded because running scripts is disabled`

**解决方案（Windows PowerShell）**：
```powershell
# 临时允许脚本执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后重新激活虚拟环境
venv\Scripts\Activate.ps1
```

### 问题5：数据获取失败
**错误信息**：网络连接错误或API限制

**解决方案**：
```bash
# 1. 检查网络连接
ping google.com

# 2. 使用模拟数据测试
python main.py test-data AAPL --mock

# 3. 配置代理（如果需要）
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

### 问题6：权限错误
**错误信息**：`Permission denied` 或无法创建文件

**解决方案**：
```bash
# 检查目录权限
ls -la

# 修改权限（Linux/macOS）
chmod 755 .
chmod -R 644 config/
chmod -R 755 logs/

# Windows: 右键项目文件夹 -> 属性 -> 安全 -> 编辑权限
```

## 🔧 高级配置

### 配置文件详解

#### 系统配置 (config/system.yaml)
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
```

#### 股票配置示例 (config/stocks/TSLA.yaml)
```yaml
stock:
  symbol: "TSLA"
  name: "Tesla Inc."
  active: true

strategy:
  type: "support_resistance"
  parameters:
    lookback_days: 20
    min_touches: 2
    tolerance: 0.5

risk:
  stop_loss_pct: 0.02
  take_profit_pct: 0.04
  max_position_pct: 0.15
  max_daily_trades: 3
```

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```bash
# 应用配置
APP_NAME=美股日内套利助手
APP_VERSION=1.0.0
DEBUG=false

# 数据源配置
DATA_SOURCE=yfinance
CACHE_ENABLED=true
CACHE_TTL=300
BACKUP_ENABLED=true

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# API密钥（可选）
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# 代理配置（如果需要）
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

## 🚀 性能优化建议

### 1. 缓存配置
```bash
# 启用数据缓存以提高性能
CACHE_ENABLED=true
CACHE_TTL=300  # 5分钟缓存
```

### 2. 日志配置
```bash
# 生产环境建议使用INFO级别
LOG_LEVEL=INFO

# 开发环境可以使用DEBUG级别
LOG_LEVEL=DEBUG
```

### 3. 内存优化
- 定期清理缓存：`python main.py config clear-cache`
- 限制历史数据获取天数
- 使用轻量级输出格式

## 📞 获取帮助

如果在安装过程中遇到问题，可以通过以下方式获取帮助：

1. **查看文档**：阅读 `docs/` 目录下的相关文档
2. **检查日志**：查看 `logs/` 目录下的错误日志
3. **运行诊断**：`python main.py status` 检查系统状态
4. **社区支持**：在GitHub Issues中提问
5. **联系开发者**：通过项目主页联系方式

## ✅ 安装完成检查清单

安装完成后，请确认以下项目都已正确配置：

- [ ] Python 3.7+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 项目依赖已安装
- [ ] 配置文件已创建和编辑
- [ ] 基础功能测试通过
- [ ] 数据获取功能正常
- [ ] 日志系统工作正常
- [ ] 缓存目录可写入

恭喜！您已成功安装美股日内套利助手。现在可以开始使用系统进行股票分析了！

## 🔄 下一步

安装完成后，建议您：

1. 阅读 [使用教程](user-guide.md) 了解详细使用方法
2. 查看 [配置说明](configuration.md) 自定义系统设置
3. 参考 [策略开发](strategy-development.md) 开发自定义策略
4. 浏览 [API文档](api.md) 了解编程接口

开始您的智能投资之旅！🚀 