import streamlit as st
import requests
import asyncio
import sqlite3
import os
import random
import subprocess


def get_url_from_db(bcIdx):
    conn = sqlite3.connect('./rdbms/mss.go.kr.db')
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM page_info WHERE bcIdx = ?", (bcIdx,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def create_download_link(filepath, filename):
    with open(filepath, "rb") as file:
        btn = st.download_button(
            label=f"Download {filename}",
            data=file,
            file_name=filename
        )
    return btn

def save_session_state_to_json():
    session_data = {
        'user_region': st.session_state.get('user_region', ""),
        'business_experience': st.session_state.get('business_experience', ""),
        'business_size': st.session_state.get('business_size', ""),
        'support_field': st.session_state.get('support_field', ""),
        'user_question': st.session_state.get('user_question', ""),
        'response_message': st.session_state.get('response_message', ""),
        'status_done': st.session_state.get('status_done', False),
        'result_answer': st.session_state.get('result_answer', ""),
        'valid_urls': st.session_state.get('valid_urls', []),
        'download_buttons': st.session_state.get('download_buttons', []),
    }
    return session_data

# Set the page title
st.set_page_config(page_title="정책비전AI")

# Display the logo using st.image
logo_url = "https://raw.githubusercontent.com/Core-BMC/SeoulPRT/main/images/bmclogo.png"
st.logo(logo_url)

# Center-align the title using markdown and CSS
st.markdown("""
    <style>
    @import url('https://webfontworld.github.io/pretendard/Pretendard.css');
    @import url('https://webfontworld.github.io/seoulhangang/SeoulHangangC.css');

    .title {
        text-align: center;
        font-size: 3.2rem;  /* 글자 크기 조정 */
        font-weight: 900; /* 가장 두꺼운 글자 두께 설정 */
        font-family: 'SeoulHangangC', sans-serif; /* 사용자 정의 폰트 적용 */
        margin-bottom: ; /* 제목과 서브타이틀 사이 간격 없애기 */
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;  /* 글자 크기 조정 */
        font-family: 'SeoulHangangC', sans-serif; /* 사용자 정의 폰트 적용 */
        text-indent: 6em; /* 들여쓰기 3번 적용 */
        margin-top: -10px; /* 서브타이틀과 간격 없애기 */
        font-weight: bold;
    }
    .center-text {
        text-align: center;
        font-family: 'Pretendard', sans-serif; /* 본문에 Pretendard 폰트 적용 */
    }
    .button-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }
    .stButton>button {
        padding: 10px 20px;
        margin-left: 25%;
        margin-right: 25%;
        width: 50%;
        border-radius: 10px;
        cursor: pointer;
        font-family: 'Pretendard', sans-serif; /* 버튼에 Pretendard 폰트 적용 */
    }
    .large-textbox > div > textarea {
        font-size: 1.2rem;
        height: 200px; /* 텍스트박스 높이 조정 */
    }
    .red-text {
        color: red; /* 빨간색 글자 */
        font-weight: bold; /* 볼드체 */
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.markdown("<h1 class='title'><b>정책</b><b>비전</b><b>AI</b></h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>for <span class='red-text'>Seoul</span></p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state['step'] = 0
if 'user_region' not in st.session_state:
    st.session_state['user_region'] = ""
if 'business_experience' not in st.session_state:
    st.session_state['business_experience'] = ""
if 'business_size' not in st.session_state:
    st.session_state['business_size'] = ""
if 'support_field' not in st.session_state:
    st.session_state['support_field'] = ""
if 'user_question' not in st.session_state:
    st.session_state['user_question'] = ""
if 'response_message' not in st.session_state:
    st.session_state['response_message'] = ""
if 'status_done' not in st.session_state:
    st.session_state['status_done'] = False
if 'result_answer' not in st.session_state:
    st.session_state['result_answer'] = ""
if 'valid_urls' not in st.session_state:
    st.session_state['valid_urls'] = []
if 'download_buttons' not in st.session_state:
    st.session_state['download_buttons'] = []

# Function to show initial message
def show_initial_message(container):
    with container:
        st.markdown("""
        <div class="center-text">
        <b>정책비전AI</b>는 서울에서 사업하시는<br>
        소상공인 및 사업주 님의 <b>지원사업<br> 정보제공</b> 및 <b>신청 간소화</b>를 위하여<br>
        서울시의 정책을 자동으로 검색하여<br> 간편하게 신청을 도와드리는<br>
        <b>서울디지털재단-BMC</b> 인공지능 서비스입니다.<br><br>
        먼저 <b>"사업주"</b>님에 대해 알려주세요.<br>
        <br><br>
        </div>
        """, unsafe_allow_html=True)
        if st.button("시작합니다", key="start"):
            st.session_state['step'] = 1
            st.session_state['response_message'] = "시작할게요!"
            st.rerun()

# Function to display the first question
def question_1(container):
    with container:
        st.markdown("""
        <div class="center-text">
        서울특별시에 사업자등록을 하셨으면 <br><b>"서울특별시"</b>를 선택해 주세요.<br><br> 
        다른 자치도 이신 경우, <b>"기타"</b>를 선택해 주세요.<br>
        <br><br>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 4, 4, 1])
        with col2:
            if st.button("서울특별시", key="seoul"):
                st.session_state['user_region'] = "서울특별시"
                st.session_state['step'] = 2
                st.session_state['response_message'] = "서울특별시를 클릭하셨습니다!"
                st.rerun()
        with col3:
            if st.button("기타", key="other"):
                st.session_state['user_region'] = "기타"
                st.session_state['step'] = 2
                st.session_state['response_message'] = "기타를 클릭하셨습니다!"
                st.rerun()

# Function to display the second question
def question_2(container):
    with container:
        st.markdown("""
        <div class="center-text">
        사업주 님의 업력을 알려주세요.<br>
        업력과 상관없이 모든 정보를 원하시면 모든 정보를 선택하세요.
        <br><br>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 4, 4, 1])
        with col2:
            if st.button("모든 정보", key="all_experience"):
                st.session_state['business_experience'] = "업력 전체"
                st.session_state['response_message'] = "업력 전체를 클릭하셨습니다!"
                st.session_state['step'] = 3
                st.rerun()
            if st.button("예비창업자", key="pre_entrepreneur"):
                st.session_state['business_experience'] = "예비창업자"
                st.session_state['response_message'] = "예비창업자를 클릭하셨습니다!"
                st.session_state['step'] = 3
                st.rerun()
        with col3:
            if st.button("기존창업자", key="existing_entrepreneur"):
                st.session_state['business_experience'] = "기존창업자"
                st.session_state['response_message'] = "기존창업자를 클릭하셨습니다!"
                st.session_state['step'] = 3
                st.rerun()

# Function to display the third question
def question_3(container):
    with container:
        st.markdown("""
        <div class="center-text">
        어떤 규모의 사업장을 운영하고 계신가요?<br>
        업장의 규모와 상관없이 모든 정보를 원하시면 모든 정보를 선택하세요.
        <br><br>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 4, 4, 1])
        with col2:
            if st.button("모든 정보", key="all_size"):
                st.session_state['business_size'] = "사업장 인원 전체"
                st.session_state['response_message'] = "사업장 인원 전체를 클릭하셨습니다!"
                st.session_state['step'] = 4
                st.rerun()
            if st.button("10인 이하", key="small"):
                st.session_state['business_size'] = "10인 이하"
                st.session_state['response_message'] = "10인 이하를 클릭하셨습니다!"
                st.session_state['step'] = 4
                st.rerun()
        with col3:
            if st.button("10인 이상", key="large"):
                st.session_state['business_size'] = "10인 이상"
                st.session_state['response_message'] = "10인 이상을 클릭하셨습니다!"
                st.session_state['step'] = 4
                st.rerun()

# Function to display the fourth question
def question_4(container):
    with container:
        st.markdown("""
        <div class="center-text">
        어떤 분야의 사업지원을 찾으시나요?<br>
        찾으시는 분야가 없으시면 기타를, <br>
        분야와 상관없이 모든 정보를 원하시면 전체를 선택하세요.
        <br><br>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 4, 4, 1])
        with col2:
            if st.button("정책", key="policy"):
                st.session_state['support_field'] = "정책"
                st.session_state['response_message'] = "정책을 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()
            if st.button("교육", key="education"):
                st.session_state['support_field'] = "교육"
                st.session_state['response_message'] = "교육을 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()
            if st.button("컨설팅", key="consulting"):
                st.session_state['support_field'] = "컨설팅"
                st.session_state['response_message'] = "컨설팅을 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()
            if st.button("시설", key="facility"):
                st.session_state['support_field'] = "시설"
                st.session_state['response_message'] = "시설을 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()
        with col3:
            if st.button("사업화", key="commercialization"):
                st.session_state['support_field'] = "사업화"
                st.session_state['response_message'] = "사업화를 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()
            if st.button("행사", key="event"):
                st.session_state['support_field'] = "행사"
                st.session_state['response_message'] = "행사를 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()
            if st.button("기타", key="others"):
                st.session_state['support_field'] = "기타"
                st.session_state['response_message'] = "기타를 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()
            if st.button("전체", key="all"):
                st.session_state['support_field'] = "전체"
                st.session_state['response_message'] = "전체를 클릭하셨습니다!"
                st.session_state['step'] = 5
                st.rerun()

# Function to display the fifth question
def question_5(container):
    with container:
        st.markdown("""
        <div class="center-text">
        사업주 님이 묻고 싶은 질문을 자유롭게 작성하실 수 있어요. (option)<br>
        <br><br>
        </div>
        """, unsafe_allow_html=True)
        user_question = st.text_area("질문을 입력하세요", 
                                     placeholder="예시 질문) 소상공인도 고용보험료 지원이 가능하다고 들었는데 어디에서 신청할 수 있나요?",
                                     height=200, key="user_question_textarea")
        if st.button("제출", key="submit"):
            st.session_state['user_question'] = user_question if user_question.strip() else "질문 없음"
            st.session_state['step'] = 6
            st.session_state['response_message'] = ""  # Clear the previous response message
            st.rerun()

async def process_and_display_result():
    json_data = str(save_session_state_to_json())
    print(json_data)
    
    with st.spinner("최신 신청 정보를 검색하고 있습니다..."):
        st.caption("정보를 검색 중입니다...")
        
        response = requests.post("http://127.0.0.1:8000/generate-answer/", json={"question": json_data})
        
        if response.status_code == 200:
            result = response.json()
            st.caption("구글AI를 통해 정보를 정리했습니다.")
            
            if 'result' in result:
                st.markdown("### 검색 결과")
                
                try:
                    rr = result['result'][-3]['re_generate']['generation']
                except:
                    rr = result['result'][2]['generate']['generation']
                    
                answer = rr['Answer']
                st.write(answer)
                
                valid_urls = []
                download_buttons = []
                
                # URL 처리
                reference_urls = rr.get('Reference', {}).get('url', [])
                if isinstance(reference_urls, str):
                    reference_urls = [reference_urls]
                valid_urls = [url for url in reference_urls if url != 'None'][:5]

                # 파일 처리
                reference_sources = rr.get('Reference', {}).get('source', [])
                if isinstance(reference_sources, str):
                    reference_sources = [reference_sources]
                
                hwpx_files = [file for file in reference_sources if file.lower().endswith(('.hwpx', '.hwp'))]
                if hwpx_files:
                    url = "http://localhost:8000/modify-hwp/"
                    payload = {
                        "prom_information": rr['Information'],
                        "file_path": hwpx_files[0]
                    }
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        subprocess.run([r'.\.fastapi_venv\Scripts\python.exe', './fastapi/modify_hwp.py'], capture_output=True, text=True)
                        random_num = random.randrange(1,100)
                        split_name = hwpx_files[0].split('.')
                        modi_name = split_name[0]+"_modified."+split_name[1]
                        change_name = split_name[0]+"_modified"+str(random_num)+"."+split_name[1]
                        os.rename(modi_name, change_name)
                        reference_sources.append(change_name)

                # 다운로드 버튼 생성
                for source in reference_sources:
                    if os.path.exists(source):
                        filename = os.path.basename(source)
                        download_buttons.append((source, filename))
                
                # 가장 최근의 5개 다운로드 버튼 유지
                download_buttons = download_buttons[-5:]

                if valid_urls:
                    answer += "\n\n## 참고 사이트"
                    for i, url in enumerate(valid_urls, start=1):
                        answer += f"\n{i}. {url}"
                
                st.session_state['result_answer'] = answer
                st.session_state['valid_urls'] = valid_urls
                st.session_state['download_buttons'] = download_buttons

                
                for filepath, filename in download_buttons:
                    create_download_link(filepath, filename)
            else:
                st.error("검색 결과를 가져오는데 문제가 발생했습니다.")
        else:
            st.error("서버와의 통신 중 오류가 발생했습니다.")
            print(response.status_code)
            print(response.json())
        
    st.session_state['status_done'] = True

def show_final_message(container):
    with container:
        st.markdown("""
        <div class="center-text">
        모든 입력이 완료되었습니다. 감사합니다!<br>
        잠시만 기다리시면 신청하실 수 있는 지원 정보를 제안해 드리겠습니다.<br>
        <br><br>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state['status_done']:
            asyncio.run(process_and_display_result())
        else:
            st.write(st.session_state['result_answer'])
            for filepath, filename in st.session_state['download_buttons']:
                create_download_link(filepath, filename)
        
        if st.button("처음으로", key="home"):
            reset_and_go_home()
            
# Function to reset and go to the initial page
def reset_and_go_home():
    st.session_state['step'] = 0
    st.session_state['user_region'] = ""
    st.session_state['business_experience'] = ""
    st.session_state['business_size'] = ""
    st.session_state['support_field'] = ""
    st.session_state['user_question'] = ""
    st.session_state['response_message'] = ""
    st.session_state['status_done'] = False
    st.session_state['result_answer'] = ""
    st.session_state['valid_urls'] = []
    st.session_state['download_buttons'] = []
    st.rerun()

# Handle the click events in Python
container = st.container()

if st.session_state['step'] == 1:
    question_1(container)
elif st.session_state['step'] == 2:
    question_2(container)
elif st.session_state['step'] == 3:
    question_3(container)
elif st.session_state['step'] == 4:
    question_4(container)
elif st.session_state['step'] == 5:
    question_5(container)
elif st.session_state['step'] == 6:
    show_final_message(container)
else:
    show_initial_message(container)

# Display the response message if any and not on the final message page
if st.session_state.get('response_message') and st.session_state['step'] != 6:
    st.success(st.session_state['response_message'], icon="✅")

# Reset the box_clicked state after displaying the message
if st.session_state.get('box_clicked'):
    st.session_state['box_clicked'] = False

# Display reset and home button in 3/4 of the screen, starting from step 1
if st.session_state['step'] >= 1 and st.session_state['step'] != 6:
    col1, col2, col3, col4 = st.columns([1, 4, 1.5, 3.5])
    with col4:
        if st.button("⬅️RESET"):
            reset_and_go_home()
