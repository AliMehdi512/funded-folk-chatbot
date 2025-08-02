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
GROQ_MODEL = "llama-3.3-70b-versatile"  # Updated to current available model

# Token limits
MAX_EMBEDDING_TOKENS = 8000  # Safe limit below 8192
MAX_CHARS_PER_CHUNK = 30000  # Rough estimate: ~7500 tokens

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
    
    def _chunk_long_text(self, text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> List[str]:
        """Split long text into smaller chunks"""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > max_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _load_conversations(self, file_path="merged.json") -> List[Dict]:
        """Load and process conversation data from JSON with chunking"""
        print(f"📂 Loading conversations from {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        chunk_id = 0
        
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
                combined_text = f"Question: {user_content}\nAnswer: {assistant_content}"
                
                # Check if text is too long and chunk if necessary
                if len(combined_text) > MAX_CHARS_PER_CHUNK:
                    print(f"⚠️  Long conversation found (ID {i}), chunking...")
                    chunks = self._chunk_long_text(combined_text)
                    
                    for chunk_idx, chunk in enumerate(chunks):
                        document = {
                            'id': chunk_id,
                            'original_id': i,
                            'chunk_index': chunk_idx,
                            'question': user_content if chunk_idx == 0 else f"[Continued] {user_content}",
                            'answer': chunk.split("Answer: ", 1)[-1] if "Answer: " in chunk else assistant_content,
                            'combined_text': chunk
                        }
                        documents.append(document)
                        chunk_id += 1
                else:
                    document = {
                        'id': chunk_id,
                        'original_id': i,
                        'chunk_index': 0,
                        'question': user_content,
                        'answer': assistant_content,
                        'combined_text': combined_text
                    }
                    documents.append(document)
                    chunk_id += 1
        
        print(f"✅ Processed {len(documents)} document chunks from {len(data)} conversations")
        return documents
    
    def _embed_text_batch(self, texts: List[str], batch_size: int = 50) -> np.ndarray:
        """Generate embeddings in smaller batches with length checking"""
        openai.api_key = OPENAI_API_KEY
        all_embeddings = []
        
        # Pre-filter texts that are too long
        processed_texts = []
        for text in texts:
            if len(text) > MAX_CHARS_PER_CHUNK:
                # Truncate if still too long
                text = text[:MAX_CHARS_PER_CHUNK] + "..."
            processed_texts.append(text)
        
        for i in range(0, len(processed_texts), batch_size):
            batch = processed_texts[i:i + batch_size]
            print(f"🔄 Processing embedding batch {i//batch_size + 1}/{(len(processed_texts) + batch_size - 1)//batch_size}")
            
            try:
                response = openai.embeddings.create(
                    input=batch,
                    model=EMBED_MODEL
                )
                batch_embeddings = [d.embedding for d in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"❌ Error in batch {i//batch_size + 1}: {e}")
                # Try individual texts in this batch
                print("🔄 Retrying individual texts...")
                for j, text in enumerate(batch):
                    try:
                        response = openai.embeddings.create(
                            input=[text],
                            model=EMBED_MODEL
                        )
                        all_embeddings.extend([response.data[0].embedding])
                    except Exception as individual_error:
                        print(f"❌ Failed on text {i+j}: {individual_error}")
                        # Use zero embedding as fallback
                        all_embeddings.append([0.0] * 1536)  # text-embedding-3-small dimension
        
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
        
        print(f"✅ Index built and saved with {len(self.documents)} document chunks")
    
    def _embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query"""
        openai.api_key = OPENAI_API_KEY
        
        # Truncate query if too long
        if len(query) > MAX_CHARS_PER_CHUNK:
            query = query[:MAX_CHARS_PER_CHUNK] + "..."
        
        response = openai.embeddings.create(
            input=[query],
            model=EMBED_MODEL
        )
        return np.array([response.data[0].embedding])
    
    def search_similar_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents using FAISS"""
        if self.index is None or self.documents is None:
            raise RuntimeError("❌ Index not loaded. Please initialize first.")
        
        # Generate query embedding
        query_embedding = self._embed_query(query)
        
        # Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Return relevant documents, avoiding duplicates from same conversation
        relevant_docs = []
        seen_original_ids = set()
        
        for idx in indices[0]:
            doc = self.documents[idx]
            original_id = doc.get('original_id', doc['id'])
            
            # Skip if we already have a chunk from this conversation
            if original_id in seen_original_ids:
                continue
                
            seen_original_ids.add(original_id)
            relevant_docs.append({
                'question': doc['question'],
                'answer': doc['answer'],
                'combined_text': doc['combined_text']
            })
            
            # Stop when we have enough unique conversations
            if len(relevant_docs) >= 3:
                break
        
        return relevant_docs
    
    def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate response using Groq Llama with better error handling"""
        # Format context - keep it concise to avoid token limits
        context_text = ""
        for i, doc in enumerate(context_docs, 1):
            # Truncate long answers to keep prompt manageable
            answer = doc['answer']
            if len(answer) > 500:
                answer = answer[:500] + "..."
            context_text += f"Example {i}:\nQ: {doc['question'][:200]}{'...' if len(doc['question']) > 200 else ''}\nA: {answer}\n\n"
        
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
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 500,
            "top_p": 1,
            "stream": False
        }

        try:
            print(f"🔍 Debug: Sending request to Groq with model: {payload['model']}")
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions", 
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            print(f"🔍 Debug: Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error response: {response.text}")
                return f"Error: Groq API returned status {response.status_code}. Please check your API key and try again."
            
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
            
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Error: Network issue - {str(e)}"
        except KeyError as e:
            return f"Error: Unexpected response format - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat(self, query: str) -> str:
        """Main chat function following the exact architecture"""
        print("🔍 Step 1: Embedding query with OpenAI...")
        
        print("🔍 Step 2: Searching FAISS index...")
        context_docs = self.search_similar_documents(query, top_k=5)
        
        print(f"✅ Step 3: Found {len(context_docs)} relevant documents:")
        for i, doc in enumerate(context_docs, 1):
            print(f"   {i}. Q: {doc['question'][:60]}...")
        
        print("🧠 Step 4: Generating response with Groq Llama...")
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
    print("🚀 Initializing Fixed Serverless RAG System...")
    print("📋 Architecture: Query → OpenAI Embedding → FAISS Search → Groq Response")
    print("🔧 Fixed: Handles long texts with proper chunking")
    print("🔄 Updated: Using Llama 3.3 70B (latest available model)")
    
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
        
        print("\n🤖 Funded Folk Fixed Serverless RAG Chatbot Ready!")
        print("💡 Following exact architecture: OpenAI → FAISS → Groq")
        print("🎯 No server hosting required!")
        print("🔧 Handles long conversations automatically!")
        print("🆕 Using Llama 3.3 70B Versatile (latest model)")
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