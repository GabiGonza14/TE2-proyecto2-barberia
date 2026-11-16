"""Issue #15 · CORS limitado al origen del frontend (architecture.md §5)."""

import asyncio

import httpx

from app.main import app

FRONTEND = "http://localhost:5173"


def request(method: str, url: str, headers: dict[str, str]) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, headers=headers)

    return asyncio.run(send())


def test_cors_allows_frontend_origin() -> None:
    response = request("GET", "/health", {"Origin": FRONTEND})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == FRONTEND


def test_cors_preflight_allows_booking_post() -> None:
    response = request(
        "OPTIONS",
        "/api/v1/bookings",
        {
            "Origin": FRONTEND,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == FRONTEND
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_preflight_allows_admin_key_header() -> None:
    """T11 enviará X-Admin-Key desde el navegador a /admin/agenda (RF-14)."""
    response = request(
        "OPTIONS",
        "/api/v1/admin/agenda",
        {
            "Origin": FRONTEND,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-admin-key",
        },
    )

    assert response.status_code == 200
    assert "x-admin-key" in response.headers.get("access-control-allow-headers", "").lower()


def test_cors_rejects_unknown_origin() -> None:
    response = request("GET", "/health", {"Origin": "http://evil.example"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_rejects_unknown_origin() -> None:
    response = request(
        "OPTIONS",
        "/api/v1/bookings",
        {"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"},
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
