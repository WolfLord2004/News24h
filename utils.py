import sqlite3
from newspaper import Article
import requests
from bs4 import BeautifulSoup
import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'NewsDB.db')

def try_bs4(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        main = (
            soup.find('div', class_='detail-content afcbc-body') or
            soup.find('div', class_='article-content') or
            soup.find('article') or
            soup.find('div', class_='main-content') or
            soup
        )
        ps = main.find_all('p')
        text = "\n".join(p.get_text(strip=True) for p in ps if p.get_text(strip=True))
        return text
    except Exception as e:
        print(f"BeautifulSoup fallback failed: {e}")
        return ""

def crawl_and_save_all():
    conn = sqlite3.connect(DB_PATH)
    cats = conn.execute("SELECT * FROM category").fetchall()
    for cat in cats:
        cat_id = cat[0]
        url = cat[2]
        try:
            import newspaper
            papers = newspaper.build(url, memoize_articles=False)
            for article in papers.articles[:30]:  # Crawl 5 bài mỗi chuyên mục
                try:
                    art = Article(article.url)
                    art.download()
                    art.parse()
                    title = art.title or ""
                    text = art.text or ""
                    top_image = art.top_image or ""
                    # Nếu không lấy được nội dung thì thử BeautifulSoup
                    if not text.strip():
                        text = try_bs4(article.url)
                    # Lưu vào bảng news
                    conn.execute(
                        "INSERT INTO news(tieude, noidung, hinhanh, linkgoc, cat_id) VALUES (?, ?, ?, ?, ?)",
                        (title, text, top_image, article.url, cat_id)
                    )
                    conn.commit()
                    # Lấy id vừa insert
                    news_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    # Lưu vào bảng DetailNews
                    conn.execute(
                        "INSERT INTO DetailNews(id, NoiDung, tieude) VALUES (?, ?, ?)",
                        (news_id, text, title)
                    )
                    conn.commit()
                    print(f"Đã lưu: {title}")
                except Exception as e:
                    print(f"Lỗi crawl/lưu bài: {e}")
        except Exception as e:
            print(f"Lỗi crawl chuyên mục {url}: {e}")
    conn.close()

def get_all(query):
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    data = conn.execute(query).fetchall()
    conn.close()
    return data

if __name__ == "__main__":
    crawl_and_save_all()