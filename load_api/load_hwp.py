import os
import olefile
import xml.etree.ElementTree as ET
import zlib
import struct
import re
import unicodedata
from ChatLLM import *
from langchain_core.prompts import PromptTemplate
from langchain.schema import Document
import json
from anthropic import AnthropicVertex
from Docs_Parsing_JY import extract_image
import shutil
import zipfile
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import duckdb
from tqdm import tqdm
# from langchain_community.vectorstores.utils import filter_complex_metadata

conn = duckdb.connect("./rdbms/prompthon.db")
cursor = conn.cursor()

class HWPExtractor(object):
    FILE_HEADER_SECTION = "FileHeader"
    HWP_SUMMARY_SECTION = "\x05HwpSummaryInformation"
    SECTION_NAME_LENGTH = len("Section")
    BODYTEXT_SECTION = "BodyText"
    HWP_TEXT_TAGS = [67]

    def __init__(self, filename):
        self._ole = self.load(filename)
        self._dirs = self._ole.listdir()

        self._valid = self.is_valid(self._dirs)
        if (self._valid == False):
            raise Exception("Not Valid HwpFile")
        
        self._compressed = self.is_compressed(self._ole)
        self.text = self._get_text()
	
    def load(self, filename):
        return olefile.OleFileIO(filename)
	
    def is_valid(self, dirs):
        if [self.FILE_HEADER_SECTION] not in dirs:
            return False

        return [self.HWP_SUMMARY_SECTION] in dirs

    def is_compressed(self, ole):
        header = self._ole.openstream("FileHeader")
        header_data = header.read()
        return (header_data[36] & 1) == 1

    def get_body_sections(self, dirs):
        m = []
        for d in dirs:
            if d[0] == self.BODYTEXT_SECTION:
                m.append(int(d[1][self.SECTION_NAME_LENGTH:]))

        return ["BodyText/Section"+str(x) for x in sorted(m)]
	
    def get_text(self):
        return self.text

    def _get_text(self):
        sections = self.get_body_sections(self._dirs)
        text = ""
        for section in sections:
            text += self.get_text_from_section(section)
            text += "\n"

        self.text = text
        return self.text

    def get_text_from_section(self, section):
        bodytext = self._ole.openstream(section)
        data = bodytext.read()

        unpacked_data = zlib.decompress(data, -15) if self._compressed else data
        size = len(unpacked_data)

        i = 0

        text = ""
        while i < size:
            header = struct.unpack_from("<I", unpacked_data, i)[0]
            rec_type = header & 0x3ff
            level = (header >> 10) & 0x3ff
            rec_len = (header >> 20) & 0xfff

            if rec_type in self.HWP_TEXT_TAGS:
                rec_data = unpacked_data[i+4:i+4+rec_len]
                
                decode_text = rec_data.decode('utf-16')
                res = self.remove_control_characters(self.remove_chinese_characters(decode_text))
                
                text += res
                text += "\n"

            i += 4 + rec_len

        return text

    @staticmethod
    def remove_chinese_characters(s: str):   
        return re.sub(r'[\u4e00-\u9fff]+', '', s)
        
    @staticmethod
    def remove_control_characters(s):    
        return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def list_files_in_directory(directory):
    """
    디렉토리의 모든 파일 목록을 반환
    """
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    return file_list

def extract_hwpx_content(hwpx_file_path):
    zip_file_path = hwpx_file_path.replace('.hwpx', '.zip')
    os.rename(hwpx_file_path, zip_file_path)
    extracted_folder_path = zip_file_path.replace('.zip', '')
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_folder_path)
    
    section0_xml_path = os.path.join(extracted_folder_path, 'Contents', 'section0.xml')
    png_path = os.path.join(extracted_folder_path, 'Preview', "PrvImage.png")
    png_doc = extract_image(url = hwpx_file_path, data_path = png_path)
    tree = ET.parse(section0_xml_path)
    root = tree.getroot()
    
    paragraphs = []
    for child in root.iter():
        if child.tag.endswith('p'):
            texts = [node.text for node in child.iter() if node.tag.endswith('t') and node.text]
            paragraph = ''.join(texts)
            if paragraph:
                paragraphs.append(paragraph)
    
    os.rename(zip_file_path, hwpx_file_path)
    shutil.rmtree(extracted_folder_path)
    
    return '\n'.join(paragraphs), png_doc

directory_path = 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads'

all_files = list_files_in_directory(directory_path)

hwpx_files = [file for file in all_files if file.lower().endswith('.hwpx') or file.lower().endswith('.hwp')]
# hwpx_files = [file for file in all_files if file.lower().endswith('.hwpx')]

gpt_json = load_llm_json()
json_template = """
Read the following explanation and write your answer using the context: ```{context}```

1. You are an expert in dividing documents into each item and distributing them in Json format.
2. I plan to convert the Json data you provided into meta data and input it into vector db.
3. Write it so that it is easy to search in vector db.
4. Please select the most important items and limit them to 20 or fewer.

Output Format (JSON)
{{
    Convert all the information you feel you need into JSON.
}}
"""
json_prompt = PromptTemplate.from_template(json_template)
json_chain = json_prompt | gpt_json

summary_gemini = load_llm_vertex()
summary_template = """
Read the following explanation and write your answer using the context: ```{context}```
1. You are an expert at summarizing content.
2. For summary information, it is best to set the search type to mmr in ChromaDB to ensure the best search.
3. Answers must be written in Korean.
4. Write simply.
5. Please write for whom this information would be good.
"""
summary_prompt = PromptTemplate.from_template(summary_template)
summary_chain = summary_prompt | summary_gemini

docs = []
processed_addr = []
for file_path in tqdm(hwpx_files):
    try:
        if file_path.lower().endswith('.hwp'):
            hwp_extractor = HWPExtractor(file_path)
            file_content = hwp_extractor.get_text()
            # print(f"Content of {file_path}:\n{file_content}\n")
        elif file_path.lower().endswith('.hwpx'):
            file_content, summary_png = extract_hwpx_content(file_path)
            # print(f"Content of {file_path}:\n{file_content}\n")
            docs.append(summary_png)
            processed_addr.append(file_path)
        json_data = json_chain.invoke({'context':file_content})
        json_convert = json.loads(json_data.content)
        document = Document(page_content=file_content, metadata=json_convert)
        summary = summary_chain.invoke({'context':file_content})
        summary_document = Document(page_content=summary, metadata=json_convert)
        docs.append(document)
        docs.append(summary_document)
        processed_addr.append(file_path)
        # print(f"{len(docs)}/{len(hwpx_files)}")
        if len(processed_addr) >= len(hwpx_files)//2:
            break
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        
def filter_complex_metadata(metadata):
    filtered_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            filtered_metadata[key] = value
        else:
            filtered_metadata[key] = str(value)
    return filtered_metadata

filtered_docs = [
    Document(
        page_content=doc.page_content,
        metadata=filter_complex_metadata(doc.metadata)
    )
    for doc in docs
]

chunk_size = 3000
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=chunk_size)
# vectordb = Chroma.from_documents(documents=filtered_docs[0:5], persist_directory="./embedding_db/20240627_openai", embedding=embeddings)
vectordb = Chroma(persist_directory="./embedding_db/20240627_openai", embedding_function=embeddings)
vectordb.add_documents(filtered_docs)

# 나머지 문서를 5개씩 추가하면서 로그 출력
batch_size = 5
total_docs = len(filtered_docs)
for i in range(5, total_docs, batch_size):
    batch_docs = filtered_docs[i:i + batch_size]
    vectordb.add_documents(batch_docs)
    print(f"Added {len(batch_docs)} documents. Total added so far: {i + len(batch_docs)}")

# 마지막에 남은 문서 추가
remaining_docs = filtered_docs[(total_docs // batch_size) * batch_size:]
if remaining_docs:
    vectordb.add_documents(remaining_docs)
    print(f"Added remaining {len(remaining_docs)} documents. Total added: {total_docs}")

print("All documents added successfully.")


db_retriever = vectordb.as_retriever(
    search_type="mmr",
    search_kwargs={'k': 5, 'fetch_k': 50}
)

db_retriever.get_relevant_documents("중소기업 수출 유공 포상")


######################### 저장하기
import pickle
with open('filtered_docs.pkl', 'wb') as f:
    pickle.dump(filtered_docs, f)

with open('processed_addr.pkl', 'wb') as f:
    pickle.dump(processed_addr, f)

# filtered_docs를 파일에서 불러오기
with open('filtered_docs.pkl', 'rb') as f:
    test_docs = pickle.load(f)

######################### 저장하기
with open('updated_filtered_docs.pkl', 'rb') as f:
     load_docs = pickle.load(f)
    
# Chroma 벡터 데이터베이스 초기화 (처음 10개의 문서 추가)
new_vectordb = Chroma.from_documents(documents=load_docs[:10], persist_directory="./embedding_db/20240628_openai", embedding=embeddings)

# 10개씩 나누어 문서 추가
batch_size = 10
total_docs = len(load_docs)

for i in tqdm(range(10, total_docs, batch_size)):
    batch_docs = load_docs[i:i + batch_size]
    new_vectordb.add_documents(batch_docs)
    print(f"Added {len(batch_docs)} documents. Total added so far: {i + len(batch_docs)}")

# 남은 문서가 있으면 추가
remaining_docs = load_docs[(total_docs // batch_size) * batch_size:]
if remaining_docs:
    new_vectordb.add_documents(remaining_docs)
    print(f"Added remaining {len(remaining_docs)} documents. Total added: {total_docs}")

print("All documents added successfully.")