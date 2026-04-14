from __future__ import annotations

import os
from typing import Optional

from .base import LLMClient


class RemoteLLM(LLMClient):
    """
    Remote LLM client supporting OpenAI GPT and Gemini APIs.
    
    Usage:
        # Set environment variable
        export LLM_API_KEY="your-api-key"
        
        # Create client
        llm = RemoteLLM(provider="openai", model="gpt-4")  # or "gpt-3.5-turbo"
        llm = RemoteLLM(provider="gemini", model="gemini-pro")
    """
    
    def __init__(
        self, 
        provider: str = "openai", 
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the appropriate API client based on provider."""
        if not self.api_key:
            return
        
        try:
            if self.provider == "openai":
                try:
                    from openai import OpenAI
                    self._client = OpenAI(api_key=self.api_key)
                except ImportError:
                    print("Warning: openai package not installed. Run: pip install openai")
                    
            elif self.provider == "gemini":
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.api_key)
                    self._client = genai.GenerativeModel(self.model or 'gemini-pro')
                except ImportError:
                    print("Warning: google-generativeai package not installed. Run: pip install google-generativeai")
                    
        except Exception as e:
            print(f"Warning: Failed to initialize {self.provider} client: {e}")
            self._client = None

    def improve(self, prompt: str, code: str) -> str:
        """Improve code using the remote LLM API."""
        if not self._client:
            return self._fallback_improve(prompt, code)
        
        try:
            if self.provider == "openai":
                return self._improve_openai(prompt, code)
            elif self.provider == "gemini":
                return self._improve_gemini(prompt, code)
            else:
                return self._fallback_improve(prompt, code)
        except Exception as e:
            print(f"Error calling {self.provider} API: {e}")
            return self._fallback_improve(prompt, code)

    def _improve_openai(self, prompt: str, code: str) -> str:
        """Improve code using OpenAI GPT."""
        system_message = """You are an expert algorithm optimizer. Your task is to improve code for better performance while maintaining correctness.
        
        Rules:
        1. Return ONLY the improved code, no explanations
        2. Maintain the same function signatures
        3. Keep the code runnable and syntactically correct
        4. Focus on the optimization goal specified in the prompt"""
        
        user_message = f"""{prompt}

Current code:
```python
{code}
```

Provide an improved version of this code."""
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1024,
            temperature=0.7
        )
        
        improved_code = response.choices[0].message.content.strip()
        
        # Extract code from markdown blocks if present
        if "```python" in improved_code:
            improved_code = improved_code.split("```python")[1].split("```")[0].strip()
        elif "```" in improved_code:
            improved_code = improved_code.split("```")[1].split("```")[0].strip()
        
        return improved_code

    def _improve_gemini(self, prompt: str, code: str) -> str:
        """Improve code using Google Gemini."""
        full_prompt = f"""You are an expert algorithm optimizer. Improve the following code based on this goal: {prompt}

Current code:
{code}

Return ONLY the improved code without any explanations or markdown formatting."""
        
        response = self._client.generate_content(full_prompt)
        improved_code = response.text.strip()
        
        # Extract code from markdown blocks if present
        if "```python" in improved_code:
            improved_code = improved_code.split("```python")[1].split("```")[0].strip()
        elif "```" in improved_code:
            improved_code = improved_code.split("```")[1].split("```")[0].strip()
        
        return improved_code

    def _fallback_improve(self, prompt: str, code: str) -> str:
        """
        Fallback improvement when API is not available.
        Adds a simple comment to indicate attempted improvement.
        """
        header = f"# Improved variant (API unavailable) - Goal: {prompt[:50]}"
        if header[:20] in code:
            return code
        return f"{header}\n{code}"

