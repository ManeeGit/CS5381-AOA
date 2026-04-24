"""Local LLM backend using llama.cpp via the llama-cpp-python package.

This backend runs a GGUF model file directly on the local machine using
llama.cpp bindings.  It requires:

    pip install llama-cpp-python

And a downloaded GGUF model file, e.g.::

    # Example: download a small Mistral 7B GGUF
    wget https://huggingface.co/TheBloke/Mistral-7B-GGUF/resolve/main/mistral-7b.Q4_K_M.gguf

If the package is not installed or no model path is provided, the backend
falls back to a deterministic no-op that returns the original code with a
comment header — ensuring the evolutionary loop never crashes.
"""
from __future__ import annotations

from typing import Optional

from .base import LLMClient


class LocalLLM(LLMClient):
    """Code-improvement backend that runs inference locally via llama.cpp.

    Intended for offline environments where cloud APIs are not available
    and Ollama cannot be installed.  Performance depends heavily on the
    model file chosen and the available hardware (CPU or GPU).

    Parameters
    ----------
    model_path : str, optional
        Absolute file path to a GGUF-format model file.  If ``None`` or
        the file does not exist, the backend silently degrades to a no-op.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._llama = None
        self._load_llama()

    def _load_llama(self) -> None:
        """Attempt to load the llama-cpp-python Llama model from disk.

        Silently sets ``self._llama = None`` if the package is not installed
        or the model file cannot be opened, so the object is always safe to
        use even in environments without GPU support.
        """
        try:
            from llama_cpp import Llama  # type: ignore

            if self.model_path:
                self._llama = Llama(model_path=self.model_path)
        except Exception:
            self._llama = None

    def improve(self, prompt: str, code: str) -> str:
        """Improve code using local llama.cpp inference.

        Constructs a system + user chat prompt and calls the loaded Llama
        model.  Falls back to ``_fallback_improve()`` if the model was not
        loaded successfully.

        Parameters
        ----------
        prompt : str
            Natural-language optimisation goal.
        code : str
            Python source code to improve.

        Returns
        -------
        str
            Improved Python source code returned by the model, or the
            original code with a header comment on fallback.
        """
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
        """Return the original code with a minimal header comment.

        Used when the llama.cpp model is unavailable.  This ensures the
        evolutionary loop keeps running — the candidate is effectively a
        clone of the parent with a distinguishing comment so it gets a
        unique cache key.

        Parameters
        ----------
        prompt : str
            Unused; present for signature consistency.
        code : str
            Original Python source code to return unchanged.

        Returns
        -------
        str
            The original code, or the original code prefixed with a comment
            if the header was not already present.
        """
        # Minimal deterministic refinement: add a comment and preserve code
        header = "# Improved variant based on prompt"
        if header in code:
            return code
        return f"{header}\n{code}"
