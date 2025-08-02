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

  // Generate response using RAG approach (without external API calls)
  async generateResponse(query) {
    const startTime = Date.now();
    
    // Search for relevant documents
    const relevantDocs = this.searchSimilarDocuments(query);
    
    // Build context from relevant documents
    let contextText = '';
    if (relevantDocs.length > 0) {
      contextText = relevantDocs.map((doc, i) => 
        `Example ${i + 1}:\nQ: ${doc.question}\nA: ${doc.answer}`
      ).join('\n\n');
    }
    
    // Create enhanced response using the best match
    let response = '';
    let modelUsed = 'rag-system';
    let complexity = 'simple';
    
    if (relevantDocs.length > 0) {
      const bestMatch = relevantDocs[0];
      
      // If we have a very good match, use it directly
      if (bestMatch.score >= 8) {
        response = bestMatch.answer;
        modelUsed = 'rag-system (exact match)';
      } else {
        // Create an enhanced response based on context
        response = this.generateEnhancedResponse(query, relevantDocs);
        modelUsed = 'rag-system (enhanced)';
      }
      
      complexity = this.classifyQueryComplexity(query);
    } else {
      // No relevant documents found
      response = this.generateFallbackResponse(query);
      modelUsed = 'rag-system (fallback)';
    }
    
    const processingTime = Date.now() - startTime;
    
    return {
      response: response,
      model_used: modelUsed,
      complexity: complexity,
      relevant_docs_count: relevantDocs.length,
      search_score: relevantDocs.length > 0 ? relevantDocs[0].score : 0,
      processing_time_ms: processingTime
    };
  }

  // Generate enhanced response based on multiple relevant documents
  generateEnhancedResponse(query, relevantDocs) {
    const baseAnswer = relevantDocs[0].answer;
    
    // Add additional context from other relevant documents
    let enhancedResponse = baseAnswer;
    
    if (relevantDocs.length > 1) {
      const additionalInfo = relevantDocs.slice(1).map(doc => doc.answer).join(' ');
      enhancedResponse += `\n\nAdditionally: ${additionalInfo}`;
    }
    
    return enhancedResponse;
  }

  // Generate fallback response when no relevant documents found
  generateFallbackResponse(query) {
    const fallbackResponses = [
      "I don't have specific information about that topic, but I can help you with questions about Funded Folk's funded trading accounts, challenge programs, platform support, pricing, and account management. Could you try asking about one of these topics?",
      "That's a great question! While I don't have specific details about that, I can help you with information about getting funded accounts, platform support, pricing, withdrawal processes, and technical issues. What would you like to know about?",
      "I'm not sure about that specific topic, but I'm here to help with Funded Folk related questions. You can ask me about account sizes, challenge programs, MT4/MT5 support, profit sharing, or any technical issues you might be experiencing."
    ];
    
    return fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
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
}

// Initialize RAG system
const ragSystem = new HybridRAGSystem();
console.log('✅ RAG System initialized with', ragSystem.documents.length, 'documents');

// Handle API requests
if (typeof window !== 'undefined') {
  // Browser environment - expose the RAG system
  window.FundedFolkRAG = {
    system: ragSystem,
    generateResponse: async (query) => {
      console.log('🔍 RAG System processing query:', query);
      return await ragSystem.generateResponse(query);
    },
    searchDocuments: (query, topK) => {
      return ragSystem.searchSimilarDocuments(query, topK);
    }
  };
  console.log('✅ FundedFolkRAG exposed to window object');
  
  // Test the RAG system
  setTimeout(() => {
    console.log('🧪 Testing RAG system...');
    ragSystem.generateResponse('How much does it cost?').then(result => {
      console.log('✅ RAG test successful:', result);
    }).catch(error => {
      console.error('❌ RAG test failed:', error);
    });
  }, 1000);
} else {
  console.log('❌ Not in browser environment');
} 