# Evolve: Evolutionary Algorithm Discovery

This project implements an AlphaEvolve-inspired evolutionary algorithm system that mutates code, evaluates fitness, selects top candidates, and iterates across generations. It supports the UC Berkeley Pacman benchmark and a 3x3 matrix multiplication optimization task.

##  Project Overview

**Evolve** is a research-style algorithm discovery system that uses Large Language Models (LLMs) and evolutionary algorithms to automatically optimize code. The system:
- Takes initial code or algorithm as input
- Generates candidate variations through mutations (random, template-based, LLM-guided)
- Evaluates fitness of each candidate
- Selects top performers and evolves them over multiple generations
- Demonstrates measurable improvement in fitness scores over time

###  Demo Video

[Project Demo Video](https://youtu.be/placeholder) *(To be updated with actual video link)*

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
  samples: 10                # Number of test cases
  max_ops: 50                # Maximum allowed operations
```

### Fitness Cache Format (JSONL)

Each line is a JSON object representing a cached evaluation:

```json
{
  "code_hash": "a3f5e8...",          # SHA-256 hash of code
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
- **Evolutionary Code Generation**: Generates code variants through random mutation, template replacement, line swaps, and LLM-guided refinement
- **Multi-Mode Comparison**: Compares three evolutionary strategies:
  - `no_evolution`: Baseline with no mutations
  - `random_mutation`: Pure random code modifications
  - `llm_guided`: AI-assisted code improvements
- **Fitness Evaluation with Caching**: Efficient evaluation system with SHA-256 based caching to avoid redundant computations
- **Interactive Streamlit UI**: Real-time visualization with fitness plots, best scores, evolution history, and operation explanations
- **RESTful API**: FastAPI endpoint for programmatic experiment execution

### Supported Problems
1. **Pacman Agent Optimization**: Evolves game-playing agents to maximize score, survival time, and efficiency
2. **Matrix Multiplication**: Optimizes 3x3 matrix multiplication for correctness and operation count

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

### Optional Components

- **UC Berkeley Pacman Project**: Required for Pacman problem evaluation
- **Local LLM Model**: GGUF format model for local inference (e.g., from Hugging Face)
- **OpenAI API Key**: For GPT-3.5/GPT-4 integration
- **Google API Key**: For Gemini integration

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
# Copy example configuration
cp config.yaml.example config.yaml

# Edit configuration as needed
# On macOS/Linux:
nano config.yaml

# On Windows:
notepad config.yaml
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

### Step 6: (Optional) Configure LLM API

```bash
# For OpenAI:
export OPENAI_API_KEY="your-openai-api-key"

# For Google Gemini:
export LLM_API_KEY="your-gemini-api-key"

# Add to shell profile for persistence (~/.bashrc, ~/.zshrc, etc.)
echo 'export OPENAI_API_KEY="your-key"' >> ~/.bashrc
```

### Step 7: Run the Application

```bash
# Start Streamlit UI
streamlit run app.py

# Or run batch experiment
python run_experiment.py

# Or start API server
uvicorn api:app --reload
```

##  Prerequisites

##  Features

### Core Capabilities

1. **Multiple Evolution Modes**:
   - `no_evolution`: Baseline with no mutations (single-shot LLM or original code)
   - `random_mutation`: Pure random code modifications (perturb, swap, template)
   - `llm_guided`: AI-assisted code improvements using language models

2. **Diverse Mutation Operators**:
   - **Random Parameter Perturbation**: Tweaks numeric literals in code
   - **Line Swapping**: Exchanges two random lines of code
   - **Template Replacement**: Injects code fragments from template library
   - **LLM-Guided Refinement**: Uses AI to improve code based on fitness goals

3. **Dual Problem Support**:
   - **Pacman Agent Optimization**: Evolves game-playing agents
     - Fitness = 0.6 × score + 0.3 × survival_time - 0.1 × steps
   - **3x3 Matrix Multiplication**: Optimizes computational efficiency
     - Fitness = 0.7 × correctness + 0.3 × (1 - normalized_ops)

4. **Advanced Caching System**:
   - SHA-256 based code hashing for deduplication
   - Persistent JSONL storage across runs
   - Eliminates redundant fitness evaluations
   - Significantly speeds up evolution process

5. **Flexible LLM Integration**:
   - **Local LLM**: llama.cpp with GGUF models (privacy-preserving)
   - **Remote LLM**: OpenAI GPT-3.5/GPT-4, Google Gemini
   - Automatic fallback to deterministic improvement if LLM unavailable

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

### Example 2: API-Based Experiment

```bash
# Start API server
uvicorn api:app --reload

# In another terminal, call API:
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

### Example 4: Using Remote LLM (OpenAI)

```bash
# Set API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Run with LLM-guided mode
streamlit run app.py

# In UI, the llm_guided mode will now use GPT-3.5-turbo
```

##  Understanding Evolution Modes

### No Evolution Mode
- **Purpose**: Establish baseline performance
- **Behavior**: Evaluates only the initial code (or single LLM pass)
- **Use Case**: Compare against evolved solutions

### Random Mutation Mode
- **Purpose**: Test pure random search effectiveness
- **Behavior**: Applies random mutations without LLM guidance
- **Operations**: Parameter perturbation, line swaps, template injection
- **Use Case**: Measure value of intelligent vs. random search

### LLM-Guided Mode
- **Purpose**: Leverage AI for intelligent code improvement
- **Behavior**: Uses language model to refine code based on fitness goals
- **Mechanism**: 60% LLM improvement, 35% random mutation, 5% cloning
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

### Best Scores Table
| Mode | Final Fitness |
|------|---------------|
| no_evolution | 0.42 |
| random_mutation | 0.68 |
| llm_guided | 0.89 |

Higher fitness indicates better performance.

- **Python 3.9 or higher**
- **(Optional) UC Berkeley Pacman project for Pacman benchmarks**
- **(Optional) Node.js 16+ for frontend development**

- **Python 3.9 or higher**
- **(Optional) UC Berkeley Pacman project for Pacman benchmarks**
- **(Optional) Node.js 16+ for frontend development**

##  Quickstart (If Already Set Up)

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
python run_experiment.py
```
Results saved to `./outputs/`

### Option C: API Server
```bash
uvicorn api:app --reload
```
API available at `http://localhost:8000`

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

### 1. Environment Setup

```bash
# Clone or navigate to the project directory
cd Project

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configuration

The project uses `config.yaml` for configuration. Default settings:
- **Generations**: 10
- **Population Size**: 8
- **Top-K Selection**: 3
- **Mutation Rate**: 0.35

You can modify these in the UI or edit `config.yaml` directly.

### 3. Running the Application

#### Option A: Interactive UI (Recommended)
```bash
streamlit run app.py
```
Then open your browser to `http://localhost:8501`

**UI Features**:
- Select problem type (Pacman or Matrix)
- Adjust hyperparameters (generations, population, mutation rate)
- View real-time fitness evolution
- Compare different mutation strategies
- Inspect best solutions and operation statistics

#### Option B: Batch Experiment
```bash
python run_experiment.py
```
This runs experiments for both problems and saves results to `./outputs/`

#### Option C: API Server
```bash
uvicorn api:app --reload
```
API available at `http://localhost:8000`

**API Usage Example**:
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
│   │   └── remote.py       # Remote LLM stub (GPT/Gemini)
│   ├── cache/               # Caching system
│   │   └── cache.py        # Fitness cache implementation
│   └── utils/               # Utilities
│       └── config.py       # Configuration management
├── outputs/                 # Generated plots and CSV files (auto-generated)
├── logs/                    # Execution logs (auto-generated)
└── third_party/
    └── pacman/             # UC Berkeley Pacman project (optional)
```

##  Pacman Setup (Optional)

To use the Pacman benchmark:

1. Download the UC Berkeley Pacman AI project from:
   http://ai.berkeley.edu/project_overview.html

2. Place the Pacman files in `./third_party/pacman/`:
   ```
   third_party/pacman/
   ├── pacman.py
   ├── game.py
   ├── util.py
   └── ... (other Pacman files)
   ```

3. Create or update the agent file at `./third_party/pacman/myAgents.py` with your base agent (or use the template provided)

4. Update `config.yaml` if your paths differ:
   ```yaml
   pacman:
     root_path: ./third_party/pacman
     base_agent_path: ./third_party/pacman/myAgents.py
   ```

**Note**: If Pacman files are missing, the evaluator will use a simulation stub with random scores.

##  LLM Integration

### Local LLM (Default)
The project uses `llama.cpp` for local LLM inference. To use:

1. Install llama-cpp-python:
   ```bash
   pip install llama-cpp-python
   ```

2. Download a GGUF model (e.g., from Hugging Face) and update the path in your code

3. If no local model is available, the system falls back to a simple deterministic improvement

### Remote LLM (Advanced)
To use OpenAI GPT or Google Gemini:

1. Set your API key as an environment variable:
   ```bash
   export LLM_API_KEY="your-api-key-here"
   ```

2. Update `config.yaml`:
   ```yaml
   llm:
     provider: openai  # or "gemini"
     model_name: gpt-4
   ```

3. Implement the provider call in `src/llm/remote.py`

##  Understanding the Output

### Fitness Metrics

**Pacman**:
- **Score**: Points earned in the game (higher is better)
- **Survival Time**: Timesteps alive (higher is better)
- **Steps**: Total moves made (lower is better)
- **Fitness**: Weighted combination: `0.6 × score + 0.3 × survival - 0.1 × steps`

**Matrix**:
- **Correctness**: Fraction of test cases passed (0.0 to 1.0)
- **Operations**: Estimated count of `*` and `+` operations (lower is better)
- **Fitness**: Combined score: `0.7 × correctness + 0.3 × ops_score`

### Generated Files
- `outputs/{problem}_fitness.png`: Fitness evolution plot
- `outputs/{problem}_fitness.csv`: Detailed results table
- `data/cache/fitness_cache.jsonl`: Persistent fitness cache

##  Advanced Configuration

### Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_generations` | 10 | Number of evolution cycles |
| `population_size` | 8 | Candidates per generation |
| `top_k` | 3 | Elite candidates preserved |
| `mutation_rate` | 0.35 | Probability of mutation |
| `seed` | 42 | Random seed for reproducibility |

### Mutation Operations

1. **Random Perturb**: Modifies numeric literals
2. **Line Swap**: Exchanges two random code lines
3. **Template Replace**: Injects code from template library
4. **LLM Improve**: AI-guided refinement (in `llm_guided` mode)

##  Troubleshooting

### Common Issues

**"Module not found" errors**:
```bash
# Ensure virtual environment is activated
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

##  Outputs

All results are saved to the `outputs/` directory:
- **Plots**: PNG visualizations of fitness over generations
- **CSV Files**: Detailed tabular data for analysis
- **Cache**: `data/cache/fitness_cache.jsonl` stores evaluated candidates for efficiency

##  Contributing

This is an academic research project. To extend:
1. Add new problems in `src/evaluators/`
2. Implement new mutation strategies in `src/engine/mutations.py`
3. Integrate different LLM providers in `src/llm/`

##  License

Academic research project for the UC Berkeley Course.

##  Acknowledgments

- Inspired by AlphaEvolve and evolutionary computation research
- UC Berkeley Pacman AI project for the benchmark domain
- Built with Streamlit, FastAPI, and modern Python ecosystem
