# 部署指南

本文档介绍如何将法律数据构建平台部署到公网，让其他人也能访问。

## 方案一：Streamlit Cloud（推荐，最简单）

Streamlit Cloud 是 Streamlit 官方提供的免费托管服务，非常适合快速部署。

### 步骤：

1. **准备代码仓库**
   - 将代码推送到 GitHub、GitLab 或 Bitbucket
   - 确保仓库是公开的（或使用私有仓库 + Streamlit Cloud 团队版）

2. **访问 Streamlit Cloud**
   - 访问 https://streamlit.io/cloud
   - 使用 GitHub 账号登录

3. **部署应用**
   - 点击 "New app"
   - 选择你的代码仓库
   - 设置：
     - **Main file path**: `legal_platform.py`
     - **Python version**: 3.9 或更高
   - 点击 "Deploy"

4. **配置环境变量**
   - 在应用设置中添加环境变量：
     - `DEEPSEEK_API_KEY`: 你的 DeepSeek API Key
     - `DEEPSEEK_API_BASE`: `https://api.deepseek.com`（可选）

5. **访问应用**
   - 部署完成后，你会得到一个类似 `https://your-app-name.streamlit.app` 的 URL
   - 分享这个 URL 即可

### 优点：
- ✅ 完全免费
- ✅ 自动 HTTPS
- ✅ 自动更新（代码推送后自动重新部署）
- ✅ 无需服务器管理

### 缺点：
- ⚠️ 需要公开代码仓库（或付费使用私有仓库）
- ⚠️ 免费版有资源限制

---

## 方案二：使用 ngrok（快速测试）

ngrok 可以将本地应用快速暴露到公网，适合临时测试。

### 步骤：

1. **安装 ngrok**
   ```bash
   # Windows (使用 Chocolatey)
   choco install ngrok
   
   # 或从官网下载: https://ngrok.com/download
   ```

2. **注册并获取 token**
   - 访问 https://ngrok.com/ 注册账号
   - 获取你的 authtoken

3. **配置 ngrok**
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

4. **启动 Streamlit 应用**
   ```bash
   cd Auto
   streamlit run legal_platform.py --server.port 8501
   ```

5. **启动 ngrok**
   ```bash
   ngrok http 8501
   ```

6. **获取公网地址**
   - ngrok 会显示一个类似 `https://xxxx-xxxx-xxxx.ngrok-free.app` 的 URL
   - 分享这个 URL 即可访问你的应用

### 优点：
- ✅ 快速简单
- ✅ 无需修改代码
- ✅ 适合临时测试

### 缺点：
- ⚠️ 免费版 URL 会变化（每次重启）
- ⚠️ 需要保持本地电脑运行
- ⚠️ 有连接数限制

---

## 方案三：云服务器部署（生产环境）

如果你有自己的云服务器（如阿里云、腾讯云、AWS 等），可以部署到服务器上。

### 步骤：

1. **准备服务器**
   - 确保服务器有公网 IP
   - 安装 Python 3.9+
   - 安装必要的系统依赖

2. **上传代码**
   ```bash
   # 使用 scp 或 git clone
   scp -r Auto/ user@your-server:/path/to/app/
   ```

3. **安装依赖**
   ```bash
   cd /path/to/app/Auto
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   export DEEPSEEK_API_KEY="your-api-key"
   export DEEPSEEK_API_BASE="https://api.deepseek.com"
   ```

5. **使用 systemd 或 supervisor 管理进程**
   
   创建 `/etc/systemd/system/legal-platform.service`:
   ```ini
   [Unit]
   Description=Legal Platform Streamlit App
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/app/Auto
   Environment="DEEPSEEK_API_KEY=your-api-key"
   Environment="DEEPSEEK_API_BASE=https://api.deepseek.com"
   ExecStart=/usr/bin/streamlit run legal_platform.py --server.port 8501 --server.address 0.0.0.0
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   启动服务：
   ```bash
   sudo systemctl enable legal-platform
   sudo systemctl start legal-platform
   ```

6. **配置 Nginx 反向代理（可选但推荐）**
   
   创建 `/etc/nginx/sites-available/legal-platform`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   启用配置：
   ```bash
   sudo ln -s /etc/nginx/sites-available/legal-platform /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

7. **配置 SSL（使用 Let's Encrypt）**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### 优点：
- ✅ 完全控制
- ✅ 性能好
- ✅ 适合生产环境

### 缺点：
- ⚠️ 需要服务器和域名
- ⚠️ 需要自己维护

---

## 方案四：使用 Railway / Render（简单云部署）

这些平台提供简单的部署流程，类似 Streamlit Cloud 但更灵活。

### Railway 部署步骤：

1. 访问 https://railway.app/
2. 使用 GitHub 登录
3. 点击 "New Project" -> "Deploy from GitHub repo"
4. 选择你的仓库
5. 添加环境变量：
   - `DEEPSEEK_API_KEY`
   - `DEEPSEEK_API_BASE`
6. Railway 会自动检测并部署

### Render 部署步骤：

1. 访问 https://render.com/
2. 创建新的 Web Service
3. 连接 GitHub 仓库
4. 设置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run legal_platform.py --server.port $PORT --server.address 0.0.0.0`
5. 添加环境变量并部署

---

## 安全注意事项

⚠️ **重要**：部署到公网时，请注意以下安全事项：

1. **API Key 安全**
   - ✅ 使用环境变量存储 API Key，不要硬编码
   - ✅ 不要在代码仓库中提交 API Key
   - ✅ 定期轮换 API Key

2. **访问控制**
   - 考虑添加身份验证（Streamlit 支持密码保护）
   - 限制 API 调用频率，防止滥用

3. **数据安全**
   - 敏感数据不要存储在 Session State 中
   - 定期清理保存的文件

4. **HTTPS**
   - 生产环境务必使用 HTTPS
   - Streamlit Cloud 和大多数云平台自动提供 HTTPS

---

## 推荐方案

- **快速测试/演示**: 使用 **ngrok**
- **个人项目/小规模使用**: 使用 **Streamlit Cloud**
- **生产环境**: 使用 **云服务器** 或 **Railway/Render**

选择最适合你需求的方案即可！
