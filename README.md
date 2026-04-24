# Evolve: Evolutionary Algorithm Discovery

*A Simplified Evolutionary Agent for Algorithm Discovery - Inspired by AlphaEvolve*

This project implements an AlphaEvolve-inspired evolutionary algorithm system that mutates code, evaluates fitness, selects top candidates, and iterates across generations. It supports the UC Berkeley Pacman benchmark and a 3x3 matrix multiplication optimization task.

##  Demo Video

[Project Demo Video](https://youtu.be/b2GBt0VEED0)

##  Group 2 Members

| # | Name | Config ID | Configuration |
|---|------|-----------|---------------|
| 1 | Bhanu Sankar Ravi | 1 | Fast Exploration (High Mutation) |
| 2 | Maneesh Malepati | 2 | Balanced Standard |
| 3 | Lakshman Pukhraj | 3 | Conservative (Low Mutation) |
| 4 | Johitha Konduru | 4 | Elite-Focused |

##  Table of Contents

- [Project Overview](#-project-overview)
- [System Architecture](#-system-architecture)
- [Data Formats](#-data-formats)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation Guide](#-step-by-step-installation-guide)
- [Quick Start](#-quickstart)
- [User Interface](#-user-interface-features)
- [Usage Examples](#-usage-examples)
- [Understanding Results](#-interpreting-results)
- [Project Structure](#-project-structure)
- [Configuration](#-advanced-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [References](#-references)

##  Project Overview

**Evolve** is a research-style algorithm discovery system that uses Large Language Models (LLMs) and evolutionary algorithms to automatically optimize code. The system:

1. Takes initial code or algorithm as input
2. Generates candidate variations through mutations (random, template-based, LLM-guided)
3. Evaluates fitness of each candidate
4. Selects top performers and evolves them over multiple generations
5. Demonstrates measurable improvement in fitness scores over time

### Supported Problems

1. **Pacman Agent Optimization**: Evolves game-playing agents to maximize score, survival time, and efficiency
   - Fitness = 0.6 × score + 0.3 × survival_time − 0.1 × steps
   
2. **3×3 Matrix Multiplication**: Optimizes code for correctness and computational efficiency
   - Fitness = 0.7 × correctness + 0.3 × (1 − normalized_ops)

3. **Pseudocode / Algorithm Description** *(Bonus)*: Evolves sorting algorithm implementations across 4 dimensions
   - Fitness = w₁×correctness + w₂×runtime + w₃×length + w₄×readability  (Σwᵢ = 1)
   - Weights are configurable live via UI sliders before each run

##  System Architecture

### High-Level Architecture Diagram

```
╔═════════════════════════════════════════════════════════════════════╗
║                         USER INTERFACE LAYER                        ║
║  ┌───────────────────┐  ┌───────────────┐  ┌─────────────────────┐ ║
║  │  Streamlit UI     │  │  FastAPI      │  │  CLI / Batch        │ ║
║  │  app.py           │  │  api.py       │  │  run_experiment.py  │ ║
║  │  • Config sliders │  │  POST /run    │  │  profile_exp.py     │ ║
║  │  • Live charts    │  │  GET  /status │  │  cProfile output    │ ║
║  │  • Code diff view │  │  GET  /result │  │                     │ ║
║  └────────┬──────────┘  └──────┬────────┘  └──────────┬──────────┘ ║
╚═══════════╪════════════════════╪═══════════════════════╪═════════════╝
            └────────────────────┼───────────────────────┘
                                 │ run_experiment(cfg, problem)
╔════════════════════════════════▼════════════════════════════════════╗
║                    EXPERIMENT ORCHESTRATION                         ║
║  src/engine/runner.py                                               ║
║  ┌──────────────────────────────────────────────────────────────┐  ║
║  │  1. random.seed(42) + np.random.seed(42)  ← reproducibility  │  ║
║  │  2. Load templates from data/templates/                       │  ║
║  │  3. Build evaluator + cache for selected problem              │  ║
║  │  4. For each mode in [no_evolution, random_mutation,          │  ║
║  │                        llm_guided]:                           │  ║
║  │       call evolve(base_code, evaluator, llm, generations)     │  ║
║  │  5. Persist results to outputs/*.csv + *.xlsx                 │  ║
║  └──────────────────────────────────────────────────────────────┘  ║
╚════════════════════════════════╤════════════════════════════════════╝
                                 │
              ┌──────────────────▼──────────────────┐
              │      EVOLUTION CORE  evolve.py       │
              │  ┌────────────────────────────────┐  │
              │  │ for gen in range(generations): │  │
              │  │   evaluate population          │  │
              │  │   sort by fitness descending   │  │
              │  │   keep top_k elites            │  │
              │  │   fill rest via mutations/LLM  │  │
              │  │   yield GenerationResult       │  │
              │  └────────────────────────────────┘  │
              └──────┬────────────────────┬──────────┘
                     │                    │
     ┌───────────────▼──┐      ┌──────────▼──────────────────────┐
     │  MUTATION ENGINE │      │  FITNESS EVALUATORS             │
     │  mutations.py    │      │  src/evaluators/                │
     ├──────────────────┤      ├─────────────────────────────────┤
     │ random_perturb() │      │ pacman.py  — game simulator     │
     │ swap_two_lines() │      │   F = 0.6·score + 0.3·survival  │
     │ replace_frag()   │      │       − 0.1·steps               │
     │ llm_improve()    │      │                                 │
     └──────────────────┘      │ matrix.py  — 3×3 mult cost      │
              │                │   F = 0.7·correct + 0.3·(1−ops) │
     ┌────────▼─────────┐      │                                 │
     │  LLM PROVIDERS   │      │ pseudocode.py — sort algorithm  │
     │  src/llm/        │      │   F = w₁·correctness            │
     ├──────────────────┤      │     + w₂·runtime                │
     │ ollama_client.py │      │     + w₃·length                 │
     │   qwen2.5-coder  │      │     + w₄·readability  (Σwᵢ=1)  │
     │ remote.py        │      │                                 │
     │   OpenAI/Gemini  │      │ wrappers.py — uniform interface │
     │ local.py         │      │   MatrixWrapper / PacmanWrapper │
     │   llama.cpp      │      │   PseudocodeWrapper             │
     └──────────────────┘      └──────────────┬──────────────────┘
                                              │
                               ┌──────────────▼───────────────────┐
                               │  FITNESS CACHE  src/cache/       │
                               │  cache.py  +  vector_cache.py    │
                               ├──────────────────────────────────┤
                               │ • SHA-256 hash for dedup         │
                               │ • JSONL append-only store        │
                               │ • Cosine-similarity vector cache │
                               │   (reuses score for near-dupe)   │
                               │ • Timestamp per entry (ISO 8601) │
                               └──────────────────────────────────┘
```

### Component Descriptions

| Layer | Component | File(s) | Key Responsibility |
|-------|-----------|---------|-------------------|
| **UI** | Streamlit Web App | `app.py` | Live charts, config sliders, code diff, export |
| **UI** | REST API | `api.py` | POST `/run`, GET `/status`, GET `/result` |
| **UI** | CLI / Profiler | `run_experiment.py`, `profile_experiment.py` | Batch runs, cProfile analysis |
| **Orchestration** | Experiment Runner | `src/engine/runner.py` | Seeds RNG, dispatches per-mode evolution, saves CSV/XLSX |
| **Core** | Evolution Loop | `src/engine/evolve.py` | Selection (top-K), population breeding, generation results |
| **Core** | Mutation Operators | `src/engine/mutations.py` | `random_perturb`, `swap_lines`, `replace_fragment` |
| **Core** | Data Types | `src/engine/types.py` | `Candidate`, `GenerationResult` dataclasses |
| **Evaluation** | Matrix Evaluator | `src/evaluators/matrix.py` | Correctness + operation-count scoring |
| **Evaluation** | Pacman Evaluator | `src/evaluators/pacman.py` | Berkeley simulator wrapper, score/survival/steps |
| **Evaluation** | Pseudocode Evaluator | `src/evaluators/pseudocode.py` | 4-dim configurable fitness (bonus) |
| **Evaluation** | Wrappers | `src/evaluators/wrappers.py` | Uniform `evaluate(code)` interface |
| **LLM** | Ollama Client | `src/llm/ollama_client.py` | HTTP calls to `localhost:11434` |
| **LLM** | Remote LLM | `src/llm/remote.py` | OpenAI / Gemini REST API calls |
| **LLM** | Local LLM | `src/llm/local.py` | llama.cpp GGUF model inference |
| **Cache** | Fitness Cache | `src/cache/cache.py` | SHA-256 keyed JSONL cache |
| **Cache** | Vector Cache | `src/cache/vector_cache.py` | Cosine similarity near-duplicate detection |
| **Config** | Config Manager | `src/utils/config.py` | YAML parsing, typed `get()`, `raw[]` access |

### Data Flow Through the System

```
  User selects problem + hyperparameters
          │
          ▼
  runner.py sets RNG seeds (42) → loads base code template
          │
          ▼
  for each mode [no_evolution → random_mutation → llm_guided]:
          │
          ├── Initialise population [base_code × population_size]
          │
          └── for each generation:
                │
                ├── For each candidate:
                │     ├── hash code (SHA-256)
                │     ├── cache hit? → reuse fitness
                │     └── cache miss? → run evaluator → store in JSONL
                │
                ├── Sort candidates by fitness (descending)
                ├── Keep top_k elites unchanged
                │
                └── Fill remaining slots:
                      ├── 40% clone (exact copy of elite)
                      ├── 40% random mutate (perturb/swap/template)
                      └── 20% LLM improve (Ollama / OpenAI prompt)
          │
          ▼
  Persist: outputs/*.csv + *.xlsx + fitness_cache.jsonl
  Display: Streamlit charts / API JSON / CLI table
```

### Evolution Mode Comparison

| Aspect | No Evolution | Random Mutation | LLM-Guided |
|--------|-------------|-----------------|------------|
| Mutations applied | None | ✅ Random | ✅ Random + LLM |
| LLM calls | None | None | ~20% of candidates |
| Baseline purpose | Establish F₀ | Measure random search | Show AI benefit |
| Typical improvement | 0% | +15–25% | +40–55% |
| Generations needed | 1 | 5–15 | 5–15 |

### Fitness Function Design

All fitness values are normalised to **[0, 1]** so modes are directly comparable.

| Problem | Formula | Weights |
|---------|---------|---------|
| **Pacman** | F = w₁·score + w₂·survival − w₃·steps | 0.6 · 0.3 · 0.1 |
| **Matrix** | F = w₁·correct + w₂·(1 − ops_ratio) | 0.7 · 0.3 |
| **Pseudocode** | F = w₁·correct + w₂·runtime + w₃·length + w₄·read | configurable (UI sliders) |

##  Data Formats

### Configuration File (config.yaml)

```yaml
project:
  max_generations: 10        # Number of evolution cycles
  population_size: 8         # Candidates per generation
  top_k: 3                   # Elite candidates preserved
  mutation_rate: 0.35        # Probability of mutation
  seed: 42                   # Random seed for reproducibility
  cache_dir: "./data/cache"  # Fitness cache directory

pacman:
  root_path: "./third_party/pacman"
  base_agent_path: "./third_party/pacman/myAgents.py"
  command: "python pacman.py -p {agent} -l {layout} -q"
  layout: "mediumClassic"

matrix:
  size: 3                    # Matrix dimension (3x3)
  samples: 5                 # Number of test cases
  max_ops: 60                # Maximum allowed operations
```

### Fitness Cache Format (JSONL)

Each line is a JSON object representing a cached evaluation:

```json
{
  "code_hash": "a3f5e8b2c4d1...",     # SHA-256 hash of code
  "fitness": 0.847,                   # Computed fitness score
  "metrics": {                        # Problem-specific metrics
    "score": 523,
    "survival": 142,
    "steps": 89
  },
  "timestamp": "2026-02-13T10:30:45"
}
```

### Results DataFrame Columns

| Column | Type | Description |
|--------|------|-------------|
| `mode` | str | Evolution mode: no_evolution, random_mutation, llm_guided |
| `generation` | int | Generation number (0 to n-1) |
| `fitness` | float | Fitness score of best candidate |
| `metric_*` | float | Problem-specific metrics (score, survival, ops, etc.) |

### Template Files

Python code files stored in `data/templates/`:
- `pacman_agent_template.py`: Base Pacman agent structure
- `matrix_base.py`: Base matrix multiplication implementation
- Additional templates for fragment replacement

##  Features

### Core Capabilities

1. **Multiple Evolution Modes**:
   - `no_evolution`: Baseline with no mutations (single-shot evaluation)
   - `random_mutation`: Pure random code modifications (perturb, swap, template)
   - `llm_guided`: AI-assisted code improvements using language models

2. **Diverse Mutation Operators**:
   - **Random Parameter Perturbation**: Tweaks numeric literals in code
   - **Line Swapping**: Exchanges two random lines of code
   - **Template Replacement**: Injects code fragments from template library
   - **LLM-Guided Refinement**: Uses AI to improve code based on fitness goals

3. **Three Problem Domains**:
   - **Pacman Agent Optimization**: Evolves game-playing agents
   - **3×3 Matrix Multiplication**: Optimizes computational efficiency
   - **Pseudocode / Algorithm Description** *(Bonus)*: Evolves sorting algorithms with configurable multi-dimensional fitness

4. **Advanced Caching System**:
   - SHA-256 based code hashing for deduplication
   - Persistent JSONL storage across runs
   - Eliminates redundant fitness evaluations
   - Significantly speeds up evolution process

5. **Flexible LLM Integration** (PDF Requirement: "Mandatory: call a small LLM API"):
   - **Remote LLM** (default): OpenAI GPT-3.5/GPT-4, Google Gemini - Required for PDF compliance
   - **Local LLM** (alternative): llama.cpp with GGUF models (privacy-preserving, for development/testing)
   - Automatic fallback to deterministic improvement if LLM unavailable
   - Configurable via `config.yaml`

6. **Rich User Interface**:
   - Real-time fitness evolution visualization
   - Generation-by-generation breakdown
   - Operation statistics and explanations
   - Code comparison (initial vs. best solution)
   - Three output modes: Web UI, API, CLI

7. **Comprehensive Evaluation**:
   - Weighted multi-objective fitness functions
   - Problem-specific metrics tracking
   - Statistical analysis across evolution modes
   - Export results to CSV and PNG

##  Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows 10/11
- **Python**: Version 3.9 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended for LLM)
- **Disk Space**: 2GB for dependencies, additional space for LLM models if using local inference

### Required Software

1. **Python 3.9+**: [Download from python.org](https://www.python.org/downloads/)
2. **pip**: Python package manager (included with Python)
3. **git**: Version control system (optional, for cloning repository)

### Required for PDF Compliance

- **OpenAI API Key** or **Google API Key**: Required for LLM API integration (PDF requirement: "Mandatory: call a small LLM API")
  - Get OpenAI key: https://platform.openai.com/api-keys
  - Get Google Gemini key: https://makersuite.google.com/app/apikey

### Optional Components

- **UC Berkeley Pacman Project**: Required for Pacman problem evaluation
- **Local LLM Model**: GGUF format model for local inference (e.g., from Hugging Face) - Alternative to remote API for development/testing

##  Step-by-Step Installation Guide

### Step 1: Clone or Download the Project

```bash
# Option A: Clone with git
git clone <repository-url>
cd Project

# Option B: Download and extract ZIP
# Then navigate to the Project directory
cd path/to/Project
```

### Step 2: Create Virtual Environment

```bash
# Create a new virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install base requirements
pip install -r requirements.txt

# Optional: Install LLM packages (choose based on your needs)
# For OpenAI GPT:
pip install openai

# For Google Gemini:
pip install google-generativeai

# For local LLM:
pip install llama-cpp-python
```

### Step 4: Configure the System

```bash
# Copy example configuration (if provided)
# cp config.yaml.example config.yaml

# Edit configuration as needed
nano config.yaml  # or your preferred editor
```

### Step 5: (Optional) Set Up Pacman

```bash
# Download UC Berkeley Pacman project
# Visit: http://ai.berkeley.edu/project_overview.html

# Extract to third_party directory
mkdir -p third_party/pacman
# Copy Pacman files to third_party/pacman/

# Verify Pacman works
cd third_party/pacman
python pacman.py
cd ../..
```

### Step 6: Configure LLM API (Required for PDF Compliance)

**Important**: The PDF requirement specifies "Mandatory: call a small LLM API". By default, the system is configured to use OpenAI GPT-3.5-turbo.

```bash
# For OpenAI (default):
export OPENAI_API_KEY="your-openai-api-key"

# For Google Gemini (alternative):
export LLM_API_KEY="your-gemini-api-key"
# Also update config.yaml: set provider to "gemini" and model_name to "gemini-pro"

# Add to shell profile for persistence (~/.bashrc, ~/.zshrc, etc.)
echo 'export OPENAI_API_KEY="your-key"' >> ~/.bashrc
```

**Note**: To use a local model instead (for development/testing), update `config.yaml`:
```yaml
llm:
  provider: local
  model_name: llama.cpp
```

### Step 7: Run the Application

```bash
# Start Streamlit UI (recommended)
streamlit run app.py

# Or run batch experiment
python run_experiment.py

# Or start API server
uvicorn api:app --reload
```

##  Quickstart

If you've already completed the installation steps above:

### Option A: Interactive UI (Recommended)
```bash
cd Project
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
streamlit run app.py
```
Then open your browser to `http://localhost:8501`

### Option B: Batch Experiment
```bash
source .venv/bin/activate
python run_experiment.py
```
Results saved to `./outputs/`

### Option C: API Server
```bash
source .venv/bin/activate
uvicorn api:app --reload
```
API available at `http://localhost:8000`

API Example:
```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "matrix",
    "generations": 15,
    "population": 10,
    "top_k": 4,
    "mutation_rate": 0.4
  }'
```

##  User Interface Features

The Streamlit web interface provides:

1. **Problem Description**: Detailed explanation of each optimization problem
2. **Initial Code Display**: View the starting code before evolution begins
3. **Hyperparameter Controls**: Adjust generations, population size, top-k, mutation rate
4. **Real-Time Visualization**: Watch fitness improve across generations
5. **Comparison Charts**: Compare all three evolution modes simultaneously
6. **Best Solution Display**: View the final optimized code
7. **Operation Explanations**: Understand what mutations were applied
8. **Statistics Dashboard**: Analyze operation counts and fitness metrics
9. **References Section**: Academic citations and resources

##  Usage Examples

### Example 1: Quick Start with Matrix Problem

```bash
# Activate environment
source .venv/bin/activate

# Run Streamlit UI
streamlit run app.py

# In browser:
# 1. Select "matrix" problem
# 2. Set generations = 10
# 3. Click "Run Evolution"
# 4. Observe fitness improvement across modes
```

### Example 2: Using Remote LLM (OpenAI)

```bash
# Set API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Run with LLM-guided mode
streamlit run app.py

# In UI, the llm_guided mode will now use GPT-3.5-turbo
```

### Example 3: Batch Experiment with Custom Config

```bash
# Edit config.yaml
nano config.yaml

# Modify settings:
# max_generations: 20
# population_size: 12
# mutation_rate: 0.5

# Run batch experiment
python run_experiment.py
```

##  Understanding Evolution Modes

### No Evolution Mode
- **Purpose**: Establish baseline performance
- **Behavior**: Evaluates only the initial code (no mutations)
- **Use Case**: Compare against evolved solutions

### Random Mutation Mode
- **Purpose**: Test pure random search effectiveness
- **Behavior**: Applies random mutations without LLM guidance
- **Operations**: Parameter perturbation, line swaps, template injection
- **Use Case**: Measure value of intelligent vs. random search

### LLM-Guided Mode
- **Purpose**: Leverage AI for intelligent code improvement
- **Behavior**: Uses language model to refine code based on fitness goals
- **Mechanism**: 45% LLM improvement, remainder random mutation/cloning
- **Use Case**: Achieve best results through human-like reasoning

##  Interpreting Results

### Fitness Plots
- **X-axis**: Generation number (0 to n-1)
- **Y-axis**: Best fitness score in that generation
- **Lines**: One per evolution mode (color-coded)
- **Expected Pattern**: Upward trend for llm_guided and random_mutation

### Operation Statistics
Shows distribution of operations in final generation:
- **clone**: Exact copy of parent (no modification)
- **mutate**: Random mutations applied
- **llm_improve**: AI-guided refinement
- **base**: Original starting code

### Example Best Scores

| Mode | Final Fitness |
|------|---------------|
| no_evolution | 0.42 |
| random_mutation | 0.68 |
| llm_guided | 0.89 |

Higher fitness indicates better performance.

##  Project Structure

```
CS5381-AOA/
├── app.py                    # Streamlit web interface (3 problems + live charts)
├── api.py                    # FastAPI REST endpoint (POST /run, GET /result)
├── run_experiment.py         # Batch experiment runner
├── profile_experiment.py     # cProfile demo (3 profiling methods)
├── collect_student_data.py   # Per-student data collection script
├── config.yaml               # Primary configuration file
├── config.yaml.example       # Reference config with all options documented
├── requirements.txt          # Python dependencies
│
├── data/
│   ├── templates/            # Seed code templates for evolution
│   │   ├── matrix_base.py           # 3×3 naive matrix multiply
│   │   ├── pacman_agent_template.py # Reflexive Pacman agent
│   │   └── pseudocode_base.py       # Bubble sort (bonus evaluator seed)
│   └── cache/
│       └── fitness_cache.jsonl      # SHA-256 keyed evaluation cache
│
├── src/
│   ├── engine/
│   │   ├── runner.py         # Experiment orchestration + RNG seeding
│   │   ├── evolve.py         # Core evolutionary loop (selection + breeding)
│   │   ├── mutations.py      # random_perturb / swap_lines / replace_fragment
│   │   └── types.py          # Candidate, GenerationResult dataclasses
│   ├── evaluators/
│   │   ├── matrix.py         # Correctness + ops-count fitness
│   │   ├── pacman.py         # Berkeley simulator wrapper
│   │   ├── pseudocode.py     # 4-dim algorithm evaluator (bonus)
│   │   └── wrappers.py       # Uniform evaluate() interface
│   ├── llm/
│   │   ├── base.py           # Abstract LLMClient interface
│   │   ├── ollama_client.py  # Ollama HTTP client (qwen2.5-coder)
│   │   ├── remote.py         # OpenAI / Gemini REST calls
│   │   └── local.py          # llama.cpp GGUF inference
│   ├── cache/
│   │   ├── cache.py          # SHA-256 JSONL fitness cache
│   │   └── vector_cache.py   # Cosine-similarity near-dup cache
│   └── utils/
│       └── config.py         # Typed YAML config with raw[] access
│
├── outputs/                  # Auto-generated CSV + XLSX results
├── student_data/             # Per-student configs + analysis reports
│   ├── Bhanu_Sankar_Ravi/
│   ├── Maneesh_Malepati/
│   ├── Lakshman_Pukhraj/
│   ├── Johitha_Konduru/
│   └── Demo_Student/
└── third_party/
    └── pacman/               # UC Berkeley Pacman project files
```

##  LLM Integration

**PDF Requirement**: "Mandatory: call a small LLM API"

### Remote LLM (Default - Required for PDF Compliance)
The system is configured by default to use OpenAI GPT-3.5-turbo:

1. **Get an API Key**: 
   - OpenAI: https://platform.openai.com/api-keys
   - Google Gemini: https://makersuite.google.com/app/apikey

2. **Set Environment Variable**:
   ```bash
   export OPENAI_API_KEY="your-api-key"  # For OpenAI
   # or
   export LLM_API_KEY="your-api-key"     # For Gemini
   ```

3. **Configuration** (`config.yaml`):
   ```yaml
   llm:
     provider: openai           # or "gemini"
     model_name: gpt-3.5-turbo  # or "gpt-4", "gemini-pro"
   ```

### Local LLM (Alternative for Development/Testing)
For development without API costs, you can use local llama.cpp:

1. Update `config.yaml`:
   ```yaml
   llm:
     provider: local
     model_name: llama.cpp
   ```

2. Install: `pip install llama-cpp-python`
3. Download a GGUF model from Hugging Face
4. Falls back to deterministic improvement if model unavailable

##  Advanced Configuration

### Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_generations` | 10 | Number of evolution cycles |
| `population_size` | 8 | Candidates per generation |
| `top_k` | 3 | Elite candidates preserved |
| `mutation_rate` | 0.35 | Probability of mutation |
| `seed` | 42 | Random seed for reproducibility |

### Fitness Functions

**Pacman**: F = 0.6 × score + 0.3 × survival - 0.1 × steps  
**Matrix**: F = 0.7 × correctness + 0.3 × (1 - normalized_ops)

##  Troubleshooting

### Common Issues

**"Module not found" errors**:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

**Streamlit not starting**:
```bash
# Check if port 8501 is in use
lsof -i :8501
# Or specify a different port
streamlit run app.py --server.port 8502
```

**Pacman evaluation failing**:
- Verify Pacman files exist in `third_party/pacman/`
- Check that `pacman.py` runs independently
- Review paths in `config.yaml`

**Low fitness scores**:
- Increase `max_generations` for more evolution time
- Adjust `mutation_rate` (try 0.2-0.5 range)
- For matrix: ensure correctness before optimizing operations

##  Generated Outputs

All results are saved to the `outputs/` directory:
- **Plots**: PNG visualizations of fitness over generations
- **CSV Files**: Detailed tabular data for analysis
- **Cache**: `data/cache/fitness_cache.jsonl` stores evaluated candidates

##  Known Issues & Solutions

| # | Issue | Solution |
|---|-------|----------|
| 1 | **Ollama not reachable** — `[OllamaLLM] Ollama server not reachable at http://localhost:11434` | Run `ollama serve` in a separate terminal before starting the app. LLM-guided mutations fall back to random mutations automatically if Ollama is unavailable. |
| 2 | **Streamlit `use_column_width` deprecation warnings** | Harmless warnings from Streamlit. Upgrade Streamlit to latest: `pip install --upgrade streamlit`. |
| 3 | **Pacman evaluation fails / returns 0 score** | Ensure the UC Berkeley Pacman files exist in `third_party/pacman/`. The system auto-falls back to simulated scores if not found. |
| 4 | **`Module not found` on startup** | Activate the virtual environment first: `source .venv/bin/activate`, then `pip install -r requirements.txt`. |
| 5 | **LLM-guided mode produces no improvement** | Set `OPENAI_API_KEY` or `LLM_API_KEY` environment variable, or configure Ollama with a pulled model (`ollama pull qwen2.5-coder:1.5b`). |
| 6 | **Port 8501 already in use** | Run `streamlit run app.py --server.port 8502` or kill the existing process: `lsof -ti:8501 | xargs kill`. |
| 7 | **Low fitness scores after many generations** | Increase `max_generations` (try 20–30) and `population_size` (try 12–15). Also try the `Optimal` preset in the UI. |
| 8 | **SSL/urllib3 warning on Python 3.9 (macOS)** | Upgrade: `pip install --upgrade urllib3`. Or use Python 3.11+. |

---

##  Suggestions & Feedback

### Suggestions for Improvement

1. **Expand LLM Support**: Add support for Anthropic Claude and Mistral AI models to give users more LLM provider options without requiring API keys (via free-tier endpoints).

2. **Distributed Evolution**: Parallelize fitness evaluations using Python `multiprocessing` or `concurrent.futures` to reduce wall-clock time per generation, especially for large population sizes.

3. **Interactive Code Diff View**: Show a side-by-side diff of the initial code vs. the best evolved code in the UI so users can visually understand what mutations improved fitness.

4. **More Benchmark Problems**: Add additional optimization problems (e.g., sorting algorithm optimization, graph traversal) to make the framework more general-purpose beyond Pacman and matrix multiplication.

5. **Export to Jupyter Notebook**: Allow users to download a Jupyter notebook version of the evolution run with all charts embedded, making it easier to share results in academic settings.

6. **Adaptive Top-K**: Dynamically adjust `top_k` based on population diversity metrics to avoid premature convergence.

### Feedback

- **What worked well**: The modular architecture (engine / evaluators / LLM separated cleanly) made it straightforward to swap out fitness functions and LLM providers without touching core logic.
- **What was challenging**: Getting reproducible Pacman scores was difficult due to randomness in the game environment; adding a fixed random seed to the Pacman runner resolved most inconsistencies.
- **Course connection**: The evolutionary selection loop directly maps to concepts from the course (greedy selection, local search, and approximation). Framing it as "code as a genome" made the algorithm intuitive to implement and explain.

---

##  Contributing

This is an academic research project. To extend:
1. Add new problems in `src/evaluators/`
2. Implement new mutation strategies in `src/engine/mutations.py`
3. Integrate different LLM providers in `src/llm/`

##  License

Academic research project for CS5381 Analysis of Algorithms course.

##  References

1. **AlphaEvolve**: A. Novikov et al., "AlphaEvolve: A coding agent for scientific and algorithmic discovery," arXiv:2506.13131, Jun. 2025. [DOI: 10.48550/arXiv.2506.13131](https://doi.org/10.48550/arXiv.2506.13131)

2. **Evolutionary Algorithms**: S. Tamilselvi, "Introduction to Evolutionary Algorithms," in *Genetic Algorithms*, IntechOpen, 2022. [DOI: 10.5772/intechopen.104198](https://doi.org/10.5772/intechopen.104198)

3. **Overview of Evolutionary Algorithms**: H. Amit, "An Overview of Evolutionary Algorithms," *We Talk Data*, [Medium Article](https://medium.com/we-talk-data/an-overview-of-evolutionary-algorithms-90a52526603e)

4. **UC Berkeley Pacman AI Project**: [Project Overview](http://ai.berkeley.edu/project_overview.html)

5. **Streamlit Documentation**: [Streamlit.io](https://streamlit.io/)

6. **FastAPI Documentation**: [FastAPI](https://fastapi.tiangolo.com/)

7. **LangChain for LLM Integration**: [LangChain Python Docs](https://python.langchain.com/)

8. **Llama.cpp**: [GitHub Repository](https://github.com/ggerganov/llama.cpp)

9. **OpenAI API Documentation**: [OpenAI Platform](https://platform.openai.com/docs/)

10. **Google Gemini API**: [Google AI for Developers](https://ai.google.dev/)

##  Acknowledgments

- Inspired by AlphaEvolve and evolutionary computation research
- UC Berkeley Pacman AI project for the benchmark domain
- Built with Streamlit, FastAPI, and modern Python ecosystem
- Course: CS5381 Analysis of Algorithms

---

**Note**: Pacman evaluation requires the UC Berkeley Pacman project in `./third_party/pacman/`. The system will use simulated scores if Pacman files are not available.
