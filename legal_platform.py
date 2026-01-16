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
    layout="wide"
)

st.title("⚖️ 法律数据构建平台")
st.caption("基于 DeepSeek API 的智能法律数据分析与题目构建工具")

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
    system_prompt = """Role: 你是一位资深的法律人工智能专家，专门负责构建高难度的 Legal LLM（法律大语言模型）评测数据集。你擅长将原始案例转化为考察模型“深度逻辑推理”与“知识检索精准度”的复杂题目。  
Task: 请参考提供的示例，对案情素材进行二次加工，构造出一个高质量的法律测评问题及其配套的“题目评价”。  
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
    system_prompt = """你是一位法律教育专家，擅长解答法律题目。
请根据提供的题目和原始案情文本，生成详细的解题思路和标准答案。
答案应该包括：
1. 解题思路：分析题目的关键点和解题步骤
2. 标准答案：完整、准确的答案内容
请用清晰、专业的方式呈现答案。"""
    
    prompt = f"""请根据以下题目和原始判决文本，生成详细的解题思路和标准答案：

【题目】
{question}

【原始判决文本】
{source_text}
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
st.divider()
with st.container():
    st.header("📄 模块 1：原始案件处理")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("输入原始判决文本")
        source_input = st.text_area(
            "判决文本",
            value=st.session_state.source_text,
            height=200,
            placeholder="请在此输入或粘贴原始判决文本...",
            help="支持直接输入文本或从文件复制粘贴"
        )
        
        # 文件上传功能
        uploaded_file = st.file_uploader(
            "或上传文本文件",
            type=["txt", "md"],
            help="支持上传 .txt 或 .md 文件"
        )
        
        if uploaded_file is not None:
            source_input = uploaded_file.read().decode("utf-8")
            st.session_state.source_text = source_input
            st.rerun()
    
    with col2:
        st.subheader("操作")
        analyze_btn = st.button(
            "🔍 分析文本",
            type="primary",
            use_container_width=True,
            disabled=not source_input.strip()
        )
        
        if analyze_btn and source_input.strip():
            st.session_state.source_text = source_input
            
            with st.spinner("正在调用 DeepSeek API 进行分析..."):
                analysis_result = analyze_source_text(source_input)
                st.session_state.source_analysis = analysis_result
    
    # 显示分析结果
    if st.session_state.source_analysis:
        st.subheader("📊 分析结果")
        st.info("以下是由 AI 生成的文本分析结果，仅供参考")
        st.markdown(st.session_state.source_analysis)
        
        # 显示状态指示
        if st.session_state.source_text:
            st.success(f"✅ 原始文本已保存（共 {len(st.session_state.source_text)} 字符）")

# ==========================================
# 模块 2：题目构建模块
# ==========================================
st.divider()
with st.container():
    st.header("❓ 模块 2：题目构建")
    
    if not st.session_state.source_text:
        st.warning("⚠️ 请先完成模块 1：输入并分析原始判决文本")
    else:
        # 在创建组件之前，先处理生成题目的逻辑
        # 这样可以确保 question_editor 的值在组件创建之前就已经设置好
        generate_question_btn = st.button(
            "🚀 生成题目",
            type="primary",
            key="generate_question_btn",
            disabled=not st.session_state.source_text
        )
        
        # 生成题目（在创建组件之前处理）
        if generate_question_btn:
            with st.spinner("正在调用 DeepSeek API 生成题目..."):
                generated = generate_question(st.session_state.source_text)
                # 更新状态：先更新 generated_question，再更新 question_editor
                # 必须在创建组件之前设置，否则会报错
                st.session_state.generated_question = generated
                st.session_state.question_editor = generated
            st.success("✅ 题目生成成功！")
            st.rerun()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("题目内容")
            
            # 如果题目已锁定，显示只读模式
            if st.session_state.question_locked:
                st.info("🔒 题目已锁定")
                question_display = st.text_area(
                    "题目（已锁定）",
                    value=st.session_state.locked_question,
                    height=150,
                    disabled=True
                )
            else:
                question_input = st.text_area(
                    "题目（可编辑）",
                    value=st.session_state.question_editor,
                    height=150,
                    placeholder="题目将在此显示，您可以手动编辑...",
                    key="question_editor"
                )
                # 同步文本框的值到 generated_question
                st.session_state.generated_question = question_input
        
        with col2:
            st.subheader("操作")
            
            lock_question_btn = st.button(
                "🔒 锁定题目",
                type="secondary",
                use_container_width=True,
                disabled=st.session_state.question_locked or not st.session_state.generated_question.strip()
            )
            
            unlock_question_btn = st.button(
                "🔓 解锁题目",
                use_container_width=True,
                disabled=not st.session_state.question_locked
            )
        
        
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
            st.info("🔓 题目已解锁，可以重新编辑")
            st.rerun()

# ==========================================
# 模块 3：解题思路与答案生成模块
# ==========================================
st.divider()
with st.container():
    st.header("💡 模块 3：解题思路与答案生成")
    
    if not st.session_state.question_locked:
        st.warning("⚠️ 请先完成模块 2：生成并锁定题目")
    elif not st.session_state.locked_question:
        st.warning("⚠️ 题目内容为空，请先生成题目")
    else:
        # 在创建组件之前，先处理生成答案的逻辑
        # 这样可以确保 answer_editor 的值在组件创建之前就已经设置好
        generate_answer_btn = st.button(
            "🚀 生成答案",
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
                # 更新状态：先更新 generated_answer，再更新 answer_editor
                # 必须在创建组件之前设置，否则会报错
                st.session_state.generated_answer = generated
                st.session_state.answer_editor = generated
            st.success("✅ 答案生成成功！")
            st.rerun()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("解题思路与答案")
            answer_input = st.text_area(
                "答案内容（可编辑）",
                value=st.session_state.answer_editor,
                height=300,
                placeholder="答案将在此显示，您可以手动编辑...",
                key="answer_editor"
            )
            # 同步文本框的值到 generated_answer
            st.session_state.generated_answer = answer_input
        
        with col2:
            st.subheader("操作")
            
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
                            "原始文本长度": len(st.session_state.source_text),
                            "题目": st.session_state.locked_question[:100] + "..." if len(st.session_state.locked_question) > 100 else st.session_state.locked_question,
                            "答案长度": len(st.session_state.generated_answer),
                            "保存路径": str(filepath)
                        })

# ==========================================
# 底部：重置功能
# ==========================================
st.divider()
with st.container():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 重置所有数据", use_container_width=True):
            for key in ["source_text", "source_analysis", "generated_question", 
                       "locked_question", "generated_answer", "question_locked"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# ==========================================
# 页脚说明
# ==========================================
st.divider()
with st.expander("ℹ️ 使用说明", expanded=False):
    st.markdown("""
    ### 使用流程
    
    1. **模块 1 - 原始案件处理**
       - 在文本框中输入或粘贴原始判决文本
       - 点击"分析文本"按钮，AI 会自动分析文本内容
       - 分析结果会显示在下方，原始文本会自动保存
    
    2. **模块 2 - 题目构建**
       - 点击"生成题目"按钮，AI 会根据原始文本生成法律题目
       - 在文本框中查看和编辑生成的题目
       - 确认无误后，点击"锁定题目"按钮
       - 锁定后可以点击"解锁题目"重新编辑
    
    3. **模块 3 - 解题思路与答案生成**
       - 题目锁定后，点击"生成答案"按钮
       - AI 会生成详细的解题思路和标准答案
       - 在文本框中查看和编辑答案内容
       - 确认无误后，点击"锁定并保存"按钮
       - 数据会自动保存到 Auto 文件夹，文件名为 `legal_data_YYYYMMDD_HHMMSS.json`
    
    ### 注意事项
    
    - 所有数据都保存在 Session State 中，刷新页面会保留数据
    - 如需重新开始，请点击底部的"重置所有数据"按钮
    - API Key 需要从侧边栏配置，或设置环境变量 `DEEPSEEK_API_KEY`
    - 保存的文件为 JSON 格式，包含原始文本、题目和答案
    """)
