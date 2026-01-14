@echo off
cd /d G:\code\韭菜助手_web

REM 启动 Python 服务（后台运行） 
start "" python app.py --serve

REM 等待服务启动（建议至少 5~10 秒）
timeout /t 8 /nobreak >nul

REM 打开默认浏览器访问页面
start "" http://127.0.0.1:5000

REM 可选：记录日志
echo [%date% %time%] Service started and browser opened. >> startup.log