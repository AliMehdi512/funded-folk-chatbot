from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uvicorn
from typing import Optional
import logging
import os
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Funded Folk RAG Chatbot API",
    description="Simplified API with OpenRouter integration",
    version="1.0.0"
)

# Add CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    session_id: Optional[str] = None
    status: str = "success"
    processing_time_ms: int = 0

class ErrorResponse(BaseModel):
    error: str
    status: str = "error"

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Funded Folk RAG Chatbot API",
        "status": "online",
        "version": "1.0.0",
        "models": "OpenRouter Integration"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "openai_key_configured": bool(OPENAI_API_KEY),
        "openrouter_key_configured": bool(OPENROUTER_API_KEY),
        "timestamp": time.time()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    start_time = time.time()
    
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenRouter API key not configured"
        )
    
    try:
        # Simple response generation using OpenRouter
        response = await generate_simple_response(request.message)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response=response,
            model_used="openai/gpt-3.5-turbo (OpenRouter)",
            session_id=request.session_id,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

async def generate_simple_response(message: str) -> str:
    """Generate response using OpenRouter"""
    
    # Funded Folk context
    funded_folk_context = """
    Funded Folk is a funded trading platform that provides:
    - Funded trading accounts
    - Challenge programs to prove trading skills
    - Multiple account sizes ($5K, $10K, $25K, $50K, $100K, $200K)
    - Support for MT4 and MT5 platforms
    - Profit sharing up to 90%
    - No time limits on challenges
    - Free retries on failed challenges
    """
    
    prompt = f"""You are Funded Folk's helpful support assistant. Answer the user's question about funded trading accounts in a concise, helpful manner.

Context about Funded Folk:
{funded_folk_context}

User Question: {message}

Please provide a helpful, accurate response. If you don't have specific information about something, say so rather than making things up."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return "I'm having trouble connecting to my knowledge base right now. Please try again in a moment."
            
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {e}")
        return "I'm experiencing technical difficulties. Please try again later."

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))) 