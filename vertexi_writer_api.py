from langchain_google_vertexai import VertexAI, ChatVertexAI
import vertexai
import os
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from datetime import datetime
import json
import win32com.client
import pyperclip
import subprocess
from dotenv import load_dotenv
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"

def extract_text_from_hwp(file_path):
    hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.Open(file_path)

    hwp.InitScan()
    action = hwp.CreateAction("SelectAll")
    action.Run()

    hwp.Run("Copy")
    
    text = pyperclip.paste()

    hwp.Quit()
    return text

vertexai.init(project="prompthon-prd-19")

# model = VertexAI(
#     model_name="gemini-1.5-pro-001",
#     max_output_token=8192,
#     temperature=0.1,
# )

model = ChatVertexAI(
    model="gemini-1.5-pro-001",
    temperature=0.1,
    max_tokens=8192,
    max_retries=6,
    stop=None,
)

prompt = PromptTemplate(
    template="""system
Read the following explanation and write your answer using the context: ```{context}```

Please follow the instructions below to answer: ```
    1. You are an expert who is familiar with Seoul City’s small business policies.
    2. You must be honest about information you do not know. If you don't know, please say 'I can't find that information.'
    3. Your answer must be supported.
    4. Please do not repeat the instructions I have written when adding numbers to your answer.
    5. Please tell us the name of the document or website address where more information can be found. But don't lie.
    6. Please be sure to answer in Korean.
    7. Please attach only the original, most carefully considered explanation to your response.
    8. Please attach the original including the webpage address corresponding to the source.
    9. Please tell us the location of the document you referenced in the references section.
    10. There is no need to refer to context that appears unrelated to the question.
```
    
Here's an example of the answer I want:
```
If you have operated a business in Jung-gu, Seoul for more than a year, you can participate in the ‘2024 Jung-gu Customized Small Business Support Project’. Since this project targets small business owners who have been operating a business in Jung-gu for more than 6 months, you meet the application qualifications.

Through this project, you can receive management improvement consulting, online conversion consulting, etc., and cost support of up to 1 million won is also available.

For more information, please refer to the ‘2024 Jung-gu Customized Small Business Support Project First Half Recruitment Notice’ on the Seoul Credit Guarantee Foundation website (https://www.seoulsbdc.or.kr/).

### Reference
2024 Jung-gu Customized Small Business Support Project** ([URL actually referenced. Please write it once.])
```

The sample answer is just an example and I would like you to write in more detail.
Please write the original part as is, but write the answer part in as much detail as possible.
After creating the answer as above, share it in detail with Json.

Example ```JSON format```:
```
{{
    "Question": "Write the original question naturally in sentence form.",
    "Answer": "Parts of the answer that do not constitute references."
    "Reference": {{
        "source": "
        1. Please write the source value in the context as is. 
        2. If there is no relevant information, please write 'None'. 
        3. Be sure to write down the source in its entirety without omitting it.
        4. There is a very high probability that there is a source in the context. For example, 'source': 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000096322\\Notice on participation in the 2024 Wonju Lacquerware Expo (exhibition) and implementation of support project for hosting it.hwp' is written like this.
        ", 
        "url": "Site address where the announcement was posted. If there is no relevant information, please write 'None'."}}
    "Information": {{
        "company_name": "Fill in if the company name is included in the question", 
        "name": "Fill out if the question includes the name of the questioner.", 
        "user_region":"place of business.",
        "business_experience":"business experience",
        "business_size":"Workplace workforce size"
        }}
    
}}
```

    user
Question: ```{question}```
    ..... 
    """,
    input_variables=["..", "..", "..", ".."],
)
chain = prompt | model | JsonOutputParser()

embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large", chunk_size=3000)
vectordb = Chroma(persist_directory="./embedding_db/20240628_openai", embedding_function=embeddings)

mmr_retriever = MultiQueryRetriever.from_llm(
    retriever=vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 5, 'fetch_k': 50}
    ), llm=model
)

similar_retriever = MultiQueryRetriever.from_llm(
    retriever=vectordb.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={'score_threshold': 0.5, 'k':3}
    ), llm=model
)

ensemble_retriever = EnsembleRetriever(
    retrievers=[mmr_retriever, similar_retriever], weights=[0.5, 0.5]
)

def retriever(context):
    result = ensemble_retriever.invoke(context)
    # BM25_retriever1 = BM25Retriever.from_documents(documents=result, k=3)
    # bm_context1 = BM25_retriever1.get_relevant_documents(context)
    # return bm_context1
    return result
    
def json_question(streamlit_template, hwp=False):
    # streamlit_template example
    # streamlit_template1 = json.loads(json.dumps({"user_region":"서울", "business_experience":"10년", "business_size":"50인 이하", "support_field":["정책"], "user_question":"소상공인도 고용보험료 지원이 가능하다고 들었는데 어디에서 신청할 수 있나요?"}))
    # streamlit_template2 = json.loads(json.dumps({"user_region":"서울", "business_experience":"1년", "business_size":"10인 이하", "support_field":["컨설팅", "사업화", "교육"], "user_question":"창업한지 1년 되었는데 무언가 지원받을 수 있는게 있는지 궁금해"}))
    # streamlit_template = json.loads(streamlit_template)
    # print(streamlit_template)
    # print(type(streamlit_template['user_region']))
    
    question = f"""
    사업하는 장소: {streamlit_template['user_region']} \n
    사업경력: {streamlit_template['business_experience']} \n
    사업장 인력 규모: {streamlit_template['business_size']} \n
    찾고있는 정보: {streamlit_template['support_field']} \n
    추가 질문 : {streamlit_template['user_question']} \n
    """
    
    # print(question)
    context = retriever(question)
    # print(context)

    # print("retriver good")
    
    result = chain.invoke({"question": question, "context": context})
    
    # print("chain good")
    
    if hwp == False:
        # print(result)
        return result, context
    
    prom_information = result
    file_path = prom_information['Reference']['source']
    hwp_content = extract_text_from_hwp(file_path)
    
    write_hwp_prompt = f"""system
    Read the following explanation and write your answer using the context: ```{prom_information['Information']}```

    Please follow the instructions below to answer: ```
    1. You are an expert who goes to the provided file location, reads the hwp and hwpx documents, finds the parts that need to be written, and writes them down.
    2. Just look at the information provided in the context and write additional information in the correct location in the document.
    3. Write the hwp writing code by referring to the code in ‘write hwp code example’.
    4. Don’t say anything else, just write the code.
    5. company_name can be a '기업명' or '기 업 명' or '회사명' or '업체명'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
    6. name can be a '이름' or '이 름' or '성함' or '성 함' or '대표자'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
    7. business_experience can be a '업력' or '업 력' or '설립일' or '설립일자'. If 'business_experience' is '설립일' or '설 립 일' or '설립일자', assume that the business_experience value is the year and write {str(datetime.today().date())} - business_experience value.
    8. business_size can be a '규모' or '사원 수' or '업장 크기' or '업장 규모'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
    9. user_region can be a '사업장 소재지' or '주소'. As in the example, n spaces or other symbols may be inserted in the middle of the letter.
    10. For numbers 5 through 9, if there is other content with similar meaning in the hwp file context, please use that content as the field name.
    10. Fields marked None do not need to be entered.
    11. If you're going to write None, don't write it at all.
    12. Do not write the value 'business_experience' in the '대표자' field.
    13. Do not enter the value 'business_size' in the '업체명' field.
    14. In addition, find words with similar meanings and write the appropriate information in the appropriate space.
    ```

    Please look at the contents of the corresponding hwp file to understand where to enter the information provided in the context: ```{hwp_content}```

    write hwp code example: ```
    from hwpapi.core import App

    # Original_hwpx_file_path is {file_path}. Please replace the example below with {file_path}. If there are multiple file_paths, select one of them and enter it.
    # Never use the example path below. Please select from the file_path above and write.
    original_hwpx_file_path = r'hwp_file_path.hwp'

    # The revision must have a different name than the original. Please additionally write that the document has been modified.
    new_hwpx_file_path = r'hwp_file_path_modified.hwp'

    app = App(is_visible=False)
    app.open(original_hwpx_file_path)

    # When the information you find is in a table and you need to write it in the next frame on the right.
    def replace_text(app, old_text, new_text):
        if app.find_text(old_text):
            app.move()
            app.actions.MoveColumnEnd().run()
            app.actions.MoveSelRight().run()
            app.actions.MoveLineEnd().run()
            app.actions.MoveRight().run()
            app.actions.MoveColumnEnd().run()
            app.actions.MoveLineEnd().run()
            app.insert_text(new_text)

    # If there is a line break, find the word before the line break and execute it.
    replace_text(app, '사업장 소재지', '서울')
    replace_text(app, "사업장\n소재지", '서울')
    replace_text(app, '사업장', '서울')
    replace_text(app, '기업명', '진영기업')
    replace_text(app, '기 업 명', '진영기업')
    replace_text(app, '사업자등록번호', '111222333')
    replace_text(app, '대표자명', '김진영')
    replace_text(app, '성명', '김진영')

    app.save(new_hwpx_file_path)
    app.quit()

    print("Done.")
    ```
    """

    test = model.invoke(write_hwp_prompt)

    test_result = test.replace(r"```python\n`", "").replace("```", "").replace("python", "")

    script_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\gemini_code\\modify_hwp.py'
    with open(script_file_path, 'w', encoding='utf-8') as file:
        file.write(test_result)

    venv_python = os.path.join('.venv', 'Scripts', 'python.exe')

    hwp_result = subprocess.run([venv_python, script_file_path], capture_output=True, text=True)


### test code
test = {
    "user_region": "서울특별시", 
    "business_experience": "예비창업자", 
    "business_size": "10인 이하", 
    "support_field": "정책", 
    "user_question": "", 
    "response_message": ""
}

result, context = json_question(test)
print(result)

# print(result['Answer'])

# print(result['Question'])


# chain_test = prompt

# tt = chain_test.invoke({"question":test, "context":context})