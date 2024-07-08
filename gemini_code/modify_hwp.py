
from hwpapi.core import App
# Original_hwpx_file_path is C:\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094409\\신청서 등 서식.hwp. Please replace the example below with C:\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094409\\신청서 등 서식.hwp. If there are multiple file_paths, select one of them and enter it.
# Never use the example path below. Please select from the file_path above and write.
original_hwpx_file_path = r'C:\Users\jinyoungkim0308\seoul_prompthon\downloads\bizinfo\PBLN_000000000094409\신청서 등 서식.hwp'
# The revision must have a different name than the original. Please additionally write that the document has been modified.
new_hwpx_file_path = r'C:\Users\jinyoungkim0308\seoul_prompthon\downloads\bizinfo\PBLN_000000000094409\신청서 등 서식_modified.hwp'
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
replace_text(app, '업력', '10년')
replace_text(app, '업 력', '10년')
replace_text(app, '사업장 인력 규모', '50인 이하')
replace_text(app, '업장 규모', '50인 이하')
app.save(new_hwpx_file_path)
app.quit()
print("Done.")