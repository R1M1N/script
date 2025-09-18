.PHONY: install run fmt lint test

install:
	pip install -r requirements.txt

run:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

fmt:
	python -m pip install ruff
	ruff check --select I --fix .
	ruff format .

test:
	pytest -q
