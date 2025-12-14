import streamlit as st
import google.generativeai as genai
import os

# 1. 환경 변수 로드 (안전장치 포함)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 2. 페이지 설정
st.set_page_config(
    page_title="Gemini Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Gemini Chatbot")

# 3. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    # API 키가 .env에 없으면 입력받기
    default_key = os.getenv("GOOGLE_API_KEY", "")
    api_key = st.text_input("Google API Key", value=default_key, type="password")
    
    if st.button("대화 내용 지우기"):
        st.session_state.messages = []
        st.rerun()

# 5. 메인 로직
if not api_key:
    st.warning("👈 사이드바에 Google API 키를 입력해주세요.")
    st.stop()

# 구글 Gemini 설정 (여기가 핵심!)
try:
    genai.configure(api_key=api_key)
    # 모델 설정 (gemini-1.5-flash가 가장 빠르고 무료입니다)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# 6. 채팅 인터페이스
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")

