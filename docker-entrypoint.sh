#!/usr/bin/env bash
# Docker entrypoint — runs DB migrations before handing off to the app server.
#
# Alembic takes a Postgres advisory lock so concurrent containers during a
# rolling deploy don't race. `set -e` means any migration failure aborts the
# boot so Coolify marks the deploy as failed rather than starting a server
# against a stale schema.
set -euo pipefail

# Legacy deploys init'd the schema via `Base.metadata.create_all` without ever
# writing to `alembic_version`. A plain `alembic upgrade head` on those DBs
# would try to re-create existing tables and crash. The bootstrap stamps the
# baseline revision when it detects this state so only *new* migrations run.
echo "[entrypoint] bootstrapping alembic state..."
python -m app.bootstrap_alembic

echo "[entrypoint] running alembic upgrade head..."
alembic upgrade head
echo "[entrypoint] migrations done — starting uvicorn"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
