# import các thư viện
import utils as utils
import render_templates as render_templates
from flask import Flask, jsonify, render_template, request
import json
import threading
from datetime import datetime
import os  # Add this import


# khai báo biến app để tạo các endpoint
app = Flask(__name__)

# define endpoint cho trang chủ
@app.route("/")
def render():
    try:
        # Get page number and keywords from query parameters
        page = int(request.args.get("page", 1))
        kw = request.args.get("keywords", None)
        per_page = 18  # Number of items per page
        
        # Get all rows first
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

        # Apply search filter if keywords provided
        if kw:
            data = [n for n in data if kw.lower() in n['tieude'].lower()]
        
        # Calculate pagination
        total_items = len(data)
        total_pages = (total_items + per_page - 1) // per_page
        
        # Ensure page number is within valid range
        page = max(1, min(page, total_pages))
        
        # Slice the data for current page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_data = data[start_idx:end_idx]
            
        return render_template("index.html", 
                             news_data=page_data,
                             current_page=page,
                             total_pages=total_pages,
                             keywords=kw)
    except Exception as e:
        print(f"Error in render: {str(e)}")
        return render_template("index.html", 
                             news_data=[], 
                             current_page=1,
                             total_pages=1,
                             keywords=None)

# define endpoint cho category
# get category in database
@app.route("/category", methods=["GET"])
def get_categories():
    try:
        rows = utils.get_all("SELECT * FROM category")
        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "subject": r[1],
                "url": r[2]
            })
        
        # Create json_file directory if it doesn't exist
        os.makedirs("json_file", exist_ok=True)
        
        # Write to JSON file
        try:
            with open("json_file/category.json", "w", encoding="utf8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing JSON: {str(e)}")
            
        return render_template("category.html", data=data)
        
    except Exception as e:
        print(f"Error in get_categories: {str(e)}")
        return f"Error: {str(e)}", 500

# define endpoint cho news
@app.route("/news", methods=["GET"])
def render_news():
    try:
        # Get page number from query parameters, default to 1
        page = int(request.args.get("page", 1))
        per_page = 18  # Number of items per page
        
        # Get all rows first
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
        
        # Handle search if keywords provided
        kw = request.args.get("keywords", None)
        if kw:
            data = [n for n in data if kw.lower() in n['tieude'].lower()]
        
        # Calculate pagination
        total_items = len(data)
        total_pages = (total_items + per_page - 1) // per_page
        
        # Ensure page number is within valid range
        page = max(1, min(page, total_pages))
        
        # Slice the data for current page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_data = data[start_idx:end_idx]
        
        # Write to JSON file
        try:
            os.makedirs("json_file", exist_ok=True)
            with open("json_file/news.json", "w", encoding="utf8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing JSON: {str(e)}")
        
        return render_template("news.html", 
                             data=page_data,
                             current_page=page,
                             total_pages=total_pages,
                             keywords=kw)
        
    except Exception as e:
        print(f"Error in render_news: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route("/news/<int:news_id>")
def news_detail(news_id):
    import sqlite3
    conn = sqlite3.connect(utils.DB_PATH)
    conn.row_factory = sqlite3.Row
    detail = conn.execute("SELECT * FROM DetailNews WHERE id=?", (news_id,)).fetchone()
    conn.close()
    if not detail:
        return "Không tìm thấy nội dung", 404
    return render_template("news_detail.html", detail=detail)

@app.route("/crawl", methods=["GET"])
def crawl_data():
    try:
        # Start crawling in a separate thread
        thread = threading.Thread(target=utils.crawl_and_save_all)
        thread.daemon = True
        thread.start()
        return render_template("crawl_popup.html")
    except Exception as e:
        print(f"Error starting crawl: {str(e)}")
        return jsonify({"error": str(e)})

@app.route("/stop_crawl", methods=["POST"])
def stop_crawl():
    try:
        result = utils.stop_crawling()
        return jsonify(result)
    except Exception as e:
        print(f"Error stopping crawl: {str(e)}")
        return jsonify({"error": str(e)})

@app.route("/get_crawl_status", methods=["GET"])
def get_crawl_status():
    try:
        results = utils.get_crawl_results()
        return jsonify(results)
    except Exception as e:
        print(f"Error getting status: {str(e)}")
        return jsonify({"error": str(e)})

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error"}), 500

@app.before_request
def before_request():
    """Log request details before processing"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{request.method}] {request.path}")
    if request.args:
        print(f"Query params: {dict(request.args)}")
    if request.form:
        print(f"Form data: {dict(request.form)}")

@app.after_request
def after_request(response):
    """Log response status after processing"""
    print(f"Response status: {response.status}")
    return response

# run module
if __name__ == "__main__":
    app.run(host='0.0.0.0', 
            port=5000, 
            debug=True, 
            use_reloader=True)