# Windows 에는 make 가 없습니다. 같은 일을 하는 ./dev.ps1 을 쓰세요.
# 프론트는 구글 드라이브에서 직접 돌리지 마세요 — dev.ps1 의 web-pull/web 을 보세요.
PY ?= python

.PHONY: dev api web test seed migrate notify fixtures sheet screens engine-check

dev:
	docker compose up -d postgres redis
	cd services/api && $(PY) -m uvicorn main:app --reload --port 8000 &
	cd apps/web && npm run dev

api:
	cd services/api && $(PY) -m uvicorn main:app --reload --port 8000

web:
	cd apps/web && npm run dev

test:
	$(PY) -m pytest tests -q

fixtures:
	$(PY) tools/make_fixtures.py

sheet:
	$(PY) tools/fixture_sheet.py 대조표.md

screens:
	$(PY) tools/screen_graph.py

migrate:
	$(PY) -m alembic upgrade head

seed:
	cd services/api && $(PY) -m scripts.seed

notify:
	cd services/api && $(PY) -m scripts.notify

# ★ 2주차 관문 — 셋 다 통과해야 다음 단계로 갑니다
engine-check:
	$(PY) -m pytest tests -q
	$(PY) tools/distribution.py
	$(PY) tools/dup_rate.py
