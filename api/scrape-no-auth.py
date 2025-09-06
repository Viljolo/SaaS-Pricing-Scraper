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
        
        # Enhanced price patterns for different currencies and formats
        price_patterns = [
            r'[\$€£¥₹₽¢₩₦₪₵₴₸₺₫₱₡₲₵₼₾₿]\s*\d{1,3}(?:[,\.\s]\d{3})*(?:[,\.]\d{2})?',  # With currency symbols
            r'\d{1,3}(?:[,\.\s]\d{3})*(?:[,\.]\d{2})?\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|CNY|INR|BRL|KRW|RUB)',  # With currency codes
            r'\d+[,\.]?\d*\s*(?:dollar|euro|pound|yen|franc|peso|rupee|yuan|won|ruble)s?',  # Written currencies
            r'\d+[,\.]?\d*\s*/\s*(?:month|year|user|seat|license|subscription)',  # Price per unit
        ]
        
        # Multi-language keywords for different pricing elements
        pricing_keywords = {
            'plan': ['plan', 'tier', 'package', 'subscription', 'paquet', 'plan', 'paquete', 'piano', 'plano', 'tarifa', 'paket', 'プラン', 'योजना', 'план', '계획', '方案'],
            'pricing': ['pricing', 'price', 'cost', 'tarif', 'prix', 'precio', 'prezzo', 'preço', 'preis', '価格', 'मूल्य', 'цена', '가격', '价格'],
            'free': ['free', 'gratuit', 'gratis', 'gratuito', 'kostenlos', '無料', 'मुफ्त', 'бесплатно', '무료', '免费'],
            'contact': ['contact', 'kontakt', 'contacter', 'contactar', 'contattare', 'entrar em contato', '連絡', 'संपर्क', 'связаться', '연락', '联系'],
            'custom': ['custom', 'enterprise', 'personnalisé', 'personalizado', 'personalizzato', 'personalizado', 'maßgeschneidert', 'カスタム', 'कस्टम', 'настроить', '맞춤', '定制'],
            'monthly': ['month', 'monthly', 'mois', 'mensual', 'mese', 'mensal', 'monat', 'monatlich', '月', 'महीना', 'месяц', '월', '月'],
            'yearly': ['year', 'yearly', 'annual', 'an', 'anual', 'anno', 'jahr', 'jährlich', '年', 'साल', 'год', '년', '年'],
            'user': ['user', 'utilisateur', 'usuario', 'utente', 'usuário', 'benutzer', 'ユーザー', 'उपयोगकर्ता', 'пользователь', '사용자', '用户']
        }
        
        # Enhanced selectors for CMS systems like HubSpot
        pricing_selectors = [
            # Standard selectors
            '[class*="pric" i]', '[class*="plan" i]', '[class*="tier" i]', '[class*="package" i]',
            '[id*="pric" i]', '[id*="plan" i]', '[id*="tier" i]',
            # HubSpot specific
            '[class*="hs-" i]', '[data-hs-*]', '.hs-cta-wrapper', '.hs-form',
            # WordPress/CMS
            '[class*="wp-" i]', '[class*="elementor" i]', '[class*="divi" i]',
            # Common CMS patterns
            '[class*="card" i]', '[class*="column" i]', '[class*="grid" i]',
            '[data-testid*="pric" i]', '[data-testid*="plan" i]'
        ]
        
        pricing_containers = []
        
        # Find containers using multiple approaches
        for selector in pricing_selectors:
            containers = soup.select(selector)
            pricing_containers.extend(containers)
        
        # Also find elements containing prices directly
        combined_price_pattern = '|'.join(price_patterns)
        price_elements = soup.find_all(text=re.compile(combined_price_pattern, re.I))
        
        for elem in price_elements:
            # Get parent containers
            parent = elem.parent
            for _ in range(3):  # Go up 3 levels to find card containers
                if parent:
                    pricing_containers.append(parent)
                    parent = parent.parent
        
        # Remove duplicates
        unique_containers = list({id(container): container for container in pricing_containers}.values())
        
        for container in unique_containers[:8]:  # Process more containers
            plan = self._extract_plan_from_container(container, pricing_keywords, price_patterns)
            if plan and (plan['price'] or plan['plan_name'] != 'Unknown Plan'):
                plans.append(plan)
        
        # If no plans found, try a different approach - look for structured data
        if not plans:
            plans = self._extract_structured_data(soup)
        
        # Remove duplicates based on plan name + price
        seen = set()
        unique_plans = []
        for plan in plans:
            key = f"{plan['plan_name'].lower()}|{plan['price'].lower()}"
            if key not in seen:
                seen.add(key)
                unique_plans.append(plan)
        
        return unique_plans[:6]  # Return max 6 plans
    
    def _extract_plan_from_container(self, container, pricing_keywords, price_patterns):
        try:
            text = container.get_text() if hasattr(container, 'get_text') else str(container)
            text_lower = text.lower()
            
            # Extract price with enhanced patterns
            price = self._extract_price(text, price_patterns)
            
            # Extract plan name with multi-language support
            plan_name = self._extract_plan_name(container, text, pricing_keywords)
            
            # Extract features
            features = self._extract_features(container)
            
            # Determine pricing model (language-agnostic)
            pricing_model = self._determine_pricing_model(text_lower, pricing_keywords, price)
            
            # Determine billing cycle (language-agnostic)
            billing_cycle = self._determine_billing_cycle(text_lower, pricing_keywords)
            
            return {
                "plan_name": plan_name,
                "price": price,
                "pricing_model": pricing_model,
                "features": features,
                "billing_cycle": billing_cycle
            }
            
        except Exception as e:
            return None
    
    def _extract_price(self, text, price_patterns):
        combined_pattern = '|'.join(price_patterns)
        price_match = re.search(combined_pattern, text, re.I)
        
        if price_match:
            return price_match.group().strip()
        
        # Handle "free" in multiple languages
        free_patterns = [
            r'\b(?:free|gratuit|gratis|gratuito|kostenlos|無料|मुफ्त|бесплатно|무료|免费)\b',
            r'\$0\b', r'€0\b', r'£0\b'
        ]
        
        for pattern in free_patterns:
            if re.search(pattern, text, re.I):
                return 'Free'
        
        # Handle "contact sales" in multiple languages  
        contact_patterns = [
            r'contact\s+(?:sales|us)',
            r'(?:kontakt|contacter|contactar|contattare)',
            r'(?:custom|enterprise|personnalisé|personalizado)',
            r'(?:request\s+quote|demander\s+devis)'
        ]
        
        for pattern in contact_patterns:
            if re.search(pattern, text, re.I):
                return 'Contact Sales'
        
        return ''
    
    def _extract_plan_name(self, container, text, pricing_keywords):
        if hasattr(container, 'find'):
            # Look for headings
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                heading = container.find(tag)
                if heading:
                    name = heading.get_text().strip()
                    if name and len(name) < 50:
                        return name
        
        # Look for common plan names in multiple languages
        common_plans = [
            'basic', 'basique', 'básico', 'base', 'grund',
            'starter', 'démarrage', 'iniciador', 'avviamento',
            'pro', 'professionnel', 'profesional', 'professionale',
            'premium', 'prémium', 'premium', 'premium',
            'enterprise', 'entreprise', 'empresa', 'enterprise',
            'business', 'affaires', 'negocio', 'business',
            'free', 'gratuit', 'gratis', 'gratuito'
        ]
        
        text_words = text.lower().split()
        for plan in common_plans:
            if plan in text_words:
                return plan.title()
        
        return 'Unknown Plan'
    
    def _extract_features(self, container):
        features = []
        if hasattr(container, 'find_all'):
            # Look for list items
            list_items = container.find_all('li')
            for li in list_items[:8]:
                feature_text = li.get_text().strip()
                if feature_text and len(feature_text) < 150 and len(feature_text) > 3:
                    features.append(feature_text)
        
        # Also look for div/p elements that might contain features
        if len(features) < 3 and hasattr(container, 'find_all'):
            feature_divs = container.find_all(['div', 'p'], class_=re.compile(r'feature|benefit|include', re.I))
            for div in feature_divs[:5]:
                feature_text = div.get_text().strip()
                if feature_text and len(feature_text) < 150 and len(feature_text) > 3:
                    features.append(feature_text)
        
        return features
    
    def _determine_pricing_model(self, text_lower, pricing_keywords, price):
        # Check for custom/enterprise (multilingual)
        custom_terms = pricing_keywords['custom'] + pricing_keywords['contact']
        if any(term in text_lower for term in custom_terms) or price == 'Contact Sales':
            return 'Custom'
        
        # Check for per-user (multilingual)
        user_terms = pricing_keywords['user']
        if any(f'/{term}' in text_lower or f'per {term}' in text_lower for term in user_terms):
            return 'Per-User'
        
        # Check for usage-based
        usage_terms = ['usage', 'api', 'request', 'transaction', 'volume', 'utilisation', 'uso', 'utilizzo']
        if any(term in text_lower for term in usage_terms):
            return 'Usage-Based'
        
        # Check for free/freemium (multilingual)
        free_terms = pricing_keywords['free']
        if any(term in text_lower for term in free_terms) or price == 'Free':
            return 'Freemium'
        
        return 'Tiered'
    
    def _determine_billing_cycle(self, text_lower, pricing_keywords):
        # Check for yearly/annual (multilingual)
        yearly_terms = pricing_keywords['yearly']
        if any(term in text_lower for term in yearly_terms):
            return 'annually'
        
        # Check for monthly (multilingual)
        monthly_terms = pricing_keywords['monthly']
        if any(term in text_lower for term in monthly_terms):
            return 'monthly'
        
        # Check for per user
        user_terms = pricing_keywords['user']
        if any(f'/{term}' in text_lower or f'per {term}' in text_lower for term in user_terms):
            return 'per user'
        
        return 'N/A'
    
    def _extract_structured_data(self, soup):
        """Try to extract from JSON-LD or other structured data"""
        plans = []
        
        # Look for JSON-LD structured data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    # Schema.org Product with offers
                    offers = data.get('offers', [])
                    if not isinstance(offers, list):
                        offers = [offers]
                    
                    for offer in offers:
                        plan = {
                            'plan_name': offer.get('name', 'Unknown Plan'),
                            'price': f"{offer.get('price', '')} {offer.get('priceCurrency', '')}".strip(),
                            'pricing_model': 'Tiered',
                            'features': [],
                            'billing_cycle': 'N/A'
                        }
                        plans.append(plan)
            except:
                continue
        
        return plans