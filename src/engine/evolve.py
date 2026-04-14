from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from ..cache.cache import FitnessCache
from ..llm.base import LLMClient
from .mutations import mutate, mutate_with_meta
from .types import Candidate, GenerationResult


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
        population = self._init_population(base_code)
        history: List[GenerationResult] = []
        
        # Adaptive mutation rate (starts high, decreases over time)
        initial_mutation_rate = self.cfg.mutation_rate
        best_fitness_ever = float('-inf')
        stagnation_count = 0

        for gen in range(self.cfg.generations):
            # Evaluate all candidates
            for cand in population:
                self._evaluate(cand)

            population.sort(key=lambda c: c.fitness or 0.0, reverse=True)
            best = population[0]
            history.append(GenerationResult(gen, population[:], best))
            
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

        return history

    def _init_population(self, base_code: str) -> List[Candidate]:
        population = [Candidate(code=base_code, meta={"op": "base", "op_description": "Original base code (seed)"})]
        while len(population) < self.cfg.population_size:
            new_code, meta = mutate_with_meta(base_code, self.templates)
            population.append(Candidate(code=new_code, meta=meta))
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
