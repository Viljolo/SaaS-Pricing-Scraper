def handler(request, context=None):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': '{"message": "Simple test working!", "timestamp": "2025-01-05"}'
    }