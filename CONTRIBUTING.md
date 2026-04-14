# Contributing to Evolve

Thank you for your interest in contributing to the Evolve project! This document provides guidelines for extending and improving the system.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/evolve.git
   cd evolve
   ```

2. **Set Up Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run Tests** (when available)
   ```bash
   pytest tests/
   ```

## Project Architecture

### Core Components

- **Engine** (`src/engine/`): Evolution algorithm implementation
- **Evaluators** (`src/evaluators/`): Fitness evaluation for different problems
- **LLM** (`src/llm/`): Language model integration
- **Cache** (`src/cache/`): Persistent fitness caching
- **Utils** (`src/utils/`): Configuration and utilities

### Adding a New Problem Domain

1. **Create an Evaluator** in `src/evaluators/`:

```python
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class YourProblemConfig:
    param1: int = 10
    param2: float = 0.5

class YourProblemEvaluator:
    def __init__(self, cfg: YourProblemConfig):
        self.cfg = cfg
    
    def evaluate(self, code: str) -> Tuple[float, Dict[str, float]]:
        # Your evaluation logic
        fitness = 0.0
        metrics = {"metric1": 0.0, "metric2": 0.0}
        return fitness, metrics
```

2. **Create a Wrapper** in `src/evaluators/wrappers.py`:

```python
@dataclass
class YourProblemWrapper:
    evaluator: YourProblemEvaluator
    
    def evaluate(self, code: str) -> Tuple[float, dict]:
        return self.evaluator.evaluate(code)
```

3. **Add to Runner** in `src/engine/runner.py`:

```python
elif problem == "your_problem":
    templates = load_templates("./data/templates", pattern="your_problem_*.py")
    base_code = _load_base_code(
        "./data/templates/your_problem_base.py",
        fallback="./data/templates/your_problem_base.py",
    )
    evaluator = YourProblemWrapper(
        YourProblemEvaluator(
            YourProblemConfig(
                param1=config.get("your_problem", "param1"),
                param2=config.get("your_problem", "param2"),
            )
        )
    )
    prompt = "Optimize for your problem domain."
```

4. **Update Config** in `config.yaml`:

```yaml
your_problem:
  enabled: true
  param1: 10
  param2: 0.5
```

5. **Add Base Template** in `data/templates/your_problem_base.py`

### Adding New Mutation Operators

Edit `src/engine/mutations.py`:

```python
def your_mutation(code: str) -> str:
    # Your mutation logic
    return modified_code

def mutate(code: str, templates: List[str]) -> str:
    ops = [
        random_perturb_parameters,
        swap_two_lines,
        lambda c: replace_fragment(c, templates),
        your_mutation,  # Add your operator
    ]
    op = random.choice(ops)
    return op(code)
```

### Integrating a New LLM Provider

1. **Extend Base Class** in `src/llm/your_provider.py`:

```python
from .base import LLMClient

class YourProviderLLM(LLMClient):
    def __init__(self, api_key: str = None, model: str = "default"):
        self.api_key = api_key
        self.model = model
    
    def improve(self, prompt: str, code: str) -> str:
        # Call your LLM API
        response = your_api_call(prompt, code)
        return response
```

2. **Update Runner** to use your provider:

```python
if config.get("llm", "provider") == "your_provider":
    llm = YourProviderLLM(
        api_key=os.getenv("YOUR_API_KEY"),
        model=config.get("llm", "model_name")
    )
```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings for public functions and classes
- Keep functions focused and concise

### Example:

```python
def evaluate_fitness(code: str, test_cases: List[TestCase]) -> float:
    """
    Evaluate the fitness of a code candidate.
    
    Args:
        code: The code string to evaluate
        test_cases: List of test cases to run
    
    Returns:
        Fitness score between 0.0 and 1.0
    """
    pass
```

## Testing

Create tests in the `tests/` directory:

```python
import pytest
from src.evaluators.matrix import MatrixEvaluator, MatrixConfig

def test_matrix_evaluator_correctness():
    evaluator = MatrixEvaluator(MatrixConfig(samples=10))
    code = """
def matmul3(a, b):
    # Correct implementation
    ...
    """
    fitness, metrics = evaluator.evaluate(code)
    assert metrics["correct"] == 1.0
```

## Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update config.yaml.example for new configuration options

## Submitting Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes with clear commit messages:
   ```bash
   git commit -m "Add support for XYZ problem domain"
   ```

3. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Review Process

- All submissions require review
- Address feedback constructively
- Ensure tests pass
- Update documentation as needed

## Questions?

Open an issue on GitHub or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
