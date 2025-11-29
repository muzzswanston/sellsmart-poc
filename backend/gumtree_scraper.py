import requests
from bs4 import BeautifulSoup
import re
import time
import random
from typing import Dict, List

def scrape_gumtree_prices(query: str, location: str = "sydney", max_results: int = 10) -> Dict:
    """Scrape Gumtree for competitive prices (ethical, throttled)"""
    base_url = "https://www.gumtree.com.au"
    search_url = f"{base_url}/s-{location}/{query.replace(' ', '-')}/k0"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Respectful delay
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        listings = []
        
        # Gumtree listing selectors (updated for current UI)
        tiles = soup.select('article[data-automation-id="item-card"]')
        
        for tile in tiles[:max_results]:
            try:
                # Title
                title_elem = tile.select_one('[data-automation-id="itemTitle"]')
                title = title_elem.get_text(strip=True) if title_elem else "No title"
                
                # Price
                price_elem = tile.select_one('[data-automation-id="itemPrice"]')
                price_text = price_elem.get_text(strip=True) if price_elem else ""
                price = extract_price(price_text)
                
                # Location
                location_elem = tile.select_one('[data-automation-id="itemArea"]')
                location_text = location_elem.get_text(strip=True) if location_elem else location
                
                if price > 0:
                    listings.append({
                        'title': title,
                        'price': round(price, 2),
                        'location': location_text,
                        'platform': 'Gumtree',
                        'url': base_url + tile.get('href', '') if tile.get('href') else None
                    })
                    
            except Exception as e:
                continue
        
        # Calculate stats
        prices = [l['price'] for l in listings]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        return {
            'prices': listings,
            'recommended': round(avg_price, 2),
            'stats': {
                'count': len(listings),
                'min': round(min_price, 2),
                'max': round(max_price, 2),
                'avg': round(avg_price, 2)
            }
        }
        
    except Exception as e:
        return {
            'prices': [],
            'recommended': 0,
            'error': f"Gumtree scrape failed: {str(e)}",
            'stats': {'count': 0}
        }

def extract_price(text: str) -> float:
    """Extract numeric price from text"""
    # Handle formats: $250, $200-$300, 250, etc.
    patterns = [
        r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d{1,3}(?:,\d{3})*)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                continue
    
    return 0.0
