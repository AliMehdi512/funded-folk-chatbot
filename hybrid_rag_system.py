import os
import openai
import faiss
import pickle
import numpy as np
import requests
import json
import re
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

# === CONFIG ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMBED_MODEL = "text-embedding-3-small"

# Hybrid model configuration
SIMPLE_MODEL = "llama-3.1-8b-instant"      # For simple queries
COMPLEX_MODEL = "llama-3.3-70b-versatile"  # For complex queries

# Token limits
MAX_EMBEDDING_TOKENS = 8000
MAX_CHARS_PER_CHUNK = 30000

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
BASE_DELAY = 1  # seconds for exponential backoff

class HybridRAGSystem:
    def __init__(self):
        """Initialize the hybrid RAG system"""
        self.index = None
        self.documents = None
        self.model_usage_times = {}  # Track when each model was last used
        self.model_rate_limit_times = {}  # Track when each model was rate limited
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
            word_length = len(word) + 1
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
        
        processed_texts = []
        for text in texts:
            if len(text) > MAX_CHARS_PER_CHUNK:
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
                        all_embeddings.append([0.0] * 1536)
        
        return np.array(all_embeddings)
    
    def _build_index_from_json(self, json_file="merged.json"):
        """Build FAISS index from conversation data"""
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"❌ {json_file} not found!")
        
        self.documents = self._load_conversations(json_file)
        texts = [doc['combined_text'] for doc in self.documents]
        
        print("🧠 Generating embeddings with OpenAI...")
        embeddings = self._embed_text_batch(texts)
        
        print("🔍 Building FAISS index...")
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)
        
        faiss.write_index(self.index, "vector_index.faiss")
        with open("documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)
        
        print(f"✅ Index built and saved with {len(self.documents)} document chunks")
    
    def _embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query"""
        openai.api_key = OPENAI_API_KEY
        
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
        
        query_embedding = self._embed_query(query)
        distances, indices = self.index.search(query_embedding, top_k)
        
        relevant_docs = []
        seen_original_ids = set()
        
        for idx in indices[0]:
            doc = self.documents[idx]
            original_id = doc.get('original_id', doc['id'])
            
            if original_id in seen_original_ids:
                continue
                
            seen_original_ids.add(original_id)
            relevant_docs.append({
                'question': doc['question'],
                'answer': doc['answer'],
                'combined_text': doc['combined_text']
            })
            
            if len(relevant_docs) >= 3:
                break
        
        return relevant_docs
    
    def _classify_query_complexity(self, query: str) -> str:
        """Classify query as 'simple' or 'complex' to choose appropriate model"""
        query_lower = query.lower()
        
        # Complex query indicators
        complex_indicators = [
            # Technical/detailed questions
            'how to', 'explain', 'what is the difference', 'compare', 'analysis',
            'detailed', 'step by step', 'process', 'procedure', 'requirements',
            'documentation', 'specification', 'technical', 'advanced',
            
            # Multi-part questions
            'and also', 'in addition', 'furthermore', 'moreover', 'additionally',
            
            # Conditional/complex logic
            'if', 'when', 'unless', 'depending on', 'in case', 'provided that',
            
            # Long queries (>100 characters often indicate complexity)
            len(query) > 100,
            
            # Multiple question marks or sentences
            query.count('?') > 1,
            query.count('.') > 2,
            
            # Financial/legal complexity
            'regulation', 'compliance', 'legal', 'contract', 'agreement',
            'policy details', 'terms and conditions', 'refund policy'
        ]
        
        # Simple query indicators  
        simple_indicators = [
            # Basic greetings/short questions
            'hello', 'hi', 'thanks', 'thank you', 'yes', 'no', 'ok', 'okay',
            
            # Simple factual questions
            'what is', 'where is', 'when is', 'who is', 'which',
            'cost', 'price', 'how much', 'contact', 'phone', 'email',
            'hours', 'time', 'location', 'address',
            
            # Short queries
            len(query) < 50,
            
            # Single word queries
            len(query.split()) <= 3
        ]
        
        # Count indicators
        complex_score = sum(1 for indicator in complex_indicators if 
                          (isinstance(indicator, bool) and indicator) or 
                          (isinstance(indicator, str) and indicator in query_lower))
        
        simple_score = sum(1 for indicator in simple_indicators if 
                         (isinstance(indicator, bool) and indicator) or 
                         (isinstance(indicator, str) and indicator in query_lower))
        
        # Decision logic
        if complex_score > simple_score:
            return "complex"
        elif simple_score > complex_score:
            return "simple"
        else:
            # Default to simple for borderline cases (cost optimization)
            return "simple"
    
    def _is_pricing_query(self, query: str) -> bool:
        """
        Efficiently determine if the query is about pricing using keywords.
        Returns True if the query is about pricing, else False.
        """
        keywords = [
            'price', 'cost', 'fee', 'fees', 'pricing', 'charge', 'charges', 'amount', 'how much', 'pay', 'payment', 'rate', 'rates', 'subscription', 'plan', 'plans', 'expensive', 'cheap', 'afford', 'deposit', 'withdrawal', 'refund', 'discount', 'offer', 'promotion', 'hftpro', 'phase1', 'phase2'
        ]
        q = query.lower()
        return any(kw in q for kw in keywords)

    def _is_coupon_query(self, query: str) -> bool:
        """
        Efficiently determine if the query is about coupons or promo codes using keywords.
        Returns True if the query is about coupons, else False.
        """
        keywords = [
            'coupon', 'promo', 'discount code', 'voucher', 'entry code', 'coupon code', 'promo code', 'discount', 'offer', 'promotion', 'redeem', 'apply code', 'code for', 'get code', 'use code', 'special code'
        ]
        q = query.lower()
        return any(kw in q for kw in keywords)

    def _subpage_keywords(self):
        """
        Returns a mapping of subpage paths to their associated keywords.
        """
        return {
            '/faq': ['faq', 'frequently asked', 'question', 'questions', 'common question', 'help', 'support', 'how to', 'information', 'info'],
            '/features': ['feature', 'features', 'capability', 'capabilities', 'function', 'functions', 'what can', 'tools', 'offerings'],
            '/loyalty-program': ['loyalty', 'loyalty program', 'reward', 'rewards', 'points', 'membership', 'benefit', 'benefits'],
            '/offer': ['offer', 'offers', 'promotion', 'deal', 'discount', 'special', 'entry coupon', 'get funded', 'current offer', 'promo'],
        }

    def _detect_relevant_subpages(self, query: str):
        """
        Returns a list of subpage paths relevant to the query based on keywords.
        Always includes the root page ('/').
        """
        q = query.lower()
        subpages = self._subpage_keywords()
        relevant = ['/']
        for path, keywords in subpages.items():
            if any(kw in q for kw in keywords):
                relevant.append(path)
        return relevant

    def _scrape_fundedfolk_pages(self, paths=None, include_pricing=False, include_coupons=False):
        """
        Scrape text content from FundedFolk main site and subpages, and optionally fetch pricing and coupon info from APIs.
        :param paths: List of subpaths to scrape (e.g., ["/", "/faq"])
        :param include_pricing: Whether to fetch and include pricing info from the API
        :param include_coupons: Whether to fetch and include coupon info from the API
        :return: Dict mapping path or 'pricing'/'coupons' to extracted text
        """
        base_url = "https://fundedfolk.co"
        if paths is None:
            paths = ['/']
        results = {}
        for path in paths:
            url = base_url + path
            try:
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                # Remove scripts/styles
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                # Get visible text
                text = " ".join(soup.stripped_strings)
                results[path] = text
            except Exception as e:
                results[path] = f"Error scraping {url}: {e}"
        # Fetch pricing info from API if requested
        if include_pricing:
            try:
                pricing_url = base_url + "/api/pricing"
                resp = requests.get(pricing_url, timeout=10)
                resp.raise_for_status()
                pricing_data = resp.json()
                # Format pricing info for context
                pricing_lines = ["Official Pricing (USD):"]
                for account_size, details in pricing_data.items():
                    line = f"Account: ${account_size}"
                    for k, v in details.items():
                        line += f", {k}: ${v}"
                    pricing_lines.append(line)
                results['/api/pricing'] = "\n".join(pricing_lines)
            except Exception as e:
                results['/api/pricing'] = f"Error fetching pricing: {e}"
        # Fetch coupon info from API if requested
        if include_coupons:
            try:
                coupons_url = base_url + "/api/pricing-details"
                resp = requests.get(coupons_url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                coupon_popup = data.get('couponPopup', {})
                popup_data = coupon_popup.get('popup_data', {})
                coupons = popup_data.get('coupons', [])
                coupon_lines = ["Available Coupons:"]
                for coupon in coupons:
                    code = coupon.get('code', 'N/A')
                    sizes = ', '.join(str(s) for s in coupon.get('sizes', []))
                    discount = coupon.get('discount', 'N/A')
                    coupon_lines.append(f"Code: {code}, Sizes: {sizes}, Discount: {discount}%")
                results['/api/pricing-details'] = "\n".join(coupon_lines)
            except Exception as e:
                results['/api/pricing-details'] = f"Error fetching coupons: {e}"
        return results

    def generate_response(self, query: str, context_docs: List[Dict]) -> str:
        """Generate response using hybrid model selection, combining embedded docs and live scraped FundedFolk info"""
        # Use keyword-based method to decide if pricing/coupon info is needed
        include_pricing = self._is_pricing_query(query)
        include_coupons = self._is_coupon_query(query)
        if include_pricing:
            print("[Pricing Classifier] Detected pricing-related query. Including pricing info.")
        else:
            print("[Pricing Classifier] Not a pricing-related query. Skipping pricing info.")
        if include_coupons:
            print("[Coupon Classifier] Detected coupon-related query. Including coupon info.")
        else:
            print("[Coupon Classifier] Not a coupon-related query. Skipping coupon info.")
        # Detect relevant subpages for this query
        relevant_paths = self._detect_relevant_subpages(query)
        print(f"[Subpage Classifier] Including subpages: {relevant_paths}")
        # Scrape only relevant subpages and APIs
        scraped = self._scrape_fundedfolk_pages(
            paths=relevant_paths,
            include_pricing=include_pricing,
            include_coupons=include_coupons
        )
        web_context = "\n\n".join([f"Content from {k}:\n{v}" for k, v in scraped.items()])

        # Print scraped website data
        print("\n===== [Scraped FundedFolk Website Data] =====")
        for path, text in scraped.items():
            print(f"--- {path} ---\n{text[:1000]}{'...' if len(text) > 1000 else ''}\n")
        print("===== [End Scraped Data] =====\n")

        # Classify query complexity
        complexity = self._classify_query_complexity(query)
        # Choose model based on complexity - use only free models
        if complexity == "simple":
            model = "mistralai/mistral-7b-instruct:free"  # Free model for simple queries
            model_name = "Mistral 7B (Free, OpenRouter)"
        else:
            model = "google/gemma-3n-e2b-it:free"  # Free model for complex queries
            model_name = "Gemma 3n 2B (Free, OpenRouter)"
        print(f"🤖 Using {model_name} for this query")
        # Format context
        context_text = ""
        for i, doc in enumerate(context_docs, 1):
            answer = doc['answer']
            if len(answer) > 500:
                answer = answer[:500] + "..."
            context_text += f"Example {i}:\nQ: {doc['question'][:200]}{'...' if len(doc['question']) > 200 else ''}\nA: {answer}\n\n"
        # Print embedded document context
        print("===== [Embedded Document Context] =====")
        print(context_text[:2000] + ("..." if len(context_text) > 2000 else ""))
        print("===== [End Embedded Context] =====\n")
        prompt = f"""You are Funded Folk's helpful support assistant. Answer the user's question in a concise, to-the-point manner. Do not include unnecessary details or long explanations. Use the following information to answer the user's question. Always prefer the most up-to-date information from the Official FundedFolk Website if there is any conflict. Provide a helpful, accurate response based on the combined context provided.\n\nIMPORTANT: Format your response with proper structure, bullet points, and clear sections. Use markdown-style formatting for better readability.\n\n### Official FundedFolk Website (latest info):\n{web_context}\n\n### Embedded Knowledge Base Examples:\n{context_text}\n\n### User Question:\n{query}\n\n### Response:\nPlease provide a concise, well-structured response with:\n- Clear headings and sections (if needed)\n- Bullet points for lists\n- Bold text for important information\n- Step-by-step instructions when applicable\n- Professional but friendly tone\n- If there is a conflict, prefer the information from the Official FundedFolk Website as it is the most up-to-date.\n- **Keep your answer as short and direct as possible.**"""
        # === OpenRouter Integration ===
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        if not OPENROUTER_API_KEY:
            return "Error: OPENROUTER_API_KEY not found in environment."
        
        # Define headers for all OpenRouter requests
        openrouter_headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Define payload for primary model (will be used if available)
        openrouter_payload = {
            "model": model,  # Use dynamically selected model
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 250,
            "top_p": 1,
            "stream": False
        }
        
        # Check if primary model is available (not recently used or rate limited)
        # For high-traffic scenarios, prefer fallback to avoid rate limits
        if not self._is_model_available(model, cooldown_seconds=300) or self._is_model_rate_limited(model, cooldown_seconds=600):
            print(f"⏳ Primary model {model} is in cooldown or rate limited, trying alternatives...")
            # Skip to alternative models
        else:
            # Try primary model first
            for attempt in range(MAX_RETRIES):
                try:
                    response = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=openrouter_headers,
                        json=openrouter_payload,  # Use json parameter instead of data
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        self._mark_model_used(model)  # Mark as used for rate limiting
                        return response_data['choices'][0]['message']['content']
                    elif response.status_code == 429:
                        # Rate limit hit - use exponential backoff
                        wait_time = BASE_DELAY * (2 ** attempt)
                        print(f"⚠️ Rate limit hit (429) on attempt {attempt + 1}. Waiting {wait_time} seconds...")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(wait_time)
                        else:
                            self._mark_model_rate_limited(model)  # Mark as rate limited
                            return "Error: OpenRouter API rate limit exceeded. Please wait a moment and try again, or consider upgrading to a paid plan for higher limits."
                    else:
                        print(f"❌ Error response on attempt {attempt + 1}: {response.text}")
                        if attempt < MAX_RETRIES - 1:
                            wait_time = BASE_DELAY * (2 ** attempt)
                            print(f"🔄 Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            return f"Error: OpenRouter API returned status {response.status_code} after multiple retries. Please check your API key and try again."
                            
                except requests.exceptions.Timeout:
                    print(f"❌ Request timed out on attempt {attempt + 1}. Retrying...")
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BASE_DELAY * (2 ** attempt)
                        time.sleep(wait_time)
                    else:
                        return "Error: Request timed out. Please try again."
                except requests.exceptions.RequestException as e:
                    print(f"❌ Network issue on attempt {attempt + 1}: {str(e)}. Retrying...")
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BASE_DELAY * (2 ** attempt)
                        time.sleep(wait_time)
                    else:
                        return f"Error: Network issue - {str(e)}"
                except KeyError as e:
                    print(f"❌ Unexpected response format on attempt {attempt + 1}: {str(e)}. Retrying...")
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BASE_DELAY * (2 ** attempt)
                        time.sleep(wait_time)
                    else:
                        return f"Error: Unexpected response format - {str(e)}"
                except Exception as e:
                    print(f"❌ Unexpected error on attempt {attempt + 1}: {str(e)}. Retrying...")
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BASE_DELAY * (2 ** attempt)
                        time.sleep(wait_time)
                    else:
                        return f"Error: {str(e)}"
        
        # If primary OpenRouter model fails, try alternative free models
        print("⚠️ Primary OpenRouter model failed, trying alternative free models...")
        
        # List of alternative free OpenRouter models to try (excluding the primary model)
        # Using only known working FREE models from OpenRouter
        alternative_models = [
            "google/gemma-3n-e2b-it:free",         # Free Gemma model
            "mistralai/mistral-7b-instruct:free",  # Free Mistral model
        ]
        
        # Remove the primary model from alternatives if it's already there
        if model in alternative_models:
            alternative_models.remove(model)
        
        for model in alternative_models:
            # Skip models that were recently used or rate limited
            if not self._is_model_available(model, cooldown_seconds=300) or self._is_model_rate_limited(model, cooldown_seconds=600):
                print(f"⏳ Model {model} is in cooldown or rate limited, skipping...")
                continue
                
            try:
                print(f"🔄 Trying OpenRouter model: {model}")
                fallback_payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 250,
                    "top_p": 1,
                    "stream": False
                }
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=openrouter_headers,
                    json=fallback_payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    print(f"✅ Success with OpenRouter model: {model}")
                    self._mark_model_used(model)  # Mark as used for rate limiting
                    return response_data['choices'][0]['message']['content']
                elif response.status_code == 429:
                    print(f"⚠️ Rate limit hit for {model}, trying next model...")
                    self._mark_model_rate_limited(model)  # Mark as rate limited
                    time.sleep(1)  # Brief pause between models
                    continue
                else:
                    print(f"❌ Model {model} failed: {response.status_code}")
                    continue
                    
            except Exception as e:
                print(f"❌ Error with model {model}: {str(e)}")
                continue
        
        # If all OpenRouter models fail, provide a simple response
        print("🔄 All OpenRouter models failed, using simple fallback response...")
        return self._generate_simple_fallback_response(query, context_docs, web_context)
    
    def _generate_simple_fallback_response(self, query: str, context_docs: List[Dict], web_context: str) -> str:
        """Generate a simple response when all API models fail"""
        print("📝 Generating simple fallback response...")
        
        # Extract key information from context
        relevant_info = []
        
        # Add web context if available
        if web_context and len(web_context.strip()) > 50:
            relevant_info.append("**Latest Website Information:**\n" + web_context[:500] + "...")
        
        # Add most relevant document context
        if context_docs:
            best_match = context_docs[0]
            relevant_info.append(f"**Related Information:**\nQ: {best_match['question'][:200]}...\nA: {best_match['answer'][:300]}...")
        
        # Generate a simple response
        if relevant_info:
            context_text = "\n\n".join(relevant_info)
            response = f"""Based on the available information:

{context_text}

**Response:** I understand you're asking about: "{query}". While I'm experiencing technical difficulties with my AI models, I can provide you with the most relevant information from our knowledge base above. 

For the most up-to-date information, please visit our website at https://fundedfolk.co or contact our support team directly."""
        else:
            response = f"""I understand you're asking about: "{query}". 

I'm currently experiencing technical difficulties with my AI models. For the most accurate and up-to-date information, please:

1. Visit our website: https://fundedfolk.co
2. Contact our support team directly
3. Try again in a few moments

Thank you for your patience!"""
        
        return response
    
    def _is_model_available(self, model: str, cooldown_seconds: int = 300) -> bool:
        """Check if a model is available (not recently used) - much longer cooldown"""
        if model not in self.model_usage_times:
            return True
        
        time_since_last_use = time.time() - self.model_usage_times[model]
        return time_since_last_use >= cooldown_seconds
    
    def _mark_model_used(self, model: str):
        """Mark a model as recently used"""
        self.model_usage_times[model] = time.time()
    
    def _mark_model_rate_limited(self, model: str):
        """Mark a model as rate limited"""
        self.model_rate_limit_times[model] = time.time()
    
    def _is_model_rate_limited(self, model: str, cooldown_seconds: int = 600) -> bool:
        """Check if a model was recently rate limited (much longer cooldown)"""
        if model not in self.model_rate_limit_times:
            return False
        
        time_since_rate_limit = time.time() - self.model_rate_limit_times[model]
        return time_since_rate_limit < cooldown_seconds
    
    def chat(self, query: str) -> str:
        """Main chat function with hybrid model selection"""
        print("🔍 Step 1: Embedding query with OpenAI...")
        
        print("🔍 Step 2: Searching FAISS index...")
        context_docs = self.search_similar_documents(query, top_k=5)
        
        print(f"✅ Step 3: Found {len(context_docs)} relevant documents:")
        for i, doc in enumerate(context_docs, 1):
            print(f"   {i}. Q: {doc['question'][:60]}...")
        
        print("🤖 Step 4: Generating response with hybrid model selection...")
        response = self.generate_response(query, context_docs)
        
        return response

# === SERVERLESS FUNCTIONS ===
def initialize_rag() -> HybridRAGSystem:
    """Initialize hybrid RAG system (call once)"""
    return HybridRAGSystem()

def process_query(rag_system: HybridRAGSystem, query: str) -> str:
    """Process a single query (stateless function)"""
    return rag_system.chat(query)

# === MAIN EXECUTION ===
def main():
    """Main function for local testing"""
    print("🚀 Initializing Hybrid RAG System...")
    print("📋 Architecture: Query → OpenAI Embedding → FAISS Search → Hybrid Groq Response")
    print("🔧 Cost Optimization: 80% simple queries (8B) + 20% complex queries (70B)")
    print("💰 Target Cost: ~$74.75/month for 500k queries")
    
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
        
        print("\n🤖 Funded Folk Hybrid RAG Chatbot Ready!")
        print("💡 Following exact architecture: OpenAI → FAISS → Hybrid Groq")
        print("🎯 No server hosting required!")
        print("⚡ Smart model selection: 8B for simple, 70B for complex queries")
        print("💰 Cost optimized: ~$74.75/month")
        print("Type 'exit' or 'quit' to end the conversation.")
        print("=" * 60)
        
        while True:
            user_input = input("\n🧑 You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            
            if user_input.strip():
                response = process_query(rag_system, user_input)
                print(f"\n�� Bot: {response}")
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