import requests
from bs4 import BeautifulSoup
from langchain.schema import Document
from glob import glob
from ChatLLM import load_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
import pandas as pd

def fetch_webpage_content(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.text

def parse_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = ' '.join([p.get_text() for p in soup.find_all('p')])
    return text

def create_langchain_document(content, url, data_path, summary=None):
    if summary is not None:
        document = Document(page_content=content, metadata={"source": url, "data_path": data_path, "summary": summary, "writer": "GPT4o"})
    else :
        document = Document(page_content=content, metadata={"source": url, "data_path": data_path, "writer": "GPT4o"})
    return document

def load_html(url, data_path, writer="GPT4o"):
    html_content = fetch_webpage_content(url)
    parsed_content = parse_html_content(html_content)
    document = create_langchain_document(parsed_content, url, data_path)
    llm = load_llm()
    # print("load llm for summarize html")

    system_pormpot = """
    1. You are an expert at summarizing content.
    2. For summary information, it is best to set the search type to mmr in ChromaDB to ensure the best search.
    3. Answers must be written in Korean.
    4. Write simply.
    5. Please write for whom this information would be good.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_pormpot),
            ("human", "{context}")
        ]
    )

    chain = create_stuff_documents_chain(llm, prompt)
    
    summary = chain.invoke({"context":[document]})
    
    document = create_langchain_document(parsed_content, url, data_path, summary)
    
    # print("create html summary document")
    
    return document