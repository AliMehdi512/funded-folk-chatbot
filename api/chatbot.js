// Funded Folk Chatbot API - JavaScript Version for Vercel
import { NextResponse } from 'next/server';

// Funded Folk context
const FUNDED_FOLK_CONTEXT = `
Funded Folk is a funded trading platform that provides:
- Funded trading accounts
- Challenge programs to prove trading skills
- Multiple account sizes ($5K, $10K, $25K, $50K, $100K, $200K)
- Support for MT4 and MT5 platforms
- Profit sharing up to 90%
- No time limits on challenges
- Free retries on failed challenges
`;

// Environment variables
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

export async function POST(request) {
  const startTime = Date.now();
  
  try {
    const { message, session_id } = await request.json();
    
    if (!message || !message.trim()) {
      return NextResponse.json(
        { error: "Message cannot be empty" },
        { status: 400 }
      );
    }
    
    if (!OPENROUTER_API_KEY) {
      return NextResponse.json(
        { error: "OpenRouter API key not configured" },
        { status: 503 }
      );
    }
    
    // Generate response using OpenRouter
    const response = await generateResponse(message);
    
    const processingTime = Date.now() - startTime;
    
    return NextResponse.json({
      response: response,
      model_used: "openai/gpt-3.5-turbo (OpenRouter)",
      session_id: session_id,
      status: "success",
      processing_time_ms: processingTime
    });
    
  } catch (error) {
    console.error('Error processing chat:', error);
    return NextResponse.json(
      { error: `Internal server error: ${error.message}` },
      { status: 500 }
    );
  }
}

async function generateResponse(message) {
  const prompt = `You are Funded Folk's helpful support assistant. Answer the user's question about funded trading accounts in a concise, helpful manner.

Context about Funded Folk:
${FUNDED_FOLK_CONTEXT}

User Question: ${message}

Please provide a helpful, accurate response. If you don't have specific information about something, say so rather than making things up.`;

  const headers = {
    "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
    "Content-Type": "application/json"
  };
  
  const payload = {
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_tokens": 500
  };
  
  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload)
    });
    
    if (response.ok) {
      const result = await response.json();
      return result.choices[0].message.content;
    } else {
      console.error(`OpenRouter API error: ${response.status} - ${await response.text()}`);
      return "I'm having trouble connecting to my knowledge base right now. Please try again in a moment.";
    }
    
  } catch (error) {
    console.error("Error calling OpenRouter API:", error);
    return "I'm experiencing technical difficulties. Please try again later.";
  }
}

// Health check endpoint
export async function GET() {
  return NextResponse.json({
    message: "Funded Folk RAG Chatbot API",
    status: "online",
    version: "1.0.0",
    models: "OpenRouter Integration",
    openai_key_configured: !!OPENAI_API_KEY,
    openrouter_key_configured: !!OPENROUTER_API_KEY,
    timestamp: Date.now()
  });
} 