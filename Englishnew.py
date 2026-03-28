import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
import emoji
from openai import OpenAI

# 1. 核心配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

# 获取全部 Emoji 列表
ALL_EMOJIS = list(emoji.EMOJI_DATA.keys())

# 2. 英语语音生成
async def get_voice_b64(text):
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate="+0%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

# 3. 极简样式
st.set_page_config(page_title="English Explorer", page_icon="🇺🇸")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    .stButton { display: flex; justify-content: center; margin-top: 30px; }
    .stButton>button { 
        width: 120px; height: 120px; font-size: 70px !important; 
        border-radius: 50%; border: 1px solid #ddd; background: #fff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .result-container { text-align: center; margin-top: 20px; }
    .emoji-font { font-size: 150px; margin-bottom: 0px; }
    .en-font { font-size: 65px; font-weight: bold; color: #3C3B6E; margin: 10px 0; }
    .cn-font { font-size: 32px; color: #FF4B4B; margin-top: 0px; font-weight: bold; }
    .hint-text { font-size: 18px; color: #999; margin-top: 10px; }
    audio { display: block; margin: 15px auto; width: 280px; }
    
    /* 中文显示按钮样式 */
    .show-cn-btn { 
        background-color: #f0f2f6; border: none; padding: 10px 20px;
        border-radius: 10px; color: #666; cursor: pointer; font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. 初始化状态
if 'step' not in st.session_state:
    st.session_state.step = 0  # 0:初始, 1:出英文和语音, 2:出中文
    st.session_state.current_data = None

# 5. 逻辑处理
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🇺🇸"):
        st.session_state.step = 1
        # 随机抽取并过滤
        icon = random.choice(ALL_EMOJIS)
        
        try:
            # 强化提示词：过滤不适宜内容，只保留健康的百科名词
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{
                    "role": "user", 
                    "content": f"""分析符号 '{icon}'。
                    1. 如果该符号涉及政治、性别争议、怀孕男性、性取向、暴力或不适宜青少年的内容，请直接返回 'SKIP|SKIP'。
                    2. 否则，给出一个最适合初中生学习的英语名词及其中文。
                    格式：英语|中文"""
                }],
                timeout=8
            )
            res = response.choices[0].message.content.strip().split("|")
            if "SKIP" in res[0]:
                st.rerun() # 如果是不适宜内容，自动重抽
            else:
                st.session_state.current_data = {"icon": icon, "en": res[0], "cn": res[1]}
        except:
            st.error("网络连接失败")

# 渲染区域
if st.session_state.step >= 1 and st.session_state.current_data:
    data = st.session_state.current_data
    
    # 第一步：展示 Emoji 和 英文
    st.markdown(f'<div class="result-container"><div class="emoji-font">{data["icon"]}</div><div class="en-font">{data["en"]}</div></div>', unsafe_allow_html=True)
    
    # 自动播放语音 (仅在刚切换到第一步时触发一次)
    if st.session_state.step == 1:
        nonce = str(time.time()).replace(".", "")
        b64_str = asyncio.run(get_voice_b64(data["en"]))
        audio_html = f"""
            <div style="display: flex; justify-content: center;">
                <audio controls autoplay id="audio_{nonce}">
                    <source src="data:audio/mp3;base64,{b64_str}" type="audio/mp3">
                </audio>
            </div>
            <script>setTimeout(() => {{ document.getElementById('audio_{nonce}').play(); }}, 200);</script>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
        
        # 显示“查看中文”按钮
        if st.button("查看中文 / Show Chinese"):
            st.session_state.step = 2
            st.rerun()

    # 第二步：展示中文
    if st.session_state.step == 2:
        st.markdown(f'<div class="result-container"><div class="cn-font">{data["cn"]}</div></div>', unsafe_allow_html=True)
