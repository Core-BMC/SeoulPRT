from multiprocessing import process
from Docs_Parsing_JY import extract_html, extract_image, extract_table, extract_text
import pandas as pd
import duckdb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os
from dotenv import load_dotenv
openaijykey='./.env'
load_dotenv(openaijykey)
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key

conn = duckdb.connect("./rdbms/prompthon.db")
cursor = conn.cursor()

### 실험 세팅    
df_list = pd.read_excel('./seoul_promp_test.xlsx')

df_list['process'] = False
df_list['process_date'] = pd.Timestamp.now()
df_list['update_count'] = 0 

df_list = df_list[['source', 'data_path', 'process', 'process_date', 'update_count']]

conn.register('df_list', df_list)
# cursor.execute("INSERT INTO parsing_list (source, data_path, process, process_date, update_count) SELECT source, data_path, process, process_date, update_count FROM df_list")

print(cursor.query("SELECT * FROM parsing_list"))
test = cursor.query("SELECT * FROM parsing_list")

### 시작
chunk_size = 2000
test_df = test.to_df()
docs = []
for i in test_df.iloc:
    processing = False
    if i['process']:
        continue
    file_format = i['data_path'].split(".")[-1].replace("'","")
    print(file_format)
    if file_format == "html":
        doc = extract_html(i['source'], i['data_path'])
        docs.append(doc)
        processing = True
    if file_format == "pdf":
        doc = extract_text(pdf_path=f"./seoul_prompthon/pdfs/{i['data_path'].replace("'","")}", text_dir='./seoul_prompthon/text/')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_size//10)
        splits = text_splitter.split_documents(doc)
        docs.extend(splits)
        processing = True
    if file_format == "png":
        doc = extract_image(url=i['source'], data_path=f"./seoul_prompthon/figures/{i['data_path'].replace("'","")}")
        docs.append(doc)
        processing = True
    if processing:
        cursor.execute(f"""
            UPDATE parsing_list
            SET 
                process = 1,
                process_date = CURRENT_TIMESTAMP,
                update_count = update_count + 1
            WHERE id = {i['id']}
        """)

# create vectorDB
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=chunk_size)
vectordb = Chroma.from_documents(documents=docs, persist_directory="./seoul_prompthon/embedding_db/20240617_openai", embedding=embeddings)

# add document
# vectordb = Chroma(persist_directory="./seoul_prompthon/embedding_db/20240617_openai", embedding_function=embeddings)
# vectordb.add_documents(docs)

# search data
db_retriever = vectordb.as_retriever(
    search_type="mmr",
    search_kwargs={'k': 5, 'fetch_k': 50}
)

db_retriever.get_relevant_documents("중대재해처벌법이 적용되는 사업장 기준")

## 지원대상이라던가 메타데이터가 저장되는 테이블 하나 더 생성해서 insert 자동으로 되도록 jsonmode로
## DB column구성이 힘들 수 있기 때문에... 어떤 방법이 더 좋을지 생각해보기

## 이런 어려움이 있다.. 정말 많이 봤던걸 알려주면 좋겠다
## RSS 피드가 동작하지 않는다... 
## PDF 안읽어진다... hwp를 잘 읽게 어떻게 했다