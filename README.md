# 🤖 Funded Folk RAG Chatbot

A minimal RAG (Retrieval-Augmented Generation) chatbot built specifically for Funded Folk customer support using:

- 🔎 **OpenAI text-embedding-3-small** for embeddings
- 🧠 **Groq Mixtral 8x7B Instruct** for response generation  
- 💽 **FAISS** for vector search (in-memory, no cloud/db needed)
- 🧩 **Fully cost-optimized**: < $100/month for 500k queries

## 📋 Prerequisites

1. **OpenAI API Key** - for generating embeddings
2. **Groq API Key** - for LLM responses
3. **Python 3.8+**
4. **merged.json file** - your conversation dataset

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the project root:
```bash
# OpenAI API Key for embeddings
OPENAI_API_KEY=sk-your-openai-key-here

# Groq API Key for LLM responses
GROQ_API_KEY=your-groq-key-here
```

### 3. Prepare Your Data
Make sure your `merged.json` file is in the project root directory. The expected format:
```json
[
  {
    "messages": [
      {
        "role": "system",
        "content": "You are Funded Folk's helpful support assistant."
      },
      {
        "role": "user", 
        "content": "User question here"
      },
      {
        "role": "assistant",
        "content": "Assistant response here"
      }
    ]
  }
]
```

### 4. Run the Chatbot
```bash
python rag_chatbot.py
```

On first run, the system will:
1. Load and process your `merged.json` file (6,069 conversations)
2. Generate embeddings for all conversations (batched for efficiency)
3. Build and save the FAISS index
4. Start the interactive chat interface

## 💡 How It Works

### Architecture Flow
```
User Query
   │
   ▼
[Embedding via OpenAI]
   │
   ▼
[Vector Search via FAISS]
   │
   ▼
[Top-k context chunks]
   │
   ▼
[Prompt → Groq Mixtral]
   │
   ▼
LLM Response
```

### Data Processing
- Each conversation pair (user question + assistant answer) becomes a document chunk
- Documents are embedded using OpenAI's `text-embedding-3-small` model
- FAISS index enables fast similarity search over all 6,069+ conversations
- Retrieved context is formatted as examples for the LLM

### Cost Optimization
- **Embeddings**: ~$0.00002/1K tokens (very cheap for one-time indexing)
- **Groq**: ~$0.0002/1K tokens (much cheaper than OpenAI GPT models)
- **FAISS**: Local, in-memory - no ongoing costs
- **Total**: Well under $100/month for 500k queries

## 🎯 Usage Examples

```
🧑 You: What platforms do you support?
🤖 Bot: We are live on MT4 and MT5 platforms.

🧑 You: Can I use a copy of my ID for KYC?
🤖 Bot: For KYC verification, we cannot accept photocopies, scans, or copies of identification documents. You need to upload a clear and valid original government-issued CNIC or passport...

🧑 You: How do I get the real challenge after passing the test?
🤖 Bot: Thank you for your patience. Our team is working to assist all valued traders with their real challenge access...
```

## 📁 File Structure

```
grok/
├── rag_chatbot.py          # Main chatbot application
├── merged.json             # Your conversation dataset
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .env                   # API keys (create this)
├── vector_index.faiss     # Generated FAISS index
└── documents.pkl          # Processed documents cache
```

## 🔧 Customization

### Adjust Search Parameters
```python
# In search_index() function
context_docs = search_index(query, top_k=5)  # Get more examples
```

### Modify Response Length
```python
# In generate_response() function
"max_tokens": 800,  # Longer responses
```

### Change Embedding Batch Size
```python
# In embed_text() function
batch_size = 50  # Smaller batches if you hit rate limits
```

## 🚨 Troubleshooting

### "merged.json file not found"
- Ensure `merged.json` is in the same directory as `rag_chatbot.py`

### API Key Errors
- Verify your `.env` file has correct API keys
- Check OpenAI and Groq account credits

### Memory Issues
- Large datasets may require more RAM during initial embedding
- Consider processing in smaller batches if needed

### Rate Limits
- OpenAI: 3,000 RPM on embedding endpoint
- Groq: Very high limits, rarely an issue

## 📊 Performance

- **Initial Setup**: ~5-10 minutes (one-time embedding generation)
- **Query Response**: ~1-3 seconds per query
- **Memory Usage**: ~500MB for 6K documents
- **Accuracy**: High relevance due to domain-specific training data

## 🎉 Ready to Chat!

Your Funded Folk RAG chatbot is now ready to answer customer questions with context from your entire support conversation history! 