from langchain_google_vertexai import VertexAI
import vertexai
import json
import os
from dotenv import load_dotenv
# 환경 변수 로드
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"

# VertexAI 초기화
vertexai.init(project="prompthon-prd-19")

example_input = json.loads({
  "Reference": [
    {
      "source": "C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094693\\2024년 기술이전 지원사업(서울 스타트업 Tech trade-on 프로그램) 공고문.hwp",
      "url": "https://startup-plus.kr/cms_for_portal/process/tech_market/list.do?show_no=750&check_no=77&c_relation=267&c_relation2=894h"
    },
    {
      "source": "C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000098045\\2024년_중소기업_CBAM_대응_인프라구축_사업_공고_2차_연장_신청서.hwp",
      "url": "I can't find that information."
    },
    {
      "source": "C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094693\\2024년 기술이전 지원사업(서울 스타트업 Tech trade-on 프로그램) 공고문.hwp",
      "url": "https://startup-plus.kr/cms_for_portal/process/tech_market/list.do?show_no=750&check_no=77&c_relation=267&c_relation2=894h"
    }
  ]
}
)


