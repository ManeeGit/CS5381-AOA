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
   - Fitness = 0.6 × score + 0.3 × survival_time - 0.1 × steps
   
2. **3x3 Matrix Multiplication**: Optimizes code for correctness and computational efficiency
   - Fitness = 0.7 × correctness + 0.3 × (1 - normalized_ops)

##  System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                         │
│  ┌──────────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  Streamlit UI    │  │  FastAPI     │  │  Command Line         │ │
│  │  (app.py)        │  │  (api.py)    │  │  (run_experiment.py)  │ │
│  └──────────────────┘  └──────────────┘  └────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                      Evolution Engine (src/engine)                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  runner.py - Orchestrates experiments                          │ │
│  │    • Load configuration and templates                          │ │
│  │    • Initialize evaluators and cache                           │ │
│  │    • Run evolution for each mode                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  evolve.py - Core evolutionary algorithm                       │ │
│  │    • Initialize population from base code                      │ │
│  │    • Evaluate fitness (with caching)                           │ │
│  │    • Select top-K elites                                       │ │
│  │    • Generate new candidates via mutation/LLM                  │ │
│  │    • Iterate for n generations                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  mutations.py - Mutation operators                             │ │
│  │    • random_perturb_parameters()                               │ │
│  │    • swap_two_lines()                                          │ │
│  │    • replace_fragment(templates)                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────┬────────────────────────────┬────────────┬───────────┘
               │                            │            │
    ┌──────────▼────────┐      ┌───────────▼──────┐    │
    │   LLM Module      │      │   Evaluators     │    │
    │   (src/llm)       │      │  (src/evaluators)│    │
    ├───────────────────┤      ├──────────────────┤    │
    │ • base.py         │      │ • pacman.py      │    │
    │   (Abstract)      │      │ • matrix.py      │    │
    │ • local.py        │      │ • wrappers.py    │    │
    │   (llama.cpp)     │      │                  │    │
    │ • remote.py       │      │ Fitness:         │    │
    │   (OpenAI/Gemini) │      │ F = Σ wᵢ·mᵢ      │    │
    └───────────────────┘      └──────────────────┘    │
                                                        │
                               ┌────────────────────────▼─────────┐
                               │  Fitness Cache (src/cache)       │
                               │  • SHA-256 based deduplication   │
                               │  • JSONL storage                 │
                               │  • Persistent across runs        │
                               └──────────────────────────────────┘
```

### Component Descriptions

| Component | Description | Key Responsibilities |
|-----------|-------------|----------------------|
| **User Interface** | Streamlit web app, FastAPI REST API, CLI | Parameter configuration, result visualization, user interaction |
| **Evolution Engine** | Core evolutionary algorithm implementation | Population management, selection, generation loop |
| **Mutation Operators** | Code transformation functions | Random perturbation, line swaps, template replacement |
| **LLM Module** | Language model integration | Code improvement via local (llama.cpp) or remote (GPT/Gemini) LLMs |
| **Evaluators** | Fitness computation | Execute code, measure metrics, compute fitness scores |
| **Fitness Cache** | Persistent cache system | Avoid redundant evaluations, SHA-256 hashing |
| **Templates** | Code fragment library | Predefined code patterns for template replacement |

### Data Flow

1. **Initialization**: Load config → Initialize population from base code
2. **Evaluation**: Execute code → Measure metrics → Compute fitness → Cache result
3. **Selection**: Sort by fitness → Keep top-K candidates
4. **Breeding**: Clone/mutate/LLM-improve elite candidates → Create new population
5. **Iteration**: Repeat steps 2-4 for n generations
6. **Output**: Generate plots, CSV files, display results

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

3. **Dual Problem Support**:
   - **Pacman Agent Optimization**: Evolves game-playing agents
   - **3x3 Matrix Multiplication**: Optimizes computational efficiency

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
Project/
├── app.py                    # Streamlit web interface
├── api.py                    # FastAPI REST endpoint
├── run_experiment.py         # Batch experiment runner
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── data/
│   ├── templates/            # Base code templates
│   │   ├── matrix_base.py
│   │   └── pacman_agent_template.py
│   └── cache/               # Fitness cache storage (auto-generated)
├── src/
│   ├── engine/              # Evolution engine
│   │   ├── evolve.py       # Core evolution algorithm
│   │   ├── mutations.py    # Mutation operators
│   │   ├── runner.py       # Experiment orchestration
│   │   └── types.py        # Data structures
│   ├── evaluators/          # Fitness evaluation
│   │   ├── matrix.py       # Matrix multiplication evaluator
│   │   ├── pacman.py       # Pacman agent evaluator
│   │   └── wrappers.py     # Evaluator wrappers
│   ├── llm/                 # Language model integration
│   │   ├── base.py         # Abstract LLM interface
│   │   ├── local.py        # Local LLM (llama.cpp)
│   │   └── remote.py       # Remote LLM (OpenAI/Gemini)
│   ├── cache/               # Caching system
│   │   └── cache.py        # Fitness cache implementation
│   └── utils/               # Utilities
│       └── config.py       # Configuration management
├── outputs/                 # Generated plots and CSV files (auto-generated)
├── logs/                    # Execution logs (auto-generated)
└── third_party/
    └── pacman/             # UC Berkeley Pacman project (optional)
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
