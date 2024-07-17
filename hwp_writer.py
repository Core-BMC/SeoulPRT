import win32com.client as win32
from datetime import datetime

def extract_text_from_hwp(file_path):
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    hwp.Open(file_path)

    full_text = ""

    def get_last_paragraph():
        hwp.MovePos(3)  # 문서의 끝으로 이동
        return hwp.GetPos()[1]  # 마지막 문단 번호 반환

    last_paragraph = get_last_paragraph()

    for i in range(last_paragraph + 1):
        hwp.SetPos(0, i, 0)  # i번째 문단의 시작으로 이동
        paragraph_text = hwp.GetTextFile("TEXT", "").strip()
        full_text += paragraph_text + "\n\n"

    hwp.Quit()
    return full_text

file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\tech\\2407051314482024년+기술이전+지원사업(서울+스타트업+Tech+trade-on+프로그램)+공고문.hwp'
prom_information={'company_name': 'Not provided', 'name': 'Not provided', 'user_region': 'Seoul', 'business_experience': 'Less than 7 years', 'business_size': 'Not provided'}
hwp_content = extract_text_from_hwp(file_path)

hwp_content.encode('latin1').decode('euc-kr')

write_hwp_prompt = f"""system
Read the following explanation and write your answer using the context: ```{prom_information}```

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

Please look at the contents of the corresponding hwp file to understand where to enter the information provided in the context: ```{hwp_content.encode('latin1').decode('euc-kr')}```

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
replace_text(app, r"사업장\n소재지", '서울')
replace_text(app, '사업장', '서울')
replace_text(app, '기업명', '진영기업')
replace_text(app, '기 업 명', '진영기업')
replace_text(app, '사업자등록번호', '111222333')
replace_text(app, '대표자명', '김진영')
replace_text(app, '성명', '김진영')
replace_text(app, r'근로자수\n(대표자포함)', '10인 이상')
replace_text(app, '근로자수', '10인 이상')

app.save(new_hwpx_file_path)
app.quit()

print("Done.")
```
"""
from dotenv import load_dotenv
import os
from langchain_google_vertexai import ChatVertexAI
import subprocess
# Load environment variables
load_dotenv('./.env')
openai_api_key = os.getenv("OPENAI_API_KEY_SSIMU")
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./vertexai_key/prompthon-prd-19-33d473e1eeb0.json"

# Define the model and prompts
model = ChatVertexAI(
    model="gemini-1.5-pro-001",
    temperature=0,
    max_tokens=8192,
    max_retries=5,
    stop=None,
)

test = model.invoke(write_hwp_prompt)
test_result = test.content.replace(r"```python\n`", "").replace("```", "").replace("python", "")

script_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\gemini_code\\modify_hwp.py'
with open(script_file_path, 'w', encoding='utf-8') as file:
    file.write(test_result)

venv_python = os.path.join('.fastapi_venv', 'Scripts', 'python.exe')

result = subprocess.run([venv_python, script_file_path], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)