@echo off
REM 美股日内套利助手 - Windows一键安装脚本
REM Stock Trading System - Windows Installation Script

setlocal enabledelayedexpansion

REM 项目信息
set PROJECT_NAME=美股日内套利助手
set PROJECT_DIR=stock-trading-system
set PYTHON_MIN_VERSION=3.7
set REPO_URL=https://github.com/your-username/stock-trading-system.git

REM 颜色定义 (Windows 10+)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "PURPLE=[95m"
set "CYAN=[96m"
set "NC=[0m"

REM 显示欢迎信息
echo %CYAN%
echo ==================================================================
echo            美股日内套利助手 - Windows安装脚本
echo            Stock Trading System - Windows Installation
echo ==================================================================
echo %NC%
echo 本脚本将自动安装和配置美股日内套利助手系统
echo 支持的系统: Windows 10, Windows 11
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo %YELLOW%[WARNING]%NC% 检测到管理员权限
    echo 建议以普通用户权限运行此脚本
    pause
)

REM 检查Python环境
echo %BLUE%[STEP]%NC% 检查Python环境...

REM 尝试不同的Python命令
for %%p in (python py python3) do (
    %%p --version >nul 2>&1
    if !errorlevel! == 0 (
        set PYTHON_CMD=%%p
        for /f "tokens=2" %%v in ('%%p --version 2^>^&1') do set PYTHON_VERSION=%%v
        echo %BLUE%[INFO]%NC% 找到Python: %%p ^(版本 !PYTHON_VERSION!^)
        
        REM 检查版本
        %%p -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" >nul 2>&1
        if !errorlevel! == 0 (
            echo %GREEN%[SUCCESS]%NC% Python版本满足要求 ^(^>= %PYTHON_MIN_VERSION%^)
            goto :python_ok
        ) else (
            echo %YELLOW%[WARNING]%NC% Python版本过低: !PYTHON_VERSION! ^(需要 ^>= %PYTHON_MIN_VERSION%^)
        )
    )
)

echo %RED%[ERROR]%NC% 未找到合适的Python版本
echo 请访问 https://www.python.org/downloads/ 下载安装Python 3.7+
pause
exit /b 1

:python_ok

REM 检查Git
echo %BLUE%[STEP]%NC% 检查Git环境...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%[WARNING]%NC% 未找到Git
    echo 请访问 https://git-scm.com/download/win 下载安装Git
    echo 或手动下载项目ZIP包
    pause
)

REM 获取项目代码
echo %BLUE%[STEP]%NC% 获取项目代码...

if exist "%PROJECT_DIR%" (
    echo %YELLOW%[WARNING]%NC% 目录 %PROJECT_DIR% 已存在
    set /p "choice=是否删除并重新下载? (y/N): "
    if /i "!choice!" == "y" (
        rmdir /s /q "%PROJECT_DIR%"
    ) else (
        echo %BLUE%[INFO]%NC% 使用现有目录
        cd "%PROJECT_DIR%"
        goto :code_ready
    )
)

REM 尝试克隆仓库
git --version >nul 2>&1
if %errorlevel% == 0 (
    echo %BLUE%[INFO]%NC% 使用Git克隆项目...
    git clone "%REPO_URL%" "%PROJECT_DIR%"
    if %errorlevel% neq 0 (
        echo %RED%[ERROR]%NC% Git克隆失败
        goto :manual_download
    )
) else (
    goto :manual_download
)

cd "%PROJECT_DIR%"
goto :code_ready

:manual_download
echo %BLUE%[INFO]%NC% 请手动下载项目代码:
echo 1. 访问项目页面
echo 2. 点击 "Code" -^> "Download ZIP"
echo 3. 解压到 %PROJECT_DIR% 目录
echo 4. 重新运行此脚本
pause
exit /b 1

:code_ready
echo %GREEN%[SUCCESS]%NC% 项目代码准备完成

REM 创建虚拟环境
echo %BLUE%[STEP]%NC% 创建Python虚拟环境...

if exist "venv" (
    echo %YELLOW%[WARNING]%NC% 虚拟环境已存在
    set /p "choice=是否重新创建? (y/N): "
    if /i "!choice!" == "y" (
        rmdir /s /q venv
    ) else (
        echo %BLUE%[INFO]%NC% 使用现有虚拟环境
        goto :venv_ready
    )
)

%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo %RED%[ERROR]%NC% 虚拟环境创建失败
    pause
    exit /b 1
)

:venv_ready
echo %GREEN%[SUCCESS]%NC% 虚拟环境准备完成

REM 激活虚拟环境并安装依赖
echo %BLUE%[STEP]%NC% 安装Python依赖包...

call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo %RED%[ERROR]%NC% 虚拟环境激活失败
    pause
    exit /b 1
)

REM 升级pip
python -m pip install --upgrade pip

REM 安装依赖
if exist "requirements.txt" (
    echo %BLUE%[INFO]%NC% 安装项目依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo %RED%[ERROR]%NC% 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo %RED%[ERROR]%NC% 未找到 requirements.txt 文件
    pause
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% 依赖包安装完成

REM 配置环境
echo %BLUE%[STEP]%NC% 配置系统环境...

REM 创建配置文件
if exist ".env.example" (
    if not exist ".env" (
        copy ".env.example" ".env" >nul
        echo %BLUE%[INFO]%NC% 已创建环境配置文件 .env
    )
)

REM 创建必要目录
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "data\cache" mkdir data\cache

echo %GREEN%[SUCCESS]%NC% 环境配置完成

REM 验证安装
echo %BLUE%[STEP]%NC% 验证安装...

REM 测试基本功能
echo %BLUE%[INFO]%NC% 测试系统版本...
python main.py --version >nul 2>&1
if %errorlevel% == 0 (
    echo %GREEN%[SUCCESS]%NC% 版本检查通过
) else (
    echo %RED%[ERROR]%NC% 版本检查失败
    pause
    exit /b 1
)

echo %BLUE%[INFO]%NC% 测试数据获取功能...
python main.py test-data AAPL --mock >nul 2>&1
if %errorlevel% == 0 (
    echo %GREEN%[SUCCESS]%NC% 数据获取测试通过
) else (
    echo %RED%[ERROR]%NC% 数据获取测试失败
    pause
    exit /b 1
)

echo %BLUE%[INFO]%NC% 测试股票分析功能...
python main.py analyze TSLA --format table >nul 2>&1
if %errorlevel% == 0 (
    echo %GREEN%[SUCCESS]%NC% 股票分析测试通过
) else (
    echo %RED%[ERROR]%NC% 股票分析测试失败
    pause
    exit /b 1
)

echo %GREEN%[SUCCESS]%NC% 所有测试通过！

REM 显示使用说明
echo.
echo %CYAN%
echo ==================================================================
echo                     安装完成！
echo ==================================================================
echo %NC%
echo 项目已成功安装到: %CD%
echo.
echo 使用方法:
echo 1. 激活虚拟环境:
echo    venv\Scripts\activate.bat
echo.
echo 2. 查看帮助信息:
echo    python main.py --help
echo.
echo 3. 分析股票:
echo    python main.py analyze TSLA
echo.
echo 4. 查看交易信号:
echo    python main.py signals --symbol AAPL
echo.
echo 5. 查看系统状态:
echo    python main.py status
echo.
echo 更多信息请查看文档:
echo - 安装指南: docs\installation-guide.md
echo - 用户教程: docs\user-guide.md
echo - 配置说明: docs\configuration.md
echo.
echo %GREEN%开始您的智能投资之旅！��%NC%
echo.

pause 