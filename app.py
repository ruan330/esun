import streamlit as st
from openai_utils import initialize_bedrock_clients, get_response
from datetime import datetime
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 設定頁面配置
st.set_page_config(
    page_title='玉山智慧GPT-beta',
    page_icon='🛡️',
    layout='wide',
    initial_sidebar_state='expanded',
)

# 自定義樣式
st.markdown(
    """
    <style>
    .main-container {
        padding: 2rem;
    }
    .user-message {
        background-color: #E0F7FA;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .assistant-message {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .rag-context {
        background-color: #FFFDE7;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid #FBC02D;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .message-timestamp {
        font-size: 0.8rem;
        color: #777;
        text-align: right;
        margin-top: 0.5rem;
    }
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        font-weight: bold;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        height: 2rem;
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 側邊欄
with st.sidebar:
    st.header('📖 關於玉山智慧智慧GPT')
    st.write('fjlaijflk;wjreiogjklrg。')
    st.write('請輸入您的問題，系統將為您檢索相關資訊並生成回答。')

    st.markdown('---')

    # 顯示 RAG 提供的資訊選項
    show_context = st.checkbox('顯示 RAG 提供的資訊', value=False)

    # 添加模型選擇
    model_option = st.selectbox(
        '選擇模型',
        ('gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o'),
        help='選擇要使用的AI模型'
    )

    st.markdown('---')
    st.write('👨‍💻 **開發者**：您的名字或團隊名稱')
    st.write('📫 **聯絡方式**：您的聯絡資訊，如 email 或網站')

    # 添加版本信息
    st.caption('版本: 0.0.3')

# 主要內容區
st.markdown("<div class='main-container'>", unsafe_allow_html=True)
st.markdown("<h1 class='main-header'>玉山智慧GPT-beta</h1>", unsafe_allow_html=True)

# 初始化 Bedrock 客戶端和 Agent 客戶端
bedrock_client, bedrock_agent_client, region = initialize_bedrock_clients()

# 初始化聊天記錄
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# 聊天區域
chat_container = st.container()


def display_messages():
    for message in st.session_state['messages']:
        if message['role'] == 'user':
            with st.chat_message("user"):
                st.markdown(message['content'])
                st.markdown(f"<div class='message-timestamp'>{message['timestamp']}</div>", unsafe_allow_html=True)
        elif message['role'] == 'assistant':
            with st.chat_message("assistant"):
                st.markdown(f"**{message['model']} 回應：**\n\n{message['content']}")
                st.markdown(f"<div class='message-timestamp'>{message['timestamp']}</div>", unsafe_allow_html=True)
        elif message['role'] == 'rag' and show_context:
            with st.chat_message("assistant"):
                st.markdown(message['content'])


with chat_container:
    display_messages()

# 輸入區域
input_container = st.container()

with input_container:
    st.markdown("### 💬 與助手對話")
    user_input = st.text_input('請輸入您的問題後，按下「發送」按鈕：', key='user_input', placeholder='在此輸入您的問題')
    send_button = st.button('發送', use_container_width=True)

if send_button and user_input:
    # 添加用戶消息
    st.session_state['messages'].append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model': model_option  # 添加當前選擇的模型
    })

    # 顯示加載指示器
    with st.spinner('助手正在思考中...'):
        try:
            # 獲取回應和上下文
            response_text, contexts = get_response(user_input, bedrock_client, bedrock_agent_client,
                                                   st.secrets['openai_api_key'], model_option)
            if not response_text:
                response_text = "抱歉，我無法生成回應。請稍後再試。"
        except Exception as e:
            logger.error(f"獲取回應時發生錯誤: {e}")
            response_text = f"發生錯誤：{str(e)}"
            contexts = []

    # 無論是否顯示，都記錄 RAG 資訊
    if contexts:
        rag_content = '\n\n'.join(contexts)
        st.session_state['messages'].append({
            'role': 'rag',
            'content': f"**📚 RAG 提供的資訊：**\n\n{rag_content}",
        })

    # 添加助手消息
    st.session_state['messages'].append({
        'role': 'assistant',
        'content': response_text,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model': model_option  # 添加當前選擇的模型
    })

    # 重新初始化客戶端
    bedrock_client, bedrock_agent_client, region = initialize_bedrock_clients()

    # 重新運行以更新介面
    st.rerun()

# 添加頁腳
st.markdown('---')
st.caption('© 2024 玉山智慧GPT-beta. All rights reserved.')
st.markdown("</div>", unsafe_allow_html=True)