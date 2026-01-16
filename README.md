# 法律数据构建平台

基于 Streamlit 和 DeepSeek API 的智能法律数据分析与题目构建工具。

## 功能特性

- 📄 **原始案件处理**：输入判决文本，AI 自动分析案件要点
- ❓ **题目构建**：根据原始文本生成法律题目，支持编辑和锁定
- 💡 **答案生成**：生成详细的解题思路和标准答案
- 💾 **数据保存**：自动保存到本地 JSON 文件

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
streamlit run legal_platform.py
```

## 配置 API Key

有两种方式配置 DeepSeek API Key：

1. **环境变量**（推荐）：
   ```bash
   # Windows PowerShell
   $env:DEEPSEEK_API_KEY="your-api-key-here"
   
   # Linux/Mac
   export DEEPSEEK_API_KEY="your-api-key-here"
   ```

2. **侧边栏输入**：在应用运行后，在侧边栏的 API 配置区域输入 API Key

## 使用流程

1. **模块 1 - 原始案件处理**
   - 输入或上传原始判决文本
   - 点击"分析文本"获取 AI 分析结果

2. **模块 2 - 题目构建**
   - 点击"生成题目"自动生成法律题目
   - 编辑题目内容（可选）
   - 点击"锁定题目"确认题目

3. **模块 3 - 答案生成**
   - 点击"生成答案"获取解题思路和答案
   - 编辑答案内容（可选）
   - 点击"锁定并保存"保存到文件

## 文件结构

```
Auto/
├── legal_platform.py    # 主应用文件
├── requirements.txt     # 依赖包列表
├── README.md           # 说明文档
└── legal_data_*.json   # 保存的数据文件（自动生成）
```

## 保存的数据格式

保存的 JSON 文件包含以下字段：

```json
{
  "timestamp": "20240101_120000",
  "source_text": "原始判决文本...",
  "question": "生成的题目...",
  "answer": "解题思路和答案...",
  "created_at": "2024-01-01T12:00:00"
}
```

## 部署到公网

想要将应用部署到公网让别人访问？请查看 [DEPLOYMENT.md](DEPLOYMENT.md) 了解详细的部署指南。

### 快速测试（使用 ngrok）

**Windows:**
```bash
start_with_ngrok.bat
```

**Linux/Mac:**
```bash
chmod +x start_with_ngrok.sh
./start_with_ngrok.sh
```

### 推荐方案

- **快速测试**: 使用 ngrok（见上方）
- **个人项目**: 使用 [Streamlit Cloud](https://streamlit.io/cloud)（免费）
- **生产环境**: 部署到云服务器或 Railway/Render

## 注意事项

- 所有数据保存在 Session State 中，刷新页面会保留
- 使用"重置所有数据"按钮可以清空所有内容
- 确保有足够的 API 配额来调用 DeepSeek API

- **部署到公网时**：请使用环境变量配置 API Key，不要硬编码
