import os
import openai
import faiss
import pickle
import numpy as np
import requests
import json
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMBED_MODEL = "text-embedding-3-small"
GROQ_MODEL = "mixtral-8x7b-32768"

# === STEP 1: Load and Process JSON Data ===
def load_and_process_json(file_path="merged.json") -> List[Dict]:
    """Load merged.json and create document chunks from conversations"""
    print(f"Loading data from {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    
    for i, entry in enumerate(data):
        messages = entry.get('messages', [])
        
        # Extract user question and assistant response
        user_content = ""
        assistant_content = ""
        
        for message in messages:
            if message['role'] == 'user':
                user_content = message['content']
            elif message['role'] == 'assistant':
                assistant_content = message['content']
        
        # Create a document chunk combining question and answer
        if user_content and assistant_content:
            document = {
                'id': i,
                'question': user_content,
                'answer': assistant_content,
                'combined_text': f"Question: {user_content}\nAnswer: {assistant_content}"
            }
            documents.append(document)
    
    print(f"Processed {len(documents)} conversation pairs from {len(data)} entries")
    return documents

# === STEP 2: Embed text chunks ===
def embed_text(texts: List[str]) -> np.ndarray:
    """Generate embeddings using OpenAI's text-embedding-3-small model"""
    openai.api_key = OPENAI_API_KEY
    
    # Process in batches to handle large datasets
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"Processing embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        response = openai.embeddings.create(
            input=batch,
            model=EMBED_MODEL
        )
        batch_embeddings = [d.embedding for d in response.data]
        all_embeddings.extend(batch_embeddings)
    
    return np.array(all_embeddings)

# === STEP 3: Build / Load Vector Index ===
def build_faiss_index_from_json(json_file="merged.json", save_path="vector_index.faiss"):
    """Build FAISS index from JSON conversation data"""
    # Load and process the JSON data
    documents = load_and_process_json(json_file)
    
    # Extract text for embedding (using combined question + answer)
    texts = [doc['combined_text'] for doc in documents]
    
    print("Generating embeddings...")
    embeddings = embed_text(texts)
    
    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    
    # Save index and documents
    faiss.write_index(index, save_path)
    with open("documents.pkl", "wb") as f:
        pickle.dump(documents, f)
    
    print(f"Index built and saved with {len(documents)} documents.")
    return index, documents

def load_index():
    """Load FAISS index and documents from disk"""
    index = faiss.read_index("vector_index.faiss")
    with open("documents.pkl", "rb") as f:
        documents = pickle.load(f)
    return index, documents

# === STEP 4: Perform Similarity Search ===
def search_index(query: str, top_k=3):
    """Search for most similar documents to the query"""
    query_emb = embed_text([query])[0].reshape(1, -1)
    index, documents = load_index()
    distances, indices = index.search(query_emb, top_k)
    
    # Return the relevant document information
    relevant_docs = []
    for i in indices[0]:
        doc = documents[i]
        relevant_docs.append({
            'question': doc['question'],
            'answer': doc['answer'],
            'combined_text': doc['combined_text']
        })
    
    return relevant_docs

# === STEP 5: LLM Response from GROQ ===
def generate_response(context_docs: List[Dict], query: str) -> str:
    """Generate response using Groq Mixtral model with retrieved context"""
    
    # Format context from retrieved documents
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
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 500,
        "top_p": 1
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        return f"Error generating response: {str(e)}"

# === MAIN CHAT FUNCTION ===
def chat(query: str):
    """Main chat function that combines search and generation"""
    print("🔍 Searching for relevant context...")
    context_docs = search_index(query, top_k=3)
    
    print(f"✅ Found {len(context_docs)} relevant examples")
    for i, doc in enumerate(context_docs, 1):
        print(f"   {i}. Q: {doc['question'][:60]}...")
    
    print("🧠 Generating response...")
    answer = generate_response(context_docs, query)
    return answer

# === INITIALIZATION ===
def initialize_from_json():
    """Initialize the RAG system from merged.json file"""
    if not os.path.exists("merged.json"):
        print("❌ Error: merged.json file not found!")
        print("Please make sure the merged.json file is in the current directory.")
        return False
    
    print("🚀 Initializing RAG system from merged.json...")
    build_faiss_index_from_json()
    print("✅ RAG system initialized successfully!")
    return True

# === RUN CHAT ===
if __name__ == "__main__":
    # Check if index exists, if not build from JSON
    if not os.path.exists("vector_index.faiss") or not os.path.exists("documents.pkl"):
        print("📊 No existing index found. Building from merged.json...")
        if not initialize_from_json():
            exit(1)
    
    print("\n🤖 Funded Folk RAG Chatbot Ready!")
    print("💡 Ask questions about Funded Folk's services, policies, and procedures.")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("=" * 60)
    
    while True:
        user_input = input("\n🧑 You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("👋 Goodbye!")
            break
        
        if user_input.strip():
            response = chat(user_input)
            print(f"\n🤖 Bot: {response}")
            print("-" * 60)
        else:
            print("Please enter a question.") 