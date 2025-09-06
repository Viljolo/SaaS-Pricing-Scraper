from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup
import re

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            url = data.get('url', 'https://stripe.com/pricing').strip()
            
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Scrape the page
            plans = self._scrape_pricing(url)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(plans).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {"error": str(e), "url": url if 'url' in locals() else 'unknown'}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_GET(self):
        # Default test with Stripe pricing
        try:
            plans = self._scrape_pricing('https://stripe.com/pricing')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(plans).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _scrape_pricing(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            plans = self._extract_pricing_plans(soup)
            
            return plans
            
        except Exception as e:
            return [{"error": f"Scraping failed: {str(e)}", "url": url}]
    
    def _extract_pricing_plans(self, soup):
        plans = []
        
        # Find elements that contain pricing information
        price_pattern = r'[\$€£¥]\s*\d{1,3}(?:[,\.]\d{3})*(?:[,\.]\d{2})?'
        
        # Look for common pricing selectors
        pricing_containers = soup.find_all(['div', 'section'], class_=re.compile(r'pric|plan|tier', re.I))
        
        for container in pricing_containers[:5]:  # Limit to 5 to avoid too many results
            text = container.get_text()
            
            # Check if this container has a price
            price_match = re.search(price_pattern, text)
            if price_match:
                price = price_match.group()
                
                # Extract plan name
                plan_name = "Unknown Plan"
                heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if heading:
                    plan_name = heading.get_text().strip()
                
                # Extract features
                features = []
                list_items = container.find_all('li')
                for li in list_items[:5]:  # Limit features
                    feature_text = li.get_text().strip()
                    if feature_text and len(feature_text) < 100:
                        features.append(feature_text)
                
                # Determine pricing model and billing cycle
                text_lower = text.lower()
                
                if 'contact' in text_lower or 'custom' in text_lower:
                    pricing_model = 'Custom'
                    if not price or price == price_match.group():
                        price = 'Contact Sales'
                elif 'per user' in text_lower or '/user' in text_lower:
                    pricing_model = 'Per-User'
                elif 'usage' in text_lower or 'api' in text_lower:
                    pricing_model = 'Usage-Based'
                elif 'free' in text_lower or price.startswith('$0'):
                    pricing_model = 'Freemium'
                else:
                    pricing_model = 'Tiered'
                
                billing_cycle = 'monthly'
                if 'year' in text_lower or 'annual' in text_lower:
                    billing_cycle = 'annually'
                elif 'per user' in text_lower:
                    billing_cycle = 'per user'
                
                plans.append({
                    "plan_name": plan_name,
                    "price": price,
                    "pricing_model": pricing_model,
                    "features": features,
                    "billing_cycle": billing_cycle
                })
        
        # If no plans found, return a default response
        if not plans:
            plans = [{
                "plan_name": "No Plans Found",
                "price": "Unable to extract pricing",
                "pricing_model": "Unknown",
                "features": ["Could not find pricing information on this page"],
                "billing_cycle": "N/A"
            }]
        
        return plans[:3]  # Return max 3 plans