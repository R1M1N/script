# api/llm_service.py
import google.generativeai as genai
from typing import List, Dict, Tuple, Optional
import json
from .qdrant_service import QdrantManager
from .embedding_service import EmbeddingGenerator

class LabellerrRAGChatbot:
    def __init__(self, qdrant_manager: QdrantManager, embedding_generator: EmbeddingGenerator, 
                 gemini_api_key: str, model: str = "gemini-2.5-pro"):
        """
        Initialize RAG chatbot with Gemini
        
        Args:
            qdrant_manager: QdrantManager instance
            embedding_generator: EmbeddingGenerator instance
            gemini_api_key: Gemini API key
            model: Gemini model to use
        """
        self.qdrant = qdrant_manager
        self.embedder = embedding_generator
        self.model = model
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.gemini = genai.GenerativeModel(model)
        
        # Conversation history
        self.conversation_history = []
    
    def retrieve_context(self, query: str, top_k: int = 5, 
                        source_filter: Optional[str] = None) -> List[Dict]:
        """
        Retrieve relevant context for a query
        """
        # Generate query embedding
        query_embedding = self.embedder.generate_single_embedding(query)
        
        # Search similar chunks
        search_results = self.qdrant.search_similar(
            query_embedding=query_embedding,
            limit=top_k,
            source_filter=source_filter,
            min_score=0.3
        )
        
        # Format results
        context_chunks = []
        for result in search_results:
            chunk = {
                'text': result.payload['text'],
                'title': result.payload['title'],
                'url': result.payload['url'],
                'heading': result.payload['heading'],
                'source_type': result.payload['source_type'],
                'score': result.score,
                'page_title': result.payload.get('page_title', ''),
            }
            context_chunks.append(chunk)
        
        return context_chunks
    
    def enhance_query(self, query: str) -> str:
        """Enhance query with Labellerr-specific context"""
        enhancements = {
            'project': 'Labellerr project creation setup workspace',
            'annotation': 'Labellerr annotation labeling tool feature',
            'export': 'Labellerr export data download format',
            'upload': 'Labellerr upload data import dataset',
            'review': 'Labellerr review quality control workflow',
            'label': 'Labellerr labeling annotation process',
            'dataset': 'Labellerr dataset management data',
            'workspace': 'Labellerr workspace management team',
            'sdk': 'Labellerr SDK API integration development',
            'ml': 'Labellerr machine learning AI model'
        }
        
        enhanced_query = query.lower()
        for key, enhancement in enhancements.items():
            if key in enhanced_query:
                enhanced_query += f" {enhancement}"
        
        return enhanced_query
        
    def generate_response(self, query: str, context: List[Dict], include_sources: bool = True) -> Dict:
        """Generate response using Gemini with comprehensive error handling"""
        
        # Prepare context text
        context_text = ""
        for i, ctx in enumerate(context, 1):
            source_info = f"Source {i}"
            if ctx.get('heading'):
                source_info += f" - {ctx['heading']}"
            
            content = ctx.get('text', '').strip()
            if content:
                context_text += f"\n{source_info}:\n{content}\n"
        
        if not context_text:
            return {
                'response': "I don't have enough information to answer that question accurately.",
                'sources': [],
                'query': query,
                'context_used': 0
            }
        
        # Simplified, safe prompt
        prompt = f"""Based on this documentation about Labellerr:

    {context_text}

    Question: {query}

    Answer:"""

        try:
            # Import safety settings
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            # Generate response
            response = self.gemini.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 800
                },
                safety_settings=[
                    {
                        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": HarmBlockThreshold.BLOCK_NONE
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE
                    }
                ]
            )
            
            # DEBUG: Log the response structure
            print(f"DEBUG: Response type: {type(response)}")
            print(f"DEBUG: Response candidates: {len(response.candidates) if response.candidates else 'None'}")
            
            if response.candidates:
                candidate = response.candidates[0]
                print(f"DEBUG: Candidate finish reason: {candidate.finish_reason}")
                print(f"DEBUG: Safety ratings: {candidate.safety_ratings}")
                
                # Check if blocked by safety
                if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                    answer = candidate.content.parts[0].text
                else:
                    # Response blocked - let's provide a fallback
                    answer = f"Based on the documentation, Labellerr is an AI data labeling platform that offers: {context_text[:300]}..."
            else:
                answer = "No candidates returned from Gemini."

            # At the end of the try block, before the except:
            if not answer or "error" in answer.lower():
                # Fallback: Create response from context
                answer = f"Based on the Labellerr documentation:\n\n"
                answer += f"Labellerr is an AI data labeling platform that provides:\n"
                for ctx in context[:2]:  # Use first 2 contexts
                    if ctx.get('text'):
                        answer += f"• {ctx['text'][:200]}...\n"
                
        except Exception as e:
            print(f"DEBUG: Exception occurred: {e}")
            # Fallback response using context directly
            answer = f"Based on the Labellerr documentation provided: {context_text[:500]}..."
        
        # Prepare sources
        sources = []
        if include_sources and context:
            for ctx in context:
                source = {
                    'title': ctx.get('title') or ctx.get('heading'),
                    'url': ctx.get('url'),
                    'score': round(ctx.get('score', 0), 3),
                    'source_type': ctx.get('source_type'),
                    'text': ctx.get('text', '')
                }
                sources.append(source)
        
        return {
            'response': answer,
            'sources': sources,
            'query': query,
            'context_used': len(context)
        }

    def chat(self, query: str, source_filter: Optional[str] = None, 
             top_k: int = 5) -> Dict:
        """
        Main chat function
        """
        # Enhance query
        enhanced_query = self.enhance_query(query)
        
        # Retrieve context
        context = self.retrieve_context(enhanced_query, top_k, source_filter)
        
        # Generate response
        result = self.generate_response(query, context)
        
        # Store in conversation history
        self.conversation_history.append({
            'query': query,
            'response': result['response'],
            'sources_count': len(result['sources'])
        })
        
        return result
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
