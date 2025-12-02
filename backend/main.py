# backend/main.py
# FULLY WORKING VERSION – DEPLOY ON RENDER, RAILWAY, FLY.IO
# Just use start command: gunicorn main:app --bind=0.0.0.0:$PORT

import os
import uuid
import json
import time
import random
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

# --- Flask app setup ---
app = Flask(__name__)           # MUST be named "app" for gunicorn
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Config ---
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# --- Gemini AI Vision (FREE) ---
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def analyze_image_with_gemini(image_path):
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        with open(image_path, "rb") as f:
            response = model.generate_content([
                "Analyze this item for selling. Return ONLY valid JSON:",
                {
                    "mime_type": "image/jpeg",
                    "data": f.read()
                }
            ], generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e), "item_name": "Unknown", "condition": "Unknown"}

# --- Gumtree Scraper ---
from bs4 import BeautifulSoup

def scrape_gumtree_prices(query, location="sydney", max_results=10):
    url = f"https://www.gumtree.com.au/s-{location}/{query.replace(' ', '-')}/k0"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        time.sleep(random.uniform(1, 3))
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        prices = []
        for item in soup.select('.css-14q6nc1, .user-ad-price__price')[:max_results]:
            text = item.get_text(strip=True)
            price = int(''.join(filter(str.isdigit, text)) or 0)
            if price > 0:
                prices.append(price)
        avg = round(sum(prices)/len(prices), 2) if prices else 0
        return {"recommended": avg, "prices": prices[:10]}
    except:
        return {"recommended": 0, "prices": []}

# --- eBay Sandbox ---
def get_ebay_prices(query):
    app_id = os.getenv('EBAY_APP_ID')
    if not app_id:
        return {"recommended": 0, "prices": []}
    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": app_id,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": query,
        "paginationInput.entriesPerPage": 10
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        items = data.get("findItemsByKeywordsResponse", [{}])[0].get("searchResult", [{}])[0].get("item", [])
        prices = []
        for item in items:
            try:
                price = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
                prices.append(round(price, 2))
            except:
                continue
        avg = round(sum(prices)/len(prices), 2) if prices else 0
        return {"recommended": avg, "prices": prices}
    except:
        return {"recommended": 0, "prices": []}

# --- Routes ---
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "version": "1.0"})

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image"}), 400
    file = request.files['image']
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    analysis = analyze_image_with_gemini(filepath)
    return jsonify({"success": True, "data": analysis})

@app.route('/prices')
def prices():
    item = request.args.get('item', '').strip()
    if not item:
        return jsonify({"error": "item required"}), 400

    ebay = get_ebay_prices(item)
    gumtree = scrape_gumtree_prices(item)

    all_prices = ebay["prices"] + gumtree["prices"]
    recommended = round(sum(all_prices)/len(all_prices), 2) if all_prices else 0

    return jsonify({
        "recommended": recommended,
        "ebay": ebay,
        "gumtree": gumtree
    })

@app.route('/')
def index():
    return jsonify({"message": "SellSmart API running!"})

# --- Run ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
