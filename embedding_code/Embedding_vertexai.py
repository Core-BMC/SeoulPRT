from langchain_google_vertexai import VertexAI, VertexAIEmbeddings, VectorSearchVectorStore
import vertexai
import os
from google.cloud import aiplatform

# 설정 변수들
PROJECT_ID = "prompthon-prd-19"
REGION = "us-central1"

# 환경 변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"
aiplatform.init(project=PROJECT_ID, location=REGION)

# 인덱스 목록 가져오기
indexes = aiplatform.MatchingEngineIndex.list()
for index in indexes:
    print(f"Index Name: {index.resource_name}")

# 엔드포인트 목록 가져오기
endpoints = aiplatform.MatchingEngineIndexEndpoint.list()
for endpoint in endpoints:
    print(f"Endpoint Name: {endpoint.resource_name}")


# 설정 변수들
PROJECT_ID = "prompthon-prd-19"
REGION = "us-central1"
BUCKET = "jy_embedding"
INDEX_ID = "jy_engine_index"
ENDPOINT_ID = "jy_engine_endpoint"

# 환경 변수 설정
vertexai.init(project=PROJECT_ID)
aiplatform.init(staging_bucket=f"gs://{BUCKET}")

# 임베딩 모델 초기화
embedding_model = VertexAIEmbeddings(model_name="textembedding-gecko@003")

# 이미 생성된 인덱스 및 엔드포인트 불러오기
my_index = aiplatform.MatchingEngineIndex(index_name="projects/219717215394/locations/us-central1/indexes/5491985813950431232")
my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name="projects/219717215394/locations/us-central1/indexEndpoints/2497655011702472704")

# 벡터 스토어 불러오기
vector_store = VectorSearchVectorStore.from_components(
    project_id=PROJECT_ID,
    region=REGION,
    gcs_bucket_name=BUCKET,
    index_id=my_index.name,
    endpoint_id=my_index_endpoint.name,
    embedding=embedding_model,
)

# 유사도 검색 수행
results = vector_store.similarity_search("pizza")
print(results)



##################
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings, VectorSearchVectorStore
import vertexai
import os
from google.cloud import aiplatform

# 설정 변수들
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings, VectorSearchVectorStore
import vertexai
import os
from google.cloud import aiplatform

# 설정 변수들
PROJECT_ID = "prompthon-prd-19"
REGION = "us-central1"
BUCKET = "jy_embedding"
INDEX_ID = "projects/219717215394/locations/us-central1/indexes/5491985813950431232"  # 인덱스 ID
ENDPOINT_ID = "projects/219717215394/locations/us-central1/indexEndpoints/2497655011702472704"  # 엔드포인트 ID

# 환경 변수 설정
vertexai.init(project=PROJECT_ID)
aiplatform.init(staging_bucket=f"gs://{BUCKET}")

# 임베딩 모델 초기화
embedding_model = VertexAIEmbeddings(model_name="textembedding-gecko@003")

# 이미 생성된 인덱스 및 엔드포인트 불러오기
my_index = aiplatform.MatchingEngineIndex(index_name=INDEX_ID)
my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(endpoint_name=ENDPOINT_ID)

# 디버깅: 인덱스 및 엔드포인트의 배포 상태 확인
print(f"Index Resource Name: {my_index.resource_name}")
print(f"Endpoint Resource Name: {my_index_endpoint.resource_name}")

# 엔드포인트에 배포된 인덱스 확인
print("Deployed Indexes on this Endpoint:")
for deployed_index in my_index_endpoint.deployed_indexes:
    print(f"Deployed Index: {deployed_index}")

# 벡터 스토어 불러오기
vector_store = VectorSearchVectorStore.from_components(
    project_id=PROJECT_ID,
    region=REGION,
    gcs_bucket_name=BUCKET,
    index_id=my_index.name,
    endpoint_id=my_index_endpoint.name,
    embedding=embedding_model,
)

# 유사도 검색 수행
results = vector_store.similarity_search("pizza")
print(results)
