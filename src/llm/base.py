from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def improve(self, prompt: str, code: str) -> str:
        raise NotImplementedError
