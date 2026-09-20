"""AI interaction package for Ollama LLM client and system prompts."""
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from config.settings import OLLAMA_BASE_URL, DEFAULT_OLLAMA_MODEL
from ai.prompts import get_combined_system_prompt


class OllamaClient:
    """
    Client for communicating with the local Ollama LLM service.
    Defaults to model 'llama3.2:3b'.
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def check_connection(self) -> bool:
        """Check if the local Ollama server is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate_coaching(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send a generation request to Ollama using default model 'llama3.2:3b'.
        Uses combined system prompt (including ai/project_context.md) if system_prompt is None.
        
        Returns a dict containing success flag, text response, or error message.
        """
        if system_prompt is None:
            system_prompt = get_combined_system_prompt()

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": stream,
        }
        headers = {"Content-Type": "application/json"}

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    response_body = json.loads(resp.read().decode("utf-8"))
                    return {
                        "success": True,
                        "response": response_body.get("response", "").strip(),
                        "model": self.model,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP Error {resp.status}",
                        "model": self.model,
                    }
        except urllib.error.URLError as exc:
            return {
                "success": False,
                "error": f"Could not connect to Ollama ({exc.reason}). Ensure 'ollama serve' is running and model '{self.model}' is pulled.",
                "model": self.model,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": f"Unexpected error: {str(exc)}",
                "model": self.model,
            }
