from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.vectorstores import Chroma
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_google_vertexai import VertexAI
import vertexai
import os
from dotenv import load_dotenv
openaijykey='./.env'
load_dotenv(openaijykey)
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"
vertexai.init(project="prompthon-prd-19")

def load_llm():
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.1
    )
    return llm

def load_llm_vertex():
    models = ["gemini-1.5-pro-001", "gemini-1.5-flash-001"]
    model = VertexAI(model_name="gemini-1.5-pro-001", temperature=0.1)
    return model
    
def load_llm_json():
    llm_json = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0.0,
    model_kwargs={"response_format": {"type": "json_object"}}
    )
    return llm_json

# model = VertexAI(
#     model_name="gemini-1.5-pro-001", 
#     temperature=0.1,
#     responseMimeType="application/json"
#     )

# prompt = """
#   List 5 popular cookie recipes.

#   Using this JSON schema:

#     Recipe = {"recipe_name": str}

#   Return a `list[Recipe]`
#   """
  
# test = model.invoke(prompt)

# import json

# test.replace("```json","").replace("```","").replace("\n","")
# json.loads(test.replace("```json","").replace("```","").replace("\n",""))