import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError
import sqlite3
import os
from datetime import datetime

os.chdir('C:\\Users\\jinyoungkim0308\\seoul_prompthon')

# SQLite 데이터베이스 연결 설정
db_conn = sqlite3.connect('./rdbms/mss.go.kr.db')
cursor = db_conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS page_info (
    bcIdx INTEGER PRIMARY KEY,
    url TEXT,
    담당부서 TEXT,
    등록일 TEXT,
    조회 INTEGER,
    작성자 TEXT,
    첨부파일 TEXT,
    컨텐트 TEXT,
    created_at TEXT,
    updated_at TEXT
)''')
db_conn.commit()


async def fetch_page_content(page, url):
    await page.goto(url)
    return await page.content()


async def download_attachments(page, soup, download_folder):
    attachments = []
    download_links = soup.select(
        'a.btn.type_down[href^="/common/board/Download.do"]')
    for link in download_links:
        href = link['href']
        full_url = f"https://www.mss.go.kr{href}"
        try:
            async with page.expect_download() as download_info:
                await page.click(f'a[href="{href}"]')
            download = await download_info.value
            filename = download.suggested_filename
            file_path = os.path.join(download_folder, filename)
            await download.save_as(file_path)
            attachments.append(file_path)
            print(f"Downloaded: {file_path}")
        except TimeoutError:
            print(f"Download timeout for link: {full_url}")
    return attachments


def parse_and_store(html, url, attachments, bcIdx):
    soup = BeautifulSoup(html, 'html.parser')

    def extract_text(th_text):
        th_element = soup.find('th', text=th_text)
        if th_element:
            return th_element.find_next('td').text.strip()
        return None

    담당부서 = extract_text('담당부서')
    등록일 = extract_text('등록일')
    조회 = extract_text('조회')
    작성자 = extract_text('작성자')
    컨텐트_element = soup.select_one('textarea#editContents')
    컨텐트 = 컨텐트_element.text.strip() if 컨텐트_element else None

    첨부파일 = ', '.join(attachments) if attachments else None

    cursor.execute("SELECT 1 FROM page_info WHERE bcIdx = ?", (bcIdx,))
    exists = cursor.fetchone()

    now = datetime.now().isoformat()
    if exists:
        print(f"bcIdx {bcIdx} already exists. Updating record.")
        cursor.execute('''UPDATE page_info SET url = ?, 담당부서 = ?, 등록일 = ?, 조회 = ?, 작성자 = ?, 첨부파일 = ?, 컨텐트 = ?, updated_at = ? WHERE bcIdx = ?''',
                       (url, 담당부서, 등록일, 조회, 작성자, 첨부파일, 컨텐트, now, bcIdx))
    else:
        cursor.execute('''INSERT INTO page_info (bcIdx, url, 담당부서, 등록일, 조회, 작성자, 첨부파일, 컨텐트, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (bcIdx, url, 담당부서, 등록일, 조회, 작성자, 첨부파일, 컨텐트, now, now))
    db_conn.commit()


async def fetch_all_links(page):
    all_links = []
    page_number = 1

    while True:
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.select('a[href="#view"][onclick*="doBbsFView"]')

        if not links and page_number == 1:
            break
        if page_number >= 10:
            break

        for link in links:
            onclick = link['onclick']
            # Extract the parameters from the onclick attribute
            params = onclick.split("doBbsFView('")[1].split(
                "');return false;")[0].split("','")
            if len(params) >= 4:
                cbIdx, bcIdx, _, parentSeq = params
                full_url = f"https://www.mss.go.kr/site/smba/ex/bbs/View.do?cbIdx={cbIdx}&bcIdx={bcIdx}&parentSeq={parentSeq}"
                all_links.append((full_url, bcIdx))
        next_page_link = await page.query_selector(f'a[onclick="doBbsFPag({page_number});return false; "]')
        if next_page_link:
            page_number += 1
            await next_page_link.click()
            await asyncio.sleep(3)
            await page.wait_for_load_state("networkidle")
        else:
            break

    return all_links


async def main():
    base_url = "https://www.mss.go.kr/site/smba/ex/bbs/List.do?cbIdx=81"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(base_url)

        links = await fetch_all_links(page)

        for url, bcIdx in links:
            html = await fetch_page_content(page, url)
            soup = BeautifulSoup(html, 'html.parser')
            download_folder = os.path.join('downloads', 'mss.go', bcIdx)
            os.makedirs(download_folder, exist_ok=True)
            attachments = await download_attachments(page, soup, download_folder)
            parse_and_store(html, url, attachments, bcIdx)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
    # SQLite 데이터베이스 연결 종료
    db_conn.close()
