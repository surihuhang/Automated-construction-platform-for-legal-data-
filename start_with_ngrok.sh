#!/bin/bash
# Linux/Mac 脚本：使用 ngrok 启动 Streamlit 应用

echo "========================================"
echo "法律数据构建平台 - ngrok 启动脚本"
echo "========================================"
echo ""

# 检查是否安装了 streamlit
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "[错误] 未安装 streamlit，正在安装..."
    pip3 install -r requirements.txt
fi

# 检查是否安装了 ngrok
if ! command -v ngrok &> /dev/null; then
    echo "[错误] 未找到 ngrok"
    echo "请先安装 ngrok："
    echo "1. 访问 https://ngrok.com/download"
    echo "2. 下载并解压"
    echo "3. 运行: ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

echo "[1/2] 启动 Streamlit 应用..."
streamlit run legal_platform.py --server.port 8501 &
STREAMLIT_PID=$!

# 等待 Streamlit 启动
sleep 3

echo "[2/2] 启动 ngrok 隧道..."
echo ""
echo "========================================"
echo "ngrok 隧道已启动！"
echo "请复制上面的 Forwarding URL 分享给其他人"
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 捕获 Ctrl+C，清理进程
trap "kill $STREAMLIT_PID 2>/dev/null; exit" INT TERM

ngrok http 8501

# 清理
kill $STREAMLIT_PID 2>/dev/null
