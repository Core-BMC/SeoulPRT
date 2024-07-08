from langchain_google_vertexai import VertexAI
import vertexai
import os
import shutil
import zipfile
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"

def extract_raw_data(hwpx_file_path):
    # Change directory to the file's location
    os.chdir(os.path.dirname(hwpx_file_path))
    path = os.path.join(os.getcwd(), "hwpx")

    # Extract the hwpx file
    with zipfile.ZipFile(hwpx_file_path, 'r') as zf:
        zf.extractall(path=path)
    
    # Read the original XML content to raw_data
    section0_xml_path = os.path.join(path, "Contents", "section0.xml")
    with open(section0_xml_path, 'r', encoding='utf-8') as file:
        raw_data = file.read()
    
    # Clean up extracted files to restore the original state
    shutil.rmtree(path)
    
    return raw_data

# vertexai.init(project="prompthon-prd-19")

model = VertexAI(
    model_name="gemini-1.5-pro-001",
    temperature=0.1,
)

# print(model.invoke("넌 누구고 뭘 할 수 있니"))

# claude-3-5-sonnet@20240620, gemini-1.5-pro-001

prompt = PromptTemplate(
    template="""system
hwpx xml: ```{context}```

Please follow the instructions below to answer: ```
1. You are an expert in xml structure analysis.
2. You are an expert who knows the hwpx structure well.
3. Remember the information provided by the other party and edit the xml by filling in the information in the appropriate field.
4. After creating the answer as above, share it in detail with Json.
5. Your answer must be in json format.
```

Example ```JSON format```:
```
{{
    "Answer": "Answer without xml code"
    "XML": "Modified xml code"
}}
```

user
Question: ```{question}```
""",
    input_variables=["..", "..", "..", ".."],
)

raw_data = extract_raw_data(r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\mss.go\\1040699\\2023년_중소기업_수출_유공_포상_후보자_모집_공고.hwpx')
question = """나는 36살이고 진영기업을 서울에서 운영하고 있어. 사업자등록번호는 111222333이야."""

chain = prompt | model | JsonOutputParser()

print("프로세싱..")

test = chain.invoke({"question": question, "context": raw_data})

print(test)