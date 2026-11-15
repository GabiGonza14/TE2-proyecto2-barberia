import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3] / "src" / "backend"

HEALTH_CHECK = """
import asyncio

import httpx

from app.main import app


async def main() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


asyncio.run(main())
"""


def test_health_works_without_db_url() -> None:
    env = os.environ.copy()
    env.pop("DB_URL", None)
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(BACKEND_DIR), env.get("PYTHONPATH")])
    )

    result = subprocess.run(
        [sys.executable, "-c", HEALTH_CHECK],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
