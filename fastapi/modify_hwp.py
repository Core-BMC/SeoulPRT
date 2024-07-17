
from hwpapi.core import App

# Original_hwpx_file_path is C:\Users\jinyoungkim0308\seoul_prompthon\downloads\tech\2407051314482024년+기술이전+지원사업(서울+스타트업+Tech+trade-on+프로그램)+공고문.hwp. Please replace the example below with C:\Users\jinyoungkim0308\seoul_prompthon\downloads\tech\2407051314482024년+기술이전+지원사업(서울+스타트업+Tech+trade-on+프로그램)+공고문.hwp. If there are multiple file_paths, select one of them and enter it.
# Never use the example path below. Please select from the file_path above and write.
original_hwpx_file_path = r'C:\Users\jinyoungkim0308\seoul_prompthon\downloads\tech\2407051314482024년+기술이전+지원사업(서울+스타트업+Tech+trade-on+프로그램)+공고문.hwp'

# The revision must have a different name than the original. Please additionally write that the document has been modified.
new_hwpx_file_path = r'C:\Users\jinyoungkim0308\seoul_prompthon\downloads\tech\2407051314482024년+기술이전+지원사업(서울+스타트업+Tech+trade-on+프로그램)+공고문_modified.hwp'

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
replace_text(app, '기 업 명', 'BMC')
replace_text(app, '대표자명', '심우현')
replace_text(app, '설 립 일', '2024-07-11 - 기존창업자')
replace_text(app, '소재지', '서울특별시')
replace_text(app, '근로자수\n(대표자포함)', '10인 이하')

app.save(new_hwpx_file_path)
app.quit()

print("Done.")

