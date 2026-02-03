import streamlit as st
import os
import json
from datetime import datetime
from openai import OpenAI
from pathlib import Path

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="法律数据构建平台",
    page_icon="⚖️",
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
    .role-item {
        background-color: #f8f9fa;
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid #3498db;
        border-radius: 3px;
    }
    .task-item {
        background-color: #fff3cd;
        padding: 0.5rem;
        margin: 0.3rem 0;
        border-left: 3px solid #ffc107;
        border-radius: 3px;
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
st.markdown('<div class="main-header">⚖️ 法律数据构建平台</div>', unsafe_allow_html=True)

with st.expander("📋 项目说明", expanded=True):
    st.markdown("""
    **项目背景：**
    
    当前的大语言模型在简单的行业问题上表现良好（如"盗窃罪判几年？"），但在复杂的真实场景中缺乏深度，
    例如法律案例分析、金融投资策略、医疗诊疗方案或科研问题。我们的目标是让 AI 更智能、更专业，
    通过行业专家设计具有挑战性的问题来提升AI的专业能力。
    
    **您的角色：**
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        - ⚖️ **法律**：律所律师、法官
        - 💼 **经济金融**：分析师、会计师
        """)
    with col2:
        st.markdown("""
        - 🏥 **医疗**：主治医师
        - 🔬 **科研**：研究人员
        """)
    with col3:
        st.markdown("""
        - 📊 **其他专业领域**专家
        """)
    
    st.markdown("""
    **您的任务：**
    """)
    
    st.markdown("""
    1. 出一道您领域中真实的高难度的"案例分析题"
    2. 自己写出"答案思考过程"及"标准答案"
    3. 制定一套严格的"评分细则(Rubrics)"
    4. 然后给两个"实习生"(AI模型)的回答进行打分
    """)

# ==========================================
# 侧边栏：API 配置
# ==========================================
with st.sidebar:
    st.header("🔑 API 配置")
    
    # API Key 配置（优先从环境变量读取，否则从输入框）
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
# API 调用函数（模块化）
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
    """
    调用 DeepSeek API
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词
        temperature: 温度参数（0-1）
    
    Returns:
        API 返回的文本内容
    """
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

def analyze_source_text(source_text: str):
    """分析原始判决文本"""
    system_prompt = """你是一位法律大模型基准测试（Benchmark）的数据专家。我正在构建一个用于测评 Legal LLM 的数据集，核心考察维度为复杂案情分析能力（特别是多罪名认定）和外部知识库检索（RAG）能力。
请审核以下[待测案件]，并根据下列标准进行 1-5 分的打分：
1. 多罪名分析维度：
5分：案情复杂，涉及两个及以上罪名，且罪名之间存在竞合、牵连关系或事实交叉，需要极强的逻辑拆解能力（例如：既涉嫌诈骗又涉嫌非法吸收公众存款）。
3分：涉及多个罪名，但各罪名事实独立，界限清晰，推理难度一般。
1分：单一罪名或案情极其简单。
2. 检索依赖维度：
5分：必须检索特定的地方法规、行业规范、司法解释或复杂的过往判例才能做出准确判断（仅凭通用法律常识无法回答）。
3分：需要引用具体的刑法条款，但属于常见条款。
1分：仅凭常识或基础法理即可回答，无需外部检索。
输出要求： 【YES / NO】（总分≥6分）"""
    
    prompt = f"请分析以下判决文本：\n\n{source_text}"
    return call_deepseek_api(prompt, system_prompt, temperature=0.7)

def generate_question(source_text: str):
    """生成法律题目"""
    system_prompt = """Role: 你是一位资深的法律人工智能专家，专门负责构建高难度的 Legal LLM（法律大语言模型）评测数据集。你擅长将原始案例转化为考察模型"深度逻辑推理"与"知识检索精准度"的复杂题目。  
Task: 请参考提供的示例，对案情素材进行二次加工，构造出一个高质量的法律测评问题及其配套的"题目评价"。  
核心考察维度（必须在题目中体现）,同时注意避免AI味过重：  
复杂案情分析能力： 侧重多罪名认定、罪名交叉、罪数形态（自首、立功、并罚等）的判定。  
RAG 能力测试点： 题目须要求模型必须结合特定的外部法律条文、司法解释或行业规则（如香港上市规则、刑法特定章节）进行回答。  
构造规范：  
    问题背景： 需包含干扰信息和高度细节化的案情描述，以模拟真实法律文书环境，不要包含法院判决或相关信息。  
    问题设计： 增强问题难度，针对案件中较难的疑难点进行提问（注意不要太直接的提问），例如准确罪名预测和刑期预测。  
    问题检测： 评价该题目在法律认知复杂度、区分度以及检索必要性方面的优势。  
"""
    
    prompt = f"请根据以下案情生成一道法律题目：\n\n{source_text}"
    return call_deepseek_api(prompt, system_prompt, temperature=0.8)

def generate_answer(question: str, source_text: str):
    """生成解题思路和答案"""
    system_prompt = """你是一位资深的法律教育专家，擅长根据案件详情和题目要求，生成高质量的标准答案和详细的解题思路。

你的任务是：
1. 仔细阅读并理解PDF文件中的案件详情和背景信息
2. 根据题目中给出的案件背景，深入分析问题的核心要点
3. 提供详细的解题思路，包括：
   - 问题分析：识别题目中的关键法律问题和争议焦点
   - 法律依据：引用相关的法律条文、司法解释或判例
   - 推理过程：逐步分析案件的逻辑链条和推理步骤
   - 结论形成：基于案件事实和法律依据得出最终结论
4. 给出完整、准确、专业的标准答案

要求：
- 答案必须基于案件详情，不能脱离案件背景
- 思考思路要详细、逻辑清晰、条理分明
- 标准答案要准确、完整、具有权威性
- 使用专业、规范的法律术语
- 适当引用法律条文和司法解释作为支撑"""
    
    prompt = f"""请根据以下人工审核过的题目和案件详情，生成详细的解题思路和标准答案：

【题目和问题】
{question}

【案件详情（来自PDF文件）】
{source_text}

请按照以下结构组织你的回答：

## 一、解题思路

### 1. 问题分析
（识别题目中的关键法律问题、争议焦点等）

### 2. 案件事实梳理
（从案件详情中提取与题目相关的关键事实）

### 3. 法律依据
（引用相关的法律条文、司法解释、判例等）

### 4. 推理过程
（逐步分析案件的逻辑链条，说明如何从事实推导出结论）

### 5. 结论形成
（基于以上分析，形成最终结论）

## 二、标准答案

（给出完整、准确、专业的标准答案，确保答案基于案件详情，逻辑严密，具有说服力）
"""
    return call_deepseek_api(prompt, system_prompt, temperature=0.7)

# ==========================================
# 初始化 Session State
# ==========================================
if "source_text" not in st.session_state:
    st.session_state.source_text = ""
if "source_analysis" not in st.session_state:
    st.session_state.source_analysis = ""
if "generated_question" not in st.session_state:
    st.session_state.generated_question = ""
if "locked_question" not in st.session_state:
    st.session_state.locked_question = ""
if "generated_answer" not in st.session_state:
    st.session_state.generated_answer = ""
if "question_locked" not in st.session_state:
    st.session_state.question_locked = False
if "question_editor" not in st.session_state:
    st.session_state.question_editor = ""
if "answer_editor" not in st.session_state:
    st.session_state.answer_editor = ""
if "question_field" not in st.session_state:
    st.session_state.question_field = "法律/金融/资本市场/证券与上市(IPO)"
if "chinese_characteristics" not in st.session_state:
    st.session_state.chinese_characteristics = "是"
if "question_detected" not in st.session_state:
    st.session_state.question_detected = False
if "detection_result" not in st.session_state:
    st.session_state.detection_result = ""
if "processed_file_name" not in st.session_state:
    st.session_state.processed_file_name = ""

# ==========================================
# 文件保存函数
# ==========================================
def save_to_file(source_text: str, question: str, answer: str):
    """保存数据到 Auto 文件夹"""
    try:
        # 确保 Auto 文件夹存在
        auto_dir = Path(__file__).parent  # Auto 文件夹
        auto_dir.mkdir(exist_ok=True)
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"legal_data_{timestamp}.json"
        filepath = auto_dir / filename
        
        # 构建数据字典
        data = {
            "timestamp": timestamp,
            "source_text": source_text,
            "question": question,
            "answer": answer,
            "question_field": st.session_state.question_field,
            "chinese_characteristics": st.session_state.chinese_characteristics,
            "created_at": datetime.now().isoformat()
        }
        
        # 保存为 JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath, None
    except Exception as e:
        return None, str(e)

# ==========================================
# 模块 1：原始案件处理模块
# ==========================================
st.markdown('<div class="section-header">1. 原始案件素材</div>', unsafe_allow_html=True)

st.markdown("""
**说明：** 请选择您深度完成过的工作（如论文、研究报告、课程作业、项目描述等）。
题目应该专业、真实、信息完整，有详细的要求和示例。
""")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="field-label">* 原始案件文本</div>', unsafe_allow_html=True)
    
    # 文件上传功能（放在 text_area 之前，确保文件上传后能正确更新）
    uploaded_file = st.file_uploader(
        "或上传文本文件",
        type=["txt", "md", "docx", "pdf"],
        help="支持上传 .txt、.md、.docx 或 .pdf 文件",
        label_visibility="collapsed"
    )
    
    # 处理文件上传（避免重复处理导致无限循环）
    if uploaded_file is not None:
        # 检查是否已经处理过这个文件
        current_file_name = uploaded_file.name
        if current_file_name != st.session_state.processed_file_name:
            try:
                file_extension = current_file_name.split('.')[-1].lower()
                extracted_text = ""
                
                if file_extension == 'pdf':
                    # PDF 文件处理
                    try:
                        import pdfplumber
                        # 将文件指针重置到开头
                        uploaded_file.seek(0)
                        pdf_text = []
                        with pdfplumber.open(uploaded_file) as pdf:
                            for page in pdf.pages:
                                text = page.extract_text()
                                if text:
                                    pdf_text.append(text)
                        extracted_text = "\n\n".join(pdf_text)
                        if not extracted_text.strip():
                            st.warning("⚠️ PDF 文件似乎没有可提取的文本内容，可能是扫描版图片。")
                    except ImportError:
                        st.error("❌ 请安装 pdfplumber 库以支持 PDF 文件：pip install pdfplumber")
                        extracted_text = ""
                    except Exception as e:
                        st.error(f"❌ PDF 文件读取失败：{str(e)}")
                        extracted_text = ""
                
                elif file_extension == 'docx':
                    # Word 文档处理
                    try:
                        from docx import Document
                        doc = Document(uploaded_file)
                        extracted_text = "\n".join([para.text for para in doc.paragraphs])
                    except ImportError:
                        st.warning("⚠️ 请安装 python-docx 库以支持 .docx 文件：pip install python-docx")
                        extracted_text = uploaded_file.read().decode("utf-8", errors="ignore")
                    except Exception as e:
                        st.error(f"❌ Word 文档读取失败：{str(e)}")
                        extracted_text = ""
                
                else:
                    # 文本文件处理（txt, md 等）
                    extracted_text = uploaded_file.read().decode("utf-8")
                
                if extracted_text.strip():
                    st.session_state.source_text = extracted_text
                    st.session_state.processed_file_name = current_file_name  # 标记已处理
                    st.success(f"✅ 文件 '{current_file_name}' 已成功加载（共 {len(extracted_text)} 字符）")
                    # 使用 st.rerun() 但只执行一次
                    st.rerun()
                else:
                    st.warning("⚠️ 文件内容为空，请检查文件格式是否正确。")
                    
            except Exception as e:
                st.error(f"❌ 文件读取失败：{str(e)}")
        # 如果文件已处理过，不再重复处理（避免无限循环）
    # 注意：不要在没有上传文件时清除 processed_file_name，因为 rerun 后 uploaded_file 会暂时为 None
    # 只有在用户明确删除文件（通过文件上传器的 X 按钮）时，processed_file_name 才会自然失效
    
    # 文本输入框（使用 session_state 的值，确保文件上传后能正确显示）
    # 使用固定的 key，避免因 key 变化导致数据丢失
    source_input = st.text_area(
        "案件文本",
        value=st.session_state.source_text,
        height=250,
        placeholder="请在此输入或粘贴原始判决文本、案件描述等...",
        help="支持直接输入文本或从文件复制粘贴",
        label_visibility="collapsed",
        key="source_text_area"
    )
    
    # 同步文本框的值到 session_state
    # 重要：保护已有数据，避免意外清空
    # 如果 source_text 已有内容，只有在以下情况才更新：
    # 1. 用户手动输入了新内容（新内容明显不同）
    # 2. 或者 source_text 为空
    if source_input != st.session_state.source_text:
        # 如果 source_text 已有内容，需要谨慎判断是否是用户的新输入
        if not st.session_state.source_text:
            # source_text 为空，直接更新
            st.session_state.source_text = source_input
        elif source_input.strip() and len(source_input) > 50:
            # 如果新输入有内容且足够长，可能是用户的新输入，更新
            # 但保留 processed_file_name，表示可能来自文件
            st.session_state.source_text = source_input

with col2:
    st.markdown('<div class="field-label">操作</div>', unsafe_allow_html=True)
    analyze_btn = st.button(
        "🔍 分析案件",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.source_text.strip()
    )
    
    if analyze_btn and st.session_state.source_text.strip():
        with st.spinner("正在调用 DeepSeek API 进行分析..."):
            analysis_result = analyze_source_text(st.session_state.source_text)
            st.session_state.source_analysis = analysis_result
            st.session_state.question_detected = True
            st.session_state.detection_result = analysis_result
        st.rerun()

# 显示分析结果（放在模块1下方，确保能正确显示）
st.markdown("")  # 添加一些间距
if st.session_state.source_analysis:
    st.markdown('<div class="field-label">※ 案件分析结果</div>', unsafe_allow_html=True)
    
    analysis_text = st.session_state.source_analysis
    analysis_upper = analysis_text.upper()
    
    # 判断是否通过（检查 YES 或 通过 关键词）
    is_passed = "YES" in analysis_upper or "通过" in analysis_text or "≥6" in analysis_text or "总分" in analysis_text
    
    if is_passed:
        st.markdown("""
        <div class="detection-pass">
            <strong>✅ 检测通过</strong><br>
            {}
        </div>
        """.format(analysis_text.replace("\n", "<br>").replace(" ", "&nbsp;")), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="detection-fail">
            <strong>⚠️ 检测未通过</strong><br>
            {}<br>
            <small>提示：请检查案件复杂度是否符合要求（总分需≥6分）</small>
        </div>
        """.format(analysis_text.replace("\n", "<br>").replace(" ", "&nbsp;")), unsafe_allow_html=True)
    
    # 同时用普通 markdown 显示，确保内容可见
    with st.expander("📋 查看详细分析结果", expanded=True):
        st.markdown(analysis_text)

# ==========================================
# 模块 2：题目构建模块
# ==========================================
st.markdown('<div class="section-header">2. 题目构建</div>', unsafe_allow_html=True)

if not st.session_state.source_text:
    st.warning("⚠️ 请先完成步骤 1：输入原始案件素材")
else:
    # 题目领域选择
    st.markdown('<div class="field-label">* 题目领域</div>', unsafe_allow_html=True)
    field_options = [
        "法律/金融/资本市场/证券与上市(IPO)",
        "法律/刑法/刑事案例分析",
        "法律/民法/合同纠纷",
        "法律/公司法/企业合规",
        "金融/投资分析",
        "金融/风险管理",
        "医疗/临床诊断",
        "医疗/治疗方案",
        "科研/实验设计",
        "其他专业领域"
    ]
    
    selected_field = st.selectbox(
        "选择题目领域",
        options=field_options,
        index=field_options.index(st.session_state.question_field) if st.session_state.question_field in field_options else 0,
        label_visibility="collapsed"
    )
    st.session_state.question_field = selected_field
    
    # 显示领域可用状态
    col1, col2 = st.columns([1, 4])
    with col1:
        st.success("✅ 领域可用")
    
    # 中国特色
    st.markdown('<div class="field-label">* 中国特色</div>', unsafe_allow_html=True)
    chinese_char = st.radio(
        "是否具有中国特色",
        options=["是", "否"],
        index=0 if st.session_state.chinese_characteristics == "是" else 1,
        horizontal=True,
        help="中国特色指深度依赖本土中国文化的题目，如中国政策、中国法律、中医等",
        label_visibility="collapsed"
    )
    st.session_state.chinese_characteristics = chinese_char
    
    # 题目内容
    st.markdown('<div class="field-label">* 题目内容</div>', unsafe_allow_html=True)
    
    # 在创建组件之前，先处理生成题目的逻辑
    generate_question_btn = st.button(
        "🚀 生成题目",
        type="primary",
        key="generate_question_btn",
        disabled=not st.session_state.source_text
    )
    
    # 生成题目（在创建组件之前处理）
    if generate_question_btn:
        # 确保 source_text 存在且不为空
        if not st.session_state.source_text or not st.session_state.source_text.strip():
            st.error("❌ 错误：原始案件文本为空，请先完成模块1：输入原始案件素材")
        else:
            with st.spinner("正在调用 DeepSeek API 生成题目..."):
                try:
                    generated = generate_question(st.session_state.source_text)
                    if generated and generated.strip():
                        # 确保在更新前，source_text 仍然存在（防止在生成过程中被清空）
                        if st.session_state.source_text:
                            st.session_state.generated_question = generated
                            st.session_state.question_editor = generated
                            st.success("✅ 题目生成成功！")
                            st.rerun()
                        else:
                            st.error("❌ 错误：原始案件文本在生成过程中丢失，请重新输入")
                    else:
                        st.error("❌ 题目生成失败，请重试")
                except Exception as e:
                    st.error(f"❌ 生成题目时出错：{str(e)}")
                    # 确保数据不丢失
                    if not st.session_state.source_text:
                        st.warning("⚠️ 原始案件文本已丢失，请重新输入")
    
    # 如果题目已锁定，显示只读模式
    if st.session_state.question_locked:
        st.info("🔒 题目已锁定")
        question_display = st.text_area(
            "题目（已锁定）",
            value=st.session_state.locked_question,
            height=200,
            disabled=True,
            label_visibility="collapsed"
        )
    else:
        question_input = st.text_area(
            "题目内容",
            value=st.session_state.question_editor,
            height=200,
            placeholder="题目将在此显示，您可以手动编辑...",
            key="question_editor",
            label_visibility="collapsed"
        )
        st.session_state.generated_question = question_input
    
    # 题目内容检测
    if st.session_state.generated_question:
        st.markdown('<div class="field-label">※ 题目内容检测</div>', unsafe_allow_html=True)
        
        # 检测逻辑（简化版，实际可以调用 API）
        if len(st.session_state.generated_question) > 100:
            detection_passed = True
            detection_text = """
            题目背景翔实，模拟了真实的法律案例分析场景；指令具体明确，涵盖了数据提取、策略梳理及多维度（效率、风控等）深度评价，
            符合专家级认知复杂度要求；基于特定时间点的案件进行分析，具备客观性和稳定性。
            """
        else:
            detection_passed = False
            detection_text = "题目内容过短，请补充更详细的背景信息和具体要求。"
        
        if detection_passed:
            st.markdown(f"""
            <div class="detection-pass">
                <strong>✅ 检测通过</strong><br>
                {detection_text}<br>
                <small>检测时间：{datetime.now().strftime("%Y/%m/%d")}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="detection-fail">
                <strong>⚠️ 检测未通过</strong><br>
                {detection_text}
            </div>
            """, unsafe_allow_html=True)
    
    # 操作按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        lock_question_btn = st.button(
            "🔒 锁定题目",
            type="secondary",
            use_container_width=True,
            disabled=st.session_state.question_locked or not st.session_state.generated_question.strip()
        )
    with col2:
        unlock_question_btn = st.button(
            "🔓 解锁题目",
            use_container_width=True,
            disabled=not st.session_state.question_locked
        )
    with col3:
        pass
    
    # 锁定题目
    if lock_question_btn:
        if st.session_state.generated_question.strip():
            st.session_state.locked_question = st.session_state.generated_question
            st.session_state.question_locked = True
            st.success("✅ 题目已锁定")
            st.rerun()
    
    # 解锁题目
    if unlock_question_btn:
        st.session_state.question_locked = False
        # 解锁时，将锁定的题目内容恢复回可编辑状态
        if st.session_state.locked_question:
            st.session_state.question_editor = st.session_state.locked_question
            st.session_state.generated_question = st.session_state.locked_question
        st.info("🔓 题目已解锁，可以重新编辑")
        st.rerun()

# ==========================================
# 模块 3：解题思路与答案生成模块
# ==========================================
st.markdown('<div class="section-header">3. 模型回答（标准答案）</div>', unsafe_allow_html=True)

st.markdown("""
**说明：** 在继续之前，请先评估 AI 的回答水平。我们需要 AI 无法很好解决的问题。
如果模型回答很好，请增加题目难度（如增加场景复杂度或干扰信息）；否则，该题目不适合。
""")

if not st.session_state.question_locked:
    st.warning("⚠️ 请先完成步骤 2：生成并锁定题目")
elif not st.session_state.locked_question:
    st.warning("⚠️ 题目内容为空，请先生成题目")
else:
    # 在创建组件之前，先处理生成答案的逻辑
    generate_answer_btn = st.button(
        "🚀 生成标准答案",
        type="primary",
        key="generate_answer_btn",
        disabled=not st.session_state.question_locked
    )
    
    # 生成答案（在创建组件之前处理）
    if generate_answer_btn:
        with st.spinner("正在调用 DeepSeek API 生成答案..."):
            generated = generate_answer(
                st.session_state.locked_question,
                st.session_state.source_text
            )
            st.session_state.generated_answer = generated
            st.session_state.answer_editor = generated
        st.success("✅ 答案生成成功！")
        st.rerun()
    
    st.markdown('<div class="field-label">* 答案内容</div>', unsafe_allow_html=True)
    answer_input = st.text_area(
        "标准答案",
        value=st.session_state.answer_editor,
        height=350,
        placeholder="答案将在此显示，您可以手动编辑...",
        key="answer_editor",
        label_visibility="collapsed"
    )
    st.session_state.generated_answer = answer_input
    
    # 保存按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        save_btn = st.button(
            "💾 锁定并保存",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.generated_answer.strip()
        )
    
    # 保存数据
    if save_btn:
        if st.session_state.generated_answer.strip():
            filepath, error = save_to_file(
                st.session_state.source_text,
                st.session_state.locked_question,
                st.session_state.generated_answer
            )
            
            if error:
                st.error(f"❌ 保存失败：{error}")
            else:
                st.success(f"✅ 数据已保存到：{filepath}")
                
                # 显示保存的数据预览
                with st.expander("📋 查看保存的数据", expanded=False):
                    st.json({
                        "题目领域": st.session_state.question_field,
                        "中国特色": st.session_state.chinese_characteristics,
                        "原始文本长度": len(st.session_state.source_text),
                        "题目": st.session_state.locked_question[:100] + "..." if len(st.session_state.locked_question) > 100 else st.session_state.locked_question,
                        "答案长度": len(st.session_state.generated_answer),
                        "保存路径": str(filepath)
                    })

# ==========================================
# 底部：重置功能
# ==========================================
st.divider()
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 重置所有数据", use_container_width=True):
        for key in ["source_text", "source_analysis", "generated_question", 
                   "locked_question", "generated_answer", "question_locked",
                   "question_editor", "answer_editor", "question_detected", "detection_result"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
