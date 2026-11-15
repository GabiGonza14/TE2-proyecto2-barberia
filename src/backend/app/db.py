import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    db_url = os.environ.get("DB_URL")
    if not db_url:
        raise RuntimeError("DB_URL no está configurada")
    return create_engine(db_url)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker:
    return sessionmaker(bind=get_engine(), autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
