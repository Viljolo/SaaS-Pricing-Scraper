import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def handler(request, context):
    # Handle CORS preflight
    if request.get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, x-api-key:'
            },
            'body': ''
        }
    
    if request.get('method') != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request body
        body = request.get('body', '{}')
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = body
        
        urls_text = data.get('urls', '').strip()
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if not urls:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No domains provided'})
            }
        
        # Limit to 2 domains for serverless function
        urls = urls[:2]
        
        results = []
        for url in urls:
            try:
                # Add protocol if missing
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Simple scraping
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=8)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract basic pricing info
                pricing_data = {
                    'url': url,
                    'plan_name': '',
                    'price': '',
                    'billing_period': '',
                    'features': [],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Look for price patterns
                text = soup.get_text()
                price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', text)
                if price_match:
                    pricing_data['price'] = price_match.group()
                
                # Look for plan names
                plan_patterns = ['basic', 'starter', 'pro', 'premium', 'enterprise']
                for pattern in plan_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        pricing_data['plan_name'] = pattern.title()
                        break
                
                results.append(pricing_data)
                
            except Exception as e:
                results.append({
                    'url': url,
                    'plan_name': '',
                    'price': '',
                    'billing_period': '',
                    'features': [],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'error': str(e)
                })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Scraped {len(results)} urls',
                'results': results,
                'total': len(results)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
