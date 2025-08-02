// Funded Folk Chatbot API - Serverless Function for Firebase Hosting
// This file will be served as a static file but contains the RAG system

// Knowledge base with embedded documents
const KNOWLEDGE_BASE = [
  {
    id: 1,
    question: "How can I get funded account?",
    answer: "To get a funded account with Funded Folk, you need to complete a challenge program. Choose your account size ($5K-$200K), pass the challenge by meeting profit targets while following risk management rules, and then receive your funded account with up to 90% profit sharing.",
    combined_text: "Question: How can I get funded account?\nAnswer: To get a funded account with Funded Folk, you need to complete a challenge program. Choose your account size ($5K-$200K), pass the challenge by meeting profit targets while following risk management rules, and then receive your funded account with up to 90% profit sharing."
  },
  {
    id: 2,
    question: "What platforms do you support?",
    answer: "Funded Folk supports both MT4 and MT5 platforms. You can trade on either platform based on your preference. Both platforms are fully supported with all the same features and benefits.",
    combined_text: "Question: What platforms do you support?\nAnswer: Funded Folk supports both MT4 and MT5 platforms. You can trade on either platform based on your preference. Both platforms are fully supported with all the same features and benefits."
  },
  {
    id: 3,
    question: "How much does it cost?",
    answer: "Funded Folk offers various account sizes: $5K, $10K, $25K, $50K, $100K, and $200K. The cost varies by account size. You only pay for the challenge program, and once you pass, you get the funded account with no additional fees.",
    combined_text: "Question: How much does it cost?\nAnswer: Funded Folk offers various account sizes: $5K, $10K, $25K, $50K, $100K, and $200K. The cost varies by account size. You only pay for the challenge program, and once you pass, you get the funded account with no additional fees."
  },
  {
    id: 4,
    question: "What is the withdrawal process?",
    answer: "After you reach your profit target in the funded account, you can withdraw your profits. The withdrawal process is straightforward - you'll need to complete KYC verification first, then you can request withdrawals through the dashboard.",
    combined_text: "Question: What is the withdrawal process?\nAnswer: After you reach your profit target in the funded account, you can withdraw your profits. The withdrawal process is straightforward - you'll need to complete KYC verification first, then you can request withdrawals through the dashboard."
  },
  {
    id: 5,
    question: "Account activation after challenge completion",
    answer: "Once you complete the challenge successfully, your funded account will be activated within 24-48 hours. You'll receive login credentials for your MT4/MT5 account and can start trading with real money.",
    combined_text: "Question: Account activation after challenge completion\nAnswer: Once you complete the challenge successfully, your funded account will be activated within 24-48 hours. You'll receive login credentials for your MT4/MT5 account and can start trading with real money."
  },
  {
    id: 6,
    question: "Dashboard not updating trades",
    answer: "If your dashboard is not updating trades, please check your MT4/MT5 connection. Sometimes there can be a delay in trade synchronization. If the issue persists, contact support with your account details.",
    combined_text: "Question: Dashboard not updating trades\nAnswer: If your dashboard is not updating trades, please check your MT4/MT5 connection. Sometimes there can be a delay in trade synchronization. If the issue persists, contact support with your account details."
  },
  {
    id: 7,
    question: "MT5 login authorization error",
    answer: "If you're getting MT5 authorization errors, please verify your login credentials. Make sure you're using the correct server settings provided by Funded Folk. If the issue continues, contact support for assistance.",
    combined_text: "Question: MT5 login authorization error\nAnswer: If you're getting MT5 authorization errors, please verify your login credentials. Make sure you're using the correct server settings provided by Funded Folk. If the issue continues, contact support for assistance."
  },
  {
    id: 8,
    question: "Help with $50K account issue",
    answer: "For issues with your $50K account, please provide your account details and specific problem description. Our support team will help you resolve any technical or trading-related issues.",
    combined_text: "Question: Help with $50K account issue\nAnswer: For issues with your $50K account, please provide your account details and specific problem description. Our support team will help you resolve any technical or trading-related issues."
  },
  {
    id: 9,
    question: "Visa card payment method",
    answer: "Funded Folk accepts various payment methods including Visa cards. You can use your Visa card to pay for the challenge program. All payments are secure and processed through our trusted payment partners.",
    combined_text: "Question: Visa card payment method\nAnswer: Funded Folk accepts various payment methods including Visa cards. You can use your Visa card to pay for the challenge program. All payments are secure and processed through our trusted payment partners."
  },
  {
    id: 10,
    question: "KYC verification delay",
    answer: "KYC verification typically takes 24-48 hours. If it's been longer, please check that all documents are clear and complete. Contact support if you need assistance with the verification process.",
    combined_text: "Question: KYC verification delay\nAnswer: KYC verification typically takes 24-48 hours. If it's been longer, please check that all documents are clear and complete. Contact support if you need assistance with the verification process."
  }
];

class HybridRAGSystem {
  constructor() {
    this.documents = KNOWLEDGE_BASE;
    this.modelUsageTimes = {};
  }

  // Enhanced similarity search using keyword matching and semantic similarity
  searchSimilarDocuments(query, topK = 5) {
    const queryLower = query.toLowerCase();
    const queryWords = queryLower.split(' ').filter(word => word.length > 2);
    
    const scoredDocs = this.documents.map(doc => {
      const questionLower = doc.question.toLowerCase();
      const answerLower = doc.answer.toLowerCase();
      const combinedLower = doc.combined_text.toLowerCase();
      
      let score = 0;
      
      // Exact phrase matching (highest priority)
      if (questionLower.includes(queryLower)) score += 10;
      if (answerLower.includes(queryLower)) score += 8;
      if (combinedLower.includes(queryLower)) score += 6;
      
      // Word matching
      queryWords.forEach(word => {
        if (questionLower.includes(word)) score += 3;
        if (answerLower.includes(word)) score += 2;
        if (combinedLower.includes(word)) score += 1;
      });
      
      // Special keywords boost
      const specialKeywords = ['funded', 'account', 'challenge', 'profit', 'withdrawal', 'kyc', 'mt4', 'mt5', 'dashboard'];
      specialKeywords.forEach(keyword => {
        if (queryLower.includes(keyword) && combinedLower.includes(keyword)) {
          score += 2;
        }
      });
      
      return { ...doc, score };
    });
    
    return scoredDocs
      .filter(doc => doc.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  // Classify query complexity
  classifyQueryComplexity(query) {
    const complexKeywords = [
      'dashboard', 'equity', 'synchronization', 'authorization', 'verification',
      'withdrawal', 'profit', 'restriction', 'violation', 'technical', 'error',
      'login', 'connection', 'update', 'refresh'
    ];
    
    const queryLower = query.toLowerCase();
    const hasComplexKeywords = complexKeywords.some(keyword => 
      queryLower.includes(keyword)
    );
    
    return hasComplexKeywords ? 'complex' : 'simple';
  }

  // Check if model is available (rate limiting)
  isModelAvailable(model, cooldownSeconds = 300) {
    const now = Date.now();
    const lastUsed = this.modelUsageTimes[model] || 0;
    return (now - lastUsed) > (cooldownSeconds * 1000);
  }

  // Mark model as used
  markModelUsed(model) {
    this.modelUsageTimes[model] = Date.now();
  }

  // Generate response using hybrid approach
  async generateResponse(query, openRouterApiKey) {
    const startTime = Date.now();
    
    // Search for relevant documents
    const relevantDocs = this.searchSimilarDocuments(query);
    
    // Classify query complexity
    const complexity = this.classifyQueryComplexity(query);
    
    // Choose model based on complexity
    const model = complexity === 'complex' ? 'anthropic/claude-3.5-sonnet' : 'openai/gpt-3.5-turbo';
    
    // Check rate limiting
    if (!this.isModelAvailable(model)) {
      console.log(`⏳ Model ${model} is in cooldown, using fallback`);
      return this.generateFallbackResponse(query, relevantDocs);
    }
    
    // Build context from relevant documents
    let contextText = '';
    if (relevantDocs.length > 0) {
      contextText = relevantDocs.map((doc, i) => 
        `Example ${i + 1}:\nQ: ${doc.question}\nA: ${doc.answer}`
      ).join('\n\n');
    }
    
    // Create prompt with hybrid context
    const prompt = `You are Funded Folk's helpful support assistant. Answer the user's question about funded trading accounts in a concise, helpful manner.

### Funded Folk Information:
- Funded trading accounts ($5K, $10K, $25K, $50K, $100K, $200K)
- Challenge programs to prove trading skills
- Support for MT4 and MT5 platforms
- Profit sharing up to 90%
- No time limits on challenges
- Free retries on failed challenges
- KYC verification process
- Dashboard for tracking trades and equity
- Withdrawal process after profit targets

### Relevant Knowledge Base Examples:
${contextText}

### User Question:
${query}

### Response:
Please provide a helpful, accurate response based on the information above. If the user's question is similar to the examples, use that information. If you don't have specific information about something, say so rather than making things up. Keep your response concise and professional.`;

    const headers = {
      "Authorization": `Bearer ${openRouterApiKey}`,
      "Content-Type": "application/json"
    };
    
    const payload = {
      "model": model,
      "messages": [{"role": "user", "content": prompt}],
      "temperature": 0.3,
      "max_tokens": 400
    };
    
    try {
      const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: headers,
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        const result = await response.json();
        this.markModelUsed(model);
        
        const processingTime = Date.now() - startTime;
        
        return {
          response: result.choices[0].message.content,
          model_used: model,
          complexity: complexity,
          relevant_docs_count: relevantDocs.length,
          search_score: relevantDocs.length > 0 ? relevantDocs[0].score : 0,
          processing_time_ms: processingTime
        };
      } else {
        console.error(`OpenRouter API error: ${response.status} - ${await response.text()}`);
        return this.generateFallbackResponse(query, relevantDocs);
      }
      
    } catch (error) {
      console.error("Error calling OpenRouter API:", error);
      return this.generateFallbackResponse(query, relevantDocs);
    }
  }

  // Fallback response generation
  generateFallbackResponse(query, relevantDocs) {
    if (relevantDocs.length > 0) {
      const bestMatch = relevantDocs[0];
      return {
        response: bestMatch.answer,
        model_used: "fallback (best match)",
        complexity: "simple",
        relevant_docs_count: relevantDocs.length,
        search_score: bestMatch.score,
        processing_time_ms: 0
      };
    } else {
      return {
        response: "I'm sorry, I don't have specific information about that. Please contact Funded Folk support for assistance.",
        model_used: "fallback (no match)",
        complexity: "simple",
        relevant_docs_count: 0,
        search_score: 0,
        processing_time_ms: 0
      };
    }
  }
}

// Initialize RAG system
const ragSystem = new HybridRAGSystem();

// Handle API requests
if (typeof window !== 'undefined') {
  // Browser environment - expose the RAG system
  window.FundedFolkRAG = {
    system: ragSystem,
    generateResponse: async (query, apiKey) => {
      return await ragSystem.generateResponse(query, apiKey);
    },
    searchDocuments: (query, topK) => {
      return ragSystem.searchSimilarDocuments(query, topK);
    }
  };
} 