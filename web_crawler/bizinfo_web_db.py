import asyncio
import os
import sqlite3
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup

os.chdir('C:\\Users\\jinyoungkim0308\\seoul_prompthon')

# SQLite 데이터베이스 설정
db_conn = sqlite3.connect('./rdbms/bizinfo.db')


async def fetch_page_content(page, url, key):
    await page.goto(url)
    content = await page.content()

    # Check for download links and download files
    download_links = await page.query_selector_all("a.icon_download")
    downloads_folder = os.path.join(os.getcwd(), f"downloads/bizinfo/{key}")
    os.makedirs(downloads_folder, exist_ok=True)

    for link in download_links:
        link_text = await link.inner_text()
        if "다운로드" in link_text:
            try:
                async with page.expect_download() as download_info:
                    await link.click()
                download = await download_info.value
                filename = download.suggested_filename
                file_path = os.path.join(downloads_folder, filename)
                await download.save_as(file_path)
                print(f"Downloaded: {file_path}")
            except TimeoutError:
                print(f"Download timeout for link: {link_text}")

    return content


def parse_and_store(html, key):
    soup = BeautifulSoup(html, 'html.parser')
    metadata = {"key": key}

    # Define the fixed columns to extract
    columns = ['소관부처·지자체', '사업수행기관', '신청기간',
               '사업개요', '사업신청 방법', '사업신청 사이트', '문의처']

    # Extract information for specific columns
    for li in soup.select('ul li'):
        key_tag = li.select_one('span.s_title')
        if key_tag:
            key = key_tag.get_text(strip=True)
            value_tag = li.select_one('div.txt')
            value = value_tag.get_text(strip=True) if value_tag else ""
            if key in columns:
                metadata[key] = value

    cursor = db_conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        key TEXT PRIMARY KEY,
        소관부처_지자체 TEXT,
        사업수행기관 TEXT,
        신청기간 TEXT,
        사업개요 TEXT,
        사업신청_방법 TEXT,
        사업신청_사이트 TEXT,
        문의처 TEXT,
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
        UPDATE projects SET 소관부처_지자체 = ?, 사업수행기관 = ?, 신청기간 = ?, 사업개요 = ?, 사업신청_방법 = ?, 사업신청_사이트 = ?, 문의처 = ?, updated_at = ?
        WHERE key = ?
        """, (metadata.get('소관부처·지자체', ''), metadata.get('사업수행기관', ''), metadata.get('신청기간', ''), metadata.get('사업개요', ''), metadata.get('사업신청 방법', ''), metadata.get('사업신청 사이트', ''), metadata.get('문의처', ''), now, metadata['key']))
    else:
        cursor.execute("""
        INSERT INTO projects (key, 소관부처_지자체, 사업수행기관, 신청기간, 사업개요, 사업신청_방법, 사업신청_사이트, 문의처, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (metadata.get('key', ''), metadata.get('소관부처·지자체', ''), metadata.get('사업수행기관', ''), metadata.get('신청기간', ''), metadata.get('사업개요', ''), metadata.get('사업신청 방법', ''), metadata.get('사업신청 사이트', ''), metadata.get('문의처', ''), now, now))
    db_conn.commit()


async def fetch_all_links(base_url, view_base_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        page_number = 1
        all_links = []

        while True:
            await page.goto(f"{base_url}&cpage={page_number}")
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.select('a[href*="view.do?pblancId="]')

            if not links:
                break

            for link in links:
                href = link.get('href')
                if href:
                    full_url = f"{view_base_url}{href}"
                    all_links.append(full_url)

            page_number += 1

        await browser.close()
        return all_links


async def main():
    base_url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/list.do?rows=15"
    view_base_url = "https://www.bizinfo.go.kr/web/lay1/bbs/S1T122C128/AS/74/"
    links = await fetch_all_links(base_url, view_base_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        for url in links:
            key = url.split('pblancId=')[-1]
            html = await fetch_page_content(page, url, key)
            parse_and_store(html, key)

        await browser.close()

asyncio.run(main())

# Close the SQLite database connection
db_conn.close()
