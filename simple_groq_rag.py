import os
import json
import requests
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "mixtral-8x7b-32768"

class SimpleGroqRAG:
    def __init__(self, json_file="merged.json"):
        """Initialize with conversation data"""
        self.conversations = self.load_conversations(json_file)
        print(f"✅ Loaded {len(self.conversations)} conversations")
    
    def load_conversations(self, file_path: str) -> List[Dict]:
        """Load and process conversation data from JSON"""
        print(f"📂 Loading conversations from {file_path}...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conversations = []
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
                conversations.append({
                    'id': i,
                    'question': user_content,
                    'answer': assistant_content
                })
        
        return conversations
    
    def search_relevant_conversations(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple keyword-based search for relevant conversations"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score conversations based on keyword overlap
        scored_conversations = []
        
        for conv in self.conversations:
            question_lower = conv['question'].lower()
            answer_lower = conv['answer'].lower()
            
            # Count keyword matches in question and answer
            question_words = set(question_lower.split())
            answer_words = set(answer_lower.split())
            
            question_score = len(query_words.intersection(question_words))
            answer_score = len(query_words.intersection(answer_words))
            
            # Weight question matches higher than answer matches
            total_score = question_score * 2 + answer_score
            
            if total_score > 0:
                scored_conversations.append((total_score, conv))
        
        # Sort by score and return top_k
        scored_conversations.sort(key=lambda x: x[0], reverse=True)
        return [conv for score, conv in scored_conversations[:top_k]]
    
    def generate_response(self, query: str, context_conversations: List[Dict]) -> str:
        """Generate response using Groq with conversation context"""
        
        # Format context from conversations
        context_text = ""
        for i, conv in enumerate(context_conversations, 1):
            context_text += f"Example {i}:\nQ: {conv['question']}\nA: {conv['answer']}\n\n"
        
        # Create prompt with context
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
        """Main chat function"""
        print("🔍 Searching for relevant conversations...")
        relevant_convs = self.search_relevant_conversations(query, top_k=3)
        
        if not relevant_convs:
            # If no relevant conversations found, use general context
            print("⚠️  No specific matches found, using general context...")
            relevant_convs = self.conversations[:3]  # Use first 3 as fallback
        
        print(f"✅ Found {len(relevant_convs)} relevant examples:")
        for i, conv in enumerate(relevant_convs, 1):
            print(f"   {i}. Q: {conv['question'][:60]}...")
        
        print("🧠 Generating response with Groq...")
        response = self.generate_response(query, relevant_convs)
        return response

def main():
    """Main function to run the chatbot"""
    # Check if data file exists
    if not os.path.exists("merged.json"):
        print("❌ Error: merged.json file not found!")
        print("Please make sure the merged.json file is in the current directory.")
        return
    
    # Check if Groq API key is set
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY not found in .env file!")
        print("Please add your Groq API key to the .env file.")
        return
    
    # Initialize the RAG system
    print("🚀 Initializing Simple Groq RAG System...")
    rag_system = SimpleGroqRAG()
    
    print("\n🤖 Funded Folk Simple RAG Chatbot Ready!")
    print("💡 Ask questions about Funded Folk's services, policies, and procedures.")
    print("🎯 No embeddings, no FAISS, no server hosting needed!")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("=" * 60)
    
    while True:
        user_input = input("\n🧑 You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("👋 Goodbye!")
            break
        
        if user_input.strip():
            response = rag_system.chat(user_input)
            print(f"\n🤖 Bot: {response}")
            print("-" * 60)
        else:
            print("Please enter a question.")

if __name__ == "__main__":
    main() 