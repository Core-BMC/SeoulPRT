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
from dotenv import load_dotenv
# 환경 변수 로드
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"

# VertexAI 초기화
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
    "Reference": {{"source": "Storage location of the document you referenced.", "url": "Site address where the announcement was posted"}}
    
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

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=2000)
vectordb = Chroma(persist_directory="./embedding_db/20240617_openai", embedding_function=embeddings)

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

question = """
서울시 중구에서 1년 넘게 사업하고 있는데, 내가 참여할 수 있는 지원사업이 있을까?
"""

context = ensemble_retriever.invoke(question)
BM25_retriever = BM25Retriever.from_documents(documents=context)

print(chain.invoke({"question": question, "context": context}))