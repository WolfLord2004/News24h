from flask import Flask, render_template
import sqlite3
import utils
import json
import os

app = Flask(__name__)

def get_news():
    try:
        # Create json_file directory if it doesn't exist
        os.makedirs("json_file", exist_ok=True)
        
        # Get news data from database
        rows = utils.get_all("SELECT * FROM news")
        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "tieude": r[1],
                "noidung": r[2],
                "hinhanh": r[3],
                "linkgoc": r[4],
                "cat_id": r[5]
            })
            
        # Write to JSON file
        with open("json_file/news.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return data
    except Exception as e:
        print(f"Error in get_news: {str(e)}")
        raise e

def read_news(keywords=None):
    try:
        # Create json_file directory if it doesn't exist
        os.makedirs("json_file", exist_ok=True)
        
        # If news.json doesn't exist, create it
        if not os.path.exists("json_file/news.json"):
            get_news()
            
        # Read from JSON file
        with open("json_file/news.json", encoding="utf-8") as f:
            news = json.load(f)
            
        # Filter by keywords if provided
        if keywords:
            news = [n for n in news if keywords.lower() in n["tieude"].lower()]
            
        return news
    except Exception as e:
        print(f"Error in read_news: {str(e)}")
        raise e

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    conn = sqlite3.connect(utils.DB_PATH)
    conn.row_factory = sqlite3.Row
    detail = conn.execute("SELECT * FROM DetailNews WHERE id=?", (news_id,)).fetchone()
    conn.close()
    if not detail:
        return "Không tìm thấy nội dung", 404
    return render_template('news_detail.html', detail=detail)

@app.route('/news')
def news_list():
    news = utils.get_all("SELECT * FROM news")
    return render_template('news_list.html', news_list=news)

@app.route('/crawl')
def crawl():
    # Crawl danh sách bài báo
    utils.get_news_url()
    # Crawl chi tiết từng bài báo và lưu vào DetailNews
    utils.crawl_detail_for_all_news()
    return render_template('crawl_result.html')  # hoặc trả về kết quả crawl

if __name__ == "__main__":
    app.run(debug=True)