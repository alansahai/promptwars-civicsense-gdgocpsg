.PHONY: install test lint typecheck run format smoke

install:
	pip install -r requirements-dev.txt

test:
	pytest -v --cov=app --cov-report=term-missing --cov-fail-under=90 tests/

lint:
	ruff check .

typecheck:
	mypy app/

format:
	ruff format .

run:
	uvicorn app.main:app --reload --port 8000

smoke:
	python scripts/smoke_test.py http://127.0.0.1:8000
