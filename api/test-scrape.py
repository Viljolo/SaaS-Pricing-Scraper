import json

def handler(request, context=None):
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
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(mock_plans)
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