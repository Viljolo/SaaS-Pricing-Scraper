from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime
import csv
from io import StringIO
import threading
import time

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variable to store scraping results
scraping_results = []
scraping_in_progress = False

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def extract_pricing_info(soup, url):
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
    for element in pricing_elements[:5]:  # Limit to first 5 elements
        text = clean_text(element.get_text())
        
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
            # Look for common plan name patterns
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
        for feature_elem in feature_elements[:10]:  # Limit features
            feature_text = clean_text(feature_elem.get_text())
            if feature_text and len(feature_text) > 3 and len(feature_text) < 200:
                if feature_text not in pricing_data['features']:
                    pricing_data['features'].append(feature_text)
    
    # If no specific pricing found, try to extract general pricing info
    if not pricing_data['price']:
        body_text = soup.get_text()
        price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', body_text)
        if price_match:
            pricing_data['price'] = price_match.group()
    
    return pricing_data

def scrape_website(url):
    """Scrape a single website for pricing information"""
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        pricing_data = extract_pricing_info(soup, url)
        
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

@app.route('/')
def index():
    return jsonify({'message': 'SaaS Pricing Scraper API', 'status': 'running', 'version': '1.0.0'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/scrape_single', methods=['POST'])
def scrape_single():
    data = request.get_json()
    domain = data.get('domain', '').strip()
    
    if not domain:
        return jsonify({'error': 'Please provide a domain'}), 400
    
    result = scrape_website(domain)
    return jsonify(result)

@app.route('/api/scrape_bulk', methods=['POST'])
def scrape_bulk():
    global scraping_results, scraping_in_progress
    
    if scraping_in_progress:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    scraping_in_progress = True
    scraping_results = []
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Please upload a CSV file'}), 400
        
        # Read CSV file
        try:
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.reader(StringIO(csv_content))
            domains = [row[0].strip() for row in csv_reader if row and row[0].strip()]
        except Exception as e:
            scraping_in_progress = False
            return jsonify({'error': f'Error reading CSV file: {str(e)}'}), 400
    
    else:
        # Get domains from text input
        try:
            data = request.get_json()
            if data:
                domains_text = data.get('domains', '').strip()
                domains = [domain.strip() for domain in domains_text.split('\n') if domain.strip()]
            else:
                domains = []
        except:
            domains = []
    
    if not domains:
        scraping_in_progress = False
        return jsonify({'error': 'No domains provided'}), 400
    
    def scrape_domains():
        global scraping_results, scraping_in_progress
        
        for i, domain in enumerate(domains):
            if not scraping_in_progress:
                break
                
            result = scrape_website(domain)
            if result['success']:
                scraping_results.append(result['data'])
            else:
                scraping_results.append({
                    'url': domain,
                    'plan_name': '',
                    'price': '',
                    'billing_period': '',
                    'features': [],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'error': result['error']
                })
            
            # Add small delay to be respectful
            time.sleep(1)
        
        scraping_in_progress = False
    
    # Start scraping in background thread
    thread = threading.Thread(target=scrape_domains)
    thread.start()
    
    return jsonify({'message': f'Started scraping {len(domains)} domains'})

@app.route('/api/get_results')
def get_results():
    global scraping_results, scraping_in_progress
    
    return jsonify({
        'results': scraping_results,
        'in_progress': scraping_in_progress,
        'total': len(scraping_results)
    })

@app.route('/api/stop_scraping')
def stop_scraping():
    global scraping_in_progress
    scraping_in_progress = False
    return jsonify({'message': 'Scraping stopped'})

@app.route('/api/download_csv')
def download_csv():
    global scraping_results
    
    if not scraping_results:
        return jsonify({'error': 'No data to download'}), 400
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['URL', 'Plan Name', 'Price', 'Billing Period', 'Features', 'Timestamp', 'Error'])
    
    # Write data
    for result in scraping_results:
        features = '; '.join(result.get('features', []))
        writer.writerow([
            result.get('url', ''),
            result.get('plan_name', ''),
            result.get('price', ''),
            result.get('billing_period', ''),
            features,
            result.get('timestamp', ''),
            result.get('error', '')
        ])
    
    output.seek(0)
    
    return send_file(
        StringIO(output.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'pricing_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

# For Vercel deployment
if __name__ == '__main__':
    app.run(debug=True)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Export for Vercel
app.debug = False
