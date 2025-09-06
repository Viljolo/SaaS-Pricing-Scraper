from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Simple test working!",
            "timestamp": "2025-01-05",
            "method": "GET"
        }
        
        self.wfile.write(json.dumps(response).encode())
        
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Simple test working!",
            "timestamp": "2025-01-05", 
            "method": "POST"
        }
        
        self.wfile.write(json.dumps(response).encode())