import asyncio
import os
import sqlite3
from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
from datetime import datetime

os.chdir('C:\\Users\\jinyoungkim0308\\seoul_prompthon')
# SQLite 데이터베이스 설정
db_conn = sqlite3.connect('./rdbms/projects_sbiz24.db')


async def fetch_page_content(page, base_url, url, key):
    await page.goto(url)
    # Wait for 5 seconds to ensure the page content is fully loaded
    await asyncio.sleep(5)
    content = await page.content()

    # 다운로드 링크 확인 및 파일 다운로드
    download_links = await page.query_selector_all("div.file-group button.q-btn[title*='다운로드']")
    downloads_folder = os.path.join(os.getcwd(), f"downloads/sbiz24/{key}")
    os.makedirs(downloads_folder, exist_ok=True)

    if download_links:
        zip_downloaded = False
        for link in download_links:
            link_text = await link.inner_text()
            download_url = await link.get_attribute('href')
            if download_url and 'zip' in download_url.lower():
                full_download_url = urljoin(base_url, download_url)
                try:
                    async with page.expect_download() as download_info:
                        await link.click()  # Click the link instead of navigating to the URL
                    download = await download_info.value
                    filename = download.suggested_filename
                    file_path = os.path.join(downloads_folder, filename)
                    await download.save_as(file_path)
                    print(f"Downloaded: {file_path}")
                    zip_downloaded = True
                    break  # If zip is downloaded, exit the loop
                except TimeoutError:
                    print(f"Download timeout for link: {link_text}")

        if not zip_downloaded:
            # Download individual files if no zip file was found
            for link in download_links:
                download_url = await link.get_attribute('href')
                if not download_url:
                    # Single file button case
                    try:
                        async with page.expect_download() as download_info:
                            await link.click()  # Click the link instead of navigating to the URL
                        download = await download_info.value
                        filename = download.suggested_filename
                        file_path = os.path.join(downloads_folder, filename)
                        await download.save_as(file_path)
                        print(f"Downloaded single file: {file_path}")
                    except TimeoutError:
                        print(f"Download timeout for single file")
    else:
        # Check for single file download button when no download links are found
        single_file_button = await page.query_selector("button.q-btn[title*='다운로드']")
        if single_file_button:
            try:
                async with page.expect_download() as download_info:
                    await single_file_button.click()
                download = await download_info.value
                filename = download.suggested_filename
                file_path = os.path.join(downloads_folder, filename)
                await download.save_as(file_path)
                print(f"Downloaded single file: {file_path}")
            except TimeoutError:
                print(f"Download timeout for single file")

    return content


def parse_and_store(html, key):
    soup = BeautifulSoup(html, 'html.parser')
    metadata = {"key": key}

    # 고정된 컬럼 정의
    columns = {
        '공고일련번호': 'f_pbancSn',
        '공고명': 'f_pbancNm',
        '모집유형': 'f_rcrtTypeCd',
        '지원사업유형명': 'f_sprtBizTypeNm',
        '사업년도': 'f_bizYr',
        '공고차수': 'f_pbancCycl',
        '사업기간': 'f_bizPd',
        '접수기간': 'f_rcptPd',
        '공고내용': 'f_pbancDtlCn',
        '첨부파일': 'f_atch',
        '연관주제어': 'f_ascTiCnList'
    }

    # 특정 컬럼 정보 추출
    for field_name, field_class in columns.items():
        field = soup.select_one(
            f'div.{field_class} .form-wrap span, div.{field_class} .form-wrap div')
        metadata[field_name] = field.get_text(strip=True) if field else ""

    cursor = db_conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        key TEXT PRIMARY KEY,
        공고일련번호 TEXT,
        공고명 TEXT,
        모집유형 TEXT,
        지원사업유형명 TEXT,
        사업년도 TEXT,
        공고차수 TEXT,
        사업기간 TEXT,
        접수기간 TEXT,
        공고내용 TEXT,
        첨부파일 TEXT,
        연관주제어 TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cursor.execute("SELECT 1 FROM projects WHERE key = ?", (metadata['key'],))
    exists = cursor.fetchone()

    now = datetime.now().isoformat()
    if exists:
        print(f"Key {metadata['key']} already exists. Updating record.")
        cursor.execute("""
        UPDATE projects SET 공고일련번호 = ?, 공고명 = ?, 모집유형 = ?, 지원사업유형명 = ?, 사업년도 = ?, 공고차수 = ?, 사업기간 = ?, 접수기간 = ?, 공고내용 = ?, 첨부파일 = ?, 연관주제어 = ?, updated_at = ?
        WHERE key = ?
        """, (metadata.get('공고일련번호', ''), metadata.get('공고명', ''), metadata.get('모집유형', ''), metadata.get('지원사업유형명', ''), metadata.get('사업년도', ''), metadata.get('공고차수', ''), metadata.get('사업기간', ''), metadata.get('접수기간', ''), metadata.get('공고내용', ''), metadata.get('첨부파일', ''), metadata.get('연관주제어', ''), now, metadata['key']))
    else:
        cursor.execute("""
        INSERT INTO projects (key, 공고일련번호, 공고명, 모집유형, 지원사업유형명, 사업년도, 공고차수, 사업기간, 접수기간, 공고내용, 첨부파일, 연관주제어, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (metadata.get('key', ''), metadata.get('공고일련번호', ''), metadata.get('공고명', ''), metadata.get('모집유형', ''), metadata.get('지원사업유형명', ''), metadata.get('사업년도', ''), metadata.get('공고차수', ''), metadata.get('사업기간', ''), metadata.get('접수기간', ''), metadata.get('공고내용', ''), metadata.get('첨부파일', ''), metadata.get('연관주제어', ''), now, now))
    db_conn.commit()


async def fetch_all_links(page):
    all_links = []
    while True:
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.select('a[href^="#/pbanc/"]')
        if not links:
            break

        for link in links:
            href = link['href']
            full_url = f"https://www.sbiz24.kr{href}"
            all_links.append(full_url)

        next_button = await page.query_selector("li.page-item.btn-next button:not([disabled])")
        if next_button:
            await next_button.click()
            await asyncio.sleep(5)
            await page.wait_for_load_state("networkidle")
        else:
            break

    return all_links


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.sbiz24.kr/#/pbanc")

        links = await fetch_all_links(page)
        base_url = "https://www.sbiz24.kr"

        for url in links:
            key = url.split('/')[-1].split('?')[0]
            html = await fetch_page_content(page, base_url, url, key)
            parse_and_store(html, key)

        await browser.close()

asyncio.run(main())

# SQLite 데이터베이스 연결 닫기
db_conn.close()
