"""Ensure alembic_version is in a sane state before `alembic upgrade head`.

Legacy deploys used `Base.metadata.create_all` from `init_db()` to build the
schema, bypassing Alembic entirely — so `alembic_version` never got populated.
A fresh `alembic upgrade head` on such a database tries to re-create tables
that already exist and crashes the container.

This script:
  1. Detects whether `alembic_version` is already tracking the DB.
  2. If not, checks whether the tables from the last pre-existing revision
     are present (uses `invoices` as the marker — added in a2b3c4d5e6f7).
  3. If yes, runs `alembic stamp a2b3c4d5e6f7` so `upgrade head` only runs
     *new* revisions on top of the existing schema.
  4. If the DB is genuinely empty it does nothing; `alembic upgrade head`
     will then build everything from scratch.

Runs before `alembic upgrade head` in docker-entrypoint.sh.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys

from sqlalchemy import text

from app.database import engine

# Last revision that was implicitly applied via `Base.metadata.create_all`.
# Bump this if you add a new migration that should be considered "baseline".
LAST_BASELINE_REVISION = "a2b3c4d5e6f7"

# Marker table introduced at LAST_BASELINE_REVISION — if it exists the schema
# is already at that revision.
MARKER_TABLE = "invoices"


async def _main() -> int:
    # Postgres-specific: to_regclass returns NULL when a relation doesn't exist.
    # Both checks are read-only so they're safe to run in any state.
    async with engine.connect() as conn:
        has_alembic_version = bool(
            (await conn.execute(text("SELECT to_regclass('public.alembic_version')"))).scalar()
        )
        has_marker = bool(
            (await conn.execute(text(f"SELECT to_regclass('public.{MARKER_TABLE}')"))).scalar()
        )

    if has_alembic_version:
        print("[bootstrap] alembic_version already tracked — nothing to do", flush=True)
        return 0

    if not has_marker:
        print("[bootstrap] empty DB — alembic upgrade will create everything", flush=True)
        return 0

    print(
        f"[bootstrap] existing schema without alembic_version — stamping to {LAST_BASELINE_REVISION}",
        flush=True,
    )
    subprocess.check_call(["alembic", "stamp", LAST_BASELINE_REVISION])
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
