import os
import openai
import faiss
import pickle
import numpy as np
import requests
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMBED_MODEL = "text-embedding-3-small"
GROQ_MODEL = "mixtral-8x7b-32768"

class ServerlessRAG:
    def __init__(self):
        """Initialize the serverless RAG system"""
        self.index = None
        self.documents = None
        self._load_or_build_index()
    
    def _load_or_build_index(self):
        """Load existing index or build new one"""
        if os.path.exists("vector_index.faiss") and os.path.exists("documents.pkl"):
            print("📦 Loading existing FAISS index...")
            self.index = faiss.read_index("vector_index.faiss")
            with open("documents.pkl", "rb") as f:
                self.documents = pickle.load(f)
            print(f"✅ Loaded index with {len(self.documents)} documents")
        else:
            print("🚀 Building new FAISS index...")
            self._build_index_from_json()
    
    def _load_conversations(self, file_path="merged.json") -> List[Dict]:
        """Load and process conversation data from JSON"""
        print(f"📂 Loading conversations from {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for i, entry in enumerate(data):
            messages = entry.get('messages', [])
            
            user_content = ""
            assistant_content = ""
            
            for message in messages:
                if message['role'] == 'user':
                    user_content = message['content']
                elif message['role'] == 'assistant':
                    assistant_content = message['content']
            
            if user_content and assistant_content:
                document = {
                    'id': i,
                    'question': user_content,
                    'answer': assistant_content,
                    'combined_text': f"Question: {user_content}\nAnswer: {assistant_content}"
                }
                documents.append(document)
        
        print(f"✅ Processed {len(documents)} conversation pairs")
        return documents
    
    def _embed_text_batch(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """Generate embeddings in batches"""
        openai.api_key = OPENAI_API_KEY
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"🔄 Processing embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            try:
                response = openai.embeddings.create(
                    input=batch,
                    model=EMBED_MODEL
                )
                batch_embeddings = [d.embedding for d in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"❌ Error in batch {i//batch_size + 1}: {e}")
                raise e
        
        return np.array(all_embeddings)
    
    def _build_index_from_json(self, json_file="merged.json"):
        """Build FAISS index from conversation data"""
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"❌ {json_file} not found!")
        
        # Load conversations
        self.documents = self._load_conversations(json_file)
        
        # Extract text for embedding
        texts = [doc['combined_text'] for doc in self.documents]
        
        print("🧠 Generating embeddings with OpenAI...")
        embeddings = self._embed_text_batch(texts)
        
        # Build FAISS index
        print("🔍 Building FAISS index...")
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)
        
        # Save index and documents
        faiss.write_index(self.index, "vector_index.faiss")
        with open("documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)
        
        print(f"✅ Index built and saved with {len(self.documents)} documents")
    
    def _embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query"""
        openai.api_key = OPENAI_API_KEY
        response = openai.embeddings.create(
            input=[query],
            model=EMBED_MODEL
        )
        return np.array([response.data[0].embedding])
    
    def search_similar_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar documents using FAISS"""
        if self.index is None or self.documents is None:
            raise RuntimeError("❌ Index not loaded. Please initialize first.")
        
        # Generate query embedding
        query_embedding = self._embed_query(query)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Return relevant documents
        relevant_docs = []
        for idx in indices[0]:
            doc = self.documents[idx]
            relevant_docs.append({
                'question': doc['question'],
                'answer': doc['answer'],
                'combined_text': doc['combined_text']
            })
        
        return relevant_docs
    
    def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate response using Groq Mixtral"""
        # Format context
        context_text = ""
        for i, doc in enumerate(context_docs, 1):
            context_text += f"Example {i}:\nQ: {doc['question']}\nA: {doc['answer']}\n\n"
        
        prompt = f"""You are Funded Folk's helpful support assistant. Use the following examples from our support database to answer the user's question. Provide a helpful, accurate response based on the context provided.

### Context Examples:
{context_text}

### User Question:
{query}

### Response:"""

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 500,
            "top_p": 1
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions", 
                json=payload, 
                headers=headers
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            return f"Error generating response: {str(e)}"
    
    def chat(self, query: str) -> str:
        """Main chat function following the exact architecture"""
        print("🔍 Step 1: Embedding query with OpenAI...")
        
        print("🔍 Step 2: Searching FAISS index...")
        context_docs = self.search_similar_documents(query, top_k=3)
        
        print(f"✅ Step 3: Found {len(context_docs)} relevant documents:")
        for i, doc in enumerate(context_docs, 1):
            print(f"   {i}. Q: {doc['question'][:60]}...")
        
        print("🧠 Step 4: Generating response with Groq Mixtral...")
        response = self.generate_response(query, context_docs)
        
        return response

# === SERVERLESS FUNCTIONS ===
def initialize_rag() -> ServerlessRAG:
    """Initialize RAG system (call once)"""
    return ServerlessRAG()

def process_query(rag_system: ServerlessRAG, query: str) -> str:
    """Process a single query (stateless function)"""
    return rag_system.chat(query)

# === MAIN EXECUTION ===
def main():
    """Main function for local testing"""
    print("🚀 Initializing Serverless RAG System...")
    print("📋 Architecture: Query → OpenAI Embedding → FAISS Search → Groq Response")
    
    # Check requirements
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in .env file!")
        return
    
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in .env file!")
        return
    
    if not os.path.exists("merged.json"):
        print("❌ merged.json file not found!")
        return
    
    try:
        # Initialize RAG system
        rag_system = initialize_rag()
        
        print("\n🤖 Funded Folk Serverless RAG Chatbot Ready!")
        print("💡 Following exact architecture: OpenAI → FAISS → Groq")
        print("🎯 No server hosting required!")
        print("Type 'exit' or 'quit' to end the conversation.")
        print("=" * 60)
        
        while True:
            user_input = input("\n🧑 You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            
            if user_input.strip():
                response = process_query(rag_system, user_input)
                print(f"\n🤖 Bot: {response}")
                print("-" * 60)
            else:
                print("Please enter a question.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        if "insufficient_quota" in str(e):
            print("💡 Please add credits to your OpenAI account.")
            print("💰 Estimated cost for setup: ~$0.015 (1.5 cents)")

if __name__ == "__main__":
    main()

# === SERVERLESS DEPLOYMENT HELPERS ===
"""
For serverless deployment (Vercel, Netlify, AWS Lambda):

1. Pre-build the index:
   python serverless_rag.py  # Run once to build index

2. Deploy files:
   - serverless_rag.py
   - vector_index.faiss
   - documents.pkl
   - .env (with API keys)

3. Use these functions in your serverless handler:
   rag_system = initialize_rag()
   response = process_query(rag_system, user_query)
""" 