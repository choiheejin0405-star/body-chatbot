import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖")

st.title("🤖 Gemini 챗봇 (수정 완료)")

# 사이드바에서 API 키 입력받기
with st.sidebar:
    st.header("설정")
    # secrets에 키가 있으면 사용, 없으면 빈 값
    if "GOOGLE_API_KEY" in st.secrets:
        default_key = st.secrets["GOOGLE_API_KEY"]
    else:
        default_key = ""
        
    api_key = st.text_input("Google API Key 입력", value=default_key, type="password")

# API 키가 없으면 경고
if not api_key:
    st.warning("왼쪽 사이드바에 API 키를 입력해주세요.")
    st.stop()

# Gemini 설정
try:
    genai.configure(api_key=api_key)
    # [수정된 부분] gemini-pro 대신 최신 모델인 gemini-1.5-flash 사용
    model = genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# 채팅 기록 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 내용 화면에 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 채팅 입력 및 처리
if prompt := st.chat_input("메시지 입력..."):
    # 유저 메시지 화면에 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # [중요] 대화 맥락을 유지하려면 이전 대화 내용을 함께 보내는 것이 좋지만,
            # 오류 수정이 우선이므로 기본 generate_content 사용
            response = model.generate_content(prompt)
            
            message_placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            # 오류 메시지를 좀 더 친절하게 표시
            st.error(f"오류가 발생했습니다: {e}")
            if "400" in str(e) or "API key" in str(e):
                st.info("💡 API 키가 정확한지, 혹은 결제 계정 설정이 필요한지 확인해주세요.")
