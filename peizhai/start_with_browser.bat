@echo off
cd /d G:\code\peizhai

REM 启动 Python 服务（后台运行） 
start "" python fetch_update.py --serve --port 8000

REM 等待服务启动（建议至少 5~10 秒）
timeout /t 8 /nobreak >nul

REM 打开默认浏览器访问页面
start "" http://127.0.0.1:8000/index.html

REM 可选：记录日志
echo [%date% %time%] Service started and browser opened. >> startup.log