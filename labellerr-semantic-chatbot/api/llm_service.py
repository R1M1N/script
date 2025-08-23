# api/llm_service.py
import logging
import time
from typing import Optional, Dict, Any
from config.settings import settings

try:
    import google.generativeai as genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._model = None
        self._inited = False

    def _ensure_init(self) -> None:
        if self._inited:
            return
        if genai is None:
            raise RuntimeError("google.generativeai package not available. Install google-generativeai.")
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set.")
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model_name)
        self._inited = True
        logger.info(f"LLM initialized: model={self.model_name}")

    def _truncate(self, text: str, max_chars: int = 40000) -> str:
        if not text or len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."

    async def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        self._ensure_init()
        
        if system_instruction:
            prompt = f"System: {system_instruction}\n\n{prompt}"
        
        safe_prompt = self._truncate(prompt, 40000)

        attempts = 0
        last_err = None
        while attempts < 3:
            attempts += 1
            try:
                response = self._model.generate_content(contents=safe_prompt)
                text = getattr(response, "text", None)
                
                if not text:
                    candidates = getattr(response, "candidates", None)
                    if candidates:
                        content = getattr(candidates[0], "content", None)
                        parts = getattr(content, "parts", None)
                        if parts and len(parts) > 0:
                            text = getattr(parts[0], "text", None)
                
                if not text:
                    raise RuntimeError("Empty response from LLM")
                return text
                
            except Exception as e:
                last_err = e
                wait_s = 0.6 * attempts
                logger.warning(f"LLM generate attempt {attempts} failed: {e}. Retrying in {wait_s:.1f}s")
                time.sleep(wait_s)
        
        raise RuntimeError(f"LLM generation failed after retries: {last_err}")

llm_service = LLMService()