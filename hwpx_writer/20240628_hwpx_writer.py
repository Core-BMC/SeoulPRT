from hwpapi.core import App

original_hwpx_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\mss.go\\1040699\\2023년_중소기업_수출_유공_포상_후보자_모집_공고.hwpx'
original_hwpx_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094693\\2024년 기술이전 지원사업(서울 스타트업 Tech trade-on 프로그램) 공고문.hwp'

new_hwpx_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\mss.go\\1040699\\2023년_중소기업_수출_유공_포상_후보자_모집_공고_수정본.hwpx'
new_hwpx_file_path = r'C:\\Users\\jinyoungkim0308\\seoul_prompthon\\downloads\\bizinfo\\PBLN_000000000094693\\2024년 기술이전 지원사업(서울 스타트업 Tech trade-on 프로그램) 공고문 수정본.hwp'

app = App(is_visible=False)
app.open(original_hwpx_file_path)

def replace_text(app, old_text, new_text):
    if app.find_text(old_text):
        app.move()
        app.actions.MoveColumnEnd().run()
        app.actions.MoveSelRight().run()
        app.actions.MoveRight().run()
        app.actions.MoveColumnEnd().run()
        app.actions.MoveLineEnd().run()
        app.insert_text(new_text)
        # app.actions.Delete().run()

replace_text(app, '기업명', '진영기업')
replace_text(app, '기 업 명', '진영기업')
replace_text(app, '사업자등록번호', '111222333')
replace_text(app, '대표자명', '김진영')
replace_text(app, '성명', '김진영')

app.save(new_hwpx_file_path)
app.quit()

print("HWP 파일이 성공적으로 수정되고 저장되었습니다.")
