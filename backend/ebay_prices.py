import requests
import os
from typing import Dict, List

def get_ebay_prices(query: str, app_id: str = None) -> Dict:
    """Get eBay prices using Finding API (Sandbox for POC)"""
    if not app_id:
        app_id = os.getenv('EBAY_APP_ID')
    
    if not app_id:
        return {
            'prices': [],
            'recommended': 0,
            'error': 'eBay App ID not configured',
            'stats': {'count': 0}
        }
    
    url = "https://svcs.ebay.com/services/search/FindingService/v1"
    params = {
        'OPERATION-NAME': 'findItemsByKeywords',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': app_id,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': query,
        'itemFilter(0).name': 'ListingType',
        'itemFilter(0).value': 'FixedPrice,Auction',
        'itemFilter(1).name': 'Condition',
        'itemFilter(1).value': 'Used,New',
        'paginationInput.entriesPerPage': 10,
        'sortOrder': 'BestMatch'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        listings = []
        search_result = data.get('findItemsByKeywordsResponse', [{}])[0]
        items = search_result.get('searchResult', [{}])[0].get('item', [])
        
        for item in items[:10]:
            try:
                title = item.get('title', 'No title')
                price_value = item['sellingStatus'][0]['currentPrice'][0]['__value__']
                price = float(price_value)
                
                listings.append({
                    'title': title[:80] + '...' if len(title) > 80 else title,
                    'price': round(price, 2),
                    'location': item.get('location', {}).get('country', 'Unknown'),
                    'platform': 'eBay',
                    'url': item.get('viewItemURL', '')
                })
            except (KeyError, ValueError, IndexError):
                continue
        
        prices = [l['price'] for l in listings]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        return {
            'prices': listings,
            'recommended': round(avg_price, 2),
            'stats': {
                'count': len(listings),
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0,
                'avg': round(avg_price, 2)
            }
        }
        
    except Exception as e:
        return {
            'prices': [],
            'recommended': 0,
            'error': f"eBay API failed: {str(e)}",
            'stats': {'count': 0}
        }
