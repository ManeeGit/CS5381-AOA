# CS5381 AOA – Group 2 Presentation Script
## "Evolve" — AlphaEvolve-Inspired Evolutionary Code Optimizer
**Target: ~2 minutes (~20 seconds per slide) | 6 Slides**

---

## Slide 1 — Title (~15 seconds)

> **Speaker: any member**

"Hello everyone. Our project is called **Evolve** — an AlphaEvolve-inspired framework that uses evolutionary algorithms to automatically improve code.
We're Group 2. Today I'll walk you through what we built, how it works, and what the results showed — in about two minutes."

---

## Slide 2 — Group Members & Configurations (~20 seconds)

> **Speaker: any member**

"Our team of five each ran the system with a different configuration — different LLM backends, population sizes, and generation counts — so we could compare results across machines and settings.
All configs use the same `seed=42` for reproducibility."

| Member | Config Highlights |
|---|---|
| Bhanu Sankar Ravi | Ollama local, matrix + pacman |
| Johitha Konduru | Remote LLM, pseudocode |
| Lakshman Pukhraj | No-LLM baseline |
| Maneesh Malepati | llm_guided, pacman |
| Demo Student | All three problems, default config |

---

## Slide 3 — What We Built (~25 seconds)

> **Speaker: whoever handles the architecture**

"We support **three problems**: Pacman (game-playing agent), Matrix multiplication (correctness + efficiency), and Pseudocode (sorting algorithm quality with four configurable fitness dimensions).

We have **three evolution modes** — a no-evolution baseline, random mutation, and LLM-guided mutation using Ollama with `qwen2.5-coder`.

And **three interfaces**: a live Streamlit UI, a FastAPI REST API, and a CLI profiler."

Key fitness functions:
- **Pacman:** `F = 0.6·score + 0.3·survival − 0.1·steps`
- **Matrix:** `F = 0.7·correct + 0.3·(1 − ops_ratio)`
- **Pseudocode:** `F = w1·correct + w2·runtime + w3·length + w4·readability`

---

## Slide 4 — The Evolutionary Loop (~20 seconds)

> **Speaker: whoever handles the algorithm**

"The loop is five steps — straight from AOA:

1. **Initialise** — seed population from a base template
2. **Evaluate** — run each candidate through the fitness function
3. **Select** — greedy top-K elite selection
4. **Mutate** — random perturbation, or LLM-guided rewrite for 20% of candidates
5. **Cache & Repeat** — vector cache avoids re-evaluating identical or near-identical code

This repeats for however many generations you configure. Greedy, randomised, and approximation — all three AOA paradigms in one loop."

---

## Slide 5 — Results (~25 seconds)

> **Speaker: whoever ran the experiments**

"Matrix fitness hits near-ceiling at 0.99 across all modes — the seed template was already close to optimal for a 2×2 problem.

Pacman is where we see the real difference: LLM-guided mutation reaches **+20–45% above baseline**, random mutation gives +8%. That's not luck — it's consistent across runs.

The caching system cut repeat evaluation cost by **60–80%** in later generations. And the pseudocode evaluator showed bubble sort evolving toward quicksort-like patterns, fitness going from 0.855 to 0.873."

| Mode | Matrix Fitness | Pacman Fitness | vs Baseline |
|---|---|---|---|
| no_evolution | 0.99 | ~58 | — |
| random_mutation | 0.99 | ~63 | +8% |
| llm_guided | 0.99 | ~70+ | +20–45% |

---

## Slide 6 — Demo & Takeaways (~15 seconds)

> **Speaker: demo runner**

"You can run the live demo with:
```
streamlit run app.py  →  http://localhost:8501
```
Select a problem, tune generations and population size, hit Run — and watch the fitness bars update in real time with a code diff.

**Key takeaways:**
- LLM guidance is consistently better than random — not luck
- Greedy top-K selection is simple but effective
- Modular design: swap evaluator or LLM backend without touching the engine
- This directly connects to AOA: **Greedy** (top-K), **Randomised** (mutations), **Approximation** (fitness budget)

GitHub: [github.com/ManeeGit/CS5381-AOA](https://github.com/ManeeGit/CS5381-AOA)
Demo Video: [youtu.be/b2GBt0VEED0](https://youtu.be/b2GBt0VEED0)"

---

## References

1. A. Novikov et al., *AlphaEvolve: A coding agent for scientific and algorithmic discovery*, arXiv:2506.13131, Jun. 2025.
2. S. Tamilselvi, *Introduction to Evolutionary Algorithms*, IntechOpen, 2022.
3. UC Berkeley, *Introduction to AI — Pacman Projects*. http://ai.berkeley.edu
4. Meta AI, *Ollama: Run large language models locally*. https://ollama.com
