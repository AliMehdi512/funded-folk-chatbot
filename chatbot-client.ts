// TypeScript client for Funded Folk RAG Chatbot API

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  model_used: string;
  session_id?: string;
  status: string;
}

export interface EnhancedChatResponse extends ChatResponse {
  complexity: string;
  search_results_count: number;
  processing_time_ms: number;
}

export interface HealthResponse {
  status: string;
  rag_system_loaded: boolean;
  documents_count: number;
}

export interface ApiError {
  error: string;
  status: string;
}

export class FundedFolkChatbotClient {
  private baseUrl: string;
  private sessionId: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Send a message to the chatbot
   */
  async chat(message: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: this.sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat request failed:', error);
      throw error;
    }
  }

  /**
   * Send a message with detailed response information
   */
  async chatDetailed(message: string): Promise<EnhancedChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/detailed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: this.sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Detailed chat request failed:', error);
      throw error;
    }
  }

  /**
   * Check API health status
   */
  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * Get current session ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * Reset session (generate new session ID)
   */
  resetSession(): void {
    this.sessionId = this.generateSessionId();
  }
}

// Export a default instance
export const chatbotClient = new FundedFolkChatbotClient();

// Utility functions
export const formatResponse = (response: ChatResponse): string => {
  return response.response;
};

export const getModelInfo = (response: EnhancedChatResponse): string => {
  let modelName = '';
  if (response.model_used === 'llama-3.1-8b-instant') {
    modelName = 'Llama 3.1 8B';
  } else if (response.model_used === 'llama-3.3-70b-versatile') {
    modelName = 'Llama 3.3 70B';
  } else if (response.model_used === 'google/gemma-3n-e2b-it:free') {
    modelName = 'Gemma 3n 2B (Free, OpenRouter)';
  } else {
    modelName = response.model_used;
  }
  return `${modelName} (${response.complexity} query)`;
};

export const formatProcessingTime = (timeMs: number): string => {
  if (timeMs < 1000) {
    return `${timeMs}ms`;
  }
  return `${(timeMs / 1000).toFixed(1)}s`;
}; 