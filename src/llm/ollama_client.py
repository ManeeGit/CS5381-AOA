"""Local LLM backend using the Ollama REST API.

Ollama (https://ollama.com) runs AI models locally on your machine and
exposes a simple HTTP API.  This module wraps that API so the Evolve
evolution engine can transparently request AI-assisted code improvements
without needing any cloud subscription.

Quick setup::

    # 1. Install Ollama (https://ollama.com/download)
    # 2. Pull a code model:
    ollama pull qwen2.5-coder:7b
    # 3. Start the server (runs in the background):
    ollama serve

Default endpoint: ``http://localhost:11434``
Default model:    ``qwen2.5-coder:7b``

If Ollama is unavailable the client degrades to a deterministic no-op so
the evolutionary loop never crashes.
"""
from __future__ import annotations

import json
import re
from typing import Optional

import requests

from .base import LLMClient

_DEFAULT_HOST = "http://localhost:11434"
_DEFAULT_MODEL = "qwen2.5-coder:7b"
_FALLBACK_MODEL = "llama3.1:8b"

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
        timeout: int = 300,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
        self._available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def improve(self, prompt: str, code: str) -> str:
        """Request an improved version of ``code`` from the local Ollama model.

        Builds a chat-style request (system prompt + user message) and posts
        it to the Ollama ``/api/chat`` endpoint with ``stream=False``.  The
        raw model output is cleaned with ``_extract_code`` and
        ``_sanitize_code`` before being returned.

        Falls back to ``_fallback_improve`` if:
        * Ollama is not running or no model is pulled.
        * The HTTP request times out or returns a non-2xx status.
        * The model returns only non-Python text.

        Parameters
        ----------
        prompt : str
            Natural-language optimisation goal, e.g.
            ``"Reduce the number of arithmetic operations."``
        code : str
            Current Python source code to improve.

        Returns
        -------
        str
            Improved Python source code, or ``code`` unchanged on failure.
        """
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
                "num_predict": 2048,
                "num_ctx": 4096,
                "num_gpu": 99,
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
            cleaned = self._extract_code(content)
            if cleaned:
                cleaned = self._sanitize_code(cleaned)
            return cleaned or code
        except Exception as exc:
            print(f"[OllamaLLM] Error calling Ollama: {exc}")
            return self._fallback_improve(code)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_available(self) -> bool:
        """Check whether Ollama is reachable and a usable model is available.

        Performs two lightweight HTTP calls on every invocation:

        1. ``GET /api/tags`` to confirm the server is up.
        2. A second ``GET /api/tags`` to check that ``self.model`` is in the
           list of pulled models.  If not, the method tries ``_FALLBACK_MODEL``
           and then the first model in the list before giving up.

        The fallback model logic means the system gracefully degrades when the
        preferred model is not pulled rather than raising a hard error.

        Returns
        -------
        bool
            ``True`` if the server is up and at least one model is available,
            ``False`` otherwise.
        """
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
        """Strip markdown fences from model output and return the longest code block.

        Models often wrap their responses in fenced code blocks::

            ```python
            def sort(arr): ...
            ```

        This method extracts all fenced blocks with ``re.findall``, strips
        whitespace, and returns the *longest* one (models tend to put the
        most complete version last).  If no fences are present it searches
        for the first line that starts with a Python keyword (``from``,
        ``import``, ``class``, ``def``) and returns everything from there.

        Parameters
        ----------
        text : str
            Raw text output from the LLM.

        Returns
        -------
        str
            Extracted Python source code, or ``text`` stripped if nothing
            recognisable was found.
        """
        # Find ALL fenced blocks (```python ... ``` or ``` ... ```)
        blocks = re.findall(r"```(?:python)?\s*\n?(.*?)```", text, re.DOTALL)
        if blocks:
            # Prefer the last non-trivial block (LLMs often put the best answer last)
            blocks = [b.strip() for b in blocks if b.strip()]
            # Return the longest block as it's most likely the complete solution
            return max(blocks, key=len)
        # No fences — find where real Python starts (first import/from/class/def)
        match = re.search(r"^(from |import |class |def )", text, re.MULTILINE)
        if match:
            return text[match.start():].strip()
        return text.strip()

    @staticmethod
    def _sanitize_code(code: str) -> str:
        """Remove duplicate class definitions from model output, keeping the last one.

        LLMs sometimes emit the original class definition followed by the
        improved one, both in the same response.  If not removed, the
        duplicate ``class`` definition will cause ``ast.parse`` errors.

        **Algorithm:**

        1. Split on ``class`` boundaries (keeping the keyword).
        2. Deduplicate import lines in the preamble.
        3. Collect class bodies in insertion order, overwriting on duplicate
           class names so the *last* (most evolved) definition wins.
        4. Reassemble preamble + unique class bodies.

        Parameters
        ----------
        code : str
            Python source code potentially containing duplicate classes.

        Returns
        -------
        str
            Deduplicated Python source code.
        """
        # Split on class boundaries
        class_pattern = re.compile(r"(?=^class )", re.MULTILINE)
        parts = class_pattern.split(code)

        if len(parts) <= 1:
            # No class boundary found; deduplicate by unique consecutive lines
            return code

        # Collect imports (everything before the first class)
        preamble = parts[0]
        # Deduplicate import lines in preamble
        seen_imports: set = set()
        clean_imports = []
        for line in preamble.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                if stripped not in seen_imports:
                    seen_imports.add(stripped)
                    clean_imports.append(line)
            elif stripped:  # keep non-empty non-import preamble lines
                clean_imports.append(line)
        preamble = "\n".join(clean_imports)

        # Collect class blocks, keep only the LAST definition of each class name
        class_blocks: dict = {}
        for part in parts[1:]:  # skip preamble
            # Extract class name
            name_match = re.match(r"class (\w+)", part)
            class_name = name_match.group(1) if name_match else "__unknown__"
            class_blocks[class_name] = part  # overwrite — keep last definition

        result_parts = [preamble] if preamble.strip() else []
        result_parts.extend(class_blocks.values())
        return "\n\n".join(result_parts).strip()

    @staticmethod
    def _fallback_improve(code: str) -> str:
        """Return the original code with a marker comment when Ollama is unavailable.

        Adds a single-line comment at the top so the candidate has a
        different hash from the base code in the fitness cache, avoiding
        spurious cache hits.  Idempotent — the marker is only added once.

        Parameters
        ----------
        code : str
            Original Python source code.

        Returns
        -------
        str
            Code with marker prepended, or original code if marker is already present.
        """
        marker = "# [ollama-fallback] minor optimisation applied"
        if marker in code:
            return code
        lines = code.splitlines()
        return "\n".join([marker] + lines)
