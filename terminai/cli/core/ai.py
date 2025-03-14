"""
AI integration module for TerminAI.
This handles interactions with AI models to generate responses for user queries.
"""

import os 
import dotenv
import requests # To enable HTTP requests to APIs
from typing import Dict, Any, Optional 
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
env_path = os.path.join(project_root, ".env")


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
            
            # Call Ollama API
            response = requests.post(f"{self.base_url}/api/generate", json={"model": self.model, "prompt": full_prompt, "stream": False})
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error: Failed to get response from AI model (HTTP {response.status_code})"

            # Trying to parse the response safely
            try:
                # Extract just the response text from the JSON
                return response.json().get("response", "No response received")
            except ValueError as json_err:
                # If JSON parsing fails, try to extract the text directly
                logger.warning(f"JSON parsing error: {json_err}. Trying alternative parsing.")
                # Try an alternative approach for the Ollama API in case it is using a newer Ollama API format
                try:
                    if "message" in response.json():
                        return response.json().get("message", {}).get("content", "No response content")
                    # Simple fallback - just return the text
                    return response.text.strip()
                except:
                    # Last resort - return raw text if all parsing attempts fail
                    return response.text.strip()
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

class APIProvider(AIProvider):
    """Integration with our secure backend API"""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        Initialize the API provider.
        
        Args:
            api_url: URL of the backend API. If None, will look for TERMINAI_API_URL env var.
            api_key: API key for authentication. If None, will look for TERMINAI_API_KEY env var.
        """
        
        # Try to get API info from env if not provided 
        self.api_url = api_url or os.environ.get("TERMINAI_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.environ.get("TERMINAI_API_KEY")
        if not self.api_key:
            logger.error("TERMINAI_API_KEY environment variable not set")
            raise ValueError("API key not provided and TERMINAI_API_KEY environment variable not set")
        
        # URL formatting
        if self.api_url.endswith('/'):
            self.api_url = self.api_url[:-1]
        
        logger.info(f"Initialized API provider with URL: {self.api_url}")
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate a response using our backend API"""
        
        try: 
            if not context:
                context = {}
            
            # Preparing request data
            data = {
                "query": prompt,
                "context": context
            }
            
            # Setting headers with API key
            header = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Calling our backend API
            response = requests.post(
                f"{self.api_url}/generate-command",
                json=data,
                headers=header
            )
            
            # Checking response
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return f"Error: Failed to get response from API (HTTP {response.status_code})"
            
            # Extract the command from the response 
            try: 
                result = response.json()
                return result.get("command", "No command recieved")
            except ValueError as json_err:
                logger.error(f"JSON parsing error: {json_err}")
                return f"Error parsing API response: {str(json_err)}"
        
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return f"Error: {str(e)}"
        

# Factory function for AI providers
def get_ai_provider() -> AIProvider:
    """Factory function to get the configured AI provider"""
    
    # Load environment variables from .env file (if it exists)
    if os.path.exists(env_path):
        print(f"Found .env at {env_path}")
        with open(env_path, 'r') as f:
            content = f.read()
            print(f"Content of .env file:\n{content}")
    
        before = os.environ.get("TERMINAI_PROVIDER", "not_set_before")
        dotenv.load_dotenv(env_path, override=True)
        after = os.environ.get("TERMINAI_PROVIDER", "not_set_after")
        print(f"TERMINAI_PROVIDER before loading: {before}")
        print(f"TERMINAI_PROVIDER after loading: {after}")
    else:
        print(f"Warning: .env file not found at {env_path}")
        
    # Get provider type from environment variable
    provider_type = os.environ.get("TERMINAI_PROVIDER", "api")
    print(f"TERMINAI_PROVIDER: {provider_type}")
    print(f"TERMINAI_API_URL: {os.environ.get('TERMINAI_API_URL', 'not set')}")
    
    if provider_type.lower() == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.environ.get("OLLAMA_MODEL", "llama3")
        return OllamaProvider(base_url=base_url, model=model)
    elif provider_type.lower() == "api":
        api_url = os.environ.get("TERMINAI_API_URL", "http://localhost:8000")
        api_key = os.environ.get("TERMINAI_API_KEY")
        return APIProvider(api_url=api_url, api_key=api_key)
    else:
        logger.error(f"Unsupported AI provider: {provider_type}")
        raise ValueError(f"Unsupported AI provider: {provider_type}")

# Convenience function for generating responses
def generate_ai_response(prompt: str, context: Dict[str, Any] = None) -> str:
    """Generate an AI response for the given prompt and context"""
    provider = get_ai_provider()
    return provider.generate_response(prompt, context)