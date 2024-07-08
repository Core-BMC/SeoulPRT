import fitz
from glob import glob
import os
import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyMuPDFLoader, CSVLoader, PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from load_api.load_html import load_html
from load_api.load_image import load_image
import tabula
import os
from dotenv import load_dotenv
openaijykey='./.env'
load_dotenv(openaijykey)
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key

def pdf_to_image(pdf_path, figure_dir):
    pdf_document = fitz.open(pdf_path)
    pdf_filename = os.path.basename(pdf_path).split('.')[0]

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # 이미지 저장 경로
            image_filename = f"{pdf_filename}_page{page_number + 1}_img{img_index + 1}.{image_ext}"
            image_path = os.path.join(figure_dir, image_filename)

            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

    #print(f"{pdf_path}: 이미지 추출 완료")
    
def extract_image(url, data_path):
    document = load_image(url, data_path, writer="GPT4o")
    return document

def extract_html(url, data_path):
    document = load_html(url, data_path, writer="GPT4o")
    return document
        
def extract_text(pdf_path, text_dir, save=True):
    pdf_filename = os.path.basename(pdf_path).split('.')[0]
    try:
        loader = PyMuPDFLoader(pdf_path)
        loaded_docs = loader.load()
    except:
        loader = PDFPlumberLoader(pdf_path)
        loaded_docs = loader.load()
    
    # if save:
    #     text_filename = f"{pdf_filename}.txt"
    #     text_path = os.path.join(text_dir, text_filename)
    #     with open(text_path, "w", encoding="utf-8") as text_file:
    #         text_file.write(loaded_docs.page_content)
    
    return loaded_docs

    #print(f"{pdf_path}: 텍스트 추출 완료")
    
def extract_table(pdf_path, table_dir):
    tables = tabula.read_pdf(pdf_path, pages="all", stream=True)
    pdf_filename = os.path.basename(pdf_path).split('.')[0]
    csv_list = []
    for idx, table in enumerate(tables):
        csv_name = f"{table_dir}{pdf_filename}_{idx}.csv"
        csv_list.append(csv_name)
        table.to_csv(csv_name, index=False)
    tables=[]
    for csv in csv_list:
        loader = CSVLoader(file_path=csv)
        tables.append(loader.load())
        
    return tables



# # example usage

# pdfs = glob('./seoul_prompthon/pdfs/*.pdf')
# loader = PyMuPDFLoader(pdfs[0])
# loader = PDFPlumberLoader(pdfs[0])
# loaded_docs = loader.load()

# loaded_docs
# figure_dir = './seoul_prompthon/figures/'
# text_dir = './seoul_prompthon/text/'
# table_dir = './seoul_prompthon/tables/'
# html_list_path = glob('./seoul_prompthon/htmls/*.xlsx')

# # extract text&table
# docs=[]
# for pdf_path in pdfs:
#     #extract_image(pdf_path, figure_dir)
#     docs.extend(extract_text(pdf_path, text_dir, save=False))
#     docs.extend(extract_table(pdf_path, table_dir))
    
# chunk_size = 2000
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_size//10)
# splits = text_splitter.split_documents(loaded_docs)

# len(splits)
# len(loaded_docs)

# # create vectorDB
# # embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=chunk_size)
# # vectordb = Chroma.from_documents(documents=splits, persist_directory="./seoul_prompthon/embedding_db/openai_no_image", embedding=embeddings)



# # extract html
# html_list = pd.read_excel(html_list_path[0])
# htmls = extract_html(html_list)

# htmls[0]

# # load vectorDB
# embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=chunk_size)
# vectordb = Chroma(persist_directory="./seoul_prompthon/embedding_db/openai_no_image", embedding_function=embeddings)

# # add htmls
# # vectordb.add_documents(htmls)

# # test
# db_retriever = vectordb.as_retriever(
#     search_type="mmr",
#     search_kwargs={'k': 5, 'fetch_k': 50}
# )
# db_retriever.get_relevant_documents('2024년 청년을 위한 복지가 무엇이 있을까?')

# db_retriever.get_relevant_documents('비영리 조직 대상 채용 관련 정책')
# db_retriever.get_relevant_documents('프렌차이즈 창업을 하려는 예비창업자가 봐야 할 정책이나 행사')

# e5 embedding, vertex gekko 임베딩 모델로 별로 어떤게 다른지
