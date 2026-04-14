.PHONY: help install run-ui run-api run-batch clean test lint format check

help:
	@echo "Evolve Project - Available Commands:"
	@echo ""
	@echo "  make install       - Set up virtual environment and install dependencies"
	@echo "  make run-ui        - Start Streamlit web interface"
	@echo "  make run-api       - Start FastAPI server"
	@echo "  make run-batch     - Run batch experiments"
	@echo "  make quick         - Run quick start demo"
	@echo "  make clean         - Remove cache, outputs, and build files"
	@echo "  make lint          - Check code style (requires pylint)"
	@echo "  make format        - Auto-format code (requires black)"
	@echo "  make check         - Run syntax checks"
	@echo "  make frontend      - Build frontend TypeScript"
	@echo ""

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Virtual environment created and dependencies installed"
	@echo "  Activate with: source .venv/bin/activate"

run-ui:
	. .venv/bin/activate && streamlit run app.py

run-api:
	. .venv/bin/activate && uvicorn api:app --reload

run-batch:
	. .venv/bin/activate && python run_experiment.py

quick:
	./quick_start.sh

clean:
	rm -rf outputs/*.png outputs/*.csv
	rm -rf data/cache/*.jsonl
	rm -rf logs/*.log
	rm -rf __pycache__ src/__pycache__ src/*/__pycache__
	rm -rf .pytest_cache
	rm -rf frontend/dist frontend/node_modules
	@echo "✓ Cleaned cache, outputs, and build files"

clean-all: clean
	rm -rf .venv
	@echo "✓ Removed virtual environment"

lint:
	. .venv/bin/activate && pylint src/ app.py api.py run_experiment.py || true

format:
	. .venv/bin/activate && black src/ app.py api.py run_experiment.py || true

check:
	. .venv/bin/activate && python3 -m py_compile app.py api.py run_experiment.py
	. .venv/bin/activate && python3 -m py_compile src/**/*.py
	@echo "✓ Syntax check passed"

frontend:
	cd frontend && npm install && npm run build
	@echo "✓ Frontend built"

test:
	@echo "Test suite not yet implemented"
	@echo "See CONTRIBUTING.md for creating tests"

# Development helpers
dev-install: install
	. .venv/bin/activate && pip install black pylint pytest ipython

watch-ui:
	. .venv/bin/activate && streamlit run app.py --server.runOnSave true

serve: run-api

ui: run-ui
