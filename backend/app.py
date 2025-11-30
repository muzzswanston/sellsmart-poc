from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import uuid
import json
from gemini_vision import analyze_image_with_gemini
from gumtree_scraper import scrape_gumtree_prices
from ebay_prices import get_ebay_prices
from database import save_analysis, get_analyses


load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'version': '1.0.0'})

@app.route('/analyze', methods=['POST'])
def analyze():
    """AI image analysis endpoint"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save image
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Analyze with FREE Gemini AI
        analysis = analyze_image_with_gemini(filepath)
        
        # Save to database
        analysis_id = save_analysis(analysis, filepath)
        analysis['id'] = analysis_id
        
        return jsonify({
            'success': True,
            'data': analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/prices', methods=['GET'])
def get_prices():
    """Get competitive prices from eBay + Gumtree"""
    item = request.args.get('item', '')
    if not item:
        return jsonify({'error': 'Item name required'}), 400
    
    try:
        # Get prices from both platforms
        ebay_result = get_ebay_prices(item)
        gumtree_result = scrape_gumtree_prices(item)
        
        # Combine for recommendation
        all_prices = []
        for platform, data in [('ebay', ebay_result), ('gumtree', gumtree_result)]:
            for listing in data.get('prices', []):
                if listing.get('price', 0) > 0:
                    all_prices.append(listing['price'])
        
        recommended_price = round(sum(all_prices) / len(all_prices), 2) if all_prices else 0
        
        return jsonify({
            'success': True,
            'recommended': recommended_price,
            'platforms': {
                'ebay': ebay_result,
                'gumtree': gumtree_result
            },
            'all_prices': all_prices
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyses', methods=['GET'])
def list_analyses():
    """List recent analyses"""
    analyses = get_analyses(limit=10)
    return jsonify({'success': True, 'data': analyses})

@app.route('/docs', methods=['GET'])
def docs():
    """API Documentation"""
    return jsonify({
        'api_version': '1.0.0',
        'endpoints': {
            '/health': 'GET - Health check',
            '/analyze': 'POST - Analyze image (multipart/form-data, field: image)',
            '/prices?item=...': 'GET - Get competitive prices',
            '/analyses': 'GET - List recent analyses'
        },
        'example_usage': {
            'analyze': 'curl -F "image=@photo.jpg" https://your-app.railway.app/analyze',
            'prices': 'curl "https://your-app.railway.app/prices?item=iPhone"'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
