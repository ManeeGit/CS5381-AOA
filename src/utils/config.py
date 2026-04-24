"""YAML configuration loader for the Evolve framework.

The entire project is configured through a single ``config.yaml`` file.  This
module provides ``Config`` — a thin wrapper around a parsed YAML dict that
offers a safe multi-level ``get()`` helper so callers never have to write
boilerplate ``dict.get`` chains with ``or``.

Typical usage::

    cfg = Config.load("config.yaml")
    model_name = cfg.get("llm", "model_name", default="qwen2.5-coder:7b")
    generations = cfg.get("evolution", "generations", default=10)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class Config:
    """Immutable wrapper around a parsed YAML configuration dictionary.

    Attributes
    ----------
    raw : dict
        The fully parsed YAML document as a plain Python dict.
    """
    raw: Dict[str, Any]

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        """Read and parse a YAML file from disk.

        Parameters
        ----------
        path : str or Path
            Path to the ``config.yaml`` file.

        Returns
        -------
        Config
            Parsed configuration wrapper.

        Raises
        ------
        FileNotFoundError
            If ``path`` does not exist.
        yaml.YAMLError
            If the file is not valid YAML.
        """
        p = Path(path)
        data = yaml.safe_load(p.read_text())
        return cls(raw=data)

    def get(self, *keys: str, default: Any = None) -> Any:
        """Retrieve a nested value by a chain of keys.

        Traverses the ``raw`` dict following ``keys`` in order.  Returns
        ``default`` as soon as any key is missing or the current value is not
        a dict (rather than raising ``KeyError``).

        Parameters
        ----------
        *keys : str
            One or more string keys forming the path to the target value,
            e.g. ``("llm", "model_name")``.
        default : any
            Value to return when the path does not exist in the config.

        Returns
        -------
        any
            The value at the specified path, or ``default``.

        Examples
        --------
        >>> cfg.get("llm", "model_name", default="qwen2.5-coder:7b")
        'qwen2.5-coder:7b'
        >>> cfg.get("nonexistent", "key", default=42)
        42
        """
        cur: Any = self.raw
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur
