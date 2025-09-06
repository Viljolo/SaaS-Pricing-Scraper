from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._send_response()
        
    def do_POST(self):
        self._send_response()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-api-key')
        self.end_headers()
        
    def _send_response(self):
        try:
            # Simple mock response for testing
            mock_plans = [
                {
                    "plan_name": "Basic",
                    "price": "$9/month",
                    "pricing_model": "Tiered",
                    "features": ["1 user", "Basic support", "5GB storage"],
                    "billing_cycle": "monthly"
                },
                {
                    "plan_name": "Pro",
                    "price": "$29/month",
                    "pricing_model": "Tiered", 
                    "features": ["5 users", "Priority support", "50GB storage"],
                    "billing_cycle": "monthly"
                },
                {
                    "plan_name": "Enterprise",
                    "price": "Contact Sales",
                    "pricing_model": "Custom",
                    "features": ["Unlimited users", "24/7 support", "Custom integration"],
                    "billing_cycle": "N/A"
                }
            ]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(mock_plans).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())