import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

def handler(request, context):
    # Handle CORS preflight
    if request.get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
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
    
    # API key authentication
    api_key_header = request.get('headers', {}).get('x-api-key')
    expected_key = context.get('SCRAPER_API_KEY', 'test-key')  # Default for testing
    if not api_key_header or api_key_header != expected_key:
        return {
            'statusCode': 401,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Unauthorized'})
        }
    
    try:
        # Parse request body
        body = request.get('body', '{}')
        if isinstance(body, str):
            data = json.loads(body)
        else:
            data = body
        
        url = data.get('url', '').strip()
        if not url:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing url parameter'})
            }
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract pricing plans
        plans = extract_pricing_plans(soup, url)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(plans)
        }
        
    except requests.RequestException as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Failed to fetch URL: {str(e)}'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Processing error: {str(e)}'})
        }

def extract_pricing_plans(soup, base_url):
    """Extract pricing plans from HTML using heuristics"""
    plans = []
    
    # Find potential pricing containers
    pricing_selectors = [
        '[class*="pricing" i]',
        '[class*="plan" i]',
        '[class*="tier" i]',
        '[class*="package" i]',
        '[class*="price" i]',
        '[id*="pricing" i]',
        '[id*="plan" i]'
    ]
    
    pricing_containers = []
    for selector in pricing_selectors:
        containers = soup.select(selector)
        pricing_containers.extend(containers)
    
    # Also look for common pricing patterns
    currency_regex = r'[\$€£¥]\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
    price_elements = soup.find_all(text=re.compile(currency_regex))
    
    for elem in price_elements:
        parent = elem.parent
        if parent:
            pricing_containers.append(parent)
    
    # Remove duplicates and get unique containers
    unique_containers = list(set(pricing_containers))
    
    # Extract plans from containers
    for container in unique_containers[:10]:  # Limit to avoid too many results
        plan = extract_plan_from_container(container)
        if plan and plan['price']:  # Only add if we found a price
            plans.append(plan)
    
    # Deduplicate plans
    seen_plans = set()
    unique_plans = []
    for plan in plans:
        plan_key = f"{plan['plan_name']}|{plan['price']}"
        if plan_key not in seen_plans:
            seen_plans.add(plan_key)
            unique_plans.append(plan)
    
    return unique_plans[:8]  # Return max 8 plans

def extract_plan_from_container(container):
    """Extract plan details from a container element"""
    text = container.get_text() if hasattr(container, 'get_text') else str(container)
    
    # Extract price
    price_regex = r'[\$€£¥]\s*\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{2})?(?:/\w+)?'
    price_match = re.search(price_regex, text)
    price = price_match.group(0) if price_match else ''
    
    # Handle special pricing
    if re.search(r'contact\s+(sales|us)|custom|enterprise', text, re.IGNORECASE):
        if not price:
            price = 'Contact Sales'
    elif re.search(r'\bfree\b', text, re.IGNORECASE) and not price:
        price = 'Free'
    
    # Extract plan name
    plan_name = ''
    if hasattr(container, 'find'):
        # Look for headings
        heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if heading:
            plan_name = heading.get_text().strip()
    
    if not plan_name:
        # Try common plan names
        plan_patterns = ['basic', 'starter', 'pro', 'premium', 'enterprise', 'business', 'free', 'plus']
        for pattern in plan_patterns:
            if re.search(rf'\b{pattern}\b', text, re.IGNORECASE):
                plan_name = pattern.title()
                break
    
    # Extract features
    features = []
    if hasattr(container, 'find_all'):
        # Look for list items
        li_elements = container.find_all('li')
        for li in li_elements[:10]:  # Limit features
            feature_text = li.get_text().strip()
            if feature_text and len(feature_text) < 100:
                features.append(feature_text)
    
    # Determine billing cycle
    billing_cycle = 'N/A'
    if re.search(r'/month|monthly|per month', text, re.IGNORECASE):
        billing_cycle = 'monthly'
    elif re.search(r'/year|yearly|annually|per year', text, re.IGNORECASE):
        billing_cycle = 'annually'
    elif re.search(r'per user|/user|per seat|/seat', text, re.IGNORECASE):
        billing_cycle = 'per user'
    
    # Determine pricing model
    pricing_model = 'Tiered'  # Default
    if re.search(r'contact\s+(sales|us)|custom|enterprise', text, re.IGNORECASE):
        pricing_model = 'Custom'
    elif re.search(r'per user|/user|per seat|/seat', text, re.IGNORECASE):
        pricing_model = 'Per-User'
    elif re.search(r'usage|pay as you go|api call|per request', text, re.IGNORECASE):
        pricing_model = 'Usage-Based'
    elif re.search(r'\bfree\b|\$0', text, re.IGNORECASE):
        pricing_model = 'Freemium'
    
    return {
        'plan_name': plan_name or 'Unknown Plan',
        'price': price,
        'pricing_model': pricing_model,
        'features': features,
        'billing_cycle': billing_cycle
    }