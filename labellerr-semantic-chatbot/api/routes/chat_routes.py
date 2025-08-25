# api/routes/chat_routes.py
from flask import Blueprint, request, jsonify
from api.llm_service import LabellerrRAGChatbot
from api.qdrant_service import QdrantManager
from api.embedding_service import EmbeddingGenerator

chat_bp = Blueprint('chat', __name__)

# Initialize components (you might want to do this in your main.py)
qdrant_manager = QdrantManager()
embedder = EmbeddingGenerator()
chatbot = LabellerrRAGChatbot(qdrant_manager, embedder, openai_api_key=os.getenv("OPENAI_API_KEY"))

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        query = data.get('query', '')
        source_filter = data.get('source_filter', None)
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        result = chatbot.chat(query, source_filter, top_k)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/search', methods=['POST'])
def search():
    """Search for relevant chunks without generating response"""
    try:
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        context = chatbot.retrieve_context(query, top_k)
        return jsonify({'results': context})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
