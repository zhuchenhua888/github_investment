@echo off
cmd /u /c "chcp 65001 >nul && cd /d "%~dp0" && python fill_stock_prices.py"


:: 切换到批处理文件所在目录
cd /d "%~dp0"

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python安装，请先安装Python。
    pause
    exit /b
)

:: 检查脚本是否存在
if not exist "fill_stock_prices.py" (
    echo 错误：当前目录下未找到 fill_stock_prices.py 脚本。
    pause
    exit /b
)

:: 运行Python脚本
echo 正在运行 fill_stock_prices.py...
python fill_stock_prices.py

:: 检查脚本执行结果
if %errorlevel% equ 0 (
    echo 脚本执行成功！
) else (
    echo 脚本执行失败，错误代码：%errorlevel%
)

pause