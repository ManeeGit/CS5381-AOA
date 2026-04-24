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
        """Look up a candidate by exact hash, then by approximate similarity.

        Two-stage lookup:

        1. **Exact match** — SHA-256 hash of ``code`` is looked up in the
           in-memory index.  O(1), no vector computation.
        2. **Approximate match** — if the index has at least 3 entries, the
           query is vectorised (TF-IDF) and the nearest cached code is found
           via cosine similarity.  If the similarity ≥ ``sim_threshold`` the
           cached record is returned as an approximate fitness estimate.

        Parameters
        ----------
        code : str
            Python source code of the candidate to look up.

        Returns
        -------
        dict or None
            Cached fitness record with keys ``hash``, ``fitness``,
            ``metrics``, ``timestamp``, or ``None`` on cache miss.
        """
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
        """Store a new fitness record in the cache.

        Computes the SHA-256 hash of ``code`` and writes the record to both
        the in-memory index and the JSONL backing file.  Idempotent — if the
        hash is already in the index the record is silently skipped.

        Also appends ``code`` to the in-memory ``_codes`` list used for
        vector similarity searches and marks ``_dirty = True`` so the
        vector index will be rebuilt on the next ``get`` call.

        Parameters
        ----------
        code : str
            Python source code of the evaluated candidate.
        fitness : float
            Fitness score in [0, 1] as returned by the evaluator.
        metrics : dict
            Detailed per-dimension metric dictionary (varies by evaluator).
        """
        from datetime import datetime, timezone
        h = self._hash(code)
        if h in self._index:
            return  # already stored
        rec = {
            "hash": h,
            "fitness": fitness,
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self._index[h] = rec
        self._codes.append(code)
        self._dirty = True
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load the JSONL cache file into the in-memory index.

        Reads each line from ``fitness_cache.jsonl``, parsing JSON records.
        Only hashes and fitness data are stored in the file (not the raw
        code), so vectors cannot be rebuilt from the file alone — they are
        built lazily from ``_codes`` which accumulates during the session.

        Silently skips malformed lines.
        """
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
        """Rebuild the TF-IDF matrix from all in-session cached codes.

        Called lazily when ``_dirty`` is set (i.e., after any ``set`` call).
        Tokenises every code in ``_codes``, re-fits the TF-IDF vocabulary,
        and stores the L2-normalised embedding matrix in ``_vectors``.
        Sets ``_dirty = False`` so subsequent queries skip the rebuild.
        """
        if not self._codes:
            return
        docs = [_tokenize(c) for c in self._codes]
        self._vectors = self._vectorizer.fit_transform(docs)
        self._dirty = False

    def _nearest(self, code: str) -> Optional[Dict]:
        """Find the most similar cached code and return its record.

        Vectorises ``code`` using the current TF-IDF vocabulary, computes
        cosine similarity against all cached vectors, and returns the record
        for the nearest neighbour if its similarity ≥ ``sim_threshold``.

        Parameters
        ----------
        code : str
            Python source code to query.

        Returns
        -------
        dict or None
            Nearest cached fitness record, or ``None`` if below threshold.
        """
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
        """Return the SHA-256 hex digest of ``code`` (UTF-8 encoded).

        Used as the unique cache key for exact-match lookups.
        """
        return hashlib.sha256(code.encode("utf-8")).hexdigest()


# -------------------------------------------------------------------------
# Backward-compatible alias so existing code using FitnessCache keeps working
# -------------------------------------------------------------------------

FitnessCache = VectorCache
