import json

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
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(mock_plans)
    }