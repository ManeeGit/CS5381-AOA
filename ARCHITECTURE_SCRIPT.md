# Architecture Diagram – Presentation Script
## CS5381 · Analysis of Algorithms · Evolve System

---

## SLIDE INTRO — Say this first

> "This is the full system architecture for **Evolve**, our evolutionary algorithm discovery
> system inspired by AlphaEvolve. The diagram is divided into six horizontal layers,
> each colour-coded, and data flows top-down from the user interface all the way down
> to the fitness cache and disk outputs."

---

## LAYER 1 – UI Layer *(Blue)*

**File:** `app.py`

> "At the very top we have the **Streamlit Web App**. This is what the user interacts with.
> It has two experiment tabs — one for the **Matrix Multiplication** problem and one for
> the **Pacman Agent** problem. Inside each tab the user can:
> - Choose which LLM provider to use (Ollama, OpenAI, or Gemini).
> - Edit the base code directly — we call this **human-in-the-loop** code injection.
> - Hit 'Run Experiment' and watch a **live fitness chart** update generation by generation.
>
> Once the user clicks Run, a call goes straight down to the Runner."

---

## LAYER 2 – Orchestration *(Blue)*

**File:** `src/engine/runner.py`

> "The **Runner** is the central coordinator of the whole system. When it receives a
> run request from the UI it does four things in order:
>
> 1. **Loads `config.yaml`** — this single file controls everything: LLM provider,
>    model name, number of generations, population size, top-k elites, mutation rate,
>    matrix size, and the Pacman layout.
> 2. **Instantiates the correct LLM** — Ollama for local GPU, RemoteLLM for OpenAI
>    or Gemini, or the LocalLLM fallback.
> 3. **Wires together the Evaluator** for the chosen problem.
> 4. **Launches the Evolver across three modes** — no_evolution, random_mutation, then
>    llm_guided — and once all three finish, **auto-saves a timestamped CSV** to
>    the `outputs/` folder."

---

## LAYER 3 – Evolution Engine *(Blue, three mode badges)*

**Files:** `src/engine/evolve.py`, `src/engine/mutations.py`

> "The heart of the system is the **Evolver**. It runs the same evolutionary loop in
> each of the three modes. Here is what happens each generation:
>
> 1. The current population of candidate code strings is **evaluated in parallel** using
>    Python's `ThreadPoolExecutor` with up to four workers.
> 2. Candidates are sorted by fitness and the **top-k elites are preserved** — this is
>    elitism, a classic EA technique.
> 3. The remainder of the next population is filled by **mutating elite parents**.
>
> **The three modes differ only in how mutation works:**
>
> | Mode | What it does |
> |------|-------------|
> | `no_evolution` | Runs exactly one generation with the original code — pure baseline. |
> | `random_mutation` | Every new child is produced by one of three blind mutations (see below). |
> | `llm_guided` | With 45% probability the LLM is asked to *improve* the parent code; otherwise falls back to random mutation. |
>
> **Adaptive mutation rate:** If the best fitness has not improved for more than two
> consecutive generations (stagnation), the mutation rate is boosted by 1.5×. Outside
> stagnation it decays by 30% over the course of the run — exploration early,
> exploitation late.
>
> **The three random mutation operators (mutations.py):**
> - `perturb` — nudges random numeric literals in the code by ±1 or ±2.
> - `swap_lines` — randomly swaps two lines in the code body.
> - `replace_fragment` — grafts a 3–6 line snippet from a template file into the code."

---

## LAYER 4a – LLM Layer *(Purple, left column)*

**Files:** `src/llm/base.py`, `src/llm/ollama_client.py`, `src/llm/remote.py`, `src/llm/local.py`

> "On the left we have the **LLM layer**. There is a single abstract `LLMClient`
> interface that defines one method: `improve(prompt, code) → code`. Three concrete
> implementations plug in behind it:
>
> - **OllamaLLM** — talks to a locally running Ollama server at `localhost:11434`.
>   The default model is `qwen2.5-coder:1.5b`. It sends the current code to the model
>   with a task description and expects clean Python back. If Ollama is not running it
>   falls back automatically.
> - **RemoteLLM** — calls the OpenAI or Google Gemini API using an API key from the
>   environment variable `LLM_API_KEY`.
> - **LocalLLM** — a zero-dependency fallback that applies a lightweight text
>   transformation without needing any external model.
>
> Only the `llm_guided` evolution mode actually calls `improve()`. The other two modes
> use the LLM layer only through the random mutations."

---

## LAYER 4b – Evaluator Layer *(Green, right column)*

**Files:** `src/evaluators/matrix.py`, `src/evaluators/pacman.py`, `src/evaluators/wrappers.py`

> "On the right we have the **Evaluators** — one per problem domain.
>
> **MatrixEvaluator:**
> The problem is to write a correct 3×3 matrix multiplication function in pure Python.
> For every candidate the evaluator:
> 1. Dynamically `exec()`s the code and extracts the `matmul3` function.
> 2. Runs it against five random integer matrices and checks results against `numpy`'s
>    `@` operator.
> 3. Counts the number of `*` and `+` operators as a proxy for operation count.
>
> The fitness formula is:
> $$\\text{fitness} = 0.7 \\times \\text{correctness} + 0.3 \\times \\text{ops\\_score}$$
>
> **PacmanEvaluator:**
> The problem is to evolve a Pacman AI agent. The evaluator writes the candidate code
> to a Python file on disk, then invokes the Pacman game engine as a **subprocess**.
> It parses stdout for three metrics and combines them:
> $$\\text{fitness} = 0.6 \\times \\text{score} + 0.3 \\times \\text{survival} - 0.1 \\times \\text{steps}$$
>
> If the Pacman binary is not available (e.g. during unit tests) the evaluator falls back
> to a deterministic heuristic simulation based on code complexity.
>
> **Wrappers:**
> `MatrixWrapper` and `PacmanWrapper` sit between the Evolver and the raw evaluators.
> The PacmanWrapper also sanitizes the evolved code through the LLM code cleaner before
> writing it to disk, with a guaranteed-valid safe agent as the last resort."

---

## LAYER 5 – Cache Layer *(Amber)*

**Files:** `src/cache/vector_cache.py`, `data/cache/fitness_cache.jsonl`

> "Every fitness evaluation is expensive — Pacman runs a full game, and matrix evaluation
> calls an LLM. The **FitnessCache** (implemented as a VectorCache) avoids redundant
> evaluations in two stages:
>
> 1. **Exact match** — SHA-256 hash of the code string. Cache hit in O(1).
> 2. **Semantic similarity** — if no exact hit, it computes a lightweight **TF-IDF
>    vector** over Python tokens (identifiers, operators, numbers) and finds the
>    nearest neighbour by cosine similarity. If the similarity exceeds a threshold,
>    the neighbour's fitness is returned instead of re-evaluating.
>
> The cache persists to a **JSONL file** on disk so results survive restarts.
> This design directly implements the AlphaEvolve requirement to reuse previous
> evaluation results rather than wasting them."

---

## LAYER 6 – Data, Config & Outputs *(Orange)*

**Files:** `config.yaml`, `data/templates/`, `outputs/`, `student_data/`, `profile_experiment.py`

> "At the bottom we have the data and configuration layer.
>
> - **`config.yaml`** is the single source of truth for every tunable parameter.
>   The UI reads it at startup; the Runner patches it for human-in-the-loop overrides.
> - **`data/templates/`** holds the seed files — `matrix_base.py` and
>   `pacman_agent_template.py`. The Runner always resets the Pacman agent back to the
>   clean template before each run so evolved code from a previous run never contaminates
>   the next baseline.
> - **`outputs/`** collects every auto-saved timestamped CSV.
> - **`profile_experiment.py`** is our cProfile demo file. It patches the config to 2
>   generations so profiling finishes in seconds, then uses `pstats` to print the
>   top-20 functions sorted by both cumulative time and self time."

---

## CLOSING — Data flow summary

> "To summarize the end-to-end data flow in one sentence:
>
> A user request in the **Streamlit UI** triggers the **Runner**, which configures and
> starts the **Evolver** across three modes. Each generation, the Evolver mutates
> candidates — using either **random operators** or an **LLM** — checks the **Cache**
> before calling the **Evaluator**, scores every candidate, keeps the elites, and
> repeats. Final results are streamed back to the UI as a live chart and saved to disk
> as a CSV."

---

## Quick Q&A Answers

**Q: Why three modes?**
> "Three modes give us a controlled comparison: baseline (no change), blind stochastic
> search (random mutation), and informed search (LLM). The fitness chart in the UI
> overlays all three so the benefit of LLM guidance is immediately visible."

**Q: Why TF-IDF for the cache instead of a real embedding model?**
> "Zero external dependencies and O(n·vocab) compute. For code that differs only in
> numeric constants or variable names — which is exactly what our mutations produce —
> token-frequency overlap is a very good proxy for semantic similarity."

**Q: How does cProfile fit in?**
> "We run `cProfile` around `run_experiment()`. The `cumtime` column tells us which
> function chain consumes the most wall-clock time end-to-end, and `tottime` tells us
> which single function body is the hottest. In our runs, `history_to_df` and the CSV
> auto-save dominate — the actual evolution loop is fast because the cache absorbs
> most re-evaluations."
