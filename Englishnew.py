import streamlit as st
import random
import edge_tts
import asyncio
import base64
import time
import emoji
from openai import OpenAI

# 1. 配置
client = OpenAI(
    api_key=st.secrets["api_key"], 
    base_url="https://api.deepseek.com"
)

ALL_EMOJIS = list(emoji.EMOJI_DATA.keys())

async def get_voice_b64(text):
    # 如果语音也卡顿，可以尝试微调语速
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate="+0%")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return base64.b64encode(audio_data).decode()

# 3. 样式
st.set_page_config(page_title="English Master", page_icon="🇺🇸")
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    .stButton { display: flex; justify-content: center; margin-top: 30px; }
    .stButton>button { 
        width: 110px; height: 110px; font-size: 60px !important; 
        border-radius: 50%; border: 2px solid #3C3B6E; background: #fff;
    }
    .result-container { text-align: center; margin-top: 15px; }
    .emoji-font { font-size: 120px; margin-bottom: 0px; }
    .type-tag { 
        display: inline-block; padding: 2px 12px; border-radius: 15px; 
        background: #E8F0FE; color: #1967D2; font-size: 14px; font-weight: bold;
        margin-bottom: 10px; text-transform: uppercase;
    }
    .en-font { font-size: 60px; font-weight: bold; color: #3C3B6E; margin: 5px 0; }
    .cn-font { font-size: 32px; color: #B22234; font-weight: bold; }
    audio { display: block; margin: 15px auto; width: 260px; }
    </style>
    """, unsafe_allow_html=True)

if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.current_data = None
    st.session_state.last_audio_nonce = ""

# 5. 核心逻辑（带重试机制）
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🇺🇸"):
        st.session_state.step = 1
        st.session_state.last_audio_nonce = str(time.time()).replace(".", "")
        
        # 尝试最多 3 次请求
        max_retries = 3
        success = False
        
        for i in range(max_retries):
            icon = random.choice(ALL_EMOJIS)
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{
                        "role": "user", 
                        "content": f"Symbol '{icon}': Filter NSFW/Politics/Gender/Violence. Return EnglishWord|PartOfSpeech|ChineseMeaning. Mix Noun/Verb/Adj/Adv."
                    }],
                    timeout=5 # 缩短单次超时时间，快进快出
                )
                res = response.choices[0].message.content.strip().split("|")
                
                if len(res) >= 3 and "SKIP" not in res[0]:
                    st.session_state.current_data = {
                        "icon": icon, "word": res[0].strip(), 
                        "type": res[1].strip(), "cn": res[2].strip()
                    }
                    success = True
                    break
            except Exception:
                time.sleep(0.5) # 稍微等半秒再试
                continue
        
        if not success:
            st.warning("DeepSeek 拥挤中，请再点一次试试 🇺🇸")

# 渲染
if st.session_state.step >= 1 and st.session_state.current_data:
    data = st.session_state.current_data
    
    st.markdown(f'''
        <div class="result-container">
            <div class="emoji-font">{data["icon"]}</div>
            <div class="type-tag">{data["type"]}</div>
            <div class="en-font">{data["word"]}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    audio_container = st.empty()
    
    if st.session_state.step == 1:
        try:
            b64_str = asyncio.run(get_voice_b64(data["word"]))
            nonce = st.session_state.last_audio_nonce
            audio_html = f'''
                <div style="display: flex; justify-content: center;" id="container_{nonce}">
                    <audio controls autoplay id="audio_{nonce}">
                        <source src="data:audio/mp3;base64,{b64_str}" type="audio/mp3">
                    </audio>
                </div>
                <script>
                    var currentAudio = document.getElementById('audio_{nonce}');
                    if (currentAudio) {{ currentAudio.play().catch(e => {{}}); }}
                </script>
            '''
            audio_container.markdown(audio_html, unsafe_allow_html=True)
        except:
            st.info("语音正在赶来...")
        
        if st.button("Reveal Meaning (显示中文)"):
            st.session_state.step = 2
            st.rerun()

    if st.session_state.step == 2:
        st.markdown(f'<div class="result-container"><div class="cn-font">{data["cn"]}</div></div>', unsafe_allow_html=True)
