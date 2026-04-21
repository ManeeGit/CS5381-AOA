from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import List

from ..cache.cache import FitnessCache
from ..llm.base import LLMClient
from ..llm.ollama_client import OllamaLLM
from .mutations import mutate, mutate_with_meta
from .types import Candidate, GenerationResult


def _sanitize(code: str) -> str:
    """Deduplicate class definitions in mutated code."""
    try:
        return OllamaLLM._sanitize_code(code)
    except Exception:
        return code


@dataclass
class EvolutionConfig:
    generations: int
    population_size: int
    top_k: int
    mutation_rate: float


class Evolver:
    def __init__(
        self,
        cfg: EvolutionConfig,
        llm: LLMClient,
        cache: FitnessCache,
        templates: List[str],
        evaluator,
        prompt: str,
    ):
        self.cfg = cfg
        self.llm = llm
        self.cache = cache
        self.templates = templates
        self.evaluator = evaluator
        self.prompt = prompt

    def run(self, base_code: str, mode: str) -> List[GenerationResult]:
        population = self._init_population(base_code, mode=mode)
        history: List[GenerationResult] = []
        
        # Adaptive mutation rate (starts high, decreases over time)
        initial_mutation_rate = self.cfg.mutation_rate
        best_fitness_ever = float('-inf')
        stagnation_count = 0

        print(f"\n{'='*60}")
        print(f"[Evolver] Mode: {mode.upper()} | Generations: {self.cfg.generations} | Population: {self.cfg.population_size}")
        print(f"{'='*60}")
        run_start = time.time()

        for gen in range(self.cfg.generations):
            gen_start = time.time()
            # Evaluate all candidates
            for cand in population:
                self._evaluate(cand)

            population.sort(key=lambda c: c.fitness or 0.0, reverse=True)
            best = population[0]
            history.append(GenerationResult(gen, population[:], best))

            gen_elapsed = time.time() - gen_start
            best_fitness = best.fitness or 0.0
            metrics_str = " | ".join(
                f"{k}: {v:.2f}" for k, v in (best.metrics or {}).items()
            )
            print(
                f"  Gen {gen+1:>3}/{self.cfg.generations}"
                f" | Best Fitness: {best_fitness:>8.4f}"
                f" | {metrics_str}"
                f" | Time: {gen_elapsed:.2f}s"
            )
            
            # Track improvement for adaptive behavior
            if best.fitness and best.fitness > best_fitness_ever:
                best_fitness_ever = best.fitness
                stagnation_count = 0
            else:
                stagnation_count += 1

            if mode == "no_evolution":
                break
            
            # Adaptive mutation rate: increase if stagnating
            if stagnation_count > 2:
                adaptive_mutation_rate = min(1.0, initial_mutation_rate * 1.5)
            else:
                # Decay mutation rate over generations for exploitation
                adaptive_mutation_rate = initial_mutation_rate * (1.0 - 0.3 * gen / self.cfg.generations)

            elites = population[: self.cfg.top_k]
            next_pop = elites[:]

            while len(next_pop) < self.cfg.population_size:
                parent = random.choice(elites)
                if mode == "llm_guided" and random.random() < 0.6:
                    new_code = self.llm.improve(self.prompt, parent.code)
                    meta = {
                        "op": "llm_improve",
                        "op_description": f"LLM (Ollama/local) refined parent code; parent fitness={parent.fitness:.4f}" if parent.fitness else "LLM refinement",
                        "parent_fitness": str(parent.fitness),
                    }
                else:
                    if random.random() < adaptive_mutation_rate:
                        new_code, mut_meta = mutate_with_meta(parent.code, self.templates)
                        new_code = _sanitize(new_code)
                        meta = {**mut_meta, "parent_fitness": str(parent.fitness)}
                    else:
                        new_code = parent.code
                        meta = {
                            "op": "clone",
                            "op_description": f"Exact clone of elite parent; parent fitness={parent.fitness:.4f}" if parent.fitness else "Clone of parent",
                            "parent_fitness": str(parent.fitness),
                        }
                next_pop.append(Candidate(code=new_code, meta=meta))

            population = next_pop

        total_elapsed = time.time() - run_start
        final_best = history[-1].best
        print(f"\n[Evolver] Mode '{mode}' complete | Total Time: {total_elapsed:.2f}s | Best Fitness: {final_best.fitness or 0.0:.4f}")
        print(f"{'='*60}\n")
        return history

    def _init_population(self, base_code: str, mode: str = "") -> List[Candidate]:
        base = Candidate(code=base_code, meta={"op": "base", "op_description": "Original base code (seed)"})
        # no_evolution: baseline uses ONLY the original code — no mutations in initial pop
        if mode == "no_evolution":
            return [base]
        population = [base]
        import ast as _ast
        attempts = 0
        while len(population) < self.cfg.population_size:
            new_code, meta = mutate_with_meta(base_code, self.templates)
            new_code = _sanitize(new_code)
            # Reject syntactically invalid mutations (keep trying, but cap attempts)
            try:
                _ast.parse(new_code)
                population.append(Candidate(code=new_code, meta=meta))
            except SyntaxError:
                attempts += 1
                if attempts > 50:  # safety valve: accept even invalid after 50 fails
                    population.append(Candidate(code=base_code, meta={"op": "clone", "op_description": "Clone (mutation rejected)"}))
        return population

    def _evaluate(self, cand: Candidate) -> None:
        cached = self.cache.get(cand.code)
        if cached is not None:
            cand.fitness = cached["fitness"]
            cand.metrics = {k: float(v) for k, v in cached["metrics"].items()}
            return
        fitness, metrics = self.evaluator.evaluate(cand.code)
        cand.fitness = fitness
        cand.metrics = metrics
        self.cache.set(cand.code, fitness, metrics)
