import os
from dotenv import load_dotenv
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

model = ChatVertexAI(
    model="gemini-1.5-pro-001",
    temperature=0.1,
    max_tokens=8192,
    max_retries=5,
    stop=None,
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
    7. Please answer in Korean.
    
    Here is the user question: {question}
    """,
    input_variables=["question"],
)

question_router = prompt | model | StrOutputParser()

question = str({
    "user_region": "서울특별시", 
    "business_experience": "예비창업자", 
    "business_size": "10인 이하", 
    "support_field": "정책", 
    "user_question": "", 
})

# question = {
#     "user_region": "", 
#     "business_experience": "", 
#     "business_size": "", 
#     "support_field": "", 
#     "user_question": "난 서울시에서 10명 이하의 직원을 고용하고 있는 1년차 자영업자야. 내가 신청할만한 정책이 있을까?",   
# }

# 질문을 잘 다듬는 것이 가능한지
advanced_question = question_router.invoke({"question": question})
print(advanced_question)
###

### RAG Agent
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
    "Question": "Write the original question naturally in sentence form.",
    "Answer": "Parts of the answer that do not constitute references."
    "Reference": {{
        "source": "
        1. Please write the source value in the context as is. 
        2. If there is no relevant information, please write 'None'. 
        3. Be sure to write down the source in its entirety without omitting it.
        4. There is a very high probability that there is a source in the context. For example, 'source': 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000096322\\Notice on participation in the 2024 Wonju Lacquerware Expo (exhibition) and implementation of support project for hosting it.hwp' is written like this.
        ", 
        "url": "Site address where the announcement was posted. If there is no relevant information, please write 'None'."}}
    "Information": {{
        "company_name": "Fill in if the company name is included in the question", 
        "name": "Fill out if the question includes the name of the questioner.", 
        "user_region":"place of business.",
        "business_experience":"business experience",
        "business_size":"Workplace workforce size"
        }}
    
}}
```

    user
Question: ```{question}```
    """,
    input_variables=["question", "context"],
)

rag_chain = prompt | model | JsonOutputParser()

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

# context = ensemble_retriever.invoke(advanced_question)
# BM25_retriever1 = BM25Retriever.from_documents(documents=context, k=3)
# bm_context1 = BM25_retriever1.get_relevant_documents(advanced_question)

# rag_response = rag_chain.invoke({"question":advanced_question, "context":context})
# print(rag_response)
###

### 답변을 context를 참조했는지 여부를 체크하는 Agent
prompt = PromptTemplate(
    template="""<|start_header_id|>system<|end_header_id|> You are a grader assessing whether 
    an answer is grounded in / supported by a set of facts. Give a binary 'yes' or 'no' score to indicate 
    whether the answer is grounded in / supported by a set of facts. Provide the binary score as a JSON with a 
    single key 'score' and no preamble or explanation. <|eot_id|><|start_header_id|>user<|end_header_id|>
    Here are the facts:
    \n ------- \n
    {documents} 
    \n ------- \n
    Here is the answer: {generation} <|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["generation", "documents"],
)

generation = []
hallucination_grader = prompt | model | JsonOutputParser()
# hallucination_grader_response = hallucination_grader.invoke({"documents": context, "generation": rag_response['Answer']})
# print(hallucination_grader_response)
###

### QC하는 Agent
prompt = PromptTemplate(
    template=""" You are a grader assessing whether an answer is useful to resolve a question. 
    Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question. 
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
    Here is the answer:
    \n ------- \n
    {generation} 
    \n ------- \n
    Here is the question: {question} """,
    input_variables=["generation", "question"],
)

answer_grader = prompt | model | JsonOutputParser()
# answer_grader_response = answer_grader.invoke({"question": advanced_question,"generation": rag_response['Answer']})
# print(answer_grader_response)
###

### 할루시 혹은 QC체크를 통과하지 못하면 돌아가서 다시 작성해야하기 때문에 rewriter
### 좀더 구체적이고 생산적인 답변을 만들어 달라고 해볼 것
### rewriter Agent
prompt = PromptTemplate(
    template="""{context}, {question}
    """,
    input_variables=[],
)
re_rag_chain = prompt | model | JsonOutputParser()
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
    question = state["advanced_question"]

    # Retrieval
    documents = ensemble_retriever.invoke(question)
    return {"documents": documents, "advanced_question": question}

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
    print(question)
    documents = state["documents"]
    
    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

def hallucination(state):
    """
    RAG is the process of ensuring that the article you write is written with reference to real-world context.
    If the RAG was not referenced, {'score': 'no'} is returned.
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    rag_response = state["generation"]
    context = state["documents"]
    
    hallucination_grader_response = hallucination_grader.invoke({"documents": context, "generation": rag_response})
    
    try: 
        if hallucination_grader_response['score'] == 'yes':
            return {'score': 'yes'}
        else :
            return {'score': 'no'}
    except:
        print("no")
        return {'score': 'no'}

def quality_checker(state):
    """
    Check that your answer adequately helped solve the question.
    """ 
    
    print("---CHECK ANSWER QUALITY---")
    answer_grader_response = answer_grader.invoke({"question": state["advanced_question"], "generation": state["generation"]})
    try: 
        if answer_grader_response['score'] == 'yes':
            return {'score': 'yes'}
        else :
            return {'score': 'no'}
    except:
        print("no")
        return {'score': 'no'}

def re_generate(state):
    
    print("---RE-GENERATE ANSWER---")
    question = state["advanced_question"]
    documents = state["documents"]
    
    response = re_rag_chain.invoke({"question": question, "context": documents})
    
    return {"generation": response}
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

app = workflow.compile()
###

###
from pprint import pprint

inputs = {"question":str({
    "user_region": "서울특별시", 
    "business_experience": "예비창업자", 
    "business_size": "10인 이하", 
    "support_field": "정책", 
    "user_question": "",})
}

def post_process_output(output):
    if output is None:
        print("Received None output")
        return

    for key, value in output.items():
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
                else:
                    print("Generation is not a string:", generation_text)
            else:
                print("No generation found in the output")
                print("Value:", value)
        else:
            print(f"Output for {key}:", value)

# 출력 처리
for output in app.stream(inputs):
    post_process_output(output)