"""Abstract base class for all LLM (Large Language Model) backends.

This module defines the single-method contract that every LLM plugin must
implement.  Using an abstract base class (ABC) means the evolution engine
(``evolve.py``) never imports Ollama, OpenAI, or any other specific library
directly — it only depends on this interface.  Swapping backends is a
one-line config change.

Currently available implementations
-------------------------------------
* ``OllamaLLM``  (ollama_client.py) — local Ollama server; default.
* ``LocalLLM``   (local.py)         — llama.cpp via llama-cpp-python.
* ``RemoteLLM``  (remote.py)        — OpenAI / Anthropic cloud APIs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for all code-improvement LLM backends.

    Any class that wants to act as an LLM inside the Evolve framework must
    inherit from ``LLMClient`` and implement the single ``improve()`` method.
    This enforces a uniform interface so the evolution engine is completely
    decoupled from which AI model or service is in use.
    """

    @abstractmethod
    def improve(self, prompt: str, code: str) -> str:
        """Return an improved version of ``code`` guided by ``prompt``.

        The implementation is free to call any AI service, run inference
        locally, or apply deterministic transformations — as long as it
        returns a string of Python source code.

        Parameters
        ----------
        prompt : str
            Natural-language description of the optimisation goal, e.g.
            ``"Make this sorting algorithm shorter and faster."``
        code : str
            The current Python source code to improve.

        Returns
        -------
        str
            Improved Python source code.  Must be a non-empty string.
            If improvement is not possible, return ``code`` unchanged rather
            than raising an exception.
        """
        raise NotImplementedError
