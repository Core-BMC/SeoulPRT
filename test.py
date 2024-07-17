import requests
import sqlite3
import json
from pprint import pprint

json_data = str({'user_region': '서울특별시', 'business_experience': '기존창업자', 'business_size': '10인 이상', 'support_field': '정책', 'user_question': '모든 기술이전 정책을 알고싶어', 'response_message': ''})
data = "서울특별시에서 10인 이상 기존창업자가 지역상권 상생과 관련하여 알 수 있는 정책 정보는 무엇인가요?"

streamlit_template1 = json.loads(json.dumps({"user_region":"서울", "business_experience":"10년", "business_size":"50인 이하", "support_field":["정책"], "user_question":"소상공인도 고용보험료 지원이 가능하다고 들었는데 어디에서 신청할 수 있나요?"}))
streamlit_template2 = json.loads(json.dumps({"user_region":"서울", "business_experience":"1년", "business_size":"10인 이하", "support_field":["컨설팅", "사업화", "교육"], "user_question":"창업한지 1년 되었는데 무언가 지원받을 수 있는게 있는지 궁금해"}))

question1 = f"""
사업하는 장소: {streamlit_template1['user_region']} \n
사업경력: {streamlit_template1['business_experience']} \n
사업장 인력 규모: {streamlit_template1['business_size']} \n
찾고있는 정보: {streamlit_template1['support_field']} \n
추가 질문 : {streamlit_template1['user_question']} \n
"""

question2 = f"""
사업하는 장소: {streamlit_template2['user_region']} \n
사업경력: {streamlit_template2['business_experience']} \n
사업장 인력 규모: {streamlit_template2['business_size']} \n
찾고있는 정보: {streamlit_template2['support_field']} \n
추가 질문 : {streamlit_template2['user_question']} \n
"""

response = requests.post("http://127.0.0.1:8000/generate-answer/", json={"question": str({'user_region': '서울특별시', 'business_experience': '기존창업자', 'business_size': '10인 이상', 'support_field': '정책', 'user_question': 'BMC 회사명으로 창업 준비 중이야. 대표자 이름은 심우현으로 2024년 창업 예정이야. 우리 회사가 기술이전 관련 받을 수 있는 혜택을 알고 싶어', 'response_message': '', 'status_done': False, 'result_answer': '', 'valid_urls': [], 'download_buttons': []})})

result = response.json()

result['result'][2]['generate']['generation']['Answer']
pprint(result['result'][-3]['re_generate']['generation']['Answer'])
result['result'][-3]['re_generate']['generation']['Information']
result['result'][2]['generate']['generation']['Reference']
pprint(result['result'][1]['retrieve']['documents'][6])

result['result'][-3].keys()

from pprint import pprint
pprint(result)

def get_url_from_db(bcIdx):
    conn = sqlite3.connect('./rdbms/mss.go.kr.db')
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM page_info  WHERE bcIdx = ?", (bcIdx,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

reference_urls = result['result'][2]['generate']['generation']['Reference']['url']
reference_sources = result['result'][2]['generate']['generation']['Reference']['source']

# 처리할 유효한 URL 리스트 생성
valid_urls = []

if isinstance(reference_urls, str):
    if reference_urls != 'None':
        valid_urls.append(reference_urls)
elif isinstance(reference_urls, list):
    valid_urls.extend([url for url in reference_urls if url != 'None'])

# Source에서 bcIdx 추출 및 DB에서 URL 조회
if isinstance(reference_sources, str):
    if 'mss.go' in reference_sources:
        bcIdx = reference_sources.split('\\')[-2]
        db_url = get_url_from_db(bcIdx)
        if db_url:
            valid_urls.append(db_url)
elif isinstance(reference_sources, list):
    for source in reference_sources:
        if 'mss.go' in source:
            bcIdx = source.split('\\')[-2]
            db_url = get_url_from_db(bcIdx)
            if db_url:
                valid_urls.append(db_url)
                
valid_urls





from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os
from dotenv import load_dotenv
openaijykey='./.env'
load_dotenv(openaijykey)
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"
from datetime import date

chunk_size = 3000
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=chunk_size)
# vectordb = Chroma.from_documents(documents=filtered_docs[0:5], persist_directory="./embedding_db/20240627_openai", embedding=embeddings)
vectordb = Chroma(persist_directory="./embedding_db/20240628_openai", embedding_function=embeddings)

db_retriever = vectordb.as_retriever(
    search_type="mmr",
    search_kwargs={'k': 5, 'fetch_k': 50}
)
today = str(date.today())
db_retriever.get_relevant_documents(f"서울특별시에서 10인 이상 기존 창업자를 위한 기술이전 관련 정책 정보를 찾습니다. 오늘은 {today}인걸 고려해서")
db_retriever.get_relevant_documents(f"기술 이전을 계획중인데 정책이나 혜택을 알고 싶어")


from glob import glob
path = glob(r'C:\Users\jinyoungkim0308\seoul_prompthon\downloads\tech\*')

import subprocess
subprocess.run([r'C:\Users\jinyoungkim0308\seoul_prompthon\.fastapi_venv\Scripts\python.exe', './fastapi/modify_hwp.py'], capture_output=True, text=True)