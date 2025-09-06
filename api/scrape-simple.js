export default async function handler(req, res) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
  };

  // CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).set(corsHeaders).send('');
  }

  if (req.method !== 'POST') {
    return res.status(405).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ 
      error: 'Method not allowed' 
    });
  }

  // API key auth
  const apiKeyHeader = req.headers['x-api-key'];
  const expectedKey = process.env.SCRAPER_API_KEY || 'test-key';
  if (apiKeyHeader !== expectedKey) {
    return res.status(401).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ 
      error: 'Unauthorized' 
    });
  }

  try {
    const { url } = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    
    if (!url) {
      return res.status(400).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ 
        error: 'Missing url parameter' 
      });
    }

    // Mock response for testing
    const mockPlans = [
      {
        plan_name: "Basic",
        price: "$9/month",
        pricing_model: "Tiered",
        features: ["1 user", "Basic support"],
        billing_cycle: "monthly"
      },
      {
        plan_name: "Pro",
        price: "$29/month",
        pricing_model: "Tiered", 
        features: ["5 users", "Priority support", "Advanced features"],
        billing_cycle: "monthly"
      }
    ];

    return res.status(200).set({ 'Content-Type': 'application/json', ...corsHeaders }).json(mockPlans);

  } catch (err) {
    return res.status(500).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ 
      error: String(err.message || err) 
    });
  }
}