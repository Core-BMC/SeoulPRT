import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict, Annotated
from langchain_core.runnables import RunnableConfig
from datetime import date
import subprocess
import warnings
warnings.filterwarnings(action='ignore')

# Load environment variables
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../vertexai_key/prompthon-prd-19-33d473e1eeb0.json"

# Define the model and prompts
model = ChatVertexAI(
    model="gemini-1.5-pro-001",
    temperature=0,
    max_tokens=8192,
    max_retries=5,
    stop=None,
)
#model="gemini-1.5-pro-001",

flash_model = ChatVertexAI(
    model="gemini-1.5-flash-001",
    temperature=0,
    max_tokens=8192,
    max_retries=5,
    stop=None,
)

llm_json = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0.0,
    model_kwargs={"response_format": {"type": "json_object"}}
)

llm_GPT = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0.0,
)

prompt = PromptTemplate(
    template="""
    1. You understand the user's question and rephrase it to make it easier to search in vectordb.
    2. You don't rewrite it so that it changes the meaning of the question.
    3. If any fields are left blank, see if you can fill them in from other fields and fill them in. If not, delete the item.
    4. If the user_question entry is not written, infer the user_question from other entries. For example, 
        "user_region": "Seoul", 
        "business_experience": "Pre-founder", 
        "business_size": "10 employees or less", 
        "support_field": "Policy", 
    then the user_question would be similar to "Are there any policies available for prospective founders who are preparing to start a business in Seoul?"
    5. Please change to Str format instead of Json and write well in sentence format.
    6. Write only the answer to be searched well in vectordb.
    7. If user_region is '서울특별시', '강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구' and '중랑구' are all included.
    8. If user_region is '기타', ensure that the regions listed in number 7 are not included in the question. ‘Other’ refers to all areas other than Seoul. You can change it to “all regions.”
    9. Please answer in Korean.
    
    Here is the user question: {question}
    """,
    input_variables=["question"],
)

question_router = prompt | flash_model | StrOutputParser()

simple_prompt = PromptTemplate(
    template="""
    You are an assistant that extracts the core information from user queries to optimize search results. 
    Your task is to identify and succinctly state the main request or topic from the user's question.
    
    Here are some guidelines:
    1. Focus only on the user's question.
    2. Ignore all other metadata (e.g., user_region, business_experience, etc.).
    3. Keep the summary short and to the point.

    Example input:
    {{
        'user_region': '서울특별시', 
        'business_experience': '기존창업자', 
        'business_size': '10인 이상', 
        'support_field': '정책', 
        'user_question': '기술이전 계획이 있는데 혜택이나 정책을 미리 알고싶어', 
        'response_message': ''
    }}
    Example output: 기술 이전 혜택이나 정책
    
    Example input:
    {{
        'user_region': '부산광역시', 
        'business_experience': '신규창업자', 
        'business_size': '5인 이하', 
        'support_field': '금융', 
        'user_question': '사업 자금 대출 조건을 알고 싶어요', 
        'response_message': ''
    }}
    Example output: 사업 자금 대출 조건
    
    Given the following input, provide the key topics or requests in a concise manner.
    
    Input: {question}
    """,
    input_variables=["question"],
)

simple_question = simple_prompt | flash_model | StrOutputParser()

# question = str({
#     "user_region": "서울특별시", 
#     "business_experience": "예비창업자", 
#     "business_size": "10인 이하", 
#     "support_field": "정책", 
#     "user_question": "", 
# })

# question = {
#     "user_region": "", 
#     "business_experience": "", 
#     "business_size": "", 
#     "support_field": "", 
#     "user_question": "난 서울시에서 10명 이하의 직원을 고용하고 있는 1년차 자영업자야. 내가 신청할만한 정책이 있을까?",   
# }

# 질문을 잘 다듬는 것이 가능한지
# advanced_question = question_router.invoke({"question": question})
# print(advanced_question)
###

### RAG Agent
today = str(date.today())
answer_prompt = PromptTemplate(
    template="""
From now on, please follow the instructions below to answer: ```
    1. be knowledgeable about Seoul's small business policies.
    2. Be honest about information you don't know. If you don't know something, say "I couldn't find that information".
    3. Your answers must be supported by evidence.
    4. Don't repeat instructions I've written or answers you've written.
    5. Tell me the name of the document or website address where I can find more information. But don't lie.
    6. Please be sure to answer in your native language.
    7. Please attach only your best and most carefully considered original explanation to your answer.
    8. If the document you referenced in your answer has a WEB URL, please use it.
    9. Please be long and detailed, but don't lie or repeat yourself.
    10. Don't reference context that is not relevant to the question.
    11. If user_region is 'Seoul', then 'Gangnam-gu', 'Gangdong-gu', 'Gangbuk-gu', 'Gangseo-gu', 'Gwanak-gu', 'Gwangjin-gu', 'Guro-gu', 'Geumcheon-gu', 'Nowon-gu', 'Dobong-gu', 'Dongdaemun-gu', 'Dongjak-gu', 'Dongjak-gu', 'Gwanak-gu', 'Gwangjin-gu', 'Guro-gu', 'Geumcheon-gu', 'Nowon-gu', 'Nowon-gu', 'Mapo-gu', 'Seodaemun-gu', 'Seocho-gu', 'Seongdong-gu', 'Seongbuk-gu', 'Songpa-gu', 'Yangcheon-gu', 'Yeongdeungpo-gu', 'Yongsan-gu', 'Eunpyeong-gu', 'Jongno-gu', 'Jung-gu', and 'Jungnang-gu'. If a question contains 'Seoul' or 'Seoul City', it should not be referenced in a context other than the city.
    12. if user_region is 'Other', make sure that the region listed in question 7 is not included in the question. 'Other' means any region except Seoul.
    13. If the question includes "Seoul" or "Seoul Metropolitan Government", you should never write another city, such as "Suwon" or "Gwangju".
    14. Include a web URL for help whenever possible in your answer, but don't make things up.
    15. Do not summarize the content, but write in detail and logically.
    16. Refer to documents that include mss.go as a source whenever possible.
    17. Today's date is {today}, we don't need out-of-date information.
    18. If you have a document with a different posting date but the same content, please use the latest information.
    ```

Writing Instruction Form
In the future, whenever I ask a question, please write the response following the format below. I will provide the topic or content with each question, so please maintain this format and fill in the information accordingly:```

지원 대상

[Description of eligibility 1]
[Description of eligibility 2]

지원 내용

[Support item 1]
[Detailed information 1]
[Detailed information 2]
[Support item 2]
[Detailed information 1]
[Detailed information 2]
[Other support items]

신청 기간

[Application period information]

문의처

[Contact information 1] (☎ [Phone number])
[Contact information 2] (☎ [Phone number])
더 자세한 내용은 아래 웹사이트에서 확인하세요:
    - [Website 1]: [URL]
    - [Website 2]: [URL]

지원 신청 절차

[Step 1]
[Step 2]
[Step 3]
[Step 4]

필요 서류

[Document 1]
[Document 2]
[Document 3]
[Document 4]
[Document 5]

제출 방법

[Submission method 1]
[Submission method 2]
[Submission method 3]

예산

총 예산: [Budget amount]
[Budget item 1]: [Budget item amount]

지원 기간

시작일: [Start date]
종료일: [End date] (사업비 소진 시까지)```

Please use this format to organize the information for any questions I provide.

Read the following explanation and write your answer using the context: ```{context}```

User question: ```{question}```
    """,
    input_variables=['context', 'question', 'today']
)
answer_chain = answer_prompt | flash_model | StrOutputParser()

url_prompt= PromptTemplate(
    template="""
Your response should be in JSON format.
User question: ```{question}```
Answer: ```{answer}```
From now on, please follow the instructions below to answer: ```
    1. gather the URLs in context.
    2. gather source from context.
    3. Extract only URLs and sources that are relevant to the user's question or answer.
    4. Be sure to extract only the URL and SOURCE of the topic that matches the question and answer.
```

If your answer is about technology transfer, enter only two in your answer, such as 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\tech\\2407051314482024년+기술이전+지원사업(서울+스타트업+Tech+trade-on+프로그램)+공고문.hwp', 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\tech\\2407051314482024년도+공공기술이전+지원사업.jpg'

Hear is context: ```{context}```

Here's an example of how the source might be stored: 'source':['C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000096322\\Notice on participation in the 2024 Wonju Lacquerware Expo (exhibition) and implementation of support project for hosting it.hwp' is written like this.', 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094693\\2024년 기술이전 지원사업(서울 스타트업 Tech trade-on 프로그램) 공고문.hwp', ...]
Here's an example of how the source might be stored: 'url':['https://www.seoulsbdc.or.kr/', 'https://news.seoul.go.kr/economy/small-business-supports', ...]
    
Output Format (JSON)Output Format (JSON)
{{
    'url': Find and record all URLs that exist in the context. Collect all website addresses in context.
    'source': Find and record all sources and data path that exist in the context. Keep a record of all your files, whether they're PDFs or HWP files or JPG files, and where they're located.
}}
    """,
    input_variables=['context', 'question', 'answer']
)

ref_chain = url_prompt | llm_json | JsonOutputParser()

infor_prompt = PromptTemplate(
    template="""
    Your response should be in JSON format.
    
    From now on, please follow the instructions below to answer: ```
        1. Extract the author's information from the answers and questions provided. For example, if the representative's name is 'kim', we assume the author's name is 'kim'.
        2. If the information in the answer and question are different, give the information in the question more weight.
        3. Think of the name of the '대표자' as the same as the author's name.

    ```
    Hear is Question: ```{question}```
    Hear is Answer: ```{answer}```
    
    Output Format (JSON)Output Format (JSON)
    {{
        "company_name": "Fill in if the company name is included in the question", 
        "name": "Fill out if the question includes the name of the questioner.", 
        "user_region":"place of business.",
        "business_experience":"business experience",
        "business_size":"Workplace workforce size"
    }}
    """,
    input_variables=['answer', 'question']
)
info_chain = infor_prompt | llm_json | JsonOutputParser()

prompt = PromptTemplate(
    template="""system
Read the following explanation and write your answer using the context: ```{context}```

Please follow the instructions below to answer: ```
    1. You are an expert who is familiar with Seoul City’s small business policies.
    2. You must be honest about information you do not know. If you don't know, please say 'I can't find that information.'
    3. Your answer must be supported.
    4. Please do not repeat the instructions I have written when adding numbers to your answer.
    5. Please tell us the name of the document or website address where more information can be found. But don't lie.
    6. Please be sure to answer in Korean.
    7. Please attach only the original, most carefully considered explanation to your response.
    8. Please attach the original including the webpage address corresponding to the source.
    9. Please tell us the location of the document you referenced in the references section.
    10. There is no need to refer to context that appears unrelated to the question.
    11. If user_region is '서울특별시', '강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구' and '중랑구' are all included. If '서울특별시' or '서울시' is included in the question, documents other than those listed are false information.
    12. If user_region is '기타', ensure that the regions listed in number 7 are not included in the question. ‘Other’ refers to all areas other than Seoul. You can change it to “all regions.”
    13. 질문에 '서울시' 혹은 '서울특별시'가 들어간다면 절대로 '수원시' or '광주시' 같은 다른 시의 정보를 작성하면 안됩니다.
    14. Answer에는 가급적 도움을 받을 수 있는 web url이 포함되어 있으면 좋습니다. 단, 없는 것을 지어내지 마세요.
    15. Don’t summarize the content, but write it in detail and logically.
    16. Please refer to documents that include mss.go as the source.
    17. 'source' must contain the address of the file.
    
```
    
Here's an example of the answer I want:
```
If you have operated a business in Jung-gu, Seoul for more than a year, you can participate in the ‘2024 Jung-gu Customized Small Business Support Project’. Since this project targets small business owners who have been operating a business in Jung-gu for more than 6 months, you meet the application qualifications.

Through this project, you can receive management improvement consulting, online conversion consulting, etc., and cost support of up to 1 million won is also available.

For more information, please refer to the ‘2024 Jung-gu Customized Small Business Support Project First Half Recruitment Notice’ on the Seoul Credit Guarantee Foundation website (https://www.seoulsbdc.or.kr/).

### Reference
2024 Jung-gu Customized Small Business Support Project** ([URL actually referenced. Please write it once.])
```

The sample answer is just an example and I would like you to write in more detail.
Please write the original part as is, but write the answer part in as much detail as possible.
After creating the answer as above, share it in detail with Json.

Example ```JSON format```:
```
{{
    "Question": "Write the original question naturally in sentence form.",
    "Answer": "Parts of the answer that do not constitute references."
    "Reference": {{
        "source": "
        1. Please write the source value in the context as is. 
        2. If there is no relevant information, please write 'None'. 
        3. Be sure to write down the source in its entirety without omitting it.
        4. There is a very high probability that there is a source in the context. For example, 'source': 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000096322\\Notice on participation in the 2024 Wonju Lacquerware Expo (exhibition) and implementation of support project for hosting it.hwp' is written like this.", 
        "url": "Site address where the announcement was posted. If there is no relevant information, please write 'None'. You should not write a web URL that is not in the context. For example, 'url': 'https://news.seoul.go.kr/economy/small-business-supports' is written like this."}}
    "Information": {{
        "company_name": "Fill in if the company name is included in the question", 
        "name": "Fill out if the question includes the name of the questioner.", 
        "user_region":"place of business.",
        "business_experience":"business experience",
        "business_size":"Workplace workforce size"
        }}
}}
```
In Json format, category "Answer" should be composed of support target, support content, application period, application method, and contact information.

    user
Question: ```{question}```
    """,
    input_variables=["question", "context"],
)

rag_chain = prompt | model | JsonOutputParser()

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=3000)
vectordb = Chroma(persist_directory="../embedding_db/20240628_openai", embedding_function=embeddings)

mmr_retriever = MultiQueryRetriever.from_llm(
    retriever=vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 5, 'fetch_k': 30}
    ), llm=llm_GPT
)

similar_retriever = MultiQueryRetriever.from_llm(
    retriever=vectordb.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={'score_threshold': 0.5, 'k':3}
    ), llm=llm_GPT
)

ensemble_retriever = EnsembleRetriever(
    retrievers=[mmr_retriever, similar_retriever], weights=[0.6, 0.4]
)

# context = ensemble_retriever.invoke(advanced_question)
# BM25_retriever1 = BM25Retriever.from_documents(documents=context, k=3)
# bm_context1 = BM25_retriever1.get_relevant_documents(advanced_question)

# rag_response = rag_chain.invoke({"question":advanced_question, "context":context})
# print(rag_response)
###

### 답변을 context를 참조했는지 여부를 체크하는 Agent
halu_prompt = PromptTemplate(
    template="""system You are a grader assessing whether an answer is grounded in and supported by a set of provided facts.
    To decide, compare the answer with the facts and check if the answer contains any specific details such as numbers, website addresses, or phone numbers from the given information.
    Give a binary 'yes' or 'no' score to indicate whether the answer is grounded in and supported by the set of facts.
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
    Write 'no' very carefully if the answer does not reflect any specific details from the facts.
    Use the following criteria to make your judgment:
    1. The answer should contain at least one specific element such as a number, website address, or phone number that directly references or is logically derived from the provided facts.
    2. Ensure the answer is not contradictory to the provided facts.

    Here are the facts:
    \n ------- \n
    {documents}
    \n ------- \n

    Here is the answer: {generation}

    Examples:
    Facts: 
    1. The sky is blue.
    2. Grass is green.
    Answer: The sky is blue and grass is green.
    Score: {{"score": "yes"}}

    Facts: 
    1. The sky is blue.
    2. Grass is green.
    Answer: The sky is red.
    Score: {{"score": "no"}}

    Facts: 
    1. The sky is blue.
    2. Grass is green.
    Answer: The sky is blue and dogs are cute.
    Score: {{"score": "no"}}

    Facts: 
    1. The sky is blue.
    2. Grass is green.
    Answer: The sky is blue, and the grass is green.
    Score: {{"score": "yes"}}
    
        Facts:
    1. The economic growth rate increased by 3%.
    2. Unemployment rates have fallen to a new low.
    Answer: The economy is improving.
    Score: {{"score": "yes"}}
    
    Facts:
    1. The economic growth rate increased by 3%.
    2. Unemployment rates have fallen to a new low.
    Answer: The stock market crashed.
    Score: {{"score": "no"}}
    
        Facts: 
    1. The company's revenue increased by 20percent in 2023.
    2. The customer service phone number is 123-456-7890.
    Answer: The company's revenue increased by 20%.
    Score: {{"score": "yes"}}

    Facts: 
    1. The company's revenue increased by 20percent in 2023.
    2. The customer service phone number is 123-456-7890.
    Answer: The company's revenue decreased.
    Score: {{"score": "no"}}

    Facts:
    1. Visit our website at www.example.com for more information.
    2. The office is open from 9 AM to 5 PM.
    Answer: Visit our website at www.example.com.
    Score: {{"score": "yes"}}
    
    Facts:
    1. Visit our website at www.example.com for more information.
    2. The office is open from 9 AM to 5 PM.
    Answer: The office opens at 8 AM.
    Score: {{"score": "no"}}
    """,
    input_variables=["generation", "documents"],
)

generation = []
hallucination_grader = halu_prompt | model | JsonOutputParser()
# hallucination_grader_response = hallucination_grader.invoke({"documents": context, "generation": rag_response['Answer']})
# print(hallucination_grader_response)
###

re_url_prompt= PromptTemplate(
    template="""
Your response should be in JSON format.
Answer: {answer}
Please follow the instructions below to answer: ```
    1. gather the URLs in context.
    2. gather source from context.
    3. You need to look at the answer you wrote, find the web address or data address you need, and extract it.
    4. Be sure to extract only the URL and SOURCE of the topic that matches the question and answer.
```

If your answer is about technology transfer, enter only two in your answer, such as 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\tech\\2407051314482024년+기술이전+지원사업(서울+스타트업+Tech+trade-on+프로그램)+공고문.hwp', 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\tech\\2407051314482024년도+공공기술이전+지원사업.jpg'

Hear is context: ```{context}```

Here's an example of how the source might be stored: 'source':['C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000096322\\Notice on participation in the 2024 Wonju Lacquerware Expo (exhibition) and implementation of support project for hosting it.hwp' is written like this.', 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094693\\2024년 기술이전 지원사업(서울 스타트업 Tech trade-on 프로그램) 공고문.hwp', ...]
Here's an example of how the source might be stored: 'url':['https://www.seoulsbdc.or.kr/', 'https://news.seoul.go.kr/economy/small-business-supports', ...]
    
Output Format (JSON)Output Format (JSON)
{{
    'url': Find and record all URLs that exist in the context. Collect all website addresses in context.
    'source': Find and record all sources and data path that exist in the context. Keep a record of all your files, whether they're PDFs or HWP files or JPG files, and where they're located.
}}
    """,
    input_variables=['context', 'answer']
)

re_ref_chain = re_url_prompt | llm_json | JsonOutputParser()

### QC하는 Agent
prompt = PromptTemplate(
    template=""" From now on, you should follow the instructions below. You are a grader assessing whether an answer is useful to resolve a question. 
    Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question. 
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
    If this is an introduction, please write yes.
    If there's a sentence that says '찾을 수 없습니다(not found)', write 'no'.
    For example, if the answer includes the sentence "I couldn't find that information.", you should write "no".
    It's okay to not have specific information once in a while, and only write "no" if you don't have information overall.
    Here is the answer:
    \n ------- \n
    {generation} 
    \n ------- \n
    Here is the question: {question} """,
    input_variables=["generation", "question"],
)

answer_grader = prompt | llm_GPT | JsonOutputParser()
# answer_grader_response = answer_grader.invoke({"question": advanced_question,"generation": rag_response['Answer']})
# print(answer_grader_response)
###

### 할루시 혹은 QC체크를 통과하지 못하면 돌아가서 다시 작성해야하기 때문에 rewriter
### 좀더 구체적이고 생산적인 답변을 만들어 달라고 해볼 것
### rewriter Agent
answer_prompt = PromptTemplate(
    template="""
From now on, please follow the instructions below to answer:

1. Be knowledgeable about Seoul's small business policies.
2. Be honest about information you don't know. If you don't know something, say "I couldn't find that information".
3. Your answers must be supported by evidence.
4. Don't repeat instructions I've written or answers you've written.
5. Tell me the name of the document or website address where I can find more information. But don't lie.
6. Please be sure to answer in your native language.
7. Please attach only your best and most carefully considered original explanation to your answer.
8. If the document you referenced in your answer has a WEB URL, please use it.
9. Please be long and detailed, but don't lie or repeat yourself.
10. Don't reference context that is not relevant to the question.
11. If user_region is 'Seoul', then 'Gangnam-gu', 'Gangdong-gu', 'Gangbuk-gu', 'Gangseo-gu', 'Gwanak-gu', 'Gwangjin-gu', 'Guro-gu', 'Geumcheon-gu', 'Nowon-gu', 'Dobong-gu', 'Dongdaemun-gu', 'Dongjak-gu', 'Dongjak-gu', 'Gwanak-gu', 'Gwangjin-gu', 'Guro-gu', 'Geumcheon-gu', 'Nowon-gu', 'Nowon-gu', 'Mapo-gu', 'Seodaemun-gu', 'Seocho-gu', 'Seongdong-gu', 'Seongbuk-gu', 'Songpa-gu', 'Yangcheon-gu', 'Yeongdeungpo-gu', 'Yongsan-gu', 'Eunpyeong-gu', 'Jongno-gu', 'Jung-gu', and 'Jungnang-gu'. If a question contains 'Seoul' or 'Seoul City', it should not be referenced in a context other than the city.
12. If user_region is 'Other', make sure that the region listed in question 7 is not included in the question. 'Other' means any region except Seoul.
13. If the question includes "Seoul" or "Seoul Metropolitan Government", you should never write another city, such as "Suwon" or "Gwangju".
14. Include a web URL for help whenever possible in your answer, but don't make things up.
15. Do not summarize the content, but write in detail and logically.
16. Refer to documents that include mss.go as a source whenever possible.
17. Be as detailed and long as possible. Don't repeat yourself or write something that isn't there.
18. Don't write the same website address over and over again.
19. Today's date is {today}, we don't need out-of-date information.
20. If you have a document with a different posting date but the same content, please use the latest information.

From now on, don't lie with information that wasn't provided. If you can't find it, say you can't find it.

Writing Instruction Form
In the future, whenever I ask a question, please write the response following the format below. I will provide the topic or content with each question, so please maintain this format and fill in the information accordingly:

지원 대상

[Description of eligibility 1]
[Description of eligibility 2]

지원 내용

[Support item 1]
[Detailed information 1]
[Detailed information 2]
[Support item 2]
[Detailed information 1]
[Detailed information 2]
[Other support items]

신청 기간

[Application period information]

문의처

[Contact information 1] (☎ [Phone number])
[Contact information 2] (☎ [Phone number])
더 자세한 내용은 아래 웹사이트에서 확인하세요:
    - [Website 1]: [URL]
    - [Website 2]: [URL]

지원 신청 절차

[Step 1]
[Step 2]
[Step 3]
[Step 4]

필요 서류

[Document 1]
[Document 2]
[Document 3]
[Document 4]
[Document 5]

제출 방법

[Submission method 1]
[Submission method 2]
[Submission method 3]

예산

총 예산: [Budget amount]
[Budget item 1]: [Budget item amount]

지원 기간

시작일: [Start date]
종료일: [End date] (사업비 소진 시까지)

Please use this format to organize the information for any questions I provide.

Read the following explanation and write your answer using the context: ```{context}```

User question: ```{question}```
    """,
    input_variables=['context', 'question', 'today']
)
rewrite_chain = answer_prompt | llm_GPT | StrOutputParser()

###

###
from typing_extensions import TypedDict, Annotated
from typing import List

class GraphState(TypedDict):
    question: str
    advanced_question: str
    documents: list
    generation: dict
    score: str
    
def route_question(state):
    print("---ROUTE QUESTION---")
    question = state["question"]
    print("Input question:", question)
    source = question_router.invoke({"question": question})
    print("Routed question:", source)
    return {"advanced_question": source}
    
def retrieve(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    og_question = state["advanced_question"]
    question = state["question"]
    question = simple_question.invoke(question)
    print(question)

    # Retrieval
    documents = ensemble_retriever.invoke(question)
    print(f"documents count: {len(documents)}")
    # BM25_retriever1 = BM25Retriever.from_documents(documents=documents, k=5)
    # bm_context1 = BM25_retriever1.get_relevant_documents(question)
    return {"documents": documents, "advanced_question": og_question}

def generate(state):
    """
    Generate answer using RAG on retrieved documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["advanced_question"]
    og_question = state['question']
    print(question)
    documents = state["documents"]
    
    # RAG generation
    # generation = rag_chain.invoke({"context": documents, "question": question})
    generation = {}
    generation['Answer'] = answer_chain.invoke({"context": documents, "question": question, "today": today})
    generation['Reference'] = ref_chain.invoke({"context": documents, "question": question, "answer": generation['Answer']})
    generation['Information'] = info_chain.invoke({"answer": generation['Answer'], 'question': og_question})
    return {"documents": documents, "question": question, "generation": generation}

def hallucination(state):
    """
    RAG is the process of ensuring that the article you write is written with reference to real-world context.
    If the RAG was not referenced, {'score': 'no'} is returned.
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    rag_response = state["generation"]['Answer']
    context = state["documents"]
    # print(state["generation"]['Answer'])
    
    hallucination_grader_response = hallucination_grader.invoke({"documents": context, "generation": rag_response})
    
    try: 
        if hallucination_grader_response['score'] == 'yes':
            return {'score': 'yes'}
        else :
            print(state["generation"]['Answer'])
            print("halu no")
            return {'score': 'no'}
    except:
        print(state["generation"]['Answer'])
        print("halu no")
        return {'score': 'no'}

def quality_checker(state):
    """
    Check that your answer adequately helped solve the question.
    """ 
    
    print("---CHECK ANSWER QUALITY---")
    answer_grader_response = answer_grader.invoke({"question": state["advanced_question"], "generation": state["generation"]['Answer']})
    try: 
        if answer_grader_response['score'] == 'yes':
            return {'score': 'yes'}
        else :
            print(state["generation"]['Answer'])
            return {'score': 'no'}
    except:
        print(state["generation"]['Answer'])
        return {'score': 'no'}

def re_generate(state):
    
    print("---RE-GENERATE ANSWER---")
    question = state["advanced_question"]
    og_question = state['question']
    documents = state["documents"]
    generation = {}
    generation['Answer'] = rewrite_chain.invoke({"question": question, "context": documents, "today": today})
    print(generation['Answer'])
    generation['Reference'] = re_ref_chain.invoke({"context": documents, "answer": generation['Answer']})
    generation['Information'] = info_chain.invoke({"answer": generation['Answer'], 'question': og_question})
    return {"documents": documents, "question": question, "generation": generation}
###

###
from langgraph.graph import END, StateGraph
workflow = StateGraph(GraphState)

workflow.add_node("route_question", route_question)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)
workflow.add_node("hallucination", hallucination)
workflow.add_node("quality_checker", quality_checker)
workflow.add_node("re_generate", re_generate)

workflow.set_entry_point("route_question")

workflow.add_edge("route_question", "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "hallucination")


def route_hallucination(state: GraphState) -> Annotated[str, {"yes": "quality_checker", "no": "re_generate"}]:
    return "quality_checker" if state["score"] == "yes" else "re_generate"

workflow.add_conditional_edges("hallucination", route_hallucination)


def route_quality(state: GraphState) -> Annotated[str, {"yes": END, "no": "re_generate"}]:
    return END if state["score"] == "yes" else "re_generate"

workflow.add_conditional_edges("quality_checker", route_quality)

workflow.add_edge("re_generate", "hallucination")

workflow_app = workflow.compile()
###

###
name= []
values= []
def post_process_output(output):
    if output is None:
        print("Received None output")
        return
    for key, value in output.items():
        name.append(key)
        print(f"Finished running: {key}:")

        if isinstance(value, dict):
            if "generation" in value:
                generation_text = value["generation"]
                if isinstance(generation_text, str):
                    # "assistant" 문자열 제거 및 앞뒤 입력 아이디 제거
                    clean_text = generation_text.replace("assistant", ""
                                               ).replace("<|begin_of_text|>", ""
                                               ).replace("<|start_header_id|>", ""
                                               ).replace("<|end_header_id|>", ""
                                               ).replace("<|eot_id|>", ""
                                               ).strip()
                    print(clean_text)
                    values.append(value)
                else:
                    print("Generation is not a string:", generation_text)
                    values.append(value)
            else:
                print("No generation found in the output")
                print("Value:", value)
                values.append(value)
        else:
            print(f"Output for {key}:", value)
            values.append(value)
    return {'name':name, 'values':values}

# 출력 처리

def stream_output(inputs):
    for output in workflow_app.stream(inputs):
        rr = post_process_output(output)
    return rr

class FilePath(BaseModel):
    file_path: str

class RequestModel(BaseModel):
    prom_information: Dict[str, Any]
    file_path: FilePath
    
# FastAPI Application
app = FastAPI()


@app.post("/modify-hwp/")
async def modify_hwp(request: Dict[str, Any]):
    try:
        prom_information = request.get('prom_information')
        file_path = request.get('file_path')

        # Extract text from the HWP file
        hwp_content = extract_text_from_hwp(file_path)

        # Prepare the prompt
        write_hwp_prompt = f"""system
        Read the following explanation and write your answer using the context: ```{prom_information}```

        Please follow the instructions below to answer: ```
        1. You are an expert who goes to the provided file location, reads the hwp and hwpx documents, finds the parts that need to be written, and writes them down.
        2. Just look at the information provided in the context and write additional information in the correct location in the document.
        3. Write the hwp writing code by referring to the code in ‘write hwp code example’.
        4. Don’t say anything else, just write the code.
        5. company_name can be a '기업명' or '기 업 명' or '회사명' or '업체명'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
        6. name can be a '이름' or '이 름' or '성함' or '성 함' or '대표자'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
        7. business_experience can be a '업력' or '업 력' or '설립일' or '설립일자'. If 'business_experience' is '설립일' or '설 립 일' or '설립일자', assume that the business_experience value is the year and write {today} - business_experience value.
        8. business_size can be a '규모' or '사원 수' or '업장 크기' or '업장 규모'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
        9. user_region can be a '사업장 소재지' or '주소'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
        10. For numbers 5 through 9, if there is other content with similar meaning in the hwp file context, please use that content as the field name.
        10. Fields marked None do not need to be entered.
        11. If you're going to write None, don't write it at all.
        12. Do not write the value 'business_experience' in the '대표자' field.
        13. Do not enter the value 'business_size' in the '업체명' field.
        14. In addition, find words with similar meanings and write the appropriate information in the appropriate space.
        ```

        Please look at the contents of the corresponding hwp file to understand where to enter the information provided in the context: ```{hwp_content.encode('latin1').decode('euc-kr')}```

        write hwp code example: ```
        from hwpapi.core import App

        # Original_hwpx_file_path is {file_path}. Please replace the example below with {file_path}. If there are multiple file_paths, select one of them and enter it.
        # Never use the example path below. Please select from the file_path above and write.
        original_hwpx_file_path = r'hwp_file_path.hwp'

        # The revision must have a different name than the original. Please additionally write that the document has been modified.
        new_hwpx_file_path = r'hwp_file_path_modified.hwp'

        app = App(is_visible=False)
        app.open(original_hwpx_file_path)

        # When the information you find is in a table and you need to write it in the next frame on the right.
        def replace_text(app, old_text, new_text):
            if app.find_text(old_text):
                app.move()
                app.actions.MoveColumnEnd().run()
                app.actions.MoveSelRight().run()
                app.actions.MoveLineEnd().run()
                app.actions.MoveRight().run()
                app.actions.MoveColumnEnd().run()
                app.actions.MoveLineEnd().run()
                app.insert_text(new_text)

        # If there is a line break, find the word before the line break and execute it.
        replace_text(app, '사업장 소재지', '서울')
        replace_text(app, '사업장', '서울')
        replace_text(app, '기업명', '진영기업')
        replace_text(app, '기 업 명', '진영기업')
        replace_text(app, '사업자등록번호', '111222333')
        replace_text(app, '대표자명', '김진영')
        replace_text(app, '성명', '김진영')
        
        # if '근로자수\n(대표자포함)' than wirte '근로자수'. for example do not write replace_text(app, '근로자수', '10인 이상'). do write replace_text(app, '근로자수', '10인 이상').
        replace_text(app, '근로자수', '10인 이상')

        app.save(new_hwpx_file_path)
        app.quit()

        print("Done.")
        ```

        """
        test = model.invoke(write_hwp_prompt)
        test_result = test.content.replace(r"```python\n`", "").replace("```", "").replace("python", "")

        script_file_path = os.path.join(os.getcwd(), 'modify_hwp.py')
        with open(script_file_path, 'w', encoding='utf-8') as file:
            file.write(test_result)

        # result = subprocess.run([r'..\.fastapi\Scripts\python.exe', 'modify_hwp.py'], capture_output=True, text=True)

        # if result.returncode != 0:
        #     raise HTTPException(status_code=500, detail=result.stderr)

        return {"message": "HWP file modified successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import win32com.client as win32
def extract_text_from_hwp(file_path):
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.Open(file_path)

    full_text = ""

    def get_last_paragraph():
        hwp.MovePos(3)  # 문서의 끝으로 이동
        return hwp.GetPos()[1]  # 마지막 문단 번호 반환

    last_paragraph = get_last_paragraph()

    for i in range(last_paragraph + 1):
        hwp.SetPos(0, i, 0)  # i번째 문단의 시작으로 이동
        paragraph_text = hwp.GetTextFile("TEXT", "").strip()
        full_text += paragraph_text + "\n\n"

    hwp.Quit()
    return full_text

class Query(BaseModel):
    question: str

@app.post("/generate-answer/")
async def generate_answer(query: Query):
    inputs = {"question": query.question}
    config = RunnableConfig(recursion_limit=12)
    try:
        result = []
        for output in workflow_app.stream(inputs, config):
            result.append(output)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
