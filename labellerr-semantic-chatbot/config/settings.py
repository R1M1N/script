# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # App settings
    APP_NAME = os.getenv('APP_NAME', 'Labellerr Semantic Chatbot')
    VERSION = os.getenv('VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # API settings
    API_V1_STR = "/api/v1"
    
    # Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
    
    # Qdrant settings
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
    
    # Embedding settings
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-mpnet-base-v2')
    MAX_CHUNK_SIZE = int(os.getenv('MAX_CHUNK_SIZE', 800))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 100))

settings = Config()
