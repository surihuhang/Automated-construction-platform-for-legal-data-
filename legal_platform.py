import streamlit as st
import os
import json
from datetime import datetime
from openai import OpenAI
from pathlib import Path
import io

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="高难度物理题目质检平台",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3498db;
    }
    .detection-pass {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .detection-fail {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .field-label {
        font-weight: bold;
        color: #495057;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 顶部：项目说明
# ==========================================
st.markdown('<div class="main-header">🔬 高难度物理题目质检平台</div>', unsafe_allow_html=True)

with st.expander("📋 项目说明", expanded=True):
    st.markdown("""
    **项目背景：**
    
    本平台用于高难度物理题目的质检和回答以及解析的评估。通过上传原始依据论文和物理题目，
    利用AI模型进行智能分析，帮助专家进行题目质量评估和答案验证。
    """)

# ==========================================
# 侧边栏：API 配置
# ==========================================
with st.sidebar:
    st.header("🔑 API 配置")
    
    api_key = st.text_input(
        "DeepSeek API Key",
        value=os.getenv("DEEPSEEK_API_KEY", ""),
        type="password",
        help="请输入您的 DeepSeek API Key，或设置环境变量 DEEPSEEK_API_KEY"
    )
    
    base_url = st.text_input(
        "API Base URL",
        value=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
        help="DeepSeek API 的基础 URL"
    )
    
    model_name = st.selectbox(
        "模型选择",
        options=["deepseek-chat", "deepseek-coder"],
        index=0,
        help="选择要使用的 DeepSeek 模型"
    )
    
    st.divider()
    st.info("💡 提示：API Key 会保存在 Session State 中，刷新页面后需要重新输入")

# ==========================================
# API 调用函数
# ==========================================
def get_openai_client():
    """获取 OpenAI 客户端（兼容 DeepSeek）"""
    api_key_value = api_key or os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key_value:
        return None
    
    return OpenAI(
        api_key=api_key_value,
        base_url=base_url or "https://api.deepseek.com"
    )

def call_deepseek_api(prompt: str, system_prompt: str = "", temperature: float = 0.7):
    """调用 DeepSeek API"""
    client = get_openai_client()
    if not client:
        return "❌ 错误：未配置 API Key，请在侧边栏输入"
    
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ API 调用失败：{str(e)}"

def extract_pdf_text(pdf_file):
    """提取PDF文本内容"""
    try:
        import pdfplumber
        pdf_file.seek(0)
        pdf_text = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pdf_text.append(text)
        return "\n\n".join(pdf_text)
    except ImportError:
        return None
    except Exception as e:
        return f"PDF读取错误：{str(e)}"

def analyze_question_with_paper(question_text: str, paper_text: str):
    """分析题目和论文"""
    system_prompt = """你是一位专业的物理学家和物理教育专家。你的任务是分析给定的物理题目和其原始依据论文，从以下维度进行评估：

1. **题目清晰度**：判断题目表述是否清晰、完整、无歧义
2. **题目准确性**：判断题目中涉及的物理概念、假设、术语是否准确规范
3. **题目与论文一致性**：判断题目是否与原始论文中的内容一致，是否有依据支撑
4. **题目难度**：评估题目的复杂度和难度等级
5. **题目质量**：综合评估题目的专业性和教育价值

请给出详细的分析报告，包括：
- 每个维度的评分（1-5分）
- 具体的评价和建议
- 是否存在问题及改进建议
- 最终结论（通过/不通过）"""
    
    prompt = f"""请分析以下物理题目和原始依据论文：

【物理题目】
{question_text}

【原始依据论文内容】
{paper_text[:5000]}  # 限制长度避免token过多

请按照上述要求进行详细分析。"""
    
    return call_deepseek_api(prompt, system_prompt, temperature=0.7)

def analyze_answer_with_paper(answer_text: str, solution_process: str, question_text: str, paper_text: str):
    """分析答案和解答过程，检查与论文依据的一致性"""
    system_prompt = """你是一位专业的物理学家和物理教育专家。你的任务是分析给定的答案和解答过程，重点检查其与原始依据论文的一致性。

请从以下维度进行评估：

1. **答案正确性**：
   - 最终答案是否正确
   - 数值计算是否准确
   - 单位是否正确

2. **解答过程质量**：
   - 解题思路是否清晰
   - 逻辑推理是否严密
   - 步骤是否完整

3. **与论文依据的一致性**：
   - 答案是否基于论文中的理论或方法
   - 使用的公式、概念是否与论文一致
   - 是否有引用论文中的关键内容
   - 是否存在与论文相矛盾的地方

4. **专业规范性**：
   - 物理术语使用是否规范
   - 数学符号是否标准
   - 表述是否专业

请给出详细的分析报告，包括：
- 每个维度的评分（1-5分）
- 具体的评价和问题指出
- 与论文依据的对照分析
- 最终结论（通过/不通过）"""
    
    prompt = f"""请分析以下答案和解答过程，并对照原始依据论文进行评估：

【物理题目】
{question_text}

【答案】
{answer_text}

【解答过程】
{solution_process}

【原始依据论文内容】
{paper_text[:5000]}  # 限制长度避免token过多

请按照上述要求进行详细分析，特别关注答案和解答过程与论文依据的一致性。"""
    
    return call_deepseek_api(prompt, system_prompt, temperature=0.7)

# ==========================================
# 初始化 Session State
# ==========================================
if "paper_text" not in st.session_state:
    st.session_state.paper_text = ""
if "paper_file_name" not in st.session_state:
    st.session_state.paper_file_name = ""
if "question_text" not in st.session_state:
    st.session_state.question_text = ""
if "question_analysis_result" not in st.session_state:
    st.session_state.question_analysis_result = ""
if "question_approved" not in st.session_state:
    st.session_state.question_approved = False
if "answer_text" not in st.session_state:
    st.session_state.answer_text = ""
if "solution_process" not in st.session_state:
    st.session_state.solution_process = ""
if "answer_analysis_result" not in st.session_state:
    st.session_state.answer_analysis_result = ""

# ==========================================
# 第一部分：题目初审
# ==========================================
st.markdown('<div class="section-header">第一部分：题目初审</div>', unsafe_allow_html=True)

st.markdown("""
**说明：** 请上传物理题目的原始依据论文（PDF格式），并输入或上传原始物理题目。
系统将分析题目和论文的一致性，并给出审核结果。
""")

# 上传论文PDF
st.markdown('<div class="field-label">* 上传原始依据论文（PDF）</div>', unsafe_allow_html=True)
uploaded_paper = st.file_uploader(
    "上传PDF论文文件",
    type=["pdf"],
    help="请上传物理题目的原始依据论文PDF文件",
    key="paper_uploader"
)

if uploaded_paper is not None:
    if uploaded_paper.name != st.session_state.paper_file_name:
        with st.spinner("正在提取PDF内容..."):
            paper_text = extract_pdf_text(uploaded_paper)
            if paper_text and not paper_text.startswith("PDF读取错误"):
                st.session_state.paper_text = paper_text
                st.session_state.paper_file_name = uploaded_paper.name
                st.success(f"✅ 论文 '{uploaded_paper.name}' 已成功加载（共 {len(paper_text)} 字符）")
            elif paper_text and paper_text.startswith("PDF读取错误"):
                st.error(paper_text)
            else:
                st.warning("⚠️ PDF文件似乎没有可提取的文本内容，可能是扫描版图片。")
        st.rerun()

if st.session_state.paper_text:
    with st.expander("📄 查看论文内容（前1000字符）", expanded=False):
        st.text(st.session_state.paper_text[:1000] + "...")

# 上传或输入物理题目
st.markdown('<div class="field-label">* 原始物理题目</div>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    # 文本输入框
    question_input = st.text_area(
        "物理题目",
        value=st.session_state.question_text,
        height=200,
        placeholder="请在此输入或粘贴原始物理题目...",
        help="支持直接输入文本或从文件复制粘贴",
        key="question_input"
    )
    st.session_state.question_text = question_input
    
    # 文件上传（可选）
    uploaded_question_file = st.file_uploader(
        "或上传题目文件",
        type=["txt", "md"],
        help="支持上传 .txt、.md 文件",
        key="question_file_uploader"
    )
    
    if uploaded_question_file is not None:
        try:
            file_content = uploaded_question_file.read().decode("utf-8")
            st.session_state.question_text = file_content
            st.success(f"✅ 题目文件已加载")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 文件读取失败：{str(e)}")

with col2:
    st.markdown('<div class="field-label">操作</div>', unsafe_allow_html=True)
    analyze_question_btn = st.button(
        "🔍 分析题目",
        type="primary",
        use_container_width=True,
        disabled=not (st.session_state.paper_text.strip() and st.session_state.question_text.strip())
    )
    
    if analyze_question_btn:
        if not st.session_state.paper_text.strip():
            st.error("❌ 请先上传原始依据论文")
        elif not st.session_state.question_text.strip():
            st.error("❌ 请输入原始物理题目")
        else:
            with st.spinner("正在调用 DeepSeek API 分析题目和论文..."):
                analysis_result = analyze_question_with_paper(
                    st.session_state.question_text,
                    st.session_state.paper_text
                )
                st.session_state.question_analysis_result = analysis_result
            st.rerun()

# 显示分析结果
if st.session_state.question_analysis_result:
    st.markdown('<div class="field-label">※ 题目分析结果</div>', unsafe_allow_html=True)
    
    analysis_text = st.session_state.question_analysis_result
    
    # 判断是否通过（简单判断，可根据实际API返回结果调整）
    analysis_upper = analysis_text.upper()
    is_passed = "通过" in analysis_text or "YES" in analysis_upper or "合格" in analysis_text
    
    if is_passed:
        st.markdown(f"""
        <div class="detection-pass">
            <strong>✅ 审核通过</strong><br>
            {analysis_text.replace(chr(10), "<br>").replace(" ", "&nbsp;")}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="detection-fail">
            <strong>⚠️ 审核未通过</strong><br>
            {analysis_text.replace(chr(10), "<br>").replace(" ", "&nbsp;")}
        </div>
        """, unsafe_allow_html=True)
    
    # 详细结果展示
    with st.expander("📋 查看详细分析结果", expanded=True):
        st.markdown(analysis_text)
    
    # 人工确认锁定按钮
    st.markdown("")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if not st.session_state.question_approved:
            approve_btn = st.button(
                "✅ 确认通过，锁定初审结果",
                type="primary",
                use_container_width=True
            )
            if approve_btn:
                st.session_state.question_approved = True
                st.success("✅ 初审结果已锁定，可以进行下一步")
                st.rerun()
        else:
            st.info("🔒 初审结果已锁定")
            unlock_btn = st.button(
                "🔓 解锁初审结果",
                use_container_width=True
            )
            if unlock_btn:
                st.session_state.question_approved = False
                st.rerun()

# ==========================================
# 第二部分：答案和解答过程分析
# ==========================================
st.markdown('<div class="section-header">第二部分：答案和解答过程分析</div>', unsafe_allow_html=True)

if not st.session_state.question_approved:
    st.warning("⚠️ 请先完成第一部分：上传论文和题目，并确认通过初审结果")
else:
    st.markdown("""
    **说明：** 请上传或输入答案和解答过程。系统将分析答案的正确性、解答过程的质量，
    并重点检查其与原始依据论文的一致性。
    """)
    
    # 答案输入
    st.markdown('<div class="field-label">* 答案</div>', unsafe_allow_html=True)
    answer_input = st.text_area(
        "答案内容",
        value=st.session_state.answer_text,
        height=150,
        placeholder="请输入最终答案...",
        key="answer_input"
    )
    st.session_state.answer_text = answer_input
    
    # 解答过程输入
    st.markdown('<div class="field-label">* 解答过程</div>', unsafe_allow_html=True)
    solution_input = st.text_area(
        "解答过程",
        value=st.session_state.solution_process,
        height=250,
        placeholder="请输入详细的解答过程，包括解题思路、计算步骤等...",
        key="solution_input"
    )
    st.session_state.solution_process = solution_input
    
    # 分析按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_answer_btn = st.button(
            "🔍 分析答案和解答过程",
            type="primary",
            use_container_width=True,
            disabled=not (st.session_state.answer_text.strip() and st.session_state.solution_process.strip())
        )
    
    if analyze_answer_btn:
        if not st.session_state.answer_text.strip():
            st.error("❌ 请输入答案")
        elif not st.session_state.solution_process.strip():
            st.error("❌ 请输入解答过程")
        else:
            with st.spinner("正在调用 DeepSeek API 分析答案和解答过程..."):
                analysis_result = analyze_answer_with_paper(
                    st.session_state.answer_text,
                    st.session_state.solution_process,
                    st.session_state.question_text,
                    st.session_state.paper_text
                )
                st.session_state.answer_analysis_result = analysis_result
            st.rerun()
    
    # 显示分析结果
    if st.session_state.answer_analysis_result:
        st.markdown('<div class="field-label">※ 答案和解答过程分析结果</div>', unsafe_allow_html=True)
        
        analysis_text = st.session_state.answer_analysis_result
        
        # 判断是否通过
        analysis_upper = analysis_text.upper()
        is_passed = "通过" in analysis_text or "YES" in analysis_upper or "合格" in analysis_text
        
        if is_passed:
            st.markdown(f"""
            <div class="detection-pass">
                <strong>✅ 审核通过</strong><br>
                {analysis_text.replace(chr(10), "<br>").replace(" ", "&nbsp;")}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="detection-fail">
                <strong>⚠️ 审核未通过</strong><br>
                {analysis_text.replace(chr(10), "<br>").replace(" ", "&nbsp;")}
            </div>
            """, unsafe_allow_html=True)
        
        # 详细结果展示
        with st.expander("📋 查看详细分析结果", expanded=True):
            st.markdown(analysis_text)

# ==========================================
# 底部：重置功能
# ==========================================
st.divider()
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 重置所有数据", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()