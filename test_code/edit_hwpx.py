import os
import shutil
import xml.etree.ElementTree as ET
import zipfile

import pandas as pd

def extract_and_modify_hwpx(hwpx_file_path, new_hwpx_file_path):
    # Change directory to the file's location
    os.chdir(os.path.dirname(hwpx_file_path))
    path = os.path.join(os.getcwd(), "hwpx")

    # Extract the hwpx file
    with zipfile.ZipFile(hwpx_file_path, 'r') as zf:
        zf.extractall(path=path)
    
    # Parse the XML file
    section0_xml_path = os.path.join(path, "Contents", "section0.xml")
    tree = ET.parse(section0_xml_path)
    root = tree.getroot()
    
    # Save the original XML content to raw_data
    with open(section0_xml_path, 'r', encoding='utf-8') as file:
        raw_data = file.read()
    
    # Define the namespace dictionary
    ns = {
        'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
        'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
        'hp10': 'http://www.hancom.co.kr/hwpml/2016/paragraph'
    }

    # Find all tables
    tbl_list = []
    for child in root.iter():
        if child.tag.endswith("}tbl"):
            tbl_list.append(child)
    
    # Modify the content of the tables
    for tbl in tbl_list:
        rows = tbl.findall('.//hp:tr', ns)
        for row in rows:
            cells = row.findall('.//hp:tc', ns)
            for i, cell in enumerate(cells):
                text_elements = cell.findall('.//hp:t', ns)
                if text_elements and text_elements[0].text in ['기업명', '사업자등록번호', '주소']:
                    if i + 1 < len(cells):
                        next_cell = cells[i + 1]
                        next_text_element = next_cell.find('.//hp:t', ns)
                        if next_text_element is not None:
                            if text_elements[0].text == '기업명':
                                next_text_element.text = '진영기업'
                            elif text_elements[0].text == '사업자등록번호':
                                next_text_element.text = 'asan1423'
                            elif text_elements[0].text == '주소':
                                next_text_element.text = '서울아산병원'
                        else:
                            new_text_element = ET.SubElement(next_cell, '{http://www.hancom.co.kr/hwpml/2011/paragraph}t')
                            if text_elements[0].text == '기업명':
                                new_text_element.text = '진영기업'
                            elif text_elements[0].text == '사업자등록번호':
                                new_text_element.text = 'asan1423'
                            elif text_elements[0].text == '주소':
                                new_text_element.text = '서울아산병원'

    # Write the modified XML back to the file
    tree.write(section0_xml_path, encoding='utf-8', xml_declaration=True)

    # Create a new hwpx file
    zip_file_path = new_hwpx_file_path.replace('.hwpx', '.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zip_ref:
        for folder_name, subfolders, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                zip_ref.write(file_path, os.path.relpath(file_path, path))
    
    # Rename the .zip file back to .hwpx
    os.rename(zip_file_path, new_hwpx_file_path)
    shutil.rmtree(path)

    return raw_data

# Example usage
original_hwpx_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\mss.go\\1040699\\2023년_중소기업_수출_유공_포상_후보자_모집_공고.hwpx'
new_hwpx_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\mss.go\\1040699\\2023년_중소기업_수출_유공_포상_후보자_모집_공고_수정본.hwpx'
raw_data = extract_and_modify_hwpx(original_hwpx_file_path, new_hwpx_file_path)
print("Modification complete.")
print("Raw Data:")
print(raw_data)
