from __future__ import annotations

from typing import Optional

from .base import LLMClient


class LocalLLM(LLMClient):
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._llama = None
        self._load_llama()

    def _load_llama(self) -> None:
        try:
            from llama_cpp import Llama  # type: ignore

            if self.model_path:
                self._llama = Llama(model_path=self.model_path)
        except Exception:
            self._llama = None

    def improve(self, prompt: str, code: str) -> str:
        if self._llama is None:
            return self._fallback_improve(prompt, code)

        system = "You are an algorithmic code improver. Return only code."
        user = f"{prompt}\n\nCurrent code:\n{code}\n\nImprove the code for fitness."
        res = self._llama.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=512,
            temperature=0.3,
        )
        content = res["choices"][0]["message"]["content"]
        return content.strip()

    def _fallback_improve(self, prompt: str, code: str) -> str:
        # Minimal deterministic refinement: add a comment and preserve code
        header = "# Improved variant based on prompt"
        if header in code:
            return code
        return f"{header}\n{code}"
