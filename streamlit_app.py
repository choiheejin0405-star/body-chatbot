import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import time

# 1. 화면 설정
st.set_page_config(page_title="6학년 우리 몸 박사", page_icon="🩺")
st.title("🩺 6학년 우리 몸 박사 (완전판)")
st.caption("소화, 호흡, 순환, 배설, 자극과 반응까지 모두 알려주는 선생님입니다.")

# --- 파일 읽기 함수 (스마트 키워드 발췌독 - 전체 단원용) ---
@st.cache_data(show_spinner=False)
def extract_text_from_files(files):
    combined_text = ""
    
    # [수정] 6학년 '우리 몸의 구조와 기능' 전체 단원 핵심어
    # '기관' 같은 너무 흔한 단어는 뺐습니다. (용량 폭발 방지)
    KEYWORDS = [
        # 1. 뼈와 근육
        "뼈", "근육", 
        # 2. 소화
        "소화", "입", "식도", "위", "창자", "항문", "영양소",
        # 3. 호흡
        "호흡", "숨", "폐", "허파", "산소", "이산화 탄소",
        # 4. 순환
        "순환", "심장", "혈관", "혈액", "맥박",
        # 5. 배설
        "배설", "콩팥", "오줌", "방광", "노폐물",
        # 6. 자극과 반응
        "자극", "반응", "신경", "뇌", "척수", "감각"
    ]
    
    total_pages_read = 0
    relevant_pages_found = 0

    for file in files:
        try:
            file_ext = file.name.split('.')[-1].lower()
            
            if file_ext == 'pdf':
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        # 키워드가 하나라도 있으면 그 페이지를 저장!
                        if any(keyword in text for keyword in KEYWORDS):
                            combined_text += f"\n\n--- [참고 자료] ---\n{text}"
                            relevant_pages_found += 1
                    total_pages_read += 1

            elif file_ext == 'docx':
                doc = Document(file)
                for para in doc.paragraphs:
                    text = para.text
                    if any(keyword in text for keyword in KEYWORDS):
                         combined_text += text + "\n"

            elif file_ext == 'txt':
                text = file.read().decode("utf-8")
                combined_text += text
            
        except Exception:
            pass 
            
    # 용량 안전장치: 내용이 5만 자를 넘어가면 앞부분만 자릅니다. (429 에러 방지)
    if len(combined_text) > 50000:
        combined_text = combined_text[:50000]
        combined_text += "\n...(내용이 많아 안전하게 요약됨)..."

    summary = f"NOTE: 시스템 참고용 - 총 {total_pages_read}페이지 중 {relevant_pages_found}페이지 발췌함.\n\n"
    return summary + combined_text
# ---------------------

# 2. 사이드바 설정
with st.sidebar:
    st.header("⚙️ 선생님 설정")
    api_key = st.text_input("🔑 API 키를 입력하세요", type="password")
    
    st.markdown("---")
    st.write("📚 **지도서/교육과정 업로드**")
    uploaded_files = st.file_uploader("파일을 올려주세요", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)
    
    if "local_knowledge" not in st.session_state:
        st.session_state.local_knowledge = ""

    if uploaded_files:
        if st.button("자료 읽기 (클릭)", type="primary"):
            with st.spinner("우리 몸 단원 내용을 쏙쏙 뽑는 중..."):
                text_data = extract_text_from_files(uploaded_files)
                
                if text_data and len(text_data) > 100:
                    st.session_state.local_knowledge = text_data
                    st.success(f"✅ 수업 준비 완료!")
                    st.caption("소화, 호흡, 배설, 자극 등 모든 내용을 준비했어요.")
                else:
                    st.error("🚨 관련 내용을 못 찾았거나 텍스트를 읽을 수 없습니다.")
    
    if st.session_state.local_knowledge:
        st.info("🧠 선생님 준비 완료!")
    else:
        st.warning("👈 파일을 올리고 버튼을 눌러주세요.")

# 3. 모델 설정
if not api_key: st.stop()

try:
    genai.configure(api_key=api_key)
    # [중요] 만약 실행이 안 되면 아래 2.5를 1.5로 바꿔보세요!
    model = genai.GenerativeModel("models/gemini-2.5-flash") 
except Exception as e:
    st.error(f"설정 오류: {e}")
    st.stop()

# 4. 시스템 프롬프트 (선생님의 4가지 원칙 유지)
system_prompt = f"""
당신은 초등학교 6학년 과학 선생님입니다.
아래 [학습 자료]의 지식을 바탕으로 학생을 가르칩니다.

[학습 자료]:
{st.session_state.local_knowledge}

[대화 및 행동 수칙 - 절대 준수]:

1. **말투 (존댓말 사용)**:
   - 학생에게 항상 친절한 존댓말(해요체)을 사용하세요.
   - 딱딱하지 않고 다정하게 말해주세요.

2. **출처 비밀 엄수**:
   - 학생에게 절대 "지도서에 따르면", "파일 내용에 의하면" 같은 말을 하지 마세요.
   - 선생님 머릿속에 있는 지식인 것처럼 자연스럽게 이야기하세요.

3. **질문은 한 번에 하나씩**:
   - 퀴즈나 확인 질문은 한 번에 **딱 하나의 질문**만 던지세요.
   - 학생이 대답하면, 그 대답에 대해 반응해주고 다음으로 넘어가세요. (질문 폭탄 금지)

4. **피드백과 비계 설정 (Scaffolding)**:
   - 학생이 "몰라요"라고 하거나 틀린 답을 말하면, 정답을 바로 알려주기보다 힌트를 주세요.
   - "괜찮아요" 하고 그냥 넘어가지 말고, 쉬운 예시를 들어 이해를 도와주세요.
   - 학생이 맞히면 구체적으로 칭찬해주세요.

5. **개념 설명 (오개념 방지)**:
   - 어려운 한자어(조건/무조건 반사 등) 대신 풀어서 설명하세요.
   - 위급 상황 반응은 "뇌가 생각할 틈도 없이 몸이 먼저 빠르게 반응한다"고 설명하세요.

자, 이제 위 규칙을 지키며 학생과 대화하세요.
"""

# 5. 대화 처리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("질문하세요"):
    if not st.session_state.local_knowledge:
        st.error("👈 선생님, 먼저 왼쪽에서 자료를 읽혀주세요!")
    else:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            msg_box = st.empty()
            try:
                full_prompt = system_prompt + f"\n\n학생 말: {prompt}"
                
                # 재시도 로직
                try:
                    response = model.generate_content(full_prompt, stream=True)
                    full_response = ""
                    for chunk in response:
                        full_response += chunk.text
                        msg_box.markdown(full_response + "▌")
                    msg_box.markdown(full_response)
                    st.session_state.messages.append({"role": "model", "content": full_response})
                    
                except Exception as e:
                    if "429" in str(e):
                        msg_box.warning("잠시만요... 선생님이 생각할 시간이 필요해요 (3초)")
                        time.sleep(3)
                        response = model.generate_content(full_prompt)
                        msg_box.markdown(response.text)
                        st.session_state.messages.append({"role": "model", "content": response.text})
                    else:
                        msg_box.error(f"오류: {e}")

            except Exception as e:
                msg_box.error(f"오류: {e}")