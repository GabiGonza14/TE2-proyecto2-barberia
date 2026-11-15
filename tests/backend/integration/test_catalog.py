import asyncio
from numbers import Real

import httpx
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.errors import VALIDATION_ERROR, DomainError
from app.main import app, domain_error_handler

error_app = FastAPI()
error_app.add_exception_handler(DomainError, domain_error_handler)


@error_app.get("/__test__/domain-error", include_in_schema=False)
def raise_domain_error() -> None:
    raise DomainError(
        VALIDATION_ERROR, "El nombre no es válido", field="client_name"
    )


async def get(path: str, target_app: FastAPI = app) -> httpx.Response:
    transport = httpx.ASGITransport(app=target_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.get(path)


def test_list_barbers_only_active(engine: Engine) -> None:
    response = asyncio.run(get("/api/v1/barbers"))

    assert response.status_code == 200
    barbers = response.json()
    assert [barber["name"] for barber in barbers] == [
        "Carlos",
        "Luis",
        "Andrés",
    ]
    assert all(set(barber) == {"id", "name"} for barber in barbers)
    assert all(isinstance(barber["id"], int) for barber in barbers)


def test_inactive_barber_not_listed(engine: Engine) -> None:
    with engine.connect() as conn:
        carlos_id = conn.execute(
            text("SELECT id FROM barbers WHERE name = 'Carlos'")
        ).scalar_one()

    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE barbers SET active = false WHERE id = :id"),
                {"id": carlos_id},
            )

        response = asyncio.run(get("/api/v1/barbers"))

        assert response.status_code == 200
        assert "Carlos" not in [barber["name"] for barber in response.json()]
    finally:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE barbers SET active = true WHERE id = :id"),
                {"id": carlos_id},
            )


def test_list_services(engine: Engine) -> None:
    response = asyncio.run(get("/api/v1/services"))

    assert response.status_code == 200
    services = response.json()
    assert [service["name"] for service in services] == [
        "Corte",
        "Barba",
        "Corte+Barba",
        "Diseño/Fade",
    ]

    expected = {
        "Corte": (30, 8.0),
        "Barba": (20, 5.0),
        "Corte+Barba": (45, 12.0),
        "Diseño/Fade": (40, 10.0),
    }
    for service in services:
        duration_min, price = expected[service["name"]]
        assert service["duration_min"] == duration_min
        assert isinstance(service["price"], Real)
        assert service["price"] == price
        assert set(service) == {"id", "name", "duration_min", "price"}


def test_domain_error_format(engine: Engine) -> None:
    response = asyncio.run(get("/__test__/domain-error", target_app=error_app))

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "El nombre no es válido",
            "details": {"field": "client_name"},
        }
    }
