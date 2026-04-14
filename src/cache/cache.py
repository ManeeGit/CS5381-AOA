# Re-export VectorCache as FitnessCache for backward compatibility.
# All cache logic now lives in vector_cache.py which provides semantic
# nearest-neighbour lookup in addition to exact hash matching.
from .vector_cache import VectorCache as FitnessCache  # noqa: F401

__all__ = ["FitnessCache"]
