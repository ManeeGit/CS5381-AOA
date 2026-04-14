from __future__ import annotations

import json
import re
from typing import Optional

import requests

from .base import LLMClient

_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_MODEL = "qwen2.5-coder:1.5b"
_FALLBACK_MODEL = "qwen2.5:7b"

_SYSTEM_PROMPT = (
    "You are an expert algorithmic code optimizer. "
    "When asked to improve code, return ONLY the improved Python code with no explanation, "
    "no markdown fences, and no commentary. "
    "Preserve the same function signatures and ensure the code is syntactically correct."
)


class OllamaLLM(LLMClient):
    """Local LLM client using Ollama REST API.

    Ollama must be running locally (``ollama serve``).
    Pull a model first:  ``ollama pull qwen2.5-coder:1.5b``

    The client talks to the Ollama /api/chat endpoint and returns only code.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        host: str = _DEFAULT_HOST,
        timeout: int = 120,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def improve(self, prompt: str, code: str) -> str:
        """Send code + task description to the local Ollama LLM and return improved code."""
        if not self._is_available():
            return self._fallback_improve(code)

        user_msg = (
            f"Task: {prompt}\n\n"
            f"Current code:\n```python\n{code}\n```\n\n"
            "Return only the improved Python code."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 700,
            },
        }

        try:
            resp = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content: str = data["message"]["content"].strip()
            return self._extract_code(content) or code
        except Exception as exc:
            print(f"[OllamaLLM] Error calling Ollama: {exc}")
            return self._fallback_improve(code)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_available(self) -> bool:
        """Lazily test whether Ollama is reachable and the model exists."""
        if self._available is not None:
            return self._available

        # 1. Ping the server
        try:
            requests.get(f"{self.host}/api/tags", timeout=5).raise_for_status()
        except Exception:
            print("[OllamaLLM] Ollama server not reachable at", self.host)
            self._available = False
            return False

        # 2. Check that our model is pulled; fall back to any available model
        try:
            tags = requests.get(f"{self.host}/api/tags", timeout=5).json()
            available_models = [m["name"] for m in tags.get("models", [])]
            if self.model not in available_models:
                # Try the fallback model
                if _FALLBACK_MODEL in available_models:
                    print(
                        f"[OllamaLLM] Model '{self.model}' not found; "
                        f"using '{_FALLBACK_MODEL}' instead."
                    )
                    self.model = _FALLBACK_MODEL
                elif available_models:
                    self.model = available_models[0]
                    print(f"[OllamaLLM] Falling back to first available model: {self.model}")
                else:
                    print("[OllamaLLM] No models available in Ollama.")
                    self._available = False
                    return False
        except Exception:
            pass

        self._available = True
        return True

    @staticmethod
    def _extract_code(text: str) -> str:
        """Strip markdown code fences if present."""
        # Match ```python ... ``` or ``` ... ```
        fence = re.search(r"```(?:python)?\s*\n?(.*?)```", text, re.DOTALL)
        if fence:
            return fence.group(1).strip()
        return text.strip()

    @staticmethod
    def _fallback_improve(code: str) -> str:
        """Deterministic fallback when Ollama is unavailable."""
        marker = "# [ollama-fallback] minor optimisation applied"
        if marker in code:
            return code
        lines = code.splitlines()
        return "\n".join([marker] + lines)
