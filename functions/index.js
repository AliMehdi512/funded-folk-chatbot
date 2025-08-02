const functions = require('firebase-functions');
const cors = require('cors')({ origin: true });
const { HybridRAGSystem } = require('./rag-system');

// Initialize RAG system
const ragSystem = new HybridRAGSystem();

exports.chat = functions.https.onRequest((req, res) => {
  cors(req, res, async () => {
    const startTime = Date.now();
    
    try {
      // Handle CORS preflight
      if (req.method === 'OPTIONS') {
        res.status(200).send();
        return;
      }
      
      // Only allow POST requests
      if (req.method !== 'POST') {
        res.status(405).json({ error: 'Method not allowed' });
        return;
      }
      
      const { message, session_id } = req.body;
      
      if (!message || !message.trim()) {
        res.status(400).json({ error: "Message cannot be empty" });
        return;
      }
      
      const OPENROUTER_API_KEY = functions.config().openrouter.key;
      
      if (!OPENROUTER_API_KEY) {
        res.status(503).json({ error: "OpenRouter API key not configured" });
        return;
      }
      
      // Generate response using RAG system
      const result = await ragSystem.generateResponse(message, OPENROUTER_API_KEY);
      
      res.json({
        response: result.response,
        model_used: result.model_used,
        session_id: session_id,
        status: "success",
        processing_time_ms: result.processing_time_ms,
        complexity: result.complexity,
        relevant_docs_count: result.relevant_docs_count,
        search_score: result.search_score
      });
      
    } catch (error) {
      console.error('Error processing chat:', error);
      res.status(500).json({ error: `Internal server error: ${error.message}` });
    }
  });
});

exports.health = functions.https.onRequest((req, res) => {
  cors(req, res, () => {
    res.json({
      message: "Funded Folk RAG Chatbot API",
      status: "online",
      version: "1.0.0",
      models: "OpenRouter Integration with RAG",
      documents_loaded: ragSystem.documents.length,
      timestamp: Date.now()
    });
  });
});

// Remove the old generateResponse function as it's now handled by the RAG system 