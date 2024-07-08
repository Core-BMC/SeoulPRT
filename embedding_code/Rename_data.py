from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from Docs_Parsing_JY import extract_image, extract_text
from glob import glob
import os
from dotenv import load_dotenv
openaijykey='./.env'
load_dotenv(openaijykey)
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key

pdfs = glob('./seoul_prompthon/data/*.pdf')
titles = [os.path.splitext(os.path.basename(pdf))[0] for pdf in pdfs]

# llm = ChatOpenAI(
#     model_name="gpt-3.5-turbo-0125",
#     temperature=0.5
# )

# template = ChatPromptTemplate.from_messages(
#     [
#         SystemMessage(
#             content=(
#     """
#     1. Remove special characters
#     2. Change the spacing to _.
#     3. If possible, please use only Korean, English, _, and numbers.
#     4. Leave the parentheses as is.
#     """
#             )
#         ),
#         HumanMessagePromptTemplate.from_template("{text}"),
#     ]
# )
# #5. Please change Korean to English.
# remake_titles = [(llm.invoke(template.format_messages(text=title))).content for title in titles]

import re
def clean_title(title):
    title = re.sub(r'[^\w\s()]+', '', title)
    title = title.replace(' ', '_')
    return title

manual_titles = [clean_title(i) for i in titles]

for pdf in pdfs:
    dir_path = os.path.dirname(pdf)
    base_name = os.path.splitext(os.path.basename(pdf))[0]
    new_name = clean_title(base_name) + ".pdf"
    new_path = os.path.join(dir_path, new_name)
    
    os.rename(pdf, new_path)
    print(f"Renamed: {pdf} -> {new_path}")