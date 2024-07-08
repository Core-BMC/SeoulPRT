import asyncio
import os
import sqlite3
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
from datetime import datetime

os.chdir('C:\\Users\\jinyoungkim0308\\seoul_prompthon')
# SQLite 데이터베이스 설정
db_conn = sqlite3.connect('./rdbms/semas.db')


async def fetch_page_content(page, url):
    await page.goto(url)
    content = await page.content()

    # Check for download links and download files
    soup = BeautifulSoup(content, 'html.parser')
    download_links = soup.select('a[href^="/common/download.kmdc?f="]')
    key = url.split('b_idx=')[-1].split('&')[0]
    downloads_folder = os.path.join(os.getcwd(), f"downloads/semas/{key}")
    os.makedirs(downloads_folder, exist_ok=True)

    for link in download_links:
        href = link.get('href')
        filename = link.text.strip()
        file_url = f"https://www.semas.or.kr{href}"
        try:
            async with page.expect_download() as download_info:
                await page.click(f'a[href="{href}"]')
            download = await download_info.value
            file_path = os.path.join(downloads_folder, filename)
            await download.save_as(file_path)
            print(f"Downloaded: {file_path}")
        except TimeoutError:
            print(f"Download timeout for link: {file_url}")

    return content, key


def parse_and_store(html, key):
    soup = BeautifulSoup(html, 'html.parser')
    metadata = {"key": key}

    # Extract information
    metadata['title'] = soup.select_one('th:-soup-contains("제목") + td').text.strip(
    ) if soup.select_one('th:-soup-contains("제목") + td') else ''
    metadata['views'] = soup.select_one('th:-soup-contains("조회수") + td').text.strip(
    ) if soup.select_one('th:-soup-contains("조회수") + td') else ''
    metadata['author'] = soup.select_one('th:-soup-contains("등록자") + td').text.strip(
    ) if soup.select_one('th:-soup-contains("등록자") + td') else ''
    metadata['date'] = soup.select_one('th:-soup-contains("등록일") + td').text.strip(
    ) if soup.select_one('th:-soup-contains("등록일") + td') else ''
    metadata['content'] = soup.select_one(
        'td.cont').text.strip() if soup.select_one('td.cont') else ''

    now = datetime.now().isoformat()

    # Insert or update into database
    cursor = db_conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        key TEXT PRIMARY KEY,
        title TEXT,
        views INTEGER,
        author TEXT,
        date TEXT,
        content TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    cursor.execute("SELECT 1 FROM posts WHERE key = ?", (metadata['key'],))
    exists = cursor.fetchone()

    if exists:
        print(f"Key {metadata['key']} already exists. Updating record.")
        cursor.execute("""
        UPDATE posts SET title = ?, views = ?, author = ?, date = ?, content = ?, updated_at = ? WHERE key = ?
        """, (metadata.get('title', ''), metadata.get('views', ''), metadata.get('author', ''), metadata.get('date', ''), metadata.get('content', ''), now, metadata['key']))
    else:
        cursor.execute("""
        INSERT INTO posts (key, title, views, author, date, content, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (metadata.get('key', ''), metadata.get('title', ''), metadata.get('views', ''), metadata.get('author', ''), metadata.get('date', ''), metadata.get('content', ''), now, now))

    db_conn.commit()


async def fetch_all_links(base_url, view_base_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        page_number = 1  # Start from page 1
        all_links = []

        while True:
            url = f"{base_url}&page={page_number}"
            await page.goto(url)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Check for "조회된 결과가 없습니다."
            if "조회된 결과가 없습니다." in content:
                break

            links = soup.select('td.left.title a')
            for link in links:
                href = link.get('href')
                if href:
                    if not href.startswith("https://www.semas.or.kr"):
                        href = f"https://www.semas.or.kr/web/board/{href.lstrip('/')}"
                    all_links.append(href)
                    print(href)

            page_number += 1

        await browser.close()
        return all_links


async def main():
    base_url = "https://www.semas.or.kr/web/board/webBoardList.kmdc?bCd=1&schCon=&schStr=&schCat=&schExpart=&schArea=&schStat=&pNm=BOA0101"
    view_base_url = "https://www.semas.or.kr/web/board/"
    links = await fetch_all_links(base_url, view_base_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        for url in links:
            html, key = await fetch_page_content(page, url)
            parse_and_store(html, key)

        await browser.close()

asyncio.run(main())

# Close the SQLite database connection
db_conn.close()
