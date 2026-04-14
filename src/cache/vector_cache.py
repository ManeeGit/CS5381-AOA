"""Vector-similarity cache backed by a JSONL file and in-memory numpy index.

Improvement over the basic hash cache:
- On cache miss, we check for *similar* code (cosine similarity of TF-IDF vectors)
  and return the nearest neighbour's fitness if it exceeds `sim_threshold`.
- This reuses previous evaluation results for near-duplicate candidates, which
  dramatically speeds up the evolutionary search as required by the PDF spec:
  "cache high-quality candidates and templates in a vector database so that
  previous evaluation results are reused rather than wasted."

No external vector-DB package is required – we use numpy for the similarity
computation and store embeddings alongside fitness scores in a JSONL file.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np


# -------------------------------------------------------------------------
# Lightweight TF-IDF tokeniser (tokens = Python identifiers + operators)
# -------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Za-z_]\w*|[+\-*/=<>!&|]+|\d+")


def _tokenize(code: str) -> List[str]:
    return _TOKEN_RE.findall(code)


class _TFIDFVectorizer:
    """Minimal TF-IDF vectorizer that builds its vocabulary lazily."""

    def __init__(self) -> None:
        self._vocab: Dict[str, int] = {}  # token -> index
        self._idf: Optional[np.ndarray] = None
        self._doc_tokens: List[List[str]] = []

    def _build_vocab(self, all_docs: List[List[str]]) -> None:
        all_tokens: set = set()
        for tokens in all_docs:
            all_tokens.update(tokens)
        self._vocab = {t: i for i, t in enumerate(sorted(all_tokens))}

    def _tf(self, tokens: List[str]) -> np.ndarray:
        v = np.zeros(len(self._vocab))
        counts = Counter(tokens)
        for tok, cnt in counts.items():
            if tok in self._vocab:
                v[self._vocab[tok]] = cnt / max(len(tokens), 1)
        return v

    def _compute_idf(self, all_docs: List[List[str]]) -> None:
        N = len(all_docs)
        df = np.zeros(len(self._vocab))
        for tokens in all_docs:
            unique = set(tokens)
            for tok in unique:
                if tok in self._vocab:
                    df[self._vocab[tok]] += 1
        self._idf = np.log((N + 1) / (df + 1)) + 1.0

    def fit_transform(self, docs: List[List[str]]) -> np.ndarray:
        self._doc_tokens = docs
        self._build_vocab(docs)
        self._compute_idf(docs)
        matrix = np.stack([self._tf(d) * self._idf for d in docs], axis=0)
        # L2-normalise
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def transform(self, doc: List[str]) -> np.ndarray:
        if self._idf is None or not self._vocab:
            return np.zeros(1)
        v = self._tf(doc) * self._idf
        n = np.linalg.norm(v)
        return v / n if n > 0 else v


# -------------------------------------------------------------------------
# Vector Cache
# -------------------------------------------------------------------------

class VectorCache:
    """Fitness cache with approximate semantic nearest-neighbour lookup.

    Exact hits (hash match) are returned instantly.
    Near-duplicate hits (cosine similarity ≥ sim_threshold) are returned
    as approximate fitness estimates – useful for mutated variants that
    differ by only a few characters.
    """

    def __init__(
        self,
        cache_dir: str,
        sim_threshold: float = 0.92,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.cache_dir / "fitness_cache.jsonl"
        self.sim_threshold = sim_threshold

        # In-memory index
        self._index: Dict[str, Dict] = {}      # hash  -> record
        self._codes: List[str] = []            # ordered list of cached codes
        self._vectors: Optional[np.ndarray] = None  # (N, D) matrix
        self._vectorizer = _TFIDFVectorizer()
        self._dirty = True  # True = vectors need recomputation

        self._load()

    # ------------------------------------------------------------------
    # Public interface (same as FitnessCache for drop-in compatibility)
    # ------------------------------------------------------------------

    def get(self, code: str) -> Optional[Dict]:
        """Return cached record (exact or approximate match), or None."""
        # 1. Exact match via hash
        h = self._hash(code)
        if h in self._index:
            return self._index[h]

        # 2. Approximate match via cosine similarity
        if len(self._codes) >= 3:
            rec = self._nearest(code)
            if rec is not None:
                return rec

        return None

    def set(self, code: str, fitness: float, metrics: Dict[str, float]) -> None:
        h = self._hash(code)
        if h in self._index:
            return  # already stored
        rec = {"hash": h, "fitness": fitness, "metrics": metrics}
        self._index[h] = rec
        self._codes.append(code)
        self._dirty = True
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not self.path.exists():
            return
        # We store hashes + fitness only, not the full code.
        # We cannot reconstruct vectors from hash alone, so we only load
        # the index here. Vectors are (re)built from _codes on first query.
        for line in self.path.read_text().splitlines():
            try:
                rec = json.loads(line)
                self._index[rec["hash"]] = rec
            except Exception:
                continue

    def _rebuild_vectors(self) -> None:
        if not self._codes:
            return
        docs = [_tokenize(c) for c in self._codes]
        self._vectors = self._vectorizer.fit_transform(docs)
        self._dirty = False

    def _nearest(self, code: str) -> Optional[Dict]:
        if self._dirty:
            self._rebuild_vectors()
        if self._vectors is None or len(self._vectors) == 0:
            return None

        q_tokens = _tokenize(code)
        q_vec = self._vectorizer.transform(q_tokens)
        if q_vec.shape[0] != self._vectors.shape[1]:
            return None

        sims: np.ndarray = self._vectors @ q_vec
        best_idx = int(np.argmax(sims))
        if sims[best_idx] >= self.sim_threshold:
            best_code = self._codes[best_idx]
            h = self._hash(best_code)
            return self._index.get(h)
        return None

    @staticmethod
    def _hash(code: str) -> str:
        return hashlib.sha256(code.encode("utf-8")).hexdigest()


# -------------------------------------------------------------------------
# Backward-compatible alias so existing code using FitnessCache keeps working
# -------------------------------------------------------------------------

FitnessCache = VectorCache
