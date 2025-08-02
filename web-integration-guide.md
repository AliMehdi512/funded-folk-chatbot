# 🌐 Web Integration Guide: Funded Folk RAG Chatbot

Complete guide to integrate your hybrid RAG chatbot with JavaScript/TypeScript websites.

## 🚀 Quick Setup

### 1. **Start the API Server**

```bash
# Install API dependencies
pip install -r requirements_api.txt

# Start the FastAPI server
python api_server.py
```

Server will run at: `http://localhost:8000`

### 2. **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/chat` | POST | Basic chat endpoint |
| `/chat/detailed` | POST | Enhanced chat with model info |

### 3. **Frontend Integration Options**

## 🎯 **Option A: React/TypeScript (Recommended)**

### Install Dependencies
```bash
npm install react @types/react
# If using Tailwind CSS
npm install tailwindcss
```

### Usage
```tsx
import ChatbotWidget from './ChatbotWidget';

function App() {
  return (
    <div className="App">
      {/* Your existing content */}
      
      {/* Add the chatbot widget */}
      <ChatbotWidget 
        apiUrl="http://localhost:8000"
        showModelInfo={true}
        showProcessingTime={true}
        theme="light"
      />
    </div>
  );
}
```

## 🎯 **Option B: Vanilla JavaScript**

### Basic Implementation
```html
<!DOCTYPE html>
<html>
<head>
    <title>Funded Folk Chatbot</title>
    <style>
        /* Add your styles here */
        .chatbot-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        /* More styles... */
    </style>
</head>
<body>
    <div id="chatbot-container"></div>
    
    <script>
        class FundedFolkChatbot {
            constructor(apiUrl = 'http://localhost:8000') {
                this.apiUrl = apiUrl;
                this.sessionId = this.generateSessionId();
                this.init();
            }
            
            generateSessionId() {
                return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            }
            
            async chat(message) {
                const response = await fetch(`${this.apiUrl}/chat`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: this.sessionId
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                return await response.json();
            }
            
            init() {
                // Initialize your chatbot UI here
                console.log('Chatbot initialized');
            }
        }
        
        // Initialize the chatbot
        const chatbot = new FundedFolkChatbot();
    </script>
</body>
</html>
```

## 🎯 **Option C: Vue.js**

```vue
<template>
  <div class="chatbot-widget">
    <!-- Chatbot UI -->
    <div v-if="isOpen" class="chat-container">
      <div class="messages">
        <div 
          v-for="message in messages" 
          :key="message.id"
          :class="['message', message.isUser ? 'user' : 'bot']"
        >
          {{ message.text }}
        </div>
      </div>
      <div class="input-area">
        <input 
          v-model="inputValue"
          @keyup.enter="sendMessage"
          placeholder="Type your message..."
        />
        <button @click="sendMessage" :disabled="isLoading">Send</button>
      </div>
    </div>
    <button v-else @click="isOpen = true" class="chat-button">💬</button>
  </div>
</template>

<script>
export default {
  name: 'ChatbotWidget',
  props: {
    apiUrl: {
      type: String,
      default: 'http://localhost:8000'
    }
  },
  data() {
    return {
      isOpen: false,
      messages: [],
      inputValue: '',
      isLoading: false,
      sessionId: this.generateSessionId()
    };
  },
  methods: {
    generateSessionId() {
      return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },
    
    async sendMessage() {
      if (!this.inputValue.trim() || this.isLoading) return;
      
      const userMessage = {
        id: Date.now(),
        text: this.inputValue,
        isUser: true
      };
      
      this.messages.push(userMessage);
      const message = this.inputValue;
      this.inputValue = '';
      this.isLoading = true;
      
      try {
        const response = await fetch(`${this.apiUrl}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: message,
            session_id: this.sessionId
          })
        });
        
        const data = await response.json();
        
        this.messages.push({
          id: Date.now() + 1,
          text: data.response,
          isUser: false
        });
      } catch (error) {
        this.messages.push({
          id: Date.now() + 1,
          text: 'Sorry, there was an error processing your request.',
          isUser: false
        });
      } finally {
        this.isLoading = false;
      }
    }
  }
};
</script>
```

## 🎯 **Option D: Next.js**

```tsx
// pages/api/chat.ts (API route)
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body)
    });

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    res.status(500).json({ message: 'Internal server error' });
  }
}
```

```tsx
// components/Chatbot.tsx
import { useState } from 'react';

export default function Chatbot() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
      });
      
      const data = await res.json();
      setResponse(data.response);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot">
      <input 
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask me anything..."
      />
      <button onClick={sendMessage} disabled={loading}>
        {loading ? 'Sending...' : 'Send'}
      </button>
      {response && <div className="response">{response}</div>}
    </div>
  );
}
```

## 🔧 **Configuration Options**

### API Client Configuration
```typescript
const client = new FundedFolkChatbotClient({
  baseUrl: 'http://localhost:8000',  // Your API URL
  timeout: 30000,                    // Request timeout
  retries: 3                         // Number of retries
});
```

### Widget Configuration
```tsx
<ChatbotWidget 
  apiUrl="http://localhost:8000"
  showModelInfo={true}           // Show which model was used
  showProcessingTime={true}      // Show response time
  theme="light"                  // 'light' or 'dark'
  maxMessages={100}              // Max messages to keep in history
  placeholder="Ask me anything..." // Input placeholder
  title="Funded Folk Support"   // Widget title
/>
```

## 🚀 **Production Deployment**

### 1. **API Server Deployment**
```bash
# Using Gunicorn (recommended for production)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_server:app --bind 0.0.0.0:8000

# Or using Docker
# Create Dockerfile and deploy to your preferred platform
```

### 2. **Environment Variables**
```bash
# .env file
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 3. **Security Considerations**
- Configure CORS properly for production
- Add rate limiting
- Implement authentication if needed
- Use HTTPS in production
- Validate and sanitize inputs

## 💰 **Cost Monitoring**

The API includes detailed response information:

```json
{
  "response": "Your answer here",
  "model_used": "llama-3.1-8b-instant",
  "complexity": "simple",
  "search_results_count": 3,
  "processing_time_ms": 1250,
  "status": "success"
}
```

Track costs by monitoring:
- `model_used`: Which model was selected
- `complexity`: Query complexity classification
- `processing_time_ms`: Response time

## 🎉 **Ready to Go!**

Your hybrid RAG chatbot is now ready for web integration with:
- ✅ **$74.75/month** cost optimization
- ✅ **Automatic model selection** (8B vs 70B)
- ✅ **Modern TypeScript/React components**
- ✅ **RESTful API** for any frontend framework
- ✅ **Production-ready** FastAPI backend

Start with the React component for the best experience, or use the vanilla JavaScript approach for simple integrations! 