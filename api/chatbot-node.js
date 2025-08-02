export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  const { query } = req.body;
  if (!query) {
    return res.status(400).json({ error: "Missing 'query' in request body." });
  }
  // TODO: Proxy to Python backend or implement logic here
  // For now, return a placeholder
  return res.status(200).json({ answer: `You asked: ${query}. (Node.js placeholder response)` });
} 