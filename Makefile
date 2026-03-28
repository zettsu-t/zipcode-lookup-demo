.PHONY: install install-hooks install-playwright format lint \
        test test-e2e test-e2e-http test-e2e-browser test-spec test-all schema \
        audit audit-code audit-deps \
        up down build dev dev-backend dev-frontend dev-down dev-migrate

VENV   = .venv
PY     = $(CURDIR)/$(VENV)/bin/python
RUFF   = $(CURDIR)/$(VENV)/bin/ruff

# ── セットアップ ───────────────────────────────────────────────

install:
	uv venv
	uv pip install -e "backend[dev]" -e "frontend[dev]" ruff pyyaml schemathesis requests pytest-playwright bandit pip-audit
	$(MAKE) install-hooks

install-hooks:
	cp scripts/hooks/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

install-playwright:
	$(PY) -m playwright install chromium

# ── コード品質 ─────────────────────────────────────────────────

format:
	$(RUFF) format backend/ frontend/

lint:
	$(RUFF) check backend/ frontend/

# ── テスト ────────────────────────────────────────────────────

test:
	$(PY) -m pytest -v

test-e2e-http:
	$(PY) -m pytest tests/e2e/test_http.py -v

test-e2e-browser:
	$(PY) -m pytest tests/e2e/test_browser.py -v

test-e2e: test-e2e-http test-e2e-browser

test-spec:
	bash scripts/test_spec.sh

test-all:
	$(MAKE) test
	$(MAKE) test-e2e
	$(MAKE) test-spec

# ── セキュリティ監査 ──────────────────────────────────────────

audit-code:
	$(PY) -m bandit -r backend/ frontend/ -c pyproject.toml

audit-deps:
	# --skip-editable: ローカルパッケージ(backend/frontend)はPyPI未公開のためスキップ
	# --ignore-vuln CVE-2026-4539: pygments の未修正CVE。schemathesis経由の開発依存のみ、本番不使用。
	#   修正版リリース後に削除すること。
	$(PY) -m pip_audit --skip-editable --ignore-vuln CVE-2026-4539

audit: audit-code audit-deps

# ── OpenAPI スキーマ生成 ───────────────────────────────────────

schema:
	$(PY) scripts/export_openapi.py > docs/openapi_spec.yaml

# ── Docker ────────────────────────────────────────────────────

up:
	docker compose up

down:
	docker compose down

build:
	docker compose build

# ── ローカル開発（Docker不使用） ──────────────────────────────

dev-migrate:
	cd frontend && $(PY) manage.py migrate

dev-backend:
	@echo "Starting backend on http://localhost:8001 ..."
	cd backend && $(PY) -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload & echo $$! > $(CURDIR)/.backend.pid
	@echo "Backend PID: $$(cat .backend.pid)"

dev-frontend:
	@echo "Starting frontend on http://localhost:8000 ..."
	cd frontend && $(PY) manage.py runserver 127.0.0.1:8000 & echo $$! > $(CURDIR)/.frontend.pid
	@echo "Frontend PID: $$(cat .frontend.pid)"

dev: dev-backend dev-frontend
	@echo "Both services started. Run 'make dev-down' to stop."

dev-down:
	@if [ -f .backend.pid ]; then \
		kill $$(cat .backend.pid) 2>/dev/null && echo "Backend stopped." || echo "Backend already stopped."; \
		rm -f .backend.pid; \
	else \
		echo "No backend PID file found."; \
	fi
	@if [ -f .frontend.pid ]; then \
		kill $$(cat .frontend.pid) 2>/dev/null && echo "Frontend stopped." || echo "Frontend already stopped."; \
		rm -f .frontend.pid; \
	else \
		echo "No frontend PID file found."; \
	fi
