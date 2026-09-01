.PHONY: dev test seed engine-check

dev:
	docker compose up -d postgres redis
	cd services/api && poetry run uvicorn main:app --reload --port 8000 &
	cd apps/web && npm run dev

test:
	cd services/api && poetry run pytest ../../tests -q

seed:
	cd services/api && poetry run python -m scripts.seed

engine-check:
	poetry run pytest tests/test_calendar.py -q
	poetry run python tools/distribution.py
	poetry run python tools/dup_rate.py
