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



