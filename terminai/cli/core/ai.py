"""
AI integration module for TerminAI.
This handles interactions with AI models to generate responses for user queries.
"""

import os 
import requests # To enable HTTP requests to APIs
from typing import Dict, Any, Optional 
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIProvider:
    """Base class for AI providers"""
    
    def generate_response(self, prompt: str, context: Dict[str,Any] = None) -> str:
        """Generate a response based on the prompt and context"""
        raise NotImplementedError("Subclasses must implement this method")
    
class OllamaProvider(AIProvider):
    """Integration with Ollama for local AI inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        logger.info(f"Initialized Ollama provider with model: {model}")
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate a response using Ollama""" 
        try: 
            # Construct the full prompt with context   
            full_prompt = self._build_prompt(prompt, context)
            
            response = requests.post(f"{self.base_url}/api/generate", json={"model": self.model, "prompt": full_prompt})
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error: Failed to get response from AI model (HTTP {response.status_code})"

            return response.json().get("response", "No response recieved") # Returns default message if "response" doesn't exist
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return f"Error: {str(e)}"
    
    def _build_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Build a comprehensive prompt with context for better responses"""
        if not context:
            context = {}
        
        # Base prompt
        system_prompt = """
        You are TerminAI, an AI assistant specialized in terminal commands and operations.
        Provide clear, concise, and accurate responses to user queries.
        For command suggestions, only output the exact command the user should run.
        For explanations, be thorough but focus on practical usage.
        """
        
        # Add user context if available 
        context_prompt = ""
        if context.get("os"):
            context_prompt += f"Operating System: {context['os']}\n"
        if context.get("shell"):
            context_prompt += f"Shell: {context['shell']}\n"
        if context.get("current_dir"):
            context_prompt += f"Current Directory: {context['current_dir']}\n"
        
        # Combine all parts
        full_prompt = f"{system_prompt}\n\n{context_prompt}\nUser Query: {prompt}\n\nResponse:"
        return full_prompt

    # Factory function for AI providers
    def get_ai_provider() -> AIProvider:
        """Factory function to get the configured AI provider"""
        # This could be extended to support difference providers based on config
        provider_type = os.environ.get("TERMINAI_PROVIDER", "ollama") # Defaulting Ollama
        
        if provider_type.lower() == "ollama":
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.environ.get("OLLAMA_MODEL", "llama3")
            return OllamaProvider(base_url=base_url, model=model)
        else:
            logger.error(f"Unsupported AI provider: {provider_type}")
            raise ValueError(f"Unsupported AI provider: {provider_type}")
    
    def generate_ai_response(prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate an AI response for the given prompt and context"""
        provider = get_ai_provider()
        return provider.generate_response(prompt, context)