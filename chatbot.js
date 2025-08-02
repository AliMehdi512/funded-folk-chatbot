// TypeScript-style JavaScript for Funded Folk Chatbot
class FundedFolkChatbot {
    constructor() {
        // Use production API URL or fallback to localhost for development
        this.apiUrl = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://your-api-domain.com';
        this.isLoading = false;
        this.sessionId = this.generateSessionId();
        
        // DOM elements
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.charCount = document.getElementById('charCount');
        this.status = document.getElementById('status');
        
        this.initializeEventListeners();
        this.updateCharCount();
    }

    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Character count
        this.messageInput.addEventListener('input', () => this.updateCharCount());

        // Suggestion buttons
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.target.dataset.query;
                this.messageInput.value = query;
                this.updateCharCount();
                this.sendMessage();
            });
        });
    }

    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = `${count}/500`;
        
        if (count > 450) {
            this.charCount.style.color = '#e74c3c';
        } else if (count > 400) {
            this.charCount.style.color = '#f39c12';
        } else {
            this.charCount.style.color = '#666';
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isLoading) {
            return;
        }

        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        this.updateCharCount();

        // Show typing indicator
        this.showTypingIndicator();
        this.setLoading(true);

        try {
            const response = await this.callChatAPI(message);
            this.hideTypingIndicator();
            
            if (response.status === 'success') {
                this.addMessage(response.response, 'bot', {
                    modelUsed: response.model_used,
                    processingTime: response.processing_time_ms,
                    relevantDocsCount: response.relevant_docs_count,
                    searchScore: response.search_score
                });
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Chat API error:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I\'m having trouble connecting. Please check your internet connection and try again.', 'bot');
            this.setStatus('Error: ' + error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async callChatAPI(message) {
        console.log('🔍 Checking for RAG system...', window.FundedFolkRAG ? 'Found' : 'Not found');
        
        // Use the RAG system directly in the browser
        if (window.FundedFolkRAG) {
            try {
                console.log('🚀 Using RAG system for query:', message);
                const result = await window.FundedFolkRAG.generateResponse(message);
                console.log('✅ RAG system result:', result);
                
                return {
                    response: result.response,
                    model_used: result.model_used,
                    status: 'success',
                    processing_time_ms: result.processing_time_ms,
                    complexity: result.complexity,
                    relevant_docs_count: result.relevant_docs_count,
                    search_score: result.search_score
                };
            } catch (error) {
                console.error('❌ RAG system error:', error);
                return {
                    response: "I'm having trouble processing your request. Please try again.",
                    model_used: "rag-system (error)",
                    status: 'error',
                    processing_time_ms: 0,
                    complexity: "simple",
                    relevant_docs_count: 0,
                    search_score: 0
                };
            }
        } else {
            console.log('⚠️ RAG system not available, using fallback');
            // Fallback to API call if RAG system not available
            const response = await fetch(`${this.apiUrl}/chat/detailed`, {
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
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        }
    }

    addMessage(text, sender, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Convert markdown-style formatting to HTML for bot messages
        if (sender === 'bot') {
            contentDiv.innerHTML = this.formatResponse(text);
        } else {
            contentDiv.textContent = text;
        }

        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';

        const timestamp = document.createElement('span');
        timestamp.className = 'timestamp';
        timestamp.textContent = this.getCurrentTime();

        metaDiv.appendChild(timestamp);

        // Add metadata if available
        if (metadata.modelUsed) {
            const modelInfo = document.createElement('div');
            modelInfo.className = 'model-info';
            modelInfo.textContent = `Model: ${this.formatModelName(metadata.modelUsed)}`;
            metaDiv.appendChild(modelInfo);
        }

        if (metadata.processingTime) {
            const timeInfo = document.createElement('div');
            timeInfo.className = 'time-info';
            timeInfo.textContent = `Response time: ${this.formatTime(metadata.processingTime)}`;
            metaDiv.appendChild(timeInfo);
        }

        // Add RAG information if available
        if (metadata.relevantDocsCount !== undefined) {
            const ragInfo = document.createElement('div');
            ragInfo.className = 'rag-info';
            ragInfo.textContent = `RAG: ${metadata.relevantDocsCount} relevant docs (score: ${metadata.searchScore || 0})`;
            metaDiv.appendChild(ragInfo);
        }

        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(metaDiv);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot-message typing-indicator-message';
        typingDiv.id = 'typingIndicator';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'typing-indicator';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            contentDiv.appendChild(dot);
        }

        typingDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.messageInput.disabled = loading;
        this.sendButton.disabled = loading;
        
        if (loading) {
            this.setStatus('Typing...', 'typing');
        } else {
            this.setStatus('Ready', '');
        }
    }

    setStatus(text, className) {
        this.status.textContent = text;
        this.status.className = `status ${className}`;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    formatModelName(modelName) {
        const modelMap = {
            'llama-3.1-8b-instant': 'Llama 3.1 8B (Fast)',
            'llama-3.3-70b-versatile': 'Llama 3.3 70B (Smart)',
            'hybrid': 'Hybrid Selection'
        };
        return modelMap[modelName] || modelName;
    }

    formatTime(milliseconds) {
        if (milliseconds < 1000) {
            return `${milliseconds}ms`;
        }
        return `${(milliseconds / 1000).toFixed(1)}s`;
    }

    formatResponse(text) {
        // Convert markdown-style formatting to HTML
        return text
            // Bold text: **text** -> <strong>text</strong>
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic text: *text* -> <em>text</em>
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Headers: ### Header -> <h3>Header</h3>
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Bullet points: - item -> <li>item</li>
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            // Numbered lists: 1. item -> <li>item</li>
            .replace(/^\d+\. (.*$)/gm, '<li>$1</li>')
            // Convert consecutive <li> elements to <ul> or <ol>
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Clean up multiple <br> tags
            .replace(/<br><br>/g, '</p><p>')
            // Wrap in paragraphs
            .replace(/^(.*)$/gm, '<p>$1</p>')
            // Clean up empty paragraphs
            .replace(/<p><\/p>/g, '')
            // Clean up paragraph wrapping around headers
            .replace(/<p>(<h[1-3]>.*<\/h[1-3]>)<\/p>/g, '$1');
    }

    // Health check method
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            if (response.ok) {
                const data = await response.json();
                console.log('API Health:', data);
                return data.status === 'healthy';
            }
        } catch (error) {
            console.error('Health check failed:', error);
        }
        return false;
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const chatbot = new FundedFolkChatbot();
    
    // Check API health on startup
    chatbot.checkHealth().then(isHealthy => {
        if (!isHealthy) {
            chatbot.setStatus('API not available', 'error');
        }
    });

    // Make chatbot globally available for debugging
    window.chatbot = chatbot;
});

// Add some utility functions for debugging
window.chatbotUtils = {
    testAPI: async () => {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'test' })
        });
        return await response.json();
    },
    
    checkHealth: async () => {
        const response = await fetch('http://localhost:8000/health');
        return await response.json();
    }
}; 