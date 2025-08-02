from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uvicorn
from typing import Optional
import logging

# Import our hybrid RAG system
from hybrid_rag_system import HybridRAGSystem, initialize_rag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Funded Folk RAG Chatbot API",
    description="Hybrid RAG system with OpenAI embeddings, FAISS search, and Groq models",
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

# Global RAG system instance
rag_system: Optional[HybridRAGSystem] = None

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    session_id: Optional[str] = None
    status: str = "success"

class ErrorResponse(BaseModel):
    error: str
    status: str = "error"

# Initialize RAG system on startup
@app.on_event("startup")
async def startup_event():
    global rag_system
    try:
        logger.info("🚀 Initializing Hybrid RAG System...")
        rag_system = initialize_rag()
        logger.info("✅ RAG System initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG system: {e}")
        raise e

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Funded Folk RAG Chatbot API",
        "status": "online",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    global rag_system
    return {
        "status": "healthy" if rag_system is not None else "unhealthy",
        "rag_system_loaded": rag_system is not None,
        "documents_count": len(rag_system.documents) if rag_system else 0
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    global rag_system
    
    if not rag_system:
        raise HTTPException(
            status_code=503, 
            detail="RAG system not initialized"
        )
    
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )
    
    try:
        # Process the query
        logger.info(f"Processing query: {request.message[:100]}...")
        
        # Get response from RAG system
        response = rag_system.chat(request.message)
        
        # Determine which model was used (extract from logs or implement tracking)
        model_used = "openrouter-free-models"  # Using only free OpenRouter models
        
        return ChatResponse(
            response=response,
            model_used=model_used,
            session_id=request.session_id,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat endpoint (for future enhancement)"""
    # For now, just return the regular response
    # Can be enhanced later for streaming responses
    return await chat_endpoint(request)

# Enhanced chat endpoint with model tracking
class EnhancedChatResponse(BaseModel):
    response: str
    model_used: str
    complexity: str
    search_results_count: int
    processing_time_ms: int
    session_id: Optional[str] = None
    status: str = "success"

@app.post("/chat/detailed", response_model=EnhancedChatResponse)
async def detailed_chat_endpoint(request: ChatRequest):
    """Enhanced chat endpoint with detailed response info"""
    global rag_system
    
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        import time
        start_time = time.time()
        
        # Classify query complexity
        complexity = rag_system._classify_query_complexity(request.message)
        
        # Get search results
        context_docs = rag_system.search_similar_documents(request.message, top_k=5)
        
        # Generate response
        response = rag_system.generate_response(request.message, context_docs)
        
        end_time = time.time()
        processing_time = int((end_time - start_time) * 1000)
        
        # Determine model used
        model_used = "openrouter-free-models"  # Using only free OpenRouter models
        
        return EnhancedChatResponse(
            response=response,
            model_used=model_used,
            complexity=complexity,
            search_results_count=len(context_docs),
            processing_time_ms=processing_time,
            session_id=request.session_id,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Error in detailed chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 