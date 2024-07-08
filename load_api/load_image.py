import requests
from bs4 import BeautifulSoup
import base64
from langchain.schema import Document
from glob import glob
from ChatLLM import load_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def load_image(url, data_path, writer="GPT4o"):
    
    image_info = encode_image(data_path)
    
    system_pormpot = """
    You are an assistant tasked with summarizing images for retrieval. \
    These summaries will be embedded and used to retrieve the raw image. \
    Give a concise summary of the image that is well optimized for retrieval. \
    If the image is a logo with no special information or there is not much information that can be extracted, write 'Null'. \
    Please summarize and write in detail, no more than 2000 characters, so as not to omit any information. \
    Please write the summary in both Korean and English.
    """

    llm = load_llm()
    
        
    prompt = llm.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": system_pormpot},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64, {image_info}"},
                    },
                ]
            )
        ]
    )

    summary = prompt.content

    document = Document(page_content=summary, metadata={"source": url, "data_path": data_path, "writer": writer})
    
    return document


# image_path = './seoul_prompthon/figures/Recruitment of companies participating in the Serious Accident Punishment Act Corporate Consulting Support Project (Seoul Business Association).png'
# image_info = encode_image(image_path)

# test = load_image(url="test", data_path=image_path)