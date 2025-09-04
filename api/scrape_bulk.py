from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import csv
from io import StringIO

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Try to parse as JSON first
            try:
                data = json.loads(post_data.decode('utf-8'))
                domains_text = data.get('domains', '').strip()
                domains = [domain.strip() for domain in domains_text.split('\n') if domain.strip()]
            except:
                # If not JSON, try to parse as form data
                domains = []
                try:
                    # Simple form data parsing
                    form_data = post_data.decode('utf-8')
                    if 'domains=' in form_data:
                        domains_part = form_data.split('domains=')[1]
                        if '&' in domains_part:
                            domains_part = domains_part.split('&')[0]
                        domains = [domain.strip() for domain in domains_part.split('\n') if domain.strip()]
                except:
                    pass
            
            if not domains:
                self.send_error_response('No domains provided')
                return
            
            # Limit to 3 domains for serverless function
            domains = domains[:3]
            
            # Scrape domains
            results = []
            for domain in domains:
                result = self.scrape_website(domain)
                if result['success']:
                    results.append(result['data'])
                else:
                    results.append({
                        'url': domain,
                        'plan_name': '',
                        'price': '',
                        'billing_period': '',
                        'features': [],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'error': result['error']
                    })
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'message': f'Scraped {len(results)} domains',
                'results': results,
                'total': len(results)
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_error_response(self, error_message):
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'error': error_message
        }
        
        self.wfile.write(json.dumps(response).encode())
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def extract_pricing_info(self, soup, url):
        """Extract pricing information from a webpage"""
        pricing_data = {
            'url': url,
            'plan_name': '',
            'price': '',
            'billing_period': '',
            'features': [],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Common pricing selectors
        pricing_selectors = [
            '.pricing', '.price', '.plan', '.subscription',
            '[class*="pricing"]', '[class*="price"]', '[class*="plan"]',
            '[id*="pricing"]', '[id*="price"]', '[id*="plan"]'
        ]
        
        # Find pricing elements
        pricing_elements = []
        for selector in pricing_selectors:
            elements = soup.select(selector)
            pricing_elements.extend(elements)
        
        # Extract information from pricing elements
        for element in pricing_elements[:3]:  # Limit to first 3 elements
            text = self.clean_text(element.get_text())
            
            # Extract price
            price_patterns = [
                r'\$[\d,]+(?:\.\d{2})?',
                r'[\d,]+(?:\.\d{2})?\s*(?:USD|dollars?|per\s+month|per\s+year)',
                r'[\d,]+(?:\.\d{2})?\s*(?:monthly|yearly|annual)'
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, text, re.IGNORECASE)
                if price_match and not pricing_data['price']:
                    pricing_data['price'] = price_match.group()
                    break
            
            # Extract plan name
            if not pricing_data['plan_name']:
                plan_patterns = [
                    r'(basic|starter|pro|premium|enterprise|business|personal)',
                    r'(free|trial|demo)',
                    r'(monthly|yearly|annual|quarterly)'
                ]
                
                for pattern in plan_patterns:
                    plan_match = re.search(pattern, text, re.IGNORECASE)
                    if plan_match:
                        pricing_data['plan_name'] = plan_match.group().title()
                        break
            
            # Extract billing period
            if not pricing_data['billing_period']:
                period_patterns = [
                    r'(monthly|per\s+month)',
                    r'(yearly|annual|per\s+year)',
                    r'(quarterly|per\s+quarter)',
                    r'(weekly|per\s+week)'
                ]
                
                for pattern in period_patterns:
                    period_match = re.search(pattern, text, re.IGNORECASE)
                    if period_match:
                        pricing_data['billing_period'] = period_match.group()
                        break
            
            # Extract features
            feature_elements = element.find_all(['li', 'p', 'span', 'div'])
            for feature_elem in feature_elements[:5]:  # Limit features
                feature_text = self.clean_text(feature_elem.get_text())
                if feature_text and len(feature_text) > 3 and len(feature_text) < 100:
                    if feature_text not in pricing_data['features']:
                        pricing_data['features'].append(feature_text)
        
        # If no specific pricing found, try to extract general pricing info
        if not pricing_data['price']:
            body_text = soup.get_text()
            price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', body_text)
            if price_match:
                pricing_data['price'] = price_match.group()
        
        return pricing_data
    
    def scrape_website(self, url):
        """Scrape a single website for pricing information"""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=8)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pricing_data = self.extract_pricing_info(soup, url)
            
            return {
                'success': True,
                'data': pricing_data,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
