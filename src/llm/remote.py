"""Remote LLM backend supporting cloud AI APIs (OpenAI, Google Gemini).

This backend delegates code-improvement calls to cloud AI services.  It
requires an API key and an active internet connection.

Configuration via environment variables::

    export LLM_API_KEY="sk-..."         # OpenAI key
    export LLM_API_KEY="AIza..."        # Gemini key

Or set ``LLM_API_KEY`` in the project's ``.env`` file.  The provider and
model are controlled via ``config.yaml`` (``llm.provider``, ``llm.model_name``).

If the API is unreachable or the key is missing the backend degrades
gracefully to a deterministic no-op (returns original code + comment header).
"""
from __future__ import annotations

import os
from typing import Optional

from .base import LLMClient


class RemoteLLM(LLMClient):
    """
    Remote LLM client supporting OpenAI GPT and Gemini APIs.
    
    Usage::

        # Set environment variable
        export LLM_API_KEY="your-api-key"
        
        # Create client
        llm = RemoteLLM(provider="openai", model="gpt-4")
        llm = RemoteLLM(provider="gemini", model="gemini-pro")
    """
    
    def __init__(
        self, 
        provider: str = "openai", 
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ):
        """Initialise the remote LLM client.

        Reads the API key from the parameter, then falls back to the
        ``LLM_API_KEY`` or ``OPENAI_API_KEY`` environment variables.
        Does not make any network calls at construction time.

        Parameters
        ----------
        provider : str
            Cloud provider to use.  Supported values: ``"openai"``, ``"gemini"``.
            Defaults to ``"openai"``.
        api_key : str, optional
            API key for the chosen provider.  If ``None``, the value is read
            from the ``LLM_API_KEY`` or ``OPENAI_API_KEY`` environment variable.
        model : str
            Model identifier, e.g. ``"gpt-4"``, ``"gpt-3.5-turbo"``,
            ``"gemini-pro"``.
        """
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
        """Improve code by calling the configured cloud AI API.

        Dispatches to the provider-specific helper (``_improve_openai`` or
        ``_improve_gemini``).  Falls back to ``_fallback_improve`` if the
        API client was not initialised or if the API call raises an exception.

        Parameters
        ----------
        prompt : str
            Natural-language optimisation goal.
        code : str
            Python source code to improve.

        Returns
        -------
        str
            Improved Python source code, or the original code with a comment
            header if the API call failed.
        """
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
        """Call the OpenAI Chat Completions API to improve the code.

        Sends a system message (optimizer role + rules) and a user message
        (goal + current code).  Strips any markdown fences from the response
        so the returned string is clean Python source code.

        Parameters
        ----------
        prompt : str
            Optimisation goal forwarded to the model.
        code : str
            Current Python source code.

        Returns
        -------
        str
            Improved Python source code as returned by the GPT model.
        """
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
        """Call the Google Gemini API to improve the code.

        Constructs a single combined prompt (goal + current code) and calls
        ``generate_content``.  Strips markdown fences from the response.

        Parameters
        ----------
        prompt : str
            Optimisation goal forwarded to the model.
        code : str
            Current Python source code.

        Returns
        -------
        str
            Improved Python source code as returned by the Gemini model.
        """
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
        """Return the original code unchanged when the API is unavailable.

        Prepends a single-line comment that encodes the optimisation goal so
        the candidate has a unique hash and is not confused with the unmodified
        base code in the fitness cache.  Idempotent — adding the header a
        second time is skipped.

        Parameters
        ----------
        prompt : str
            Optimisation goal (first 50 characters used in the comment).
        code : str
            Original Python source code.

        Returns
        -------
        str
            Code with header comment, or original code if already present.
        """
        header = f"# Improved variant (API unavailable) - Goal: {prompt[:50]}"
        if header[:20] in code:
            return code
        return f"{header}\n{code}"

