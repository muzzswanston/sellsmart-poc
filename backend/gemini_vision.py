import google.generativeai as genai
import os
import json
from PIL import Image
import io

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def analyze_image_with_gemini(image_path):
    """Analyze item image using FREE Gemini 1.5 Flash"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    try:
        # Load and resize image for faster processing
        with Image.open(image_path) as img:
            img = img.resize((1024, 1024))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=85)
            img_byte_arr = img_byte_arr.getvalue()
        
        response = model.generate_content([
            """Analyze this item for selling on marketplace sites. 
            Extract and return ONLY valid JSON with:
            {
              "item_name": "exact item name",
              "condition": "Excellent|Good|Fair|Poor",
              "brand": "brand name or null",
              "category": "Electronics|Furniture|Clothing|etc",
              "key_features": ["feature1", "feature2"],
              "title": "Catchy marketplace title (max 80 chars)",
              "description": "Detailed description (200-300 words)",
              "estimated_value": "Low|Medium|High"
            }
            Be specific about model numbers, colors, sizes.""",
            {"inline_data": {
                "mime_type": "image/jpeg",
                "data": img_byte_arr.hex()
            }}
        ])
        
        # Parse JSON response
        content = response.text.strip()
        if content.startswith('```json'):
            content = content[7:-3]  # Remove markdown
        elif content.startswith('```'):
            content = content[3:-3]
        
        analysis = json.loads(content)
        
        # Ensure required fields
        defaults = {
            "item_name": "Unknown Item",
            "condition": "Good",
            "brand": None,
            "category": "General",
            "key_features": [],
            "title": "Great condition item for sale",
            "description": "Well-maintained item in good working condition. Perfect for immediate use.",
            "estimated_value": "Medium"
        }
        
        for key, default in defaults.items():
            if key not in analysis:
                analysis[key] = default
        
        return analysis
        
    except json.JSONDecodeError:
        # Fallback parsing
        return {
            "item_name": "Item detected",
            "condition": "Good",
            "brand": None,
            "category": "General",
            "key_features": [],
            "title": "Quality item for sale",
            "description": f"AI analysis: {response.text[:200]}...",
            "estimated_value": "Medium"
        }
    except Exception as e:
        return {
            "item_name": "Analysis failed",
            "condition": "Unknown",
            "error": str(e),
            "title": "Item for sale",
            "description": "Please manually describe this item"
        }
