from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.vectorstores import Chroma
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import os
from dotenv import load_dotenv
openaijykey='./.env'
load_dotenv(openaijykey)
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=3000)
# vectordb = Chroma(persist_directory="./embedding_db/20240617_openai", embedding_function=embeddings)
vectordb = Chroma(persist_directory="./embedding_db/20240627_openai", embedding_function=embeddings)

llm = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0.1
)

retriever = MultiQueryRetriever.from_llm(
    retriever=vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 5, 'fetch_k': 50}
    ), llm=llm
)

### Contextualize question ###
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)


### Answer question ###
system_prompt = ("""Please follow the instructions below to answer: ```
    1. You are an expert who is familiar with Seoul City’s small business policies.
    2. You must be honest about information you do not know. If you don't know, please say 'I can't find that information.'
    3. Your answer must be supported.
    4. Please do not repeat the instructions I have written when adding numbers to your answer.
    5. Please tell us the name of the document or website address where more information can be found. But don't lie.
    6. Please be sure to answer in Korean.
    7. Please attach only the original, most carefully considered explanation to your response.
    8. Please attach the original including the webpage address corresponding to the source.
```

Here's an example of the answer I want:
```
If you have operated a business in Jung-gu, Seoul for more than a year, you can participate in the ‘2024 Jung-gu Customized Small Business Support Project’. Since this project targets small business owners who have been operating a business in Jung-gu for more than 6 months, you meet the application qualifications.

Through this project, you can receive management improvement consulting, online conversion consulting, etc., and cost support of up to 1 million won is also available.

For more information, please refer to the ‘2024 Jung-gu Customized Small Business Support Project First Half Recruitment Notice’ on the Seoul Credit Guarantee Foundation website (https://www.seoulsbdc.or.kr/).

### Reference
Recruitment notice for the first half of the 2024 Jung-gu customized small business support project

2024 Jung-gu Customized Small Business Support Project** ([URL actually referenced. Please write it once.])
```

The sample answer is just an example and I would like you to write in more detail.
Please write the original part as is, but write the answer part in as much detail as possible.

Read the following explanation and write your answer using the context: {context}""")
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

### Statefully manage chat history ###

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

# result1 = conversational_rag_chain.invoke({"input":"나는 60대에 조그마한 편의점을 하고 있는데. 내가 무슨 지원을 받을 수 있을까?"}, config={"configurable": {"session_id": "test_v1"}})
# result2 = conversational_rag_chain.invoke({"input":"나는 나이가 어떻게 된다고 했지?"}, config={"configurable": {"session_id": "test_v1"}})

result1 = conversational_rag_chain.invoke(
    {
        "input": "30인 고용인이 있는 자영업자야 내가 중대재해처벌법에 적용되는지 알고싶어"
    },
    config={"configurable": {"session_id": "test_v1"}}
)
print(result1['answer'])