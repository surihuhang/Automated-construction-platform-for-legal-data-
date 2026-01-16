@echo off
REM Windows 批处理脚本：使用 ngrok 启动 Streamlit 应用

echo ========================================
echo 法律数据构建平台 - ngrok 启动脚本
echo ========================================
echo.

REM 检查是否安装了 streamlit
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [错误] 未安装 streamlit，正在安装...
    pip install -r requirements.txt
)

REM 检查是否安装了 ngrok
where ngrok >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 ngrok
    echo 请先安装 ngrok：
    echo 1. 访问 https://ngrok.com/download
    echo 2. 下载并解压到系统 PATH 中
    echo 3. 运行: ngrok config add-authtoken YOUR_TOKEN
    pause
    exit /b 1
)

echo [1/2] 启动 Streamlit 应用...
start "Streamlit App" cmd /k "streamlit run legal_platform.py --server.port 8501"

REM 等待 Streamlit 启动
timeout /t 3 /nobreak >nul

echo [2/2] 启动 ngrok 隧道...
echo.
echo ========================================
echo ngrok 隧道已启动！
echo 请复制上面的 Forwarding URL 分享给其他人
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

ngrok http 8501

pause
