import streamlit as st
import time
import vertexi_writer_api
import asyncio

async def run_json_question(json_data):
    return await asyncio.to_thread(vertexi_writer_api.json_question, json_data)

def save_session_state_to_json():
    session_data = {
        'user_region': st.session_state.get('user_region', ""),
        'business_experience': st.session_state.get('business_experience', ""),
        'business_size': st.session_state.get('business_size', ""),
        'support_field': st.session_state.get('support_field', ""),
        'user_question': st.session_state.get('user_question', ""),
        'response_message': st.session_state.get('response_message', ""),
    }
    return session_data

# Set the page title
st.set_page_config(page_title="SeoulQUERY")

# Display the logo using st.logo
logo_url = "https://raw.githubusercontent.com/Core-BMC/SeoulPRT/main/images/bmclogo.png"
st.logo(image=logo_url, link="https://github.com/Core-BMC")

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
    </style>
    """, unsafe_allow_html=True)

# Title
st.markdown("<h1 class='title'><b>Seoul</b><b>QUERY</b></h1>", unsafe_allow_html=True)
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

# Function to show initial message
def show_initial_message(container):
    with container:
        st.markdown("""
        <div class="center-text">
        <b>SeoulQUERY</b>는 서울에서 사업하시는<br>
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
    json_data = save_session_state_to_json()
    print(json_data)
    
    with st.status("최신 신청 정보를 검색하고 있습니다...", expanded=True) as status:
        st.caption("정보를 검색 중입니다...")
        
        # 비동기 실행
        result = await run_json_question(json_data)
        
        st.caption("구글AI를 통해 정보를 정리했습니다.")
        status.update(label="검색 완료!", state="complete", expanded=False)
        
        # 결과 표시
        if 'Answer' in result:
            st.markdown("### 검색 결과")
            st.write(result['Answer'])
        else:
            st.error("검색 결과를 가져오는데 문제가 발생했습니다.")
        
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
            if st.button("결과 확인하기"):
                asyncio.run(process_and_display_result())
        
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
