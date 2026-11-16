from datetime import datetime

from app.domain.rules import TZ


def get_now() -> datetime:
    return datetime.now(TZ)
