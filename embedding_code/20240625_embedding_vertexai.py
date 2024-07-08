from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
import vertexai
import os
from google.cloud import aiplatform
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VectorSearchVectorStore

# 설정 변수들
PROJECT_ID = "prompthon-prd-19"
REGION = "us-central1"
BUCKET = "jy_embedding"
BUCKET_URI = f"gs://{BUCKET}"
DISPLAY_NAME = "seoul_prompthon_v1"
DEPLOYED_INDEX_ID = "seoul_prompthon_v1_endpoint"

# 환경 변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"
vertexai.init(project=PROJECT_ID)
aiplatform.init(staging_bucket=BUCKET_URI)

# 임베딩 모델 초기화
embedding_model = VertexAIEmbeddings(model_name="textembedding-gecko-multilingual")

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

import pickle
from tqdm import tqdm
from langchain.docstore.document import Document

# 복잡한 메타데이터를 단순한 형식으로 필터링하는 함수
def filter_complex_metadata(metadata):
    filtered_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            filtered_metadata[key] = value
        else:
            filtered_metadata[key] = str(value)  # 복잡한 데이터 타입을 문자열로 변환
    return filtered_metadata

# `filtered_docs.pkl` 파일에서 `test_docs`를 불러오기
with open('filtered_docs.pkl', 'rb') as f:
    test_docs = pickle.load(f)

# `processed_addr.pkl` 파일에서 `processed_addr`를 불러오기
with open('processed_addr.pkl', 'rb') as f:
    processed_addr = pickle.load(f)

# 새로운 리스트 생성
updated_processed_addr = []
# print(len(processed_addr))
# .hwpx로 끝나는 파일을 이전 값으로 추가
for i in tqdm(range(len(processed_addr))):
    updated_processed_addr.append(processed_addr[i])
    updated_processed_addr.append(processed_addr[i])
    if processed_addr[i].endswith('.hwpx') and i > 0:
        updated_processed_addr.append(processed_addr[i])

# 업데이트된 파일 경로 리스트를 저장
with open('updated_processed_addr.pkl', 'wb') as f:
    pickle.dump(updated_processed_addr, f)

print(len(updated_processed_addr), len(processed_addr))

# 복잡한 메타데이터 필터링 및 새로운 변수 생성
filtered_docs = [
    Document(
        page_content=doc.page_content,
        metadata={**filter_complex_metadata(doc.metadata), 'source': updated_processed_addr[idx]}
    )
    for idx, doc in enumerate(test_docs)
]

# 업데이트된 `filtered_docs`를 저장
with open('updated_filtered_docs.pkl', 'wb') as f:
    pickle.dump(filtered_docs, f)

print("Filtered docs updated and saved successfully.")





vector_store.from_documents(documents=docs, persist_directory="./embedding_db/20240620_vertexai", embedding=embedding_model)
# vectordb = Chroma(persist_directory="./embedding_db/20240627_openai", embedding_function=embedding_model)



# texts = [doc.page_content for doc in docs]
# vector_store.add_texts(texts=texts)

# 유사도 검색 수행
results = vector_store.similarity_search("중대재해처벌법이 적용되는 사업장 기준")
print(results)