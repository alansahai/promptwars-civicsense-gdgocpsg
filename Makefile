.PHONY: install test lint run format smoke

install:
	pip install -r requirements-dev.txt

test:
	pytest -v --asyncio-mode=auto tests/

lint:
	ruff check .

format:
	ruff format .

run:
	uvicorn app.main:app --reload --port 8000

smoke:
	python scripts/smoke_test.py http://127.0.0.1:8000
