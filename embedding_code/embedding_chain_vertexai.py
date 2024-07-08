from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
import vertexai
import os
from google.cloud import aiplatform
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VectorSearchVectorStore
import duckdb
from Docs_Parsing_JY import extract_html, extract_image, extract_text
from glob import glob

# 설정 변수들
PROJECT_ID = "prompthon-prd-19"
REGION = "us-central1"
BUCKET = "jy_embedding"  # 이미 존재하는 버킷 이름
BUCKET_URI = f"gs://{BUCKET}"
DISPLAY_NAME = "seoul_prompthon_v1"
DEPLOYED_INDEX_ID = "seoul_prompthon_v1_endpoint"

# 환경 변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"
vertexai.init(project=PROJECT_ID)
aiplatform.init(staging_bucket=BUCKET_URI)

# 임베딩 모델 초기화
embedding_model = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual")

# DuckDB 연결 및 데이터 로드
dbs = glob('./rdbms/*.db')
duckdb.sql("LOAD sqlite")
conn = duckdb.connect(dbs[1])
cursor = conn.cursor()
conn.query(f"SELECT name FROM sqlite_master WHERE type='table'")
mss_data = conn.query("select * from page_info;")
mss_data = mss_data.to_df()
mss_data.keys()

# 문서 추출 및 텍스트 분할
chunk_size = 2000
docs = []
for i in test_df.iloc:
    file_format = i['data_path'].split(".")[-1].replace("'","")
    if file_format == "html":
        doc = extract_html(i['source'], i['data_path'])
        docs.append(doc)
    if file_format == "pdf":
        doc = extract_text(pdf_path=f"./seoul_prompthon/pdfs/{i['data_path'].replace("'","")}", text_dir='./text/')
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_size//10)
        splits = text_splitter.split_documents(doc)
        docs.extend(splits)
    if file_format == "png":
        doc = extract_image(url=i['source'], data_path=f"./figures/{i['data_path'].replace("'","")}")
        docs.append(doc)

# 인덱스 생성
my_index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name=DISPLAY_NAME,
    dimensions=768,
    approximate_neighbors_count=150,
    distance_measure_type="DOT_PRODUCT_DISTANCE",
    index_update_method="STREAM_UPDATE",
)

# 엔드포인트 생성
my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name=f"{DISPLAY_NAME}-endpoint", public_endpoint_enabled=True
)

# 인덱스 엔드포인트에 배포
my_index_endpoint = my_index_endpoint.deploy_index(
    index=my_index, deployed_index_id=DEPLOYED_INDEX_ID
)

# 벡터 스토어 생성 및 텍스트 추가
vector_store = VectorSearchVectorStore.from_components(
    project_id=PROJECT_ID,
    region=REGION,
    gcs_bucket_name=BUCKET,
    index_id=my_index.name,
    endpoint_id=my_index_endpoint.name,
    embedding=embedding_model,
    stream_update=True,
)

vector_store.from_documents(documents=docs, persist_directory="./embedding_db/20240620_vertexai", embedding=embedding_model)



# texts = [doc.page_content for doc in docs]
# vector_store.add_texts(texts=texts)

# 유사도 검색 수행
results = vector_store.similarity_search("중대재해처벌법이 적용되는 사업장 기준")
print(results)