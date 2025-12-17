import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import os

# 1. 화면 설정 및 브라우저 탭 정보 설정
# 목적: 웹 앱의 제목과 아이콘을 설정하여 학생에게 프로젝트 주제를 명확히 전달함
# 결과: 브라우저 탭에 '4.우리 몸의 구조와 기능'이라는 제목과 청진기(🩺) 아이콘이 표시됨
st.set_page_config(page_title="4.우리 몸의 구조와 기능", page_icon="🩺")

# 2. API 키 설정 
# 목적: Google Gemini AI 모델을 사용하기 위한 인증 키를 설정함. 이때 학생이 키를 입력하는 것이 아니라 이미 키 입력이 완료된 상태에서 학생이 챗봇을 활용할 수 있도록 함.
YOUR_API_KEY = "AIzaSyDdXoT68U4tQYOQutWqzBSlNM-AiMmowh8" 

if not YOUR_API_KEY or YOUR_API_KEY == "여기에_AIza로_시작하는_키를_붙여넣으세요":
    st.error("🚨 코드 12번째 줄에 API 키를 입력해주세요!")
    st.stop()

# 3. 모델 연결할 때 자동으로 모델 선택하게 함함
# 목적: 사용 가능한 Gemini 모델 목록을 가져와 최신 모델을 자동으로 연결하거나 사용자가 선택할 수 있게 함
# 결과: 왼쪽에 현재 연결된 모델 이름이 표시됨
try:
    genai.configure(api_key=YOUR_API_KEY)
    
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
            available_models.append(m.name)
            
    if available_models:
        with st.sidebar:
            # ---------------------------------------------------------
            # [수정] 이미지와 동일한 구성: 초록색 상자에 연결 정보 표시
            # ---------------------------------------------------------
            st.success(f"🚀 연결 성공:\n\n{available_models[0]}") 
            
            # 아래는 기존의 모델 선택 기능을 유지하고 싶을 때 사용하세요
            st.header("⚙️ 모델 설정")
            selected_model_name = st.selectbox("연결된 모델:", available_models, index=0)
        
        model = genai.GenerativeModel(selected_model_name)
    else:
        model = genai.GenerativeModel('gemini-pro')

except Exception as e:
    st.error(f"❌ 연결 오류: {e}\n(잠시 후 다시 시도하거나, 키를 확인해주세요)")
    st.stop()
# 4. 메인 화면 제목 및 설명 출력
# 결과: 화면 최상단(채팅 위)에 큰 제목과 학습의 시작을 여는 메시지가 보임
st.title("4.우리 몸의 구조와 기능")
st.caption("선생님과 함께 우리 몸에 대해 재미있게 알아보아요!")

# 5. data 폴더에 있는 PDF 학습 자료를 읽음.
# 목적: 'data' 폴더 내의 PDF 파일을 읽어 AI가 답변할 때 이를 기반으로 답함.
# 유의: st.cache_data를 사용하여 매번 파일을 읽지 않고 답변 속도를 최적화함
@st.cache_data(show_spinner=False)
def load_data():
    folder_path = 'data'
    combined_text = ""
    
    if not os.path.exists(folder_path):
        return ""

    files = os.listdir(folder_path)
    # 우리 몸과 관련된 핵심 키워드가 포함된 파일 부분만 선별하여 학습 효율을 높임
    KEYWORDS = ["뼈", "근육", "소화", "심장", "호흡", "배설", "뇌", "신경", "감각"]

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        try:
            content = ""
            # 파일 형식별(PDF, DOCX, TXT) 텍스트 추출에 대한 코드. 실제로 교사가 넣을만한 파일들은 다양하게 대비할 수 있게 파일 형식마다 코드 구현.
            if filename.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        content += page.extract_text()
            elif filename.endswith('.docx'):
                doc = Document(file_path)
                for para in doc.paragraphs:
                    content += para.text + "\n"
            elif filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            if any(k in content for k in KEYWORDS):
                combined_text += f"\n\n--- [참고 자료: {filename}] ---\n{content}"
        except Exception:
            pass 
    # 텍스트가 너무 길어 모델의 제한을 넘지 않도록 최대 글자수 제한.
    if len(combined_text) > 60000:
        combined_text = combined_text[:60000] + "\n...(이하 생략)..."
        
    return combined_text
# 6. 세션 상태를 활용한 지식 및 대화 기록 유지
# 목적: 웹 페이지가 새로고침되어도 학습 자료와 대화 내용이 사라지지 않게 함
if "knowledge" not in st.session_state:
    with st.spinner("선생님이 자료를 챙겨오고 있어요... 📚"):
        st.session_state.knowledge = load_data()

# 7. 챗봇의 역할 설정 및 학습 지침(System Prompt) 설정
# 목적: AI에게 '초등학교 6학년 담임 선생님'이라는 역할을 부여하고, 윤리적 판단 및 오개념 교정 등 구체적인 행동 규칙을 설정함함
system_prompt = f"""
당신은 초등학교 6학년 학생들을 가르치는 유능하고 지혜로운 '담임 선생님'입니다.
당신의 목표는 학생이 **좌절하지 않고 올바른 과학적 태도와 지식을 갖도록 돕는 것**입니다.

[학습 자료]:{st.session_state.knowledge}

---
**🚨 [선생님 행동 지침 (Teacher Guidelines)] 🚨**

**1. 호칭 및 이름 짓기 절대 금지**
   - 학생의 이름을 마음대로 지어 부르지 마세요. (예: 승민이, 우리 친구 등 금지)
   - 불필요한 호칭 없이 바로 본론을 이야기하세요.

**2. 오개념 교정 (1~2회 시도 후 정답 제시)**
   - 학생이 틀린 말을 하면 바로 "땡!" 하지 말고, **처음 1~2번은** "어? 정말 그럴까요?"라며 반문하여 스스로 생각하게 유도하세요.
   - **중요:** 힌트를 줬는데도 학생이 계속 틀리거나 어려워하면, **더 이상 질문하지 말고 즉시 올바른 정답과 이유를 친절하게 설명해 주세요.** (학생을 지치게 하지 마세요)

**3. "몰라요"에 대한 대응**
   - 학생이 "몰라요"라고 하면, 아주 쉬운 결정적 힌트(선택지 등)를 딱 한 번 줍니다.
   - 그래도 모르면 바로 정답을 알려주세요.

**4. 윤리 및 안전 지도 (강력 제재)**
   - **비속어/욕설**뿐만 아니라, **[생명 윤리]**와 **[연구 윤리]**에 어긋나는 탐구를 하려 할 때 **단호하게 제지하고 훈육**하세요.
     - **생명 윤리 위반 예시:** "개구리를 가위로 잘라볼래요", "햄스터에게 이상한 걸 먹여봐요" 
       → **대응:** "살아있는 생명은 소중해요. 함부로 해치거나 고통을 주면 절대 안 됩니다."
     - **연구 윤리 위반 예시:** "결과가 이상하니 숫자를 고칠래요", "친구 거 베껴서 낼래요"
       → **대응:** "과학자는 정직해야 해요. 결과를 조작하는 건 거짓말과 같아요. 실패한 결과도 소중한 데이터랍니다."
     - **안전 수칙 위반:** "위험한 약품을 섞어볼래요"
       → **대응:** "정말 위험한 생각이에요! 선생님이나 어른 없이 그런 실험을 하면 크게 다칠 수 있어요."

**5. 눈높이 설명 (6학년)**
   - 전문 용어 금지. 비유(펌프, 풍선, 공장 등)를 사용하여 쉽게 설명하세요.
   - 말투는 항상 따뜻한 존댓말(~해요)을 사용하세요.
---
"""
# 8. 학습자와 챗봇이 실시간으로 대화를 주고받는 채팅 화면을 구성함
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕! 반가워. 선생님이랑 우리 몸에 대해 재미있게 이야기 나눠볼까? 혹시 궁금한 점이 있니? 😊"}
    ]
# 저장된 대화 기록을 화면에 표시할 때 선생님/학생 아이콘 구분
for message in st.session_state.messages:
    avatar = "🧑‍🏫" if message["role"] == "assistant" else "🧑‍🎓"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 9. 학생의 입력 처리 및 AI 답변 생성 (스트리밍 방식)
# 목적: 사용자의 질문을 받아 시스템 프롬프트와 결합하여 전달하고, 답변을 실시간으로 출력함
# 결과: 사용자가 질문을 입력하면 AI 선생님이 실시간으로 타이핑하는 듯한 효과와 함께 답변이 생성됨
if prompt := st.chat_input("질문이나 대답을 입력하세요"):
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🧑‍🏫"):
        msg_box = st.empty()
        # 역할 지침과 학습 자료, 학습자의 현재 질문을 합쳐 챗봇에게 전달
        try:
            full_prompt = system_prompt + f"\n\n학생 말: {prompt}"
            response = model.generate_content(full_prompt, stream=True)
            full_response = ""
            for chunk in response:
                full_response += chunk.text
                msg_box.markdown(full_response + "▌")
            msg_box.markdown(full_response)
            st.session_state.messages.append({"role": "model", "content": full_response})     
        except Exception as e:
            msg_box.error(f"답변을 만드는 중 문제가 생겼어요: {e}")