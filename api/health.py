from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'API is running'})

# Export for Vercel
app.debug = False

# Vercel serverless function handler
def handler(request, context):
    return app(request, context)
