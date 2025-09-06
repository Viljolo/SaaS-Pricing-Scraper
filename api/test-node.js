module.exports = async (req, res) => {
  // Simple test function
  if (req.method === 'OPTIONS') {
    return res.status(200).set({
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    }).send('');
  }

  return res.status(200).set({
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
  }).json({
    message: 'Node.js endpoint working!',
    method: req.method,
    url: req.url
  });
};