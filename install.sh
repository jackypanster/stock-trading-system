#!/bin/bash

# 美股日内套利助手 - 一键安装脚本 (Linux/macOS)
# Stock Trading System - One-Click Installation Script

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="美股日内套利助手"
PROJECT_DIR="stock-trading-system"
PYTHON_MIN_VERSION="3.7"
REPO_URL="https://github.com/your-username/stock-trading-system.git"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 显示欢迎信息
show_welcome() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "           美股日内套利助手 - 一键安装脚本"
    echo "           Stock Trading System - Installation Script"
    echo "=================================================================="
    echo -e "${NC}"
    echo "本脚本将自动安装和配置美股日内套利助手系统"
    echo "支持的操作系统: Ubuntu, Debian, CentOS, RHEL, macOS"
    echo ""
}

# 检测操作系统
detect_os() {
    log_step "检测操作系统..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
            log_info "检测到 Debian/Ubuntu 系统"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
            log_info "检测到 RedHat/CentOS 系统"
        else
            OS="linux"
            log_info "检测到 Linux 系统"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "检测到 macOS 系统"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查Python版本
check_python() {
    log_step "检查Python环境..."
    
    # 尝试不同的Python命令
    for cmd in python3 python; do
        if command -v $cmd &> /dev/null; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$($cmd --version 2>&1 | cut -d' ' -f2)
            log_info "找到Python: $cmd (版本 $PYTHON_VERSION)"
            
            # 检查版本是否满足要求
            if python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                log_success "Python版本满足要求 (>= $PYTHON_MIN_VERSION)"
                return 0
            else
                log_warning "Python版本过低: $PYTHON_VERSION (需要 >= $PYTHON_MIN_VERSION)"
            fi
        fi
    done
    
    log_error "未找到合适的Python版本"
    return 1
}

# 安装Python (如果需要)
install_python() {
    log_step "安装Python..."
    
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        "redhat")
            sudo yum install -y python3 python3-pip
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install python
            else
                log_error "请先安装Homebrew或手动安装Python"
                exit 1
            fi
            ;;
        *)
            log_error "无法自动安装Python，请手动安装"
            exit 1
            ;;
    esac
    
    log_success "Python安装完成"
}

# 安装系统依赖
install_system_deps() {
    log_step "安装系统依赖..."
    
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y git curl wget build-essential
            ;;
        "redhat")
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y git curl wget
            ;;
        "macos")
            # macOS通常已有这些工具
            if ! command -v git &> /dev/null; then
                log_info "请安装Xcode Command Line Tools"
                xcode-select --install
            fi
            ;;
    esac
    
    log_success "系统依赖安装完成"
}

# 获取项目代码
get_project_code() {
    log_step "获取项目代码..."
    
    if [ -d "$PROJECT_DIR" ]; then
        log_warning "目录 $PROJECT_DIR 已存在"
        read -p "是否删除并重新下载? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            log_info "使用现有目录"
            cd "$PROJECT_DIR"
            return 0
        fi
    fi
    
    # 尝试克隆仓库
    if command -v git &> /dev/null; then
        log_info "使用Git克隆项目..."
        git clone "$REPO_URL" "$PROJECT_DIR"
    else
        log_error "Git未安装，无法克隆项目"
        log_info "请手动下载项目代码到 $PROJECT_DIR 目录"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    log_success "项目代码获取完成"
}

# 创建虚拟环境
create_venv() {
    log_step "创建Python虚拟环境..."
    
    if [ -d "venv" ]; then
        log_warning "虚拟环境已存在"
        read -p "是否重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            log_info "使用现有虚拟环境"
            return 0
        fi
    fi
    
    $PYTHON_CMD -m venv venv
    log_success "虚拟环境创建完成"
}

# 激活虚拟环境并安装依赖
install_dependencies() {
    log_step "安装Python依赖包..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        log_info "安装项目依赖..."
        pip install -r requirements.txt
    else
        log_error "未找到 requirements.txt 文件"
        exit 1
    fi
    
    log_success "依赖包安装完成"
}

# 配置环境
setup_config() {
    log_step "配置系统环境..."
    
    # 创建配置文件
    if [ -f ".env.example" ] && [ ! -f ".env" ]; then
        cp .env.example .env
        log_info "已创建环境配置文件 .env"
    fi
    
    # 创建必要目录
    mkdir -p logs data/cache
    
    # 设置权限
    chmod 755 .
    chmod -R 644 config/ 2>/dev/null || true
    chmod -R 755 logs/ data/ 2>/dev/null || true
    
    log_success "环境配置完成"
}

# 验证安装
verify_installation() {
    log_step "验证安装..."
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 测试基本功能
    log_info "测试系统版本..."
    if python main.py --version; then
        log_success "版本检查通过"
    else
        log_error "版本检查失败"
        return 1
    fi
    
    log_info "测试数据获取功能..."
    if python main.py test-data AAPL --mock; then
        log_success "数据获取测试通过"
    else
        log_error "数据获取测试失败"
        return 1
    fi
    
    log_info "测试股票分析功能..."
    if python main.py analyze TSLA --format table > /dev/null; then
        log_success "股票分析测试通过"
    else
        log_error "股票分析测试失败"
        return 1
    fi
    
    log_success "所有测试通过！"
}

# 显示使用说明
show_usage() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "                    安装完成！"
    echo "=================================================================="
    echo -e "${NC}"
    echo "项目已成功安装到: $(pwd)"
    echo ""
    echo "使用方法:"
    echo "1. 激活虚拟环境:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. 查看帮助信息:"
    echo "   python main.py --help"
    echo ""
    echo "3. 分析股票:"
    echo "   python main.py analyze TSLA"
    echo ""
    echo "4. 查看交易信号:"
    echo "   python main.py signals --symbol AAPL"
    echo ""
    echo "5. 查看系统状态:"
    echo "   python main.py status"
    echo ""
    echo "更多信息请查看文档:"
    echo "- 安装指南: docs/installation-guide.md"
    echo "- 用户教程: docs/user-guide.md"
    echo "- 配置说明: docs/configuration.md"
    echo ""
    echo -e "${GREEN}开始您的智能投资之旅！🚀${NC}"
}

# 错误处理
handle_error() {
    log_error "安装过程中发生错误"
    echo "请检查错误信息并重试，或查看安装指南获取帮助"
    echo "安装指南: docs/installation-guide.md"
    exit 1
}

# 主安装流程
main() {
    # 设置错误处理
    trap handle_error ERR
    
    # 显示欢迎信息
    show_welcome
    
    # 检测操作系统
    detect_os
    
    # 检查Python环境
    if ! check_python; then
        log_warning "Python环境不满足要求，尝试自动安装..."
        install_python
        if ! check_python; then
            log_error "Python安装失败"
            exit 1
        fi
    fi
    
    # 安装系统依赖
    install_system_deps
    
    # 获取项目代码
    get_project_code
    
    # 创建虚拟环境
    create_venv
    
    # 安装依赖
    install_dependencies
    
    # 配置环境
    setup_config
    
    # 验证安装
    verify_installation
    
    # 显示使用说明
    show_usage
}

# 检查是否以root权限运行
if [ "$EUID" -eq 0 ]; then
    log_warning "不建议以root权限运行此脚本"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 运行主程序
main "$@" 