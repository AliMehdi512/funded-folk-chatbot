// Configuration for Funded Folk Chatbot
const config = {
    // API Configuration
    api: {
        // Development API URL
        development: 'http://localhost:5001/prac-22736/us-central1/chat',
        // Production API URL - Firebase Functions with RAG
        production: 'https://us-central1-prac-22736.cloudfunctions.net/chat',
        // Auto-detect environment
        get url() {
            return window.location.hostname === 'localhost' ? this.development : this.production;
        }
    },
    
    // AI Models Configuration
    models: {
        // OpenRouter models for different complexity levels
        simple: 'openai/gpt-3.5-turbo',
        complex: 'anthropic/claude-3.5-sonnet',
        fallback: 'mistralai/mistral-7b-instruct:free'
    },
    
    // Chat Configuration
    chat: {
        maxMessageLength: 500,
        typingIndicatorDelay: 1000,
        retryAttempts: 3,
        retryDelay: 2000
    },
    
    // UI Configuration
    ui: {
        theme: {
            primary: '#667eea',
            secondary: '#764ba2',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        },
        animations: {
            enabled: true,
            duration: 300
        }
    },
    
    // Feature Flags
    features: {
        debugMode: window.location.hostname === 'localhost',
        healthCheck: true,
        sessionTracking: true,
        errorReporting: true
    }
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
} else {
    window.config = config;
} 