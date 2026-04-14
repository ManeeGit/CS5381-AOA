#!/usr/bin/env python3
"""
Quick integration test for the Evolve project.
Tests basic functionality of all major components.
"""

import sys

def main():
    print('Testing project imports and basic functionality...')
    print('=' * 60)
    
    all_passed = True

    # Test imports
    try:
        from src.utils.config import Config
        print(' Config module imported')
    except Exception as e:
        print(f' Config import failed: {e}')
        all_passed = False

    try:
        from src.engine.evolve import Evolver, EvolutionConfig
        print(' Evolution engine imported')
    except Exception as e:
        print(f' Evolution engine import failed: {e}')
        all_passed = False

    try:
        from src.evaluators.matrix import MatrixEvaluator, MatrixConfig
        print(' Matrix evaluator imported')
    except Exception as e:
        print(f' Matrix evaluator import failed: {e}')
        all_passed = False

    try:
        from src.llm.local import LocalLLM
        print(' LLM module imported')
    except Exception as e:
        print(f' LLM module import failed: {e}')
        all_passed = False

    try:
        from src.cache.cache import FitnessCache
        print(' Cache module imported')
    except Exception as e:
        print(f' Cache module import failed: {e}')
        all_passed = False

    # Test configuration loading
    try:
        from src.utils.config import Config
        cfg = Config.load('./config.yaml')
        print(f' Config loaded: {cfg.get("project", "name")}')
    except Exception as e:
        print(f' Config loading failed: {e}')
        all_passed = False

    # Test matrix evaluator
    try:
        from src.evaluators.matrix import MatrixEvaluator, MatrixConfig
        evaluator = MatrixEvaluator(MatrixConfig(samples=2))
        test_code = '''
def matmul3(a, b):
    res = [[0, 0, 0] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                res[i][j] += a[i][k] * b[k][j]
    return res
'''
        fitness, metrics = evaluator.evaluate(test_code)
        print(f' Matrix evaluator works: fitness={fitness:.2f}, correct={metrics["correct"]:.2f}')
    except Exception as e:
        print(f' Matrix evaluator test failed: {e}')
        all_passed = False

    # Test cache
    try:
        from src.cache.cache import FitnessCache
        cache = FitnessCache('./data/cache')
        test_code = 'def test(): return 42'
        cache.set(test_code, 1.0, {'test': 1.0})
        cached = cache.get(test_code)
        assert cached is not None
        print(' Cache works: stored and retrieved fitness')
    except Exception as e:
        print(f' Cache test failed: {e}')
        all_passed = False

    print('=' * 60)
    if all_passed:
        print(' All basic tests passed!')
        print('')
        print('Project is ready to use. Try:')
        print('  streamlit run app.py')
        print('  ./quick_start.sh')
        print('  make run-ui')
        return 0
    else:
        print(' Some tests failed. Check the errors above.')
        return 1

if __name__ == '__main__':
    sys.exit(main())
