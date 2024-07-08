import os
import shutil
import xml.etree.ElementTree as ET
import zipfile
import pandas as pd

def list_files_in_directory(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)
    return file_list

directory_path = 'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads'

all_files = list_files_in_directory(directory_path)

hwpx_files = [file for file in all_files if file.lower().endswith('.hwpx')]

os.chdir(os.path.dirname(hwpx_files[0]))
path = os.path.join(os.getcwd(), "hwpx")

with zipfile.ZipFile(hwpx_files[0], 'r') as zf:
    zf.extractall(path=path)

tree = ET.parse(os.path.join(os.getcwd(), "hwpx", "Contents", "section0.xml"))
root = tree.getroot()

tbl_list = []
for child in root.iter():
    if child.tag.endswith("}tbl"):
        tbl_list.append(child)

tbl = tbl_list[0]
tbl_cols = int(tbl.attrib["colCnt"])
tbl_rows = int(tbl.attrib["rowCnt"])

data = []
for i in tbl.iter():
    if i.tag.endswith("}t"):
        data.append(i.text)

df = pd.DataFrame(data)
df = pd.DataFrame(data=df.iloc[tbl_cols:, :].values.reshape(-1, tbl_cols), columns=df.iloc[:tbl_cols, 0].values)
df = df.astype({"total_bill": "float", "tip": "float", "size": "int"})

shutil.rmtree(path)

df.describe()
