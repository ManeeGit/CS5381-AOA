#!/usr/bin/env bash

# Quick start script for Evolve project
# This script demonstrates a simple experiment run

set -e

echo "=== Evolve: Quick Start Script ==="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "=== Running Matrix Multiplication Experiment ==="
echo "This will evolve code for 3x3 matrix multiplication"
echo ""

# Run a simple matrix experiment
python3 -c "
from src.utils.config import Config
from src.engine.runner import run_experiment, history_to_df

# Load config
cfg = Config.load('./config.yaml')

# Override for quick demo
cfg.raw['project']['max_generations'] = 5
cfg.raw['project']['population_size'] = 6

print('Running evolution with 5 generations, population size 6...')
print('Problem: Matrix Multiplication (3x3)')
print('-' * 60)

# Run experiment
results = run_experiment(cfg, problem='matrix')

# Display results
df = history_to_df(results)
print('')
print('Results Summary:')
print('=' * 60)
for mode in results.keys():
    final_gen = results[mode].history[-1]
    best = final_gen.best
    print(f'{mode:20s}: fitness={best.fitness:.4f}, correct={best.metrics.get(\"correct\", 0):.2f}, ops={best.metrics.get(\"ops\", 0):.0f}')

print('')
print('=' * 60)
print('Experiment complete! Check ./outputs/ for detailed results.')
print('')
print('To run the full interactive UI:')
print('  streamlit run app.py')
print('')
print('To run the API server:')
print('  uvicorn api:app --reload')
"

echo ""
echo "=== Quick Start Complete ==="
