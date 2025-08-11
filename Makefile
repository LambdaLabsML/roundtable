.PHONY: install test clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-test.txt

install-all:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-verbose:
	pytest tests/ -vv -s

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

run:
	python main.py