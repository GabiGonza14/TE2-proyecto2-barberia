import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

BACKEND_DIR = Path(__file__).resolve().parents[2] / "src" / "backend"


def run_alembic(*args: str, db_url: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env={**os.environ, "DB_URL": db_url},
        check=True,
    )


@pytest.fixture(scope="session")
def db_url() -> str:
    url = os.environ.get("DB_URL")
    if not url:
        pytest.skip("DB_URL no está configurada")
    return url


@pytest.fixture(scope="session")
def migrated_db(db_url: str) -> str:
    run_alembic("upgrade", "head", db_url=db_url)
    return db_url


@pytest.fixture(scope="session")
def engine(migrated_db: str):
    eng = create_engine(migrated_db)
    yield eng
    eng.dispose()


@pytest.fixture
def clean_bookings(engine: Engine):
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE bookings RESTART IDENTITY CASCADE"))
    yield
