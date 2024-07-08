from langchain_google_vertexai import VertexAI
import vertexai
import os
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from dotenv import load_dotenv
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"

vertexai.init(project="prompthon-prd-19")

# 모델 설정
# model = VertexAI(
#     model_name="gemini-1.5-pro-001",
#     temperature=0.1,
#     response_mime_type="application/json"
# ).bind(response_mime_type={"type": "application/json"})

model = VertexAI(
    model_name="gemini-1.5-pro-001",
    temperature=0.1,
)

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
    "Question": "Original answer.",
    "Answer": "Parts of the answer that do not constitute references."
    "Reference": {{"source": "Please write the source value in the context as is.", "url": "Site address where the announcement was posted"}}
    "Information": {{
        "company_name": "Fill in if the company name is included in the question", 
        "name": "Fill out if the question includes the name of the questioner.", 
        "user_region":"place of business.",
        "business_experience":"business experience",
        "business_size":"Workplace workforce size"
        }}
    
}}
```
Let your imagination run wild and create something extraordinary!

    user
Question: ```{question}```
    ..... 
    
    assistant
    """,
    input_variables=["..", "..", "..", ".."],
)
chain = prompt | model | JsonOutputParser()

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=3000)
vectordb = Chroma(persist_directory="./embedding_db/20240628_openai", embedding_function=embeddings)

mmr_retriever = MultiQueryRetriever.from_llm(
    retriever=vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 5, 'fetch_k': 50}
    ), llm=model
)

similar_retriever = MultiQueryRetriever.from_llm(
    retriever=vectordb.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={'score_threshold': 0.5, 'k':3}
    ), llm=model
)

ensemble_retriever = EnsembleRetriever(
    retrievers=[mmr_retriever, similar_retriever], weights=[0.5, 0.5]
)

## Streamlit에서 받은 템플릿 포함
## 기존창업자 부분이 좀 더 세분화가 있으면 좋을 듯 -> 공고문에 업력 10년 미만 이런식의 조건이 있기 때문
## support_field는 복수의 선택이면 좋을 것 같음 여러개를 원할 수 있기 때문에

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


## BM25 리트리버 사용시 정보를 제대로 못찾는 경향이 있음. context를 영어로 변환하는 과정에서 문제가 발생한 것 같은데, 추후 원인 파악 해야함

context1 = ensemble_retriever.invoke(question1)
BM25_retriever1 = BM25Retriever.from_documents(documents=context1, k=4)
bm_context1 = BM25_retriever1.get_relevant_documents(question1)

context2 = ensemble_retriever.invoke(question2)
BM25_retriever2 = BM25Retriever.from_documents(documents=context2, k=4)
bm_context2 = BM25_retriever2.get_relevant_documents(question2)


result1 = chain.invoke({"question": question1, "context": context1})
result2 = chain.invoke({"question": question2, "context": context2})

print(result1)
print(result2)